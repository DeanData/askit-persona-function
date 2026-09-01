#!/usr/bin/env python3
"""Compute METRIC.md's distance-to-real fidelity measures on generated text.

Reuses the exact 10-feature pipeline from the Phase 1 separation pre-check
(src/separation_precheck.py) — not re-derived. Real reference statistics come
from the eval pool (data/finance_forums/eval/, disjoint from the few-shot pool
used in prompts). For each generated condition supplied:

  - centroid fidelity(A)      = dist(centroid_gen(A), centroid_real(A)) / W_real(A)
  - within-variation fidelity(A) = (W_gen(A) - W_real(A)) / W_real(A)      [signed]
  - between-separation fidelity  = (B_gen - B_real) / B_real               [signed]

All distances computed in one shared standardized feature space (a single
StandardScaler fit across every text passed to this run — real eval texts and
all supplied generated conditions together), per METRIC.md section 2/5.

Also runs the required self-labeling check (METRIC.md section 6) and reports
bootstrap CIs (resample with replacement within each audience's generated set,
n=1000) on every per-audience fidelity number and on the aggregate MARE.

Usage:
    python3 src/compute_metrics.py --conditions baseline:data/generations/dev/baseline.jsonl
    python3 src/compute_metrics.py --conditions baseline:...,fewshot:...
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from separation_precheck import features, clean_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "finance_forums" / "eval"
AUDIENCES = ["personalfinance", "wallstreetbets", "fatFIRE", "thetagang", "povertyfinance"]
FEATURE_KEYS = [
    "avg_sentence_len", "ttr_guiraud", "avg_word_len", "first_person_rate",
    "hedge_rate", "core_punct_rate", "emoji_rate", "exclaim_rate",
    "allcaps_rate", "meme_token_rate",
]
N_BOOTSTRAP = 1000
SEED = 42

SELF_LABEL_PATTERNS = {
    aud: re.compile(
        r"\br/" + re.escape(aud) + r"\b"
        r"|\b" + re.escape(aud.lower()) + r"\b"
        r"|as an? " + re.escape(aud.lower()) + r"\b",
        re.IGNORECASE,
    )
    for aud in AUDIENCES
}
# thetagang/wsb-style short aliases worth checking too
EXTRA_ALIASES = {
    "wallstreetbets": [r"\bwsb\b"],
    "fatFIRE": [r"\bfat\s?fire\b"],
}


def feature_vector(text_features):
    return np.array([text_features[k] for k in FEATURE_KEYS])


def load_eval_texts(audience):
    texts = []
    with open(EVAL_DIR / f"{audience}.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            texts.append(clean_text(rec["title"], rec["selftext"]))
    return texts


def load_generated(path, audience, exclude_self_labeled=True):
    """Returns (kept_texts, n_flagged). Self-labeled texts are excluded from the
    fidelity computation by default -- a model could otherwise inflate its
    separation score simply by naming the audience, which is exactly the
    shortcut this check exists to catch (METRIC.md section 6)."""
    texts, n_flagged = [], 0
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            if rec["audience"] != audience:
                continue
            if check_self_labeling(rec["text"], audience):
                n_flagged += 1
                if exclude_self_labeled:
                    continue
            texts.append(rec["text"])
    return texts, n_flagged


def check_self_labeling(text, audience):
    if SELF_LABEL_PATTERNS[audience].search(text):
        return True
    for pat in EXTRA_ALIASES.get(audience, []):
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def avg_pairwise_dist(X):
    if len(X) < 2:
        return 0.0
    diffs = X[:, None, :] - X[None, :, :]
    dists = np.sqrt((diffs ** 2).sum(axis=-1))
    iu = np.triu_indices(len(X), k=1)
    return dists[iu].mean()


def cross_pairwise_dist(X, Y):
    diffs = X[:, None, :] - Y[None, :, :]
    dists = np.sqrt((diffs ** 2).sum(axis=-1))
    return dists.mean()


def between_stat(X_by_audience, audiences):
    pair_means = []
    for a, b in combinations(audiences, 2):
        pair_means.append(cross_pairwise_dist(X_by_audience[a], X_by_audience[b]))
    return float(np.mean(pair_means))


def bootstrap_ci(values_fn, X_by_audience, audiences, n_bootstrap=N_BOOTSTRAP, seed=SEED):
    """values_fn(sampled_X_by_audience) -> dict of stat_name -> value (per audience or aggregate)."""
    rng = np.random.default_rng(seed)
    samples = defaultdict(list)
    for _ in range(n_bootstrap):
        sampled = {}
        for a in audiences:
            X = X_by_audience[a]
            idx = rng.integers(0, len(X), size=len(X))
            sampled[a] = X[idx]
        for stat_name, val in values_fn(sampled).items():
            samples[stat_name].append(val)
    ci = {}
    for stat_name, vals in samples.items():
        vals = np.array(vals)
        ci[stat_name] = (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))
    return ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", required=True,
                     help="comma-separated name:path pairs, e.g. baseline:data/generations/dev/baseline.jsonl")
    ap.add_argument("--audiences", default=",".join(AUDIENCES))
    args = ap.parse_args()

    audiences = args.audiences.split(",")
    conditions = {}
    for spec in args.conditions.split(","):
        name, path = spec.split(":", 1)
        conditions[name] = path

    # --- load raw texts; self-labeled texts are excluded from gen_texts and counted ---
    real_texts = {a: load_eval_texts(a) for a in audiences}
    gen_texts = {}
    flagged_counts = {}
    for cond, path in conditions.items():
        gen_texts[cond] = {}
        flagged_counts[cond] = {}
        for a in audiences:
            texts, n_flagged = load_generated(path, a)
            gen_texts[cond][a] = texts
            flagged_counts[cond][a] = n_flagged

    print("=== self-labeling check (flagged texts excluded from fidelity computation below) ===")
    for cond in conditions:
        total_flagged = sum(flagged_counts[cond].values())
        total_seen = sum(flagged_counts[cond][a] + len(gen_texts[cond][a]) for a in audiences)
        print(f"{cond}: {total_flagged} / {total_seen} flagged")
        for a in audiences:
            if flagged_counts[cond][a]:
                print(f"  {a}: {flagged_counts[cond][a]} flagged, {len(gen_texts[cond][a])} kept")

    # --- fit ONE scaler across everything: real eval texts + all supplied generated conditions ---
    all_feature_dicts = []
    for a in audiences:
        for t in real_texts[a]:
            core, slang = features(t)
            all_feature_dicts.append({**core, **slang})
    for cond in conditions:
        for a in audiences:
            for t in gen_texts[cond][a]:
                core, slang = features(t)
                all_feature_dicts.append({**core, **slang})

    all_matrix = np.array([[d[k] for k in FEATURE_KEYS] for d in all_feature_dicts])
    mean = all_matrix.mean(axis=0)
    std = all_matrix.std(axis=0)
    std[std == 0] = 1.0

    def standardize_texts(texts):
        vecs = []
        for t in texts:
            core, slang = features(t)
            v = feature_vector({**core, **slang})
            vecs.append((v - mean) / std)
        return np.array(vecs)

    real_X = {a: standardize_texts(real_texts[a]) for a in audiences}
    W_real = {a: avg_pairwise_dist(real_X[a]) for a in audiences}
    centroid_real = {a: real_X[a].mean(axis=0) for a in audiences}
    B_real = between_stat(real_X, audiences)

    print(f"\n=== real reference (eval pool, n per audience: {[len(real_texts[a]) for a in audiences]}) ===")
    print(f"B_real (between, real) = {B_real:.4f}")
    for a in audiences:
        print(f"  W_real[{a}] = {W_real[a]:.4f}")

    for cond in conditions:
        gen_X = {a: standardize_texts(gen_texts[cond][a]) for a in audiences}
        W_gen = {a: avg_pairwise_dist(gen_X[a]) for a in audiences}
        centroid_gen = {a: gen_X[a].mean(axis=0) for a in audiences}
        B_gen = between_stat(gen_X, audiences)

        centroid_fid = {a: float(np.linalg.norm(centroid_gen[a] - centroid_real[a]) / max(W_real[a], 1e-9)) for a in audiences}
        within_fid = {a: float((W_gen[a] - W_real[a]) / max(W_real[a], 1e-9)) for a in audiences}
        between_fid = float((B_gen - B_real) / max(B_real, 1e-9))

        mare_within = float(np.mean([abs(within_fid[a]) for a in audiences]))
        mare_centroid = float(np.mean([abs(centroid_fid[a]) for a in audiences]))

        print(f"\n=== condition: {cond} ===")
        print(f"n per audience: {[len(gen_texts[cond][a]) for a in audiences]}")
        print(f"{'audience':<16} {'centroid_fid':>13} {'within_fid':>11}")
        for a in audiences:
            print(f"{a:<16} {centroid_fid[a]:>13.3f} {within_fid[a]:>11.3f}")
        print(f"between_fid (global) = {between_fid:.3f}")
        print(f"MARE (within, aggregate)   = {mare_within:.3f}")
        print(f"MARE (centroid, aggregate) = {mare_centroid:.3f}")

        # bootstrap CIs
        def stat_fn(sampled):
            out = {}
            for a in audiences:
                Wg = avg_pairwise_dist(sampled[a])
                cg = sampled[a].mean(axis=0)
                out[f"within_fid_{a}"] = (Wg - W_real[a]) / max(W_real[a], 1e-9)
                out[f"centroid_fid_{a}"] = np.linalg.norm(cg - centroid_real[a]) / max(W_real[a], 1e-9)
            Bg = between_stat(sampled, audiences)
            out["between_fid"] = (Bg - B_real) / max(B_real, 1e-9)
            return out

        ci = bootstrap_ci(stat_fn, gen_X, audiences)
        print(f"\nbootstrap 95% CIs ({N_BOOTSTRAP} resamples):")
        for a in audiences:
            lo, hi = ci[f"within_fid_{a}"]
            print(f"  within_fid[{a}]:   [{lo:.3f}, {hi:.3f}]")
        for a in audiences:
            lo, hi = ci[f"centroid_fid_{a}"]
            print(f"  centroid_fid[{a}]: [{lo:.3f}, {hi:.3f}]")
        lo, hi = ci["between_fid"]
        print(f"  between_fid:        [{lo:.3f}, {hi:.3f}]")


if __name__ == "__main__":
    main()

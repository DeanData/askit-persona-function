#!/usr/bin/env python3
"""Phase 1 empirical separation pre-check.

Before locking the audience list and designing the formal metric: do these
5 audiences actually separate in real text? Computes a small set of cheap
stylometric features, then checks separation with a nearest-centroid
classifier under two conditions:

  - "full"       — all features, including slang/meme-token markers
  - "core_only"  — the same features minus anything slang/surface-specific
                    (emoji, exclamation rate, all-caps, meme tokens)

If an audience separates in "core_only" too, its separation is more likely
structural, not just WSB-style surface slang. Reports per-audience recall
in both conditions, not just an aggregate, so a single weak audience shows
up rather than being averaged away.
"""
import json
import re
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestCentroid
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "finance_forums"
AUDIENCES = ["personalfinance", "wallstreetbets", "fatFIRE", "thetagang", "povertyfinance"]
SEED = 42

HEDGES = {"maybe", "perhaps", "might", "could", "seems", "seem", "think", "guess",
          "probably", "likely", "possibly", "sort", "kind", "somewhat", "roughly"}
FIRST_PERSON = {"i", "me", "my", "mine", "we", "us", "our", "ours"}
MEME_TOKENS = {"rocket", "moon", "stonk", "stonks", "yolo", "tendies", "ape", "apes",
               "hodl", "diamond", "hands", "gme", "wsb", "retard", "autist", "tits",
               "print", "loss", "gain", "yolo'd", "wife's", "boyfriend"}
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)
WORD_RE = re.compile(r"[A-Za-z']+")
SENT_SPLIT_RE = re.compile(r"[.!?]+")


def clean_text(title, selftext):
    text = f"{title}. {selftext}"
    text = re.sub(r"&amp;#x200B;|&amp;|&#x200B;", " ", text)
    text = re.sub(r"http\S+", " ", text)
    return text


def features(text):
    words = WORD_RE.findall(text)
    n = max(len(words), 1)
    lower_words = [w.lower() for w in words]
    sentences = [s for s in SENT_SPLIT_RE.split(text) if s.strip()]
    n_sent = max(len(sentences), 1)

    core = {
        "avg_sentence_len": n / n_sent,
        "ttr_guiraud": len(set(lower_words)) / (n ** 0.5),
        "avg_word_len": sum(len(w) for w in words) / n,
        "first_person_rate": 100 * sum(w in FIRST_PERSON for w in lower_words) / n,
        "hedge_rate": 100 * sum(w in HEDGES for w in lower_words) / n,
        "core_punct_rate": 100 * sum(c in ".,;:" for c in text) / max(len(text), 1),
    }
    slang = {
        "emoji_rate": 100 * len(EMOJI_RE.findall(text)) / n,
        "exclaim_rate": 100 * text.count("!") / max(len(text), 1),
        "allcaps_rate": 100 * sum(w.isupper() and len(w) >= 2 for w in words) / n,
        "meme_token_rate": 100 * sum(w in MEME_TOKENS for w in lower_words) / n,
    }
    return core, slang


def load_dataset():
    texts, labels = [], []
    for sub in AUDIENCES:
        with open(DATA_DIR / f"{sub}.jsonl") as f:
            for line in f:
                rec = json.loads(line)
                texts.append(clean_text(rec["title"], rec["selftext"]))
                labels.append(sub)
    return texts, labels


def run_condition(X, y, name):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )
    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    clf = NearestCentroid()
    clf.fit(X_train_s, y_train)
    preds = clf.predict(X_test_s)

    overall_acc = (preds == np.array(y_test)).mean()
    print(f"\n=== {name} ===")
    print(f"overall accuracy: {overall_acc:.3f}  (chance = {1/len(AUDIENCES):.3f}, n_test={len(y_test)})")
    print(f"{'audience':<16} {'recall':>8} {'n_test':>7}")
    y_test_arr = np.array(y_test)
    per_audience = {}
    for aud in AUDIENCES:
        mask = y_test_arr == aud
        recall = (preds[mask] == aud).mean() if mask.sum() else float("nan")
        per_audience[aud] = recall
        print(f"{aud:<16} {recall:>8.3f} {mask.sum():>7}")

    print(f"\nconfusion matrix (rows=true, cols=predicted):")
    header = "true\\pred".ljust(16) + "".join(a[:8].rjust(9) for a in AUDIENCES)
    print(header)
    for true_aud in AUDIENCES:
        mask = y_test_arr == true_aud
        row = [(preds[mask] == pred_aud).sum() for pred_aud in AUDIENCES]
        print(true_aud.ljust(16) + "".join(str(c).rjust(9) for c in row))

    return overall_acc, per_audience


def main():
    texts, labels = load_dataset()
    core_feats, slang_feats = [], []
    for t in texts:
        c, s = features(t)
        core_feats.append(c)
        slang_feats.append(s)

    core_keys = list(core_feats[0].keys())
    slang_keys = list(slang_feats[0].keys())

    X_core = np.array([[f[k] for k in core_keys] for f in core_feats])
    X_slang = np.array([[f[k] for k in slang_keys] for f in slang_feats])
    X_full = np.hstack([X_core, X_slang])

    print(f"n texts: {len(texts)}, core features: {core_keys}, slang features: {slang_keys}")

    full_acc, full_per = run_condition(X_full, labels, "FULL (core + slang/meme features)")
    core_acc, core_per = run_condition(X_core, labels, "CORE_ONLY (slang/meme features dropped)")

    print("\n=== summary: recall drop when slang features removed ===")
    print(f"{'audience':<16} {'full':>8} {'core_only':>10} {'drop':>8}")
    for aud in AUDIENCES:
        drop = full_per[aud] - core_per[aud]
        print(f"{aud:<16} {full_per[aud]:>8.3f} {core_per[aud]:>10.3f} {drop:>8.3f}")
    print(f"\noverall accuracy: full={full_acc:.3f}  core_only={core_acc:.3f}  drop={full_acc-core_acc:.3f}")


if __name__ == "__main__":
    main()

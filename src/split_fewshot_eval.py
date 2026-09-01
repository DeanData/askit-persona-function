#!/usr/bin/env python3
"""Split each audience's real-text sample into a disjoint few-shot pool and eval pool.

Why this exists: an earlier draft plan for the Part 2 few-shot improvement would have
pulled prompt examples from the same real-text files used to compute the METRIC.md
fidelity reference (real centroid / real within-variation / real between-separation).
That's train-on-your-eval-set — the improved condition could score better purely by
echoing text that is literally inside its own scoring reference, not because it
generalized audience voice. Caught before any generation ran (see WORKLOG.md).

Fix: draw a small, fixed-seed few-shot pool per audience now, disjoint from the eval
pool. The few-shot pool is used only in prompts (Part 2 improvement). The eval pool is
used only to compute real reference statistics in METRIC.md's fidelity measures. Never
the same posts in both roles.

Simplification, named explicitly (not hidden): the few-shot pool is a fixed per-audience
style primer — the same N_FEWSHOT posts are reused across every persona and both
elicitation contexts for that audience, not re-selected per persona or matched to
context. Cheaper, but a real scope simplification worth stating in the writeup.
"""
import json
from pathlib import Path

AUDIENCES = ["personalfinance", "wallstreetbets", "fatFIRE", "thetagang", "povertyfinance"]
N_FEWSHOT = 8
SEED = 42

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "finance_forums"
FEWSHOT_DIR = DATA_DIR / "fewshot"
EVAL_DIR = DATA_DIR / "eval"


def main():
    FEWSHOT_DIR.mkdir(exist_ok=True)
    EVAL_DIR.mkdir(exist_ok=True)

    summary = {}
    for sub in AUDIENCES:
        with open(DATA_DIR / f"{sub}.jsonl") as f:
            recs = [json.loads(line) for line in f]

        # deterministic split: rank by hash(id + seed), same mechanism already used
        # for the original sampling, so this is reproducible from the committed data
        recs_sorted = sorted(recs, key=lambda r: hash(f"{r['id']}{SEED}"))
        fewshot = recs_sorted[:N_FEWSHOT]
        evalset = recs_sorted[N_FEWSHOT:]

        fewshot_ids = {r["id"] for r in fewshot}
        eval_ids = {r["id"] for r in evalset}
        assert fewshot_ids.isdisjoint(eval_ids), f"{sub}: few-shot/eval overlap!"
        assert len(fewshot_ids) == N_FEWSHOT

        with open(FEWSHOT_DIR / f"{sub}.jsonl", "w") as f:
            for r in fewshot:
                f.write(json.dumps(r) + "\n")
        with open(EVAL_DIR / f"{sub}.jsonl", "w") as f:
            for r in evalset:
                f.write(json.dumps(r) + "\n")

        summary[sub] = {"fewshot": len(fewshot), "eval": len(evalset)}
        print(f"{sub}: fewshot={len(fewshot)} eval={len(evalset)} (disjoint, verified)")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

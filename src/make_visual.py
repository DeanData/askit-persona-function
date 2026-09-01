#!/usr/bin/env python3
"""The one required visual: baseline vs. best attempt (fewshot), within-audience
and between-audience fidelity, on dev and held-out audiences, with bootstrap
uncertainty. Reads the JSON summaries compute_metrics.py already produced --
no numbers recomputed here.
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "artifacts" / "baseline_vs_fewshot.png"

COND_COLORS = {"baseline": "#8896a8", "fewshot": "#4472c4"}
COND_LABELS = {"baseline": "baseline", "fewshot": "fewshot (best attempt)"}


def load(name):
    with open(ROOT / "artifacts" / "metrics" / f"{name}_summary.json") as f:
        return json.load(f)


def main():
    dev = load("dev")
    heldout = load("heldout")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle("Persona-function fidelity to real audience text: baseline vs. fewshot", fontsize=13)

    # --- Panel 1: within-audience variation fidelity, per audience, dev + heldout ---
    ax = axes[0]
    labels, base_vals, base_err, few_vals, few_err = [], [], [], [], []
    for dataset, tag in [(dev, "dev"), (heldout, "held-out")]:
        for a in dataset["audiences"]:
            labels.append(f"{a}\n({tag})")
            for cond, vals, errs in [("baseline", base_vals, base_err), ("fewshot", few_vals, few_err)]:
                v = dataset["conditions"][cond]["within_fid"][a]
                lo, hi = dataset["conditions"][cond]["ci"]["within_fid"][a]
                vals.append(v)
                errs.append([v - lo, hi - v])

    x = np.arange(len(labels))
    w = 0.35
    base_err_arr = np.array(base_err).T
    few_err_arr = np.array(few_err).T
    ax.bar(x - w / 2, base_vals, w, yerr=base_err_arr, capsize=3, color=COND_COLORS["baseline"], label=COND_LABELS["baseline"])
    ax.bar(x + w / 2, few_vals, w, yerr=few_err_arr, capsize=3, color=COND_COLORS["fewshot"], label=COND_LABELS["fewshot"])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(len(dev["audiences"]) - 0.5, color="gray", linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("within-variation fidelity\n(relative error vs. real; 0 = perfect)")
    ax.set_title("Within-audience: dev (left) vs. held-out (right)")
    ax.legend(fontsize=8)

    # --- Panel 2: between-audience separation fidelity, dev vs heldout, both conditions ---
    ax = axes[1]
    datasets = [("dev", dev), ("held-out", heldout)]
    x2 = np.arange(len(datasets))
    for i, cond in enumerate(["baseline", "fewshot"]):
        vals = [d["conditions"][cond]["between_fid"] for _, d in datasets]
        cis = [d["conditions"][cond]["ci"]["between_fid"] for _, d in datasets]
        errs = np.array([[v - lo, hi - v] for v, (lo, hi) in zip(vals, cis)]).T
        offset = (i - 0.5) * w
        ax.bar(x2 + offset, vals, w, yerr=errs, capsize=4, color=COND_COLORS[cond], label=COND_LABELS[cond])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x2)
    ax.set_xticklabels([name for name, _ in datasets])
    ax.set_ylabel("between-audience separation fidelity\n(relative error vs. real; 0 = perfect)")
    ax.set_title("Between-audience: dev vs. held-out")
    ax.legend(fontsize=8)

    fig.text(0.5, 0.01,
              "0 = matches real audiences exactly. Negative = less diverse/separated than real (collapse). "
              "Error bars: bootstrap 95% CI (n=1000).",
              ha="center", fontsize=8, style="italic")

    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(OUT_PATH, dpi=150)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

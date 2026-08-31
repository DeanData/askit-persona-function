#!/usr/bin/env python3
"""Pull a small real-text sample per audience subreddit from winddude/reddit_finance_43_250k.

Queries the remote parquet directly via duckdb (HTTP range requests, no full
download, no login, no scraping — this is HF's standard public data
distribution mechanism). Keeps only post title+selftext (not comments, to
keep register consistent across audiences), filters for a minimum body
length so we're not sampling one-line posts, dedupes, and samples N per
subreddit with a fixed seed for reproducibility.
"""
import json
import sys
from pathlib import Path

import duckdb

AUDIENCES = ["personalfinance", "wallstreetbets", "fatFIRE", "thetagang", "povertyfinance"]
N_PER_AUDIENCE = 250
MIN_CHARS = 120
SEED = 42

PARQUET_URLS = [
    "https://huggingface.co/datasets/winddude/reddit_finance_43_250k/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet",
    "https://huggingface.co/datasets/winddude/reddit_finance_43_250k/resolve/refs%2Fconvert%2Fparquet/default/train/0001.parquet",
]

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "finance_forums"


def main():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    urls = ", ".join(f"'{u}'" for u in PARQUET_URLS)
    subs = ", ".join(f"'{s}'" for s in AUDIENCES)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Deterministic pseudo-random sample per subreddit via hash(id) ranking,
    # computed in one pass over the remote data (not one query per subreddit) —
    # `USING SAMPLE ... (reservoir, seed)` over this remote parquet source
    # silently returned a handful of rows instead of a real sample, so this
    # avoids that operator entirely.
    query = f"""
        WITH deduped AS (
            -- source is post/comment PAIRS, so the same post repeats once per
            -- paired comment; dedupe on id before ranking or the sample is
            -- dominated by whichever posts happen to have the most comments
            SELECT DISTINCT id, title, selftext, subreddit
            FROM read_parquet([{urls}])
            WHERE subreddit IN ({subs})
              AND length(selftext) >= {MIN_CHARS}
              AND selftext NOT IN ('[removed]', '[deleted]')
        ), ranked AS (
            SELECT *, row_number() OVER (PARTITION BY subreddit ORDER BY hash(id || '{SEED}')) AS rn
            FROM deduped
        )
        SELECT id, title, selftext, subreddit
        FROM ranked
        WHERE rn <= {N_PER_AUDIENCE}
    """
    rows = con.execute(query).fetchall()
    cols = [d[0] for d in con.description]

    by_sub = {s: [] for s in AUDIENCES}
    for row in rows:
        rec = dict(zip(cols, row))
        by_sub[rec["subreddit"]].append(rec)

    summary = {}
    for sub, recs in by_sub.items():
        out_path = OUT_DIR / f"{sub}.jsonl"
        with open(out_path, "w") as f:
            for rec in recs:
                f.write(json.dumps(rec) + "\n")
        summary[sub] = len(recs)
        print(f"{sub}: wrote {len(recs)} texts -> {out_path}")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

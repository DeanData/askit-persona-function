# Time log

Rough log, updated as we go. Times are wall-clock, not effort.

| Time | Activity |
|---|---|
| 2026-08-31 15:28 | Assignment start. Read guidelines.pdf, confirmed understanding with candidate. |
| 2026-08-31 15:30 | Repo scaffolding (git init, folder structure, time log). |
| 2026-08-31 15:30–16:00 | Logistics: GitHub repo, git identity fix, WORKLOG.md + METRIC.md policy, session-log export tool. |
| 2026-08-31 16:00–16:35 | Phase 1 planning: 5-phase plan approved (depth allocation, protected Part 3 block, stop signal, cut order); domain discussion (demographic vs. decision-framing audiences), resolved to investing-forum proxy. |
| 2026-08-31 16:35–16:48 | Data sourcing for candidate audiences (`winddude/reddit_finance_43_250k` via HF + duckdb, under 15-20 min cap). Paused before locking audience list — open question on flair/experience-level substitution. |
| 2026-08-31 16:48 | Break. ~1h20m elapsed of the 5h budget. |
| 2026-08-31 16:48–16:58 | Resolved flair/experience-level substitution question; caught and fixed own design error (fatFIRE mislabeled as uniquely intersectional in a full 2x2) via candidate's pushback; locked 5-audience design. |
| 2026-08-31 16:58–17:35 | Data pull for real audience samples: hit and fixed two bugs (`USING SAMPLE` silently under-sampling; missing `DISTINCT` letting post/comment-pair duplicates through). 250 unique real posts/audience pulled and committed. |
| 2026-08-31 17:35–18:05 | Empirical separation pre-check built and run: 42.0% (full) vs 41.6% (core-only) accuracy vs 20% chance, confusion tracks shared attributes. No swap needed — audience design locked. |
| 2026-08-31 18:05–18:50 | Persona format discussion: structured schema locked (n=40-50/audience, fixed-seed shared roster, age-conditioned occupation sampling instead of vague "light guards"). |
| 2026-08-31 18:50–19:10 | Elicitation contexts: locked one structural (advice-giving, $10k) + one surface (casual money check-in) context, both finance-anchored — checked and confirmed this doesn't conflict with the function-generality requirement. |
| 2026-08-31 19:10–19:18 | Formal metric design proposed (reuse pre-check's 10 features; real-data fidelity anchor via audience centroids; within/between via avg pairwise distance + ratio; 5 named blind spots) — **not yet locked or committed to METRIC.md.** |
| 2026-08-31 19:18 | Break. ~3h50m elapsed of the 5h budget — audiences, persona format, and contexts locked; metric design is the one open item in Phase 1. |

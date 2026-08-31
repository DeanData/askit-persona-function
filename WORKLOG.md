# Worklog

Running lab notebook. Everything load-bearing gets written here the moment it happens, not reconstructed later. This is the source material for REPORT.md, TIME_LOG.md, and the Part 3 proposal.

## Decisions + why

- 2026-08-31 — Repo layout: `data/`, `src/`, `artifacts/`, `logs/` + `.gitignore`. Kept generated/large artifacts out of git per the "no large data files" requirement; exact split of what's committed vs. gitignored still open, to be decided once we know what the data looks like.
- 2026-08-31 — Logistics agreed with candidate: single running `WORKLOG.md` (this file) instead of scattering decisions/failures/timing across files; `METRIC.md` to be committed before any text generation, as a verifiable pre-commitment.
- 2026-08-31 — GitHub repo created public at `DeanData/askit-persona-function` via `gh repo create`. Public deliberately: interviewer needs to reach it from just the link, and transparent commit history (including dead ends) is treated as a feature of the submission, not a risk.
- 2026-08-31 — Rewrote local + pushed commit authorship (3 commits) from an auto-detected local identity to `DeanData <83536999+DeanData@users.noreply.github.com>` (GitHub noreply address, since the account's email is private) via `git filter-branch --env-filter`, preserving original author/committer dates, then force-pushed. Done for consistent, correctly-linked attribution across the submission.

## What we tried / what didn't work

(none yet — Part 1/2 work hasn't started)

## Part 3 (slow research) ideas — parking lot

(none yet — capture anything that comes up while working on Part 1/2 here immediately, even half-formed)

## Claude Code: plausible-but-wrong moments

(none yet — log the instant one happens, with how it was caught)

## Rough timestamps per phase

- 2026-08-31 15:28 — Assignment start, read guidelines.pdf, confirmed understanding.
- 2026-08-31 15:30 — Repo scaffolding (git init, folders, .gitignore, TIME_LOG.md).
- 2026-08-31 — Logistics discussion: repo/GitHub, data handling, session-log export, git identity, REPORT.md-as-draft, WORKLOG.md + METRIC.md agreed.

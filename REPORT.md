# REPORT.md

*Full reasoning, dead ends, and every decision's rationale live in `WORKLOG.md`
(chronological) and `METRIC.md` (the metric, committed before any generation). This
report summarizes; those are the record.*

## The function

`f(audience description, persona description, context) -> text`. Audiences: 5 finance-
forum populations (r/personalfinance, r/wallstreetbets, r/fatFIRE, r/thetagang,
r/povertyfinance), chosen over demographic-bin alternatives because they give a genuine
two-attribute intersection (risk-orientation × sophistication) without inventing one —
fatFIRE is the dev intersectional audience, thetagang (held out) mirrors its compound
pattern but swaps the risk attribute. povertyfinance is held out as a single-attribute,
demographically distinct population. Personas: a structured schema (age, age-conditioned
occupation, region, family status, one open-ended detail), rendered through one fixed
template, 40 per audience, fixed seed, shared roster across every condition (paired
comparison). No persona field restates the audience's defining trait. Contexts: one
structural ("$10k advice-giving," forces justification/argument) and one surface ("weekly
money check-in," low-stakes, lets register surface unforced) — deliberately chosen to pull
on the function differently, both finance-anchored (checked against the generality
requirement; audiences, not topics, are what must generalize).

## Metric (committed in `METRIC.md` before any text was generated)

Ten cheap stylometric features (6 structural: sentence length, lexical diversity, word
length, first-person rate, hedge rate, punctuation density; 4 surface: emoji, exclaim,
all-caps, meme-token rate) — validated empirically in a Phase 1 pre-check on real data
(5-class nearest-centroid accuracy 42.0% full vs. 41.6% structural-only vs. 20% chance:
separation is structural, not slang-driven). Ground truth is real Reddit text, split into
a disjoint eval pool (242/audience, used only for reference statistics) and a few-shot
pool (8/audience, used only in prompts) — a contamination risk caught before it was
built, not after. Success is defined as **matching real audiences, not maximizing
separation**: an earlier draft treated a bigger between/within ratio as better, which
directly rewards within-audience collapse; both fidelity measures are now signed relative
error against real references (0 = perfect match). Self-labeled texts (literal audience
name-dropping) are excluded from fidelity, counted separately. Bootstrap 95% CIs (n=1000)
on every number. **What a perfect score would still miss**: style, not content;
personalfinance/povertyfinance are known-hard to separate on this feature set; the
meme-token wordlist is crude; personas are demographically uniform by design, so some
fidelity gap may reflect demographic mismatch rather than voice failure.

## Numbers (see `artifacts/baseline_vs_fewshot.png`)

**Baseline** (naive prompt: audience + persona + context, nothing else) shows a
consistent homogenization pattern on dev: within-variation fidelity negative for all 3
dev audiences (personalfinance −0.17, wallstreetbets −0.43, fatFIRE −0.12; all CIs
exclude zero), centroid drift substantial (0.37–0.52), between-separation also negative
(−0.20). The baseline is more homogeneous than real text on every axis at once.

**Fewshot** (8 real per-audience examples added as a style primer) was evaluated against
this on the same paired roster. On dev, the result is **mixed-to-negative**: within-
variation flat in aggregate (MARE 0.242→0.243) and worse for fatFIRE specifically
(−0.12→−0.15); between-separation moved *away* from zero (−0.20→−0.25, worse); centroid
drift improved only marginally, driven almost entirely by fatFIRE. On held-out
(thetagang, povertyfinance — run exactly once, after dev was finalized), the picture
flips: every measure moves in the favorable direction (within-variation, centroid drift,
and between-separation all improve). But baseline/fewshot bootstrap CIs overlap for most
held-out measures — a consistent directional signal, not a statistically decisive win.
**Dev and held-out disagreed about whether the improvement helped** — exactly the
disagreement the held-out mechanism exists to surface.

## What didn't work

Few-shot's dev self-labeling rate more than doubled (6/240→13/240 texts), concentrated
almost entirely in fatFIRE (3→12 of 80). Inspected the fatFIRE few-shot pool directly: 2
of its 8 real examples literally self-label ("Fatfire in unconventional cities," "...
achieve fatFIRE?"). Showing the model real text that names its own community taught it to
imitate that. This is a real, well-evidenced negative finding, not just a weak result.
**Not fixed now**: filtering self-labeled examples from the few-shot pool and rerunning
is exactly the "further tuning past the first defensible improvement" we agreed to cut
if time was short — named here as a next step, not executed.

## Part 3: Slow research

*Placeholder — pending remaining time in the 5-hour budget. Working through the
mechanism, cost, falsification test, and kill criterion collaboratively rather than
proposing it cold; to be filled in if time allows, reported honestly as not reached
otherwise.*

## What we'd do with another week

Filter self-labeled examples from the few-shot pool and rerun, to isolate whether the
between-separation regression was a few-shot-mechanism problem or specifically the
self-labeling leakage. Add a third, topic-neutral elicitation context to test whether
audience voice survives outside finance-adjacent situations — the current two contexts
can't distinguish that. Relax the demographically-uniform persona design (named as a
blind spot in `METRIC.md`) to test whether real audiences' demographic differences, not
just voice, are driving some of the fidelity gap. Re-run the classifier-style separation
check from Phase 1 directly on generated text (not just real text) with cross-validation
instead of a single split, now that we have a reason to trust it at this sample size.
Widen the audience set beyond one dataset (investing forums) to check whether the metric
and findings generalize to a genuinely different domain.

## Where Claude Code was plausible but wrong

Early in Part 1, I proposed a 2×2 design (risk-orientation × sophistication) for the five
audiences and labeled fatFIRE as "the intersectional audience." This sounded coherent —
fatFIRE genuinely is defined by two attributes — but was actually inconsistent: in a full
2×2, *every* audience (personalfinance, wallstreetbets, fatFIRE, thetagang) is equally
defined by both attributes, so none is uniquely "the" compound one. The design silently
erased the single-vs-compound contrast the requirement ("at least one audience must be an
intersection... rather than a single attribute") actually depends on — "intersectional"
would have been true by construction, not by design. The candidate caught it by asking
directly: "isn't by your logic the others also an intersection in the same way?" The fix
was to make risk-orientation the sole defining attribute for personalfinance/
wallstreetbets/povertyfinance (sophistication left unspecified, matching the guidelines'
own worked example), reserving the deliberate two-attribute combination for fatFIRE (dev)
and thetagang (held out, testing whether the compound pattern generalizes rather than
being memorized from fatFIRE alone). Logged in `WORKLOG.md` the moment it was caught.

# METRIC.md — committed before any persona text is generated

This is the metric for evaluating `f(audience description, persona description) → text`.
Committed now, before Part 2 generates anything, per the assignment's pre-commitment
requirement. Full design discussion and the dead ends along the way are in `WORKLOG.md`.

## 1. Axes of variation: surface vs. structural

Validated empirically on real data in the Phase 1 separation pre-check
(`src/separation_precheck.py`), not asserted: a nearest-centroid classifier on 5 real
audiences (n=250 each) scored 42.0% accuracy (vs. 20% chance) using all 10 features below,
and 41.6% using only the structural subset — separation is overwhelmingly structural, not
driven by surface slang/emoji.

- **Structural axes** (how something is said): sentence construction, lexical diversity,
  word length, hedging language, self-reference, punctuation density.
- **Surface axes** (topic-adjacent decoration): emoji use, exclamation marks, all-caps,
  meme/in-group vocabulary.

## 2. Feature set (unchanged from the pre-check — reused, not re-derived)

Computed per text (title + selftext concatenated, HTML entities and URLs stripped):

**Core / structural**
| feature | definition |
|---|---|
| `avg_sentence_len` | words / sentences (sentences split on `[.!?]+`) |
| `ttr_guiraud` | unique words / sqrt(total words) — length-corrected lexical diversity |
| `avg_word_len` | mean characters per word |
| `first_person_rate` | first-person pronouns per 100 words |
| `hedge_rate` | hedging words (maybe, perhaps, might, ...) per 100 words |
| `core_punct_rate` | `.,;:` per 100 characters |

**Surface / slang**
| feature | definition |
|---|---|
| `emoji_rate` | emoji characters per 100 words |
| `exclaim_rate` | `!` per 100 characters |
| `allcaps_rate` | ALLCAPS words (len ≥ 2) as a fraction of words |
| `meme_token_rate` | curated meme/in-group wordlist, per 100 words |

All 10 features are standardized (z-score) using a single scaler fit across **all** texts —
real and generated, all audiences, both conditions — so every downstream distance is in the
same space.

## 3. Ground truth / reference

The real audience samples already pulled and committed (`data/finance_forums/*.jsonl`,
250 unique real posts per audience) are the ground truth. This is used two ways:

1. As the empirical basis for the axis analysis above (already done).
2. As the **reference distribution** every generated-text statistic below is compared
   against — not an internal-consistency check between generated audiences alone, but a
   fidelity check against how the real population actually writes.

## 4. Within-audience and between-audience: what "good" means

Earlier drafts of this metric treated a bigger between/within ratio as better. That's
wrong and was caught before committing: it rewards within-audience collapse (personas
that are all near-identical would shrink "within" toward zero and blow the ratio up,
looking great while being a worse, less realistic system — real audiences carry
individual variation, and the persona mechanism exists specifically to produce that
variation). **Success is defined as matching the real within- and between-audience
numbers, not maximizing separation.** An over-separated system is exactly as wrong as
an under-separated one.

For each audience A, in a given context and condition (baseline / improved):

- `W_real(A)` = average pairwise feature-space distance among real posts of audience A
- `W_gen(A)` = average pairwise feature-space distance among generated persona texts of A
- `centroid_real(A)`, `centroid_gen(A)` = mean feature vectors, real and generated
- `B_real` = average pairwise distance between real posts of *different* audiences
  (averaged across all audience pairs)
- `B_gen` = same, for generated texts

### The three reported fidelity measures (all signed, all normalized — see §5)

1. **Centroid fidelity** (location, per audience) — is the generated audience's average
   position where the real audience's is?
2. **Within-variation fidelity** (spread, per audience) — is generated individual
   variation the same size as real individual variation? Signed: negative = collapse
   (less diverse than real), positive = over-dispersion (noisier than real).
3. **Between-separation fidelity** (spread, across audiences) — are generated audiences
   as separated from each other as real audiences are? Signed the same way.

**#2 is the required "within" number, #3 is the required "between" number** — reported
separately per the task's explicit instruction ("a system can look strong on one while
failing the other"), each redefined as distance-to-real rather than a raw magnitude a
degenerate system could game.

## 5. Normalization

Raw distances aren't comparable across audiences with different natural scales (e.g. one
audience may just write longer, more varied posts than another as a baseline fact about
that community). Each measure is normalized by its own real reference, as a signed
relative error:

- **Within-variation fidelity(A)** = `(W_gen(A) − W_real(A)) / W_real(A)`
- **Between-separation fidelity** = `(B_gen − B_real) / B_real`
- **Centroid fidelity(A)** = `distance(centroid_gen(A), centroid_real(A)) / W_real(A)` —
  normalized by the audience's own real within-spread, turning drift into an
  effect-size-like number: below 1 means the generated centroid sits within the natural
  scatter of real individuals (noise, not a real shift); above 1 means a genuine,
  larger-than-individual-variation drift.

**Assumption, named explicitly:** relative-error normalization is unstable if a real
reference value is near zero. Not expected to bite here — real stylometric spread across
250 real Reddit posts per audience won't be near-zero — but it's an assumption, not a
guarantee, and is recorded here rather than left implicit.

**Aggregate reporting:** per audience/per-pair signed values are reported for diagnosis
(so one weak audience is visible, not averaged away — this is also why the audience-level
empirical pre-check was run before any of this was locked). For the headline
baseline-vs-improved comparison and the required visual, **mean absolute relative error**
per condition is the one clean summary number.

## 6. Required implementation details (not just described — must actually run)

- **Self-labeling check:** a post-hoc scan of every generated text for literal
  self-naming of the audience (e.g. "as a wallstreetbets poster...", the subreddit name,
  or close paraphrases). Flagged/excluded texts are reported as a count, not silently
  dropped — a model hitting high separation via name-dropping rather than genuine voice
  is a real failure mode this metric would otherwise miss entirely.
- **Bootstrap confidence intervals** on every reported number (resample with replacement
  within each audience's generated set, n=1000 resamples), given the small per-audience
  sample size (n=40-50). Numbers are reported with their interval, not bare.

## 7. What a perfect score on this metric would still miss

1. **Style, not content.** All 10 features are stylometric. A system could match real
   audiences perfectly on every feature here while producing text that's factually wrong,
   generic in substance, or reasoning-empty — nothing here checks argument content.
2. **personalfinance vs. povertyfinance are known-hard to separate** on this feature set
   (found in the pre-check: their real-data confusion is concentrated with each other,
   not spread randomly) — a perfect score doesn't fix a representational blind spot in
   the features themselves.
3. **The meme-token wordlist is crude** and likely includes generic finance vocabulary
   ("gain," "loss," "print") alongside genuine slang — weakens the surface/structural
   split's precision specifically for that one feature.
4. **Self-labeling is checked, but only for literal naming** — a subtler shortcut
   (e.g. paraphrasing audience identity without naming it) wouldn't be caught.
5. **n=40-50 personas per audience** bounds statistical precision regardless of how good
   the underlying generation is — addressed with bootstrap CIs (§6), not eliminated by
   them.

## 8. Held-out discipline

This metric applies identically, unmodified, to dev and held-out audiences. Held-out
audiences (thetagang, povertyfinance) are run exactly once, at the end of Part 2, after
the metric and the improvement are both already finalized on dev.

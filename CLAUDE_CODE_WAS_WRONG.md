# Where Claude Code was plausible but wrong

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

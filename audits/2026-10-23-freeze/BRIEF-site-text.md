# Brief: site text for the frozen forecast (2026-10-23)

For the owner's approval (QC.md §4b) before the UAT build. Owner, 2026-10-23:
"Site text can be looked at when we have something fina[l]". The frozen
settings and their effect are in MODEL-LOG §1.335 and
`reports/model-changes/2026-10-23-freeze/report.html`.

Every figure on the site is a token, so it updates by itself, and its tooltip
now says what it was ("45% chance since 23 October. Was 58% on 21 October.").
This brief covers only prose that the new figures make untrue, and the two
places that state the withdrawn ActionSA call.

## 1. Forecast page, "what the model says now" (`forecast-sheet.html`)

**Now:** "The ANC is now ahead for largest party, where on 8 August the DA led
clearly: {p_anc_largest} chance it's the ANC alone and {p_da_largest} chance
it's the DA alone."

The new forecast gives the DA 47% alone and the ANC 45%, so "the ANC is now
ahead" is untrue.

**Proposed:** "The race for largest party is now close, where on 8 August the
DA led clearly: {p_da_largest} chance it's the DA alone and {p_anc_largest}
chance it's the ANC alone."

## 2. Forecast page, Limits (`forecast-sheet.html`)

**Now:** "One party's level is a judgement. ActionSA's expected share is set by
our judgement, at {judgement_asa_support} of the list vote, not by This Model."

**Proposed:** "ActionSA has stood in one local election, so This Model carries
its 2021 result forward at the share a typical party of its size keeps between
local elections. Parties at their second local election have kept from a fifth
of their first result to one and a half times it. Until 23 October ActionSA's
share was set by our judgement at 17.6%; it is now This Model's own."

## 3. Methodology page, "How each party's support moves" (`docs-public/methodology.md`)

**Now:** "In this forecast its level is set by our judgement instead, at 17.6%
of the list vote: This Model carries the 2021 result forward at the share a
typical party of its size keeps between local elections, and its by-elections
lift it part of the way back; we judge that ActionSA keeps more of that vote
than This Model does. Every other party's share is scaled down in proportion
so the shares still add up, and ActionSA keeps This Model's usual uncertainty
for a party of that size. It cannot be changed on your forecast."

**Proposed:** "This Model carries the 2021 result forward at the share a
typical party of its size keeps between local elections, and its by-elections
lift it part of the way back. Parties at their second local election have kept
from a fifth of their first result to one and a half times it, and the record
does not say which ActionSA will be. From 21 to 23 October ActionSA's level
was set by our judgement at 17.6%; that judgement was withdrawn on 23 October."

## 4. Records that follow (no reader-facing words)

- `content/joburg/stats.toml`: retire `judgement_asa_support` (its source no
  longer exists) and the `[[audit.fixed]]` 17.6% entry. Add the fixed figures
  the new sentences use ("a fifth", "one and a half times"), sourced to MODEL-LOG
  §1.334, and "17.6%" as a historical figure, sourced to JUDGEMENT-CALLS §SJ2.
- `content/joburg/model-claims.toml`: claim `actionsa-judged-level` retired.
- `src/tooltip_says.py`: the `judgement_asa_support` entry removed.
- `src/stats.py:65`: the docstring example updated.

## Not in this brief

- **No corrections entry.** Nothing published was wrong when it was published.
- **The γ changes** reach the page only through figures and the ward map.
- **The marketing and billboard copy** names no forecast figure.

## Limits

Branch `site-sweep-1`. A writer makes the edits; I review the diff before
anything is built. Then `render_sheet.py`, `build_site.py --as-published`, the
targeted site tests, one UAT upload and the whole suite once for that version.
No live promotion without the owner's yes.

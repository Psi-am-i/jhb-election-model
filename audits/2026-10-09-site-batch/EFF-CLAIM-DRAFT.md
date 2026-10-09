# EFF claim draft: Malema, "no outright winner" (2026-10-09)

Status: draft for the owner. `content/joburg/claims.toml` is not changed.

## The source, verified
- Mail & Guardian, "Malema: The future of South Africa is the EFF, ANC and MK
  Party", Lunga Mzangwe, 9 April 2026.
  https://mg.co.za/politics/2026-04-09-malema-the-future-of-south-africa-is-the-eff-anc-and-mk-party/
- The passage, as printed:
  > Malema told the briefing that there would be no outright winner in any of
  > the metros, except in Cape Town, after the 2026 local government elections.
  > The EFF, he added, would also fight to reduce the DA's majority in the Cape
  > Town metro.
- **These are the journalist's words. They are reported speech and carry no
  quotation marks.** Every other entry in `claims.toml` has a verbatim `quote`,
  and the page prints it in quotation marks as the speaker's words.
- Searched without success: a direct quote of the same claim in another
  outlet. Checked TimesLive, 25 July 2026 (mayoral candidates). Malema's
  direct quotes there say nothing about outright winners.

## Owner decision needed
1. **Use the reported speech, marked as reported.** For example, the quote box
   reads: *Malema told the briefing that there would be no outright winner in
   any of the metros, except in Cape Town* (Mail & Guardian). This needs the
   renderer to print a reported claim without quotation marks, which is a
   `render_sheet.py` change.
2. **Find a direct quote.** The briefing's video or the EFF's own statement of
   9 April 2026 may carry his words.
3. **Drop it** until he says it on the record.

## What the model tests
The site models Johannesburg only, so the claim is tested for Johannesburg.
The other metros are out of scope, and the page says so.

- tests: "P(no party reaches a majority of council alone)"
- chance: `1 - <name>`, where `<name>` is `scenarios.majority_alone_share`,
  the same definition as the `tile.p_alone` tile.
  - The claims block has no `[[name]]` for it yet. `render_sheet.py` needs one
    line in `since_vals`, for example
    `"any_alone_share": chance("claim.any_alone.share", p_alone)`, read from
    the one definition.
- The figure today, read from the published run's `data/processed/seat_draws.csv`
  (29 Sep 2026, seed 20261104, 5,000 simulations):
  - one party alone: 0.0008;
  - no party alone: 0.9992;
  - `render_sheet.scale_verdict(0.9992)` gives **NEAR CERTAIN**.
  - This is the published model. The model batch in progress re-runs it, and
    the verdict is re-read at that build.
- Badge: `near-certain` is one of the three badges the owner has not yet drawn
  (`owner-stamps/verdicts/`).

## Draft entry (option 1 wording)

```toml
[[claim]]
party = "EFF"
party_name = "Economic Freedom Fighters"
chip = "#E1251B"          # check against the site's EFF colour
logo = "EFF"
quote = """There would be no outright winner in any of the metros, except in Cape Town"""
reported = true           # new field: reported speech, printed without quotation marks
speaker = "Julius Malema, EFF leader, as reported"
outlet = "Mail & Guardian, 9 April 2026"
url = "https://mg.co.za/politics/2026-04-09-malema-the-future-of-south-africa-is-the-eff-anc-and-mk-party/"
verdict = "NEAR CERTAIN"
chance = "1 - any_alone_share"
tests = "P(no party reaches a majority of council alone), Johannesburg only"
label = "No party will win Johannesburg outright"
captured = "2026-04-09"
intro = """We model Johannesburg only, so that is the metro tested here. An outright winner needs {{majority}} of the {{council_size}} seats. One party reaches it in {{p_alone}} of the {{n_draws}} simulations."""
steps = [
  """**No party comes close alone.** The ANC's median is [[anc_median]] seats and the DA's [[da_median]], against the {{majority}} needed.""",
  """**First place is still contested.** The ANC alone is largest in [[anc_largest_share]] of simulations and the DA alone in [[da_largest_share]]. Being largest is not the same as governing.""",
  """**What this cannot see.** The other metros. Malema made the same claim about every metro except Cape Town, and this model does not forecast them.""",
]
```

The `reported` field and its rendering do not exist yet. They follow
`QC.md` §4b: an owner-approved brief, then a diff review.

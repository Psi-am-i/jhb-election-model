# Slice M4 review summary (2026-10-10)

Writer: commits 7297ccd, 03bf2f0, e0ce282, 121f9de. Blind review: packet
`M4-PACKET.md` (e2df5b3). Coordinator re-derivation: `bye_value.py --out`
into scratch reproduced both classes exactly (under 1%: 34 pairs, G −0.017,
5th percentile −0.043, weight 0; 1% or over: 35 pairs, G −0.070, 5th
percentile −0.318, weight 0). The reviewer reproduced the same with an
independent plain-loop implementation.

**No blocking finding.** Writer and reviewer agree on every row below, or the
row is the reviewer's alone and the writer's report does not contradict it.
No disagreement goes to the owner.

## Fix round (one writer, one commit per row or group)

| row | finding | source | fix |
|---|---|---|---|
| 1 | The pre-registration is unscored; its ≥1% bullet is falsified (−0.318 against ±0.3); its claim that independents fall out of the population is wrong | both | Append a dated scoring section to `prereg/2026-10-10-byelection-value-test.md` (never edit the predictions) and a MODEL-LOG entry: held / falsified per bullet, the IND error, and the reviewer's measured effect of removing IND (under class 5th percentile −0.0435 → −0.0351, verdict unchanged). The population stays as pre-registered. |
| 2 | `build_play.py:480` and `:522` fail on `w_bye = None`; `interactive/js/model.js:214` orders the published cell arbitrarily | both | The published cell sorts and compares by its effective weight, read from the manifest's per-party class weights, not by `w_bye`. Unit-test with a constructed manifest. Reader copy ("Partly, as the forecast does", "The forecast counts them partly") is listed for the site step, not changed here. |
| 3 | `bye_value_key` omits the raw election files `B`, the outcome and the θ record are built from, and `cities/*.toml` | reviewer | Add their shas to the key; a test edits one in a scratch tree and sees the refusal, reverted it passes. |
| 4 | G23 cannot see a bootstrap that resamples pairs rather than metros | reviewer | A constructed case where pair and metro resampling give different 5th percentiles; the mutation is caught and goes quiet when reverted. |
| 5 | G26 skips `export_draws.build` and `write_index`'s manifest read | reviewer | G26 runs through both; deleting either line turns it red. |
| 6 | Nothing stops a city toml from reintroducing `w_bye` | reviewer | A scan over `cities/*.toml` (population asserted equal to the city list, both ways) refusing a `w_bye` key; constructed violation caught. |
| 7 | Stale text: `backtest.py:501`, `test_levers_are_live.py:1505` | both | Correct the descriptions. |

**Noted, no change now:**
- `_bye_weight` records a class weight for parties gated out by
  `BYE_MIN_WEIGHT`, and `w` not `w_used` under `inverse_variance`; invisible
  while both weights are 0. Recorded in §A55's limits.
- The test's `B` is not the 2026 spine and carries a party-signed bias (DA
  e > 0 in all six metros, ANC e < 0 in all six); the eThekwini ANC pair
  (e = −34.1, MK's arrival) dominates the ≥1% class. Both belong in §A55's
  limits; neither moves the verdict (without that pair the 5th percentile is
  −0.150).
- `tests/run_all.py -k temporal` rewrites two files in `data/processed` by
  design (byte-identical to the 2026-10-09 backup). Review packets must say so.
- Step 9 (arm E): with both weights 0, arm E equals arm D on every centre;
  `bye_weight_mode` and `BYE_MIN_WEIGHT` become inert at 2026 and need
  `EXPECTED_INERT` entries with a gate check.

## Rules for the fix round
As `M4-WRITER-BRIEF.md`: no sub-delegation, nothing written to `data/`,
`site/`, `content/` or `publications/`, no `--emit`, docs in the same commit,
targeted modules per commit quoted in the body, new reds on a dated R3.6
addendum, stop after a commit if credit runs short.

# Everything the blind review raised, and where each item stands

Source: `brief-blind.md` (the brief), the review's own report, and the
independent re-checks run here before acting on any of it. Status is one of
DONE / OPEN / OWNER / REJECTED, and nothing is deleted from this list.

## Published-site defects

| # | item | status |
|---|---|---|
| A1 | Four "as published 31 August" figures were never published; three arrows pointed the wrong way; the since-then sentence was false in the same direction; five articles mis-dated | **DONE** `84ea514` — re-sourced to the ledger, arrows recomputed, sentence rewritten, articles re-dated against the archived bytes, correction filed |
| A1b | The omission behind A1: the convention named its source in prose and nothing read it | **DONE** `84ea514` — `test_a_frozen_as_published_figure_is_sourced_to_the_LEDGER_not_to_a_build` requires the citation AND the match |
| A2 | The "dead heat" headline is decided by `np.argmax` awarding all 91 DA/ANC ties to the DA. Sole: ANC 47.20%, DA 45.52%, tied 1.82%. Split evenly the ANC leads 48.1 / 46.4 and the dead-heat sentence does not fire | **OWNER** — verified here. A definition change, so a publish must declare it; also appears in two tested-claims boxes on `/forecast` |
| A3 | `IND` (independents) is on the certified ballot, has a by-election record (2 contests, 8.39% mean, +6.5pp) and has **no pool membership**, so cannot win a seat in any simulation. `/forecast` states "Every party on the IEC's certified ballot is named in the simulations" | **OPEN** — needs the D3 measurement before a fix |
| A3b | The other seven parties that never win a seat hold real pool weights, so they are drawn and simply never clear a quota. §5b item 1 still wants one named defence each, in public | **OPEN** |
| A4 | `/about` calls a 12-party table "every party that won a seat in 2021"; Johannesburg seated 18. The page's own printed total (62) does not match its visible rows (56), and the gap is exactly the 6 missing parties | **OPEN** |
| A4b | `/about` is a 400-draw run from 2026-08-11 while every other figure is the 23 September 5,000-draw run; `README.md` says regenerate before citing | **OPEN** — see D6 |
| A4c | The three baselines exclude `benchmarks.uniform_swing_roster`, which `README.md` calls "the honest opponent at 2021". The +37% headline is against the weaker field | **OPEN** |
| A5a | The Zille since-then box prints a range "34 – 34" from a single simulation | **OPEN** |
| A5b | `/portal` claims "every assumption a slider you can move" — no slider exists; and calls the other metros "not modelled yet" while `/about` publishes their 2021 backtests | **OPEN** — and `deploy_check` does not scan the portal (known) |
| A5c | The home page's interactive panel claims the real model in the present tense, ahead of the input route being chosen | **OPEN** |

## The plan

| # | item | status |
|---|---|---|
| B1 | A 300-draw browser default is the **first 300 draws** of the published run, so it disagrees with the headline identically for every reader (prints 50%/45% against 47%/47%). Sampling sd at 300 draws: 2.9pp on largest-party, 1.41 seats on the ANC median | **OPEN** — needs a stated rule: deltas only, both counts side by side, or ship only the control that needs no browser |
| B2 | `MEASURED.md`'s "paired at one seed" claim is **false for `dirichlet_scale`** — a Dirichlet's variate count depends on alpha, so the stream desynchronises and the runs are independent samples. "halved: 2 seats" is inside the noise. The two dropped levers are unaffected (a normal's variate count does not depend on its scale) | **OPEN** — see D2; fix the harness, never the model |
| B3 | Scoring a hand-drawn map: independent marginals would rank the model's own modal map above 95% of the maps it actually draws. "Distance to the nearest draw" is decided by single extreme draws. Use the reader's **percentile in the draw-to-draw distance distribution**, scored against the committed 5,000-draw ward file | **OPEN** — adopted as the design |
| B3b | The PR half of a hand-drawn forecast has no score in the plan at all | **OPEN** |
| B3c | Distance measures agreement, not quality — keep "how far from ours" and "how right you were" as two named quantities, never merged | **OPEN** |
| B4 | A reader's control must not touch the published headline | **DONE as a decision** — the ledger and `deploy_check` already make a copy the only survivable form |
| B5a | The four regime artefacts are **not committed** — `data/**` is gitignored. They exist on Atlas only | **OPEN** — blocks the PR-law page |
| B5b | `level_shrink`, the backlog's "single biggest modelling choice", is in no measurement and is not a candidate lever. A reader who reads §3 will ask why | **OPEN** — needs a sentence, not a slider (owner ruled it unpublishable as a control) |
| B5c | The plan never says what happens to the coalition table, ward map, cartogram and tested claims when a lever moves | **OPEN** |
| B5d | A URL-borne forecast is untrusted input: 135 ward calls, a PR vector and lever positions. No validation rule, no bound on what a link may assert | **OPEN** |
| B5e | Post-election scoring is promised but the rule, the result-ingest path and the party-name mapping are not fixed in advance — and the IEC spells four Johannesburg parties differently from our baseline files | **OPEN — MOVE EARLIER.** Cheap now, impossible to do credibly once the result is known |
| B5f | No browser measurement exists; the Node figure is explicitly a floor. The trivia timer is being designed against a duration nobody has observed | **OPEN** — see D7 |
| B5g | The judgement calls were the plan's stated differentiator and now have no published surface | **OWNER** — unpublished on your instruction; needs its replacement defined |

## Measurements that would settle the open questions

| # | measurement | status |
|---|---|---|
| D1 | Run `run_model` at 300 draws, seed 20261104, and confirm it reproduces the first 300 of the published run | OPEN |
| D2 | Re-run the lever pairs with `SeedSequence(seed).spawn(draws)` and report paired differences with their own sd | OPEN |
| D3 | Give `IND` the city's own pool composition, re-emit, and diff the ward winner probabilities | OPEN |
| D4 | Rebuild and diff every sentence that reads the four corrected tokens | **DONE** — the rebuild moved exactly the four figures, their four arrows and the one sentence |
| D5 | Read the 2026 arrival group's band out of `pools_2026.json` and put it beside ActionSA's 2021 error | OPEN |
| D6 | Regenerate `validation_2021.json` at the current tree and compare with the canonical key | OPEN |
| D7 | One Pyodide run in a real browser at two draw counts | OPEN |

## Carried from before the review

| item | status |
|---|---|
| Deploy the six unshipped commits | OWNER |
| Close the 13 newsdesk PRs; put the merged `CLAUDE.md` on GitHub | BLOCKED — external writes refused in-session |
| Turnout by group and by area: the control the owner asked for does not exist | OPEN |
| Polls: define the 0→100% dial; it is not what `poll_credence` does | OWNER |
| `HANDOVER.md`'s banner was 14 hours stale about what is live | **DONE** — corrected in this pass |

## Raised in conversation and not previously written down

⛔ **This section exists because things were discussed and then lost.** An item
agreed in conversation and not in this file is an item that will be rediscovered
in three weeks. Nothing is deleted from here either.

| # | item | status |
|---|---|---|
| C1 | **The input route.** 76% of the 141 MB is other metros' VD results, read only to build the theta record, which serialises to 18.8 KB. Route B (precompute the reductions) recommended | **DONE as analysis** `35d5e59` — `INPUT-ROUTE.md`. **OWNER** to choose |
| C2 | The precomputed theta record must be checked byte-for-byte against the live path, or it becomes a second definition | OPEN — blocks C1 shipping |
| C3 | Johannesburg's own 31.8 MB has not been broken down by what the draw loop needs vs its setup | OPEN |
| C4 | **Turnout by population group** — decided (§9a), never built | OPEN |
| C5 | **Turnout by area** — no geographic grouping of the 135 wards exists anywhere in the model. The City's own regions A–G have an authority behind them; compass points do not | OWNER to choose the grouping |
| C6 | **The polls dial.** "0 = no effect, 100% = the poll happens exactly" is NOT what `poll_credence` does — 1.0 is the identity and 0 does not turn polls off (the arrivals path is gated by `poll_paths` alone). Needs defining as a new parameterisation | OWNER |
| C7 | The Ipsos Khayabus CoJ poll (ANC 31 / DA 27–28 / ASA 14 / EFF 8 / MK 6) is not in `polls.json`; the DA figure is disputed between outlets | OPEN |
| C8 | The poll trust ceiling (E = 3.0pp against ≥5pp) | **DONE as a decision** 2026-09-27 — it is the reader's, and ours is zero. Already true: `poll_paths` ships `off`, so the slider's zero position IS the published forecast. The page must say that zero is a position, not an unset control |
| C9 | Eight of the ten reinstatable levers are poll levers behind the single `poll_paths = "off"` | OPEN — context for C6 |
| C10 | **`within-pool movement` is the only surviving model lever besides `w_bye`**, and B2 says its "halved" reading is inside the noise. If D2 confirms, half that slider does nothing measurable | OPEN |
| C11 | **The IEC's per-VD 2026 registration** is not published; only ward level is. Worth asking the IEC for it directly | OPEN |
| C12 | The IEC's own page gives two CoJ totals 613 apart (2,417,302 vs 2,417,915). Unreconciled | OPEN |
| C13 | The CoJ PR-ballot party count is disputed 82 vs 75 between outlets, and our roster's `complete = true` licenses deleting parties on the strength of it. The 23 September ballot draw would settle it | OPEN |
| C14 | `inputs_preflight` reports **Tshwane** missing two required inputs (its roll and roster) | OPEN |
| C15 | The newsdesk rules are written but not live — they sit in `newsroom/NEWSDESK-RULES.md` and the routine still reads GitHub's `CLAUDE.md` | BLOCKED on the GitHub write |
| C16 | The newsdesk routine has produced nothing since 20 September; the armed re-check loop is disabled but no replacement schedule exists | OPEN |
| C17 | `splinter-rule-and-historical-tail`, `atlas/a5e8c5d` and Scout's 14-Sep stash are all marked discard and none has been deleted | OWNER |
| C18 | Six commits and counting are unpushed to Atlas and Scout | OWNER |
| C19 | **Post-election scoring** — the review's "move earlier". Rule, result-ingest path and party-name mapping all unfixed, and the IEC spells four Johannesburg parties differently from our baseline files | OPEN — do before 4 November |

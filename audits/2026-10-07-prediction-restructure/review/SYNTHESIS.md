# Blind review synthesis, 2026-10-08

Two reviewers (A, B) received `PACKET.md` verbatim. Scratch work:
`~/.claude/jobs/26965cd4/tmp/review-A/`, `review-B/` (job scratch, not durable).
Figures below are measurements of 2026-10-08 against the published draws;
`rederive.py` reproduces the ones marked *re-derived*.

## Agreed by both

| finding | evidence |
|---|---|
| Option (b) (today's start: vote = seats ÷ council) should not ship | ANC "% of votes" 25.9 vs model median combined share 21.3 (*re-derived*); scored on key 3 even if hidden; worst of all candidates on all three expected scoring keys |
| Option (a) as written cannot be built from published data | draws carry no combined share (`export_draws.COMBINED_SHARE_REFUSAL`); per-party medians sum to 87.3% (*re-derived*), and renormalising pushes DA to 76–77 seats |
| Any vote rule needs per-draw combined shares exported into `site/draws/` | model/pipeline tier, whole suite; captured run reproduces 5000 of 5000 published draws, so no published seat moves (*re-derived*) |
| The single-simulation bar and strip on `/forecast` must go or become our prediction | `site/forecast.html`, sim 1622, BOSA 16 seats (median 1) |
| The redirect must read the query: lever-only links go to `/forecast`, links with `f` to `/your-prediction/`; re-point `/play/` | `yf-url.js` key sets; `worker.js` `MOVED` is path-only |
| Seals, D1 entries and `context_ref` survive the move | `seal.js` signs `v c f n`; `context_ref` excludes the start |
| The brief reverses the 2026-10-06 seal-on-levers rule without saying so, and leaves the hand-off payload unspecified | `play-card.js` header; `make.js` follow |
| Two or more definitions of "the model as a reader" exist | `score_forecasts` docstring (median combined shares) vs `start_rule` |
| Rule 11's vote share needs its ballot named: entries are scored on the list ballot | `score_forecasts` key 3 |
| "Most likely" is not literally true of any complete scenario | modal ward counts match no draw; no draw within 20 seats of (a) or (b) |

## Disagreement (to the owner, unsplit)

**How to reduce the forecast to our prediction.**

- **A: constructed.** Each ward to its most likely winner; each party's vote its
  mean combined share; seats by the law. Gives ANC 70 (11 excessive), DA 65,
  ActionSA 28, EFF 26, PA 24, MK 23, others 34; each named party at its 48th–59th
  seat percentile (*re-derived*). A possible result in the legal sense; matches no
  single simulation.
- **B: one real simulation.** The simulation that would score best in the
  competition if each other simulation were the result (sim 519): ANC 79, DA 68,
  ActionSA 35, EFF 33, MK 23, PA 23. Every number from one simulated election;
  ANC well above its middle. (Not re-derived.)

Expected competition scores against the draws (reviewers' figures, not
re-derived): A's rule seat error 104.1, sim 519 104.2, (b) 108.5.

## One reviewer only

- B: our prediction must be frozen before polls open and scored by the same
  `score()` as readers; today it is not an entry.
- B: acceptance "same preview image" contradicts the retitle; use "same entry,
  same seats, same chance".
- A: the estimate of a day is low.

# STYLE.md sweep of the Johannesburg site's reader-facing words — 2026-10-01

Brief: rewrite every reader-facing word against `STYLE.md`; keep meaning, cut
words; change no figure, mechanism or verdict; move no token.

## Decisions on what is frozen

| text | treated as | why |
|---|---|---|
| `docs-public/corrections.md` entries | rewritten to STYLE §3 | owner asked; dates, `data-asof` spans and the 27 Sep table kept |
| `content/joburg/claims.toml` `intro` and `steps`, all four claims | frozen; proposals in `claims-proposals.md` | dated, published write-ups (8 Aug and 26 Sep) |
| claims' `since` boxes (DA 490,000; ANC alone) | edited | the "what the model says now" note the convention exists for |
| `docs-public/review.md` body (intro and every `data-asof="2026-08-06"` span) | frozen; proposals in `review-proposals.md` | a published piece dated 6 August, with its own since box. The brief listed `review` in scope; its body is the convention's case |
| `review.md` since box; its kicker/standfirst in `build_site.py` | edited | live box; site chrome |
| the 8 August article (`forecast-sheet.html` `__ARTICLE_ONLY__` regions) and `articles.toml` standfirsts | not touched | published piece |
| the article's three since boxes | edited (one left as it was) | live |
| MODEL-LOG.md, JUDGEMENT-CALLS.md, other internal records | not touched | outside the sweep |

## Files changed

| file | what |
|---|---|
| `docs-public/corrections.md` | four entries in What was wrong / What changed form; two-party entry is STYLE.md's example verbatim; "how it happened" cut to one sentence; "unchanged" clauses removed; closing paragraph cut to one sentence |
| `docs-public/methodology.md` | whole page tightened; "This page has twice described…" reduced to the two facts; the "Corrections and review" sermon cut to the facts plus a link to /corrections; "What we intend" now points to /play/ (see Meaning changes) |
| `docs-public/sources.md`, `support.md`, `privacy.md` | tightened. All POPIA items, the funding policy, the analytics/no-analytics markers and the owner line kept |
| `src/build_validation.py` → `docs-public/about-the-model.md` | prose strings in the generator; the page regenerated with `--from-json` (nothing re-run; every figure identical, checked by diff) |
| `docs-public/review.md` | since box only |
| `home.html` | "Make your own forecast" box (contains the STYLE §1 example sentence, which is in `home.html`, not `src/reweight.py` as the brief said); the "How this is built" descriptions |
| `src/render_home.py` → `home.html` | lede's second paragraph; "we have a dead heat" → "it is a dead heat". The lede ladder (owner's wording) untouched. Regenerated; render_home reproduces the committed page byte for byte before the edit |
| `forecast-sheet.html` | forecast-only prose: seat chart caption, tile eyebrow, "How to read", limits list, claims lede, colophon; article since boxes |
| `src/render_sheet.py` → `forecast-sheet.html`, `drafts/forecast-draft.html` | tile labels, govern lede, "How to read it" note (now names the table's own column headers), seats note, two-ballot caption. Regenerated; render_sheet reproduced the committed pages before the edit |
| `content/joburg/claims.toml` | two `since` boxes |
| `interactive/model.html` | /play/ prose: lede, turnout, polls, by-elections, results, share, published panels |
| `interactive/js/model.js` | refusal, band note, by-election empty row |
| `interactive/js/play-card.js` | share card: the same-house line is now `Counted as independent: polls from one house, <house>` (`sameHouseShort`); the page keeps the full `sameHouse` sentence. STAMP reworded, still "Not the model's forecast." |
| `interactive/js/play-share.js` | one sentence |
| `src/reweight.py` (+ `interactive/py` via `sync_py.mjs`) | `POLL_LABEL` "the model's draws nearest this poll" → "the model's simulations nearest this poll"; the effective-draws refusal says "simulations" (STYLE §6) |
| `interactive/tests/native-play.json` | regenerated with `tools/native_play.py --write`: only the label text and `page_ref` (the code hash) changed |
| `tests/test_reweight.py` | two wording assertions updated to the new text (POLL_LABEL; "effective simulations") |
| `src/build_site.py` | standfirsts for corrections, methodology, about, sources, support; reader-edition note; og:description's last sentence ("Explore every ward…") cut |
| `content/joburg/stats.toml` | 13 `[[audit.fixed]]` `context` strings re-keyed to the new wording, each marked `# re-keyed 2026-10-01: wording only`. Value, kind, source, reviewed date untouched. One entry (`"12"`, "an input until 12 September. Removing them is not a") now matches nothing: its sentence was deleted. Left in place for the owner |
| `SITE-TEXT.md` | re-exported (the committed one was already stale) |

## Tokens

No token added, removed or moved. Checked per file: token multisets of
`docs-public/*.md`, `forecast-sheet.html`, `home.html`,
`drafts/forecast-draft.html` equal HEAD's; `site_text.py` refuses a changed
set on `--apply`; the scratch build against a copy of the ledger reports the
same 319 tokens, 0 new, 0 visibly changed.

Typed (non-token) figures deleted with their sentence: in the two-party
correction, "on 27 September it reached a majority in 44% of simulations"
(STYLE.md's verbatim example omits it). In the 27 September correction, the
sentence "from almost every simulation to about two in three" (the table above
it carries the figures). Date formats kept where a registered fixed fact keys
on them ("2026-08-22", "as it stood on 6 August 2026", "never means a vote
share").

## Meaning changes (each a fact, flagged for the owner)

- `/methodology` "What we intend" said the per-poll trust control "is not built
  yet". /play/ ships it, so the paragraph now says /play/ has a first version
  and that the published forecast uses no poll.
- `home.html` "Make your own forecast": still "Not built yet", now with a link
  to /play/.
- Coalition table note: "% of simulations it can govern" and "survivability"
  are now called by the table's column names ("Governs in", "If a partner
  leaves").

## Left for the owner (seen, not changed)

- `/methodology` "Two of the three baselines … which the range-based score
  treats kindly" inverts `/about`'s caveat (HANDOVER fix-soon). Kept as it was.
- `/methodology` still says "Two inputs could not be confined"; `/about` says
  the breakaway record has not been a leak since 14 August.
- `/about` "Seven of the eight are cities the model was never designed against"
  and "The largest 55 parties" (HANDOVER fix-soon) kept.
- `/review` body: "They are now wired in" (polls) and "the council growing
  beyond 270" are untrue today; see `review-proposals.md`.
- Home claims list: the DA 490,000 claim shows "said 7 Aug" (`captured`) for a
  Business Day quote dated March 2026.
- `site/` not rebuilt (no publish), so `test_published_page` now lists ten
  stale pages instead of five; same test, same cause.
- The newsdesk's `bin/sync-context.sh` was not run (another repository); two
  claim `since` boxes changed.

## Five representative before/after pairs

1. STYLE §1 example (`home.html`)
   - before: "Your forecast is **yours**, and the page says so — ours stays where it is, and a small note shows how far apart the two are."
   - after: "The note under your council shows how far it is from the model's forecast."
2. Correction, 30 September (`corrections.md`)
   - before: "…**What changed.** The title now says what was tested: *"The DA can govern without the ANC, the EFF or MK"*. The verdict and its figures are unchanged. The quote it tests is now dated 13 September…"
   - after: "**What changed.** The title now reads *"The DA can govern without the ANC, the EFF or MK"*. The quote is dated 13 September, the date of the report it cites; it was shown as 11 September."
3. Govern lede (`render_sheet.py`)
   - before: "…it has one realistic governing option: working with ActionSA and the PA — this coalition has the numbers in {X} … Nothing here says which deal is politically likely; just what is mathematically possible."
   - after: "…its one realistic option is ActionSA and the PA, which have the numbers in {X} … This is arithmetic, not a judgement of which deal is likely."
4. Share card (`play-card.js`)
   - before: "Counted as independent: SRF · Johannesburg · July 2026 and SRF · Johannesburg · Feb–Mar 2026 are from one polling house (SRF/Victory Research) and are counted as independent, so that house's error counts once for each." (the polls line above it already lists both)
   - after: "Counted as independent: polls from one house, SRF/Victory Research"
5. Methodology, "Where polls fit"
   - before: "*This page has twice described the wrong state of that switch, and both times in the same direction — the text stayed still while the model moved. … which is the most serious error this site has carried; … So the date is not decoration.*"
   - after: "*This section has described that switch wrongly twice: for a day after 2026-08-22 it said no poll was used when one was, and for three weeks it described a weighting cap that had been retired.*"

## Verification

- `src/site_text.py --export` then `--apply --dry-run`: "no edits to apply."
- `build_site.py --out <scratch> --ledger-root <copy of publications/>`:
  sourcing audit 0 unsourced figures, 0 unsourced claims; number review 0
  blocking; ledger 319 tokens, 0 new, 0 visibly changed; the ledger copy is
  byte-identical afterwards. Before the stats.toml re-keying the same build
  reported 16 blocking, all re-worded sentences around registered fixed facts.
- Python: `test_site_text`, `test_home_page`, `test_number_scan`,
  `test_play_page`, `test_build_all`, `test_site_headers`,
  `test_publication_ledger`, `test_stat_freshness`, `test_reweight` pass;
  `test_published_page` fails as before (site/ is the UAT build).
- `node --test interactive/tests/*.test.mjs`: 31 pass, 0 fail, 2 skipped
  (Pyodide not installed), as before.
- The whole suite: see the commit message.

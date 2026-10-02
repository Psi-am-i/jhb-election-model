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
- The whole suite (`tests/run_all.py`, 67 modules, after the last edit): four
  failures. `test_published_page` (known; site/ is the UAT build). Three that
  touch no file in this sweep: `test_model_index` (MODEL-INDEX.md lists
  `reweight.MAX_FIGURE_SE_SEATS` under 2.0; the constant is 2.5 at HEAD),
  `test_no_numeric_module_constant_is_a_default_argument` (`deploy_check.py:34`),
  `test_pool_bounds::test_no_emitted_composition_weight_is_arithmetically_impossible`.

## After the check (2026-10-01)

The check of this sweep listed must-fix, should-fix and taste items. What was
applied, and what was not and why.

### Applied

| item | file | change |
|---|---|---|
| M1 home, present tense for an unbuilt feature | `home.html` | "You can also call wards yourself" → "You will also be able to call wards yourself"; the two bullets under "Not built yet" now say "will show" and "will carry" (also should-fix "home · tense") |
| M3 about, "largest 55 parties" | `src/build_validation.py` → `about-the-model.md` (`--from-json`) | 55 was the artefact's row cap, not the rows shown. Now "The largest parties in each city, by seats won in 2021; the note under each table says how many are shown." Each table's note already prints `len(shown)`. |
| M5 corrections, 27 September table | `corrections.md` | column header "today" → "on 27 September" |
| M6 methodology grammar | `methodology.md` | "handed parties … more than the entire electorate" → "gave parties … more votes than the entire electorate"; the verbless excessive-seats sentence → "The excessive-seats clause catches the ANC in {{p_excessive_anc}} of simulations: …"; "measures by how much … separately for each party" → "measures the gap for each party from its own national-to-local transitions on record" |
| claim 1 since box | `claims.toml` (rendered into `forecast-sheet.html`) | "no longer appears in any simulation"; "A DA majority depends less on turnout than it did" |
| privacy | `privacy.md` | "If that changes, this page changes with it." restored |
| support | `support.md` | "two kinds of backer only" restored |
| review since box | `review.md` | "the ANC triggers the excessive-seats clause in {{p_excessive_anc}}"; adds "No poll has been an input since 12 September 2026", the date in a `data-asof="2026-09-12"` span as on the forecast dateline |
| about, standfirst repeated by first paragraph | `src/build_validation.py` | paragraph cut; "Every figure here is generated … None was typed by a person" → "Every result on this page is generated from the run recorded at its foot. The examples under *The technical measures* are illustrations." |
| forecast typed figures | `forecast-sheet.html`, `drafts/forecast-draft.html` | "about 4,450 of the {{n_draws}}" → "that share of the {{n_draws}}"; "all 15 CoJ by-elections" → "all CoJ by-elections" |
| forecast repetition | `forecast-sheet.html` | Limits bullet "Viability is not intent" keeps its first two sentences; "The model says which deals have the numbers, not which will happen" cut (its token stays) |
| corrections last paragraph | `corrections.md` | the 23 September check keeps its date and verdict and one sentence naming the draft entries; the figures of drafts no reader saw are cut; the HTML comment says so |
| play, unexplained "effective simulations" | `interactive/js/model.js`, `interactive/js/play-card.js` | the page's band note defines the term ("the number of equally weighted simulations the re-weighted set is worth"); the share card says "the range covering nine in ten of the re-weighted simulations. They count as N of M equally weighted ones." The live count stays. |
| taste: "overwhelmingly" softened to "mostly" twice; contrast clause dropped | `methodology.md` | restored |
| claims proposals | `claims-proposals.md` | C1 steps[0] "every registered DA voter"; C3 steps[0] "against the ANC and the DA"; C4 steps[0] heading no longer says "about half"; C4 steps[2] keeps "on this arithmetic" and its inline reason, note rewritten |
| `stats.toml` | | the `"4,450"` audit entry (its sentence is gone) and the orphaned `"12"` entry removed |

No token was added, removed or moved: the `{{…}}`/`[[…]]` sequence of every
changed page source is identical to `84f7084`.

### Not applied

| item | why |
|---|---|
| home seat table order (§7) | Re-sorting the rows moves tokens. |
| methodology typed figures (300,000; 560,000; 18.12%; 6.22%; 42/18/35/25%; "about ten points"; "seven elections … six seats"; "3 of 4 wards on 23%") | Making them tokens adds tokens and `stats.toml` entries. |
| methodology "Where polls fit" self-correction → /corrections | Both misstatements were in the repository between deploys: the live site served the 8 August build until 26 September. Whether a reader saw either is not established. If none did, the sentence should be deleted, not promoted to a correction. Owner's call. |
| corrections, "the most reliable majority" entry | Its text is STYLE.md §3's own example. |
| share card wording "matching simulations" | Re-weighting selects nothing; every simulation is kept with a weight. "Matching" misdescribes it. The term is defined instead (above). |
| `src/reweight.py` refusal "{n} effective simulations of {m}" | Changing it changes the interactive copy, the code hash and the fixture. Left as it is. |
| remaining taste items | left |

### Correction for M4 (applied in `85254b1`; text as drafted here, the live entry is in `corrections.md`)

> **What was wrong.** The standfirst of "When the ANC falls, nobody catches the
> votes" said the opposition captured none of "the 587,000 votes the ANC shed
> between 2016 and 2021". The figure is the ANC bloc's loss between the 2019
> national election and the 2021 local election, as the forecast article
> states it.
>
> **What changed.** The standfirst now reads "… the 587,000 votes the ANC bloc
> shed between the 2019 national election and the 2021 local election."

### Seen, not changed

- `/about`, "Saying 'between 85 and 95 seats' and being right scores better
  than saying 'exactly 90' and being right": under CRPS a point forecast that
  is exactly right scores 0, the best possible. The example is wrong as
  written.
- The newsdesk's `bin/sync-context.sh` was not run; claim 1's since box changed
  again.

### Verification (after the check)

- `render_sheet` and `render_home` reproduced the committed pages exactly
  before any edit; `build_validation --from-json` reproduced
  `about-the-model.md` byte for byte.
- `site_text --export` then `--apply --dry-run`: "no edits to apply."
- Scratch build (`--out <scratch>`, copy of `publications/`): 0 unsourced
  figures, 0 unsourced claims, 0 blocking; 319 tokens, 0 new, 0 visibly
  changed.
- UAT build of `site/` (copy of `publications/`, ledger cut to its first 665
  rows, `--publish --change-class mechanism --reason` = the reason on the
  `r-c68c627d287e` rows): 0 blocking; 319 rows appended to the scratch ledger
  (984). The real ledger's sha256 is unchanged.
- `src/deploy_check.py` passes.
- `/play/` screenshots retaken (`interactive/tools/play_screenshots.mjs`, port
  8801): no page errors.

## Done since (2026-10-02)

| item | where | status |
|---|---|---|
| M2 claim 4, "about half the time", "a coin flip", verdict "A COIN FLIP" | `claims.toml`, `corrections.md` | done in `85254b1`: heading, clause and verdict corrected, with a /corrections entry. The entry now says the figure was 59% "on 26 and 27 September" (was "on every edition") |
| M4 the 587,000 standfirst | `articles.toml`, `corrections.md` | done in `85254b1`, with a /corrections entry |

## STYLE.md rule 9 (2026-10-02)

Owner: "Almost every subheading contains duplication of the body text first
line." Rule 9 added to `STYLE.md`. Every page standfirst and section intro was
checked against its first paragraph, and every prose sentence met on the way
for a main verb. `render_doc` now prints no standfirst when it is empty.

| page | change |
|---|---|
| /corrections | standfirst removed (it repeated the page's own opening lines) |
| /methodology | standfirst is the owner's wording; the body's restating first sentence cut, its two pointers kept. "Three checks, in increasing order of difficulty." and "To use every poll received …" given verbs |
| /about | standfirst names the 2021 election, the eight cities, the census exception and the three baselines ("simple alternatives"); "What this page is" says the example forecasts and scores under *The technical measures* are made up |
| /review | standfirst removed; the frozen first paragraph says the same |
| /sources | standfirst rewritten; the body's restating first sentence cut, the pointer to `SOURCES.md` kept. The claim "Every number in this model traces back to a public record" is gone (see below) |
| /support, /privacy | standfirsts given a subject and verb |
| home | "How this is built" teasers given verbs; "How to read the page" teaser now says what that section says; "Not built yet." → "Until it is built, …" |
| /forecast | claims band lede given a verb |
| /play/ | "Seat law" intro given a verb |
| portal | standfirst's first sentence given a verb |
| /corrections | new entry for the 26 September /about leak sentence; four-figures entry cut to two parts, the third table column (the model's 26 September figures 61, 58, 65%, 47%) dropped |

Frozen text the rule would change: `standfirst-proposals.md`.

No token added, removed or moved. Typed figures deleted: the four in the
dropped table column.

### Left for the owner

- /methodology standfirst (owner's wording) has no main verb, against rule 9's
  own second sentence. One-word fix: "This page explains how the council is
  elected, …".
- /about body, "using only what a forecaster could have had before polling day"
  (`build_validation.py`, "How it was tested"): the 2022 census is used, as the
  page's own "What this does not prove" says. The standfirst now states the
  exception; the body sentence does not.
- /sources: the standfirst's "Every number in this model traces back to a public
  record" was dropped, not reworded. The values in `JUDGEMENT-CALLS.md` trace to
  no public record.
- /play/ lede, "Each control picks out the simulated elections that match your
  settings": re-weighting keeps every simulation with a weight, and the
  by-election control switches between separate runs. A mechanism description,
  not changed.
- /methodology "How accurate is it?" and "How we know it works" both describe
  the eight-city backtest.


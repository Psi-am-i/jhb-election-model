# Share sheets: one graphic and one line per article and per claim (mock-ups)

Owner, 2026-10-11: *"we need share sheets for each article and also party claims. Many are just headline. A single graphic and a line that goes with it."*

Mock-ups only. Built against the release tree `atlas-jhb-site-release` at `dfa92dc`. Nothing in `src/`, `site/`, `content/`, `data/` or `publications/` was edited, and nothing was deployed.

## How the mock-ups were made

`make_mockups.py` runs the release tree's real `build_site.main` into a temporary `--out` with no `--publish`, so it appends no ledger row and writes its number review beside the temporary output. It wraps `build_site.share_images` and `og_pages.figure_pool` to keep the token pool the build hands to the share images. Each card spec is then built with og_pages' own helpers: `_fig` refuses a token no page printed or one printed two ways, `verdict_badge`, `stamp_path`, `kind_colour`, and `check`, which refuses a glyph the card faces lack or a carried figure that is not drawn. `mock-cards.mjs` draws the specs. It takes the frame from `og-pages.mjs`'s own `LAYOUTS.article` with an empty headline and adds the new graphic, using share-card.js primitives, the owner's stamps from `src/stamps/` and `site/logos/`. Rasterising goes through `og-raster-node.mjs`. Bar lengths come from the token records' `value`. Every printed string is the token's `display`.

To check the pipeline, the two images that already exist were also rendered here, `article-nobody-will-win.png` and `claims-page.png`. Both are **byte-identical** to the live `site/og-page/nobody-will-win-mcnbdedcnhnc.png` and `claims-aaojcljlbcij.png` (same md5).

Re-run: `cd atlas-jhb-site-release && <main>/.venv/bin/python <this folder>/make_mockups.py`. It writes `specs.json`, `share-lines.json`, every PNG and `contact-sheet.png`.

## Page → graphic → tokens → share line

Each share line is shown with its tokens, and each token's resolved value is in [brackets]. Characters are counted on the resolved line. The limit is 200.

| page / image | graphic | figure tokens on the image | share line | chars |
|---|---|---|---|---|
| `/nobody-will-win` · `article-nobody-will-win.png` | unchanged: seat ranges of the six largest parties, majority line | `seats.<CODE>.median/p5/p95`, `majority`, `p_alone`, `seats.band`, `generated_date` | Chance any one party wins a majority of Johannesburg's council: {{p_alone}} [0.1%]. The ANC's middle is {{seats.ANC.median}} [66] seats, the DA's {{seats.DA.median}} [66]; a majority is {{majority}} [136]. | 131 |
| `/nobody-catches-the-votes` · `article-nobody-catches-the-votes.png` | two bars on one scale: votes lost by the ANC bloc and by the DA bloc | `bloc_leak_votes` [587,000], `hist_da_bloc_change_votes` [52,000] | Between 2019 and 2021 the ANC bloc in Johannesburg shed {{bloc_leak_votes}} [587,000] votes. The DA bloc lost {{hist_da_bloc_change_votes}} [52,000] over the same period. The ANC's lost votes became abstention. | 156 |
| `/minority-administrations` · `article-minority-administrations.png` | the page's table as four chance bars from 0 to 100%. Candidates in alphabetical order (ANC, DA; STYLE 7), page order within each candidate, labels from the page's table | `minority.ANC_minority_only_DA_opposes` [48%], `minority.ANC_minority_DA_ASA_oppose` [13%], `minority.DA_minority_ANC_EFF_MK_oppose` [4.0%], `minority.DA_minority_only_ANC_opposes_2021_pattern` [50%], `generated_date` | Abstention can elect a minority mayor. Opposed only by the DA, an ANC candidate wins: {{minority.ANC_minority_only_DA_opposes}} [48%] chance. Opposed only by the ANC, a DA candidate: {{minority.DA_minority_only_ANC_opposes_2021_pattern}} [50%]. | 143 |
| `/if-the-law-were-german` · `article-if-the-law-were-german.png` | one bar per seat law: the council at its size, ANC and DA seats inside it, majority tick, council size at the end | **none exist**: read from the rendered regimes table (see *Could not source*) | The same simulated votes under four seat laws. Ours keeps the council at {{regime.deduct.council}} [270] seats; Germany's 2015 law grows it to {{regime.level.council}} [287] so every party's seats match its vote. *(both tokens proposed)* | 157 |
| `/laingsburg-2021` · `article-laingsburg-2021.png` | headline = the page's `<h1>`. The chance the clause fires for the ANC, large, over a 0 to 100% bar, with ANC wards (middle) and entitlement under it | `p_excessive_anc` [62%], `anc_ward_median` [60], `anc_entitlement` [58], `generated_date`. These are the live tokens, not the `pub0831_*` pinned ones | Johannesburg's excessive-seats clause has fired once before, in Laingsburg in 2021. Chance it fires for the ANC in Johannesburg in November: {{p_excessive_anc}} [62%]. | 145 |
| `/claims` · `claims-page.png` | unchanged: one badge per party | none | What the parties say about Johannesburg's council vote, each claim tested against the forecast and given a verdict. | 115 |
| claim: Zille, 490,000 voters · `claim-da-turnout-majority.png` | quote (full), DA logo, speaker, outlet; FALSE badge; figure | `claim_half_surged` [644,000], `claim_zille_votes` [490,000]. Both are fixed tokens from the 7 August test, so the date line reads "Figures from that test" | Helen Zille: {{claim_zille_votes}} [490,000] DA voters would win the DA a majority. If they all vote, the total rises and half of it is {{claim_half_surged}} [644,000]. Verdict: FALSE. | 136 |
| claim: Masemola, absolute authority · `claim-anc-absolute-authority.png` | cut quote, ANC logo; NEAR IMPOSSIBLE badge | `claim.anc_alone.share` [under 0.1%], the claim's `chance` | Dickson Masemola asks for the ANC to have absolute authority in Johannesburg. Chance it wins a council majority alone: {{claim.anc_alone.share}} [under 0.1%]. Verdict: NEAR IMPOSSIBLE. | 156 |
| claim: Baloyi, biggest party · `claim-mk-biggest-party.png` | cut quote, MK logo; EXTREMELY UNLIKELY badge | `claim.mk_largest.share` [1.4%], the claim's `chance` | Bongani Baloyi says MK will be the biggest party in Johannesburg. Chance MK wins the most seats: {{claim.mk_largest.share}} [1.4%]. Verdict: EXTREMELY UNLIKELY. | 131 |
| claim: Zille, red lines · `claim-da-coalition-red-lines.png` | cut quote, DA logo; VERY LIKELY badge | `claim.red_lines.no_red_share` [87%], the claim's `chance` | Helen Zille rules out coalitions with the EFF and MK. Chance of a council majority without the ANC, the EFF and MK: {{claim.red_lines.no_red_share}} [87%]. Verdict: VERY LIKELY. | 142 |
| claim: Mashaba, Soweto · `claim-asa-soweto.png` | quote (full), ActionSA logo; VERY LIKELY badge | `claim.soweto.realistic_given_none` [23%]. The verdict rests on its complement, which no page prints (see *Could not source*) | Herman Mashaba: the DA cannot win Joburg without Soweto. If it wins no Soweto ward, chance the DA governs with ActionSA and the PA or the ANC: {{claim.soweto.realistic_given_none}} [23%]. Verdict: VERY LIKELY. | 169 |

The `[[name]]` → token map for the claims is read from `render_sheet.py`'s `since_vals` and `chance(...)` calls with a regex, which is its one definition. Nothing was matched by hand.

### Proposed claims.toml fields (shown on the mock-ups)

| claim `label` | `slug` (no digits) | `quote_short` |
|---|---|---|
| 490,000 DA voters would win the city outright | `da-turnout-majority` | none (full quote fits) |
| The ANC can govern Johannesburg alone again | `anc-absolute-authority` | "We can only be able to do so if the people of greater Johannesburg give their organisation, the ANC, absolute authority" |
| MK will be the biggest party in the city | `mk-biggest-party` | "According to us, we are going to be the biggest party in the city" |
| A majority without the ANC, the EFF and MK | `da-coalition-red-lines` | "We won't go into a coalition with MK, and we will not go into coalition with the EFF" |
| The DA cannot win Joburg without Soweto | `asa-soweto` | none |

Each cut is a contiguous, word-aligned piece of the quote with no ellipsis. A slug carries no digit for the same reason og_pages names images in letters: the number scan reads `content="…"` attributes, and the per-claim URL appears in `og:url`.

## How the line is emitted

**What the pages emit today** (checked in the built HTML):

- `og:description` on an article is its articles.toml `standfirst`, with its tokens rendered by `plain_tokens` (`build_site.artefact_head`). On `/claims` it is the description typed in `ARTEFACTS["claims.html"]`.
- There is **no `twitter:description`**. `OG_META` carries `twitter:card` and `twitter:image` only, and X falls back to `og:description` [argued, documented platform behaviour, not tested here].
- **No article and no claims page has a share control.** `grep -c "navigator\|share-sheet"` gives 0 for `nobody-will-win.html` and `claims.html`. `navigator.share` exists only in the interactive (`interactive/js/share-sheet.js`, `share.js`).

**Proposed:**

1. A new optional field, `share_line`, in each `[[article]]` and `[[claim]]`. It holds `{{tokens}}` and no typed figure, and is rendered through the same `plain` path as the standfirst, so its figures are recorded and ledgered under the page.
2. Emitted as `og:description` and as a new `twitter:description`, added to `OG_META` and rewritten by `page_og`. The standfirst stays on the page and stops being the card text.
3. If the owner wants a share button on articles and claims, it passes `{title, text: share_line, url}` to `navigator.share`, with copy-link as the fallback, as the interactive does. That is new reader-facing UI and a separate brief item.

## D1: how a claim gets its own image

**Recommendation: (a), a static page per claim at `/claims/<slug>`.** Each page holds that claim's box, its own `og:url`, `canonical`, `og:image`, `og:description` (the claim's `share_line`) and a link to all claims. `/claims` gives each box `id="<slug>"` and a "link to this claim" pointing at `/claims/<slug>`.

Why (a) and not (b), a Worker rewrite of `/claims?c=<slug>`:

- The Worker already runs first for every request (`wrangler.toml` `run_worker_first = true`), so (b) is a small route either way.
- (b) cannot be indexed, adds an edge dependency to every claim share, and has to rewrite `og:url` too. Platforms key the card on `og:url`, so leaving it at `/claims` collapses every claim back to the page image.
- (a) is static. It refuses at build time like the other share images, and it puts the reader on the claim.

**Cost of (a):**

- `render_sheet.py`: emit each claim box with a stable `id` and write one page body per claim.
- `build_site.py`: render those pages with `page_og`.
- `og_pages.py`: `designed` recognises `claims/<slug>.html`, plus a `claim_spec` and a `claim` layout in `og-pages.mjs`. `mock-cards.mjs` `claim()` is the draft.
- claims.toml: `slug`, `quote_short`, `share_line`.

Each claim's figures are printed twice, on `/claims` and on its own page. The `AMBIGUOUS` rule already refuses a mismatch. Also confirm the assets binding serves `claims/<slug>.html` at `/claims/<slug>` beside `claims.html`; this was not tested here. The tier is interactive (sharing) under QC §4b.

## Production

- Two private functions in `og-pages.mjs` are copied in `mock-cards.mjs`, `headline` and `stamp`. The frame is borrowed by calling `LAYOUTS.article` with an empty headline. Production would add `bars`, `councils`, `meter` and `claim` as layouts inside `og-pages.mjs`, beside `article`, and drop the borrow.
- `articles.toml` `og_visual` gains `"bars"`, `"councils"` and `"meter"`. `og_pages.VISUALS` and `article_spec` name each visual's tokens, as it does for `seat-ranges`.
- Laingsburg: `og_headline` set to the page's `<h1>` text, which the mock reads from the page.

## Tests to add (`tests/test_og_pages.py`)

1. **Population, both directions:** the set of image specs equals articles.toml entries + claims.toml entries + the designed pages, and every page or claim named in the specs exists in the toml.
2. **Share line:** at most 200 characters resolved. No digit outside `{{…}}` after tokens are stripped. That rule fails the three lines that type a year today (*Could not source*, item 4), so it lands with those fixed. The German line also fails it on its two proposed tokens, until they exist. Every token in a line resolves through `_fig`.
3. **Per-claim badge = that claim's printed verdict**, matched claim by claim, not as the multiset that `claims_spec` checks today. Mutation: change one verdict in a fixture claims.toml, and the test goes red. Revert it, and the test goes green.
4. **A claim card's figure is the claim's `chance` token** when the claim is chance-rated. A `"1 - <name>"` claim is refused until its complement exists as a generated token.
5. **`quote_short` is a word-aligned contiguous substring of `quote`.**
6. **Per-claim page head:** `og:url` and `canonical` are `/claims/<slug>`, `og:image` is that claim's image, and the slug has no digit and is unique.
7. **Bar geometry from records:** each drawn bar's value equals the record `value` of the token printed beside it. This catches a bar drawn from one token and labelled with another.

## Could not source from a token (not typed in; listed)

1. **German regimes table.** `render_sheet` writes it into the page from `regime_*_summary.json` and `regime_*_seat_draws.csv`. No cell is a token, so `figure_pool` has none. The mock reads the cells from the rendered `<table class="rg">`, and its `figures` is empty, so these figures are **unledgered**. The image needs the tokens `regime.<rule>.council`, `regime.<rule>.majority` and `regime.<rule>.<party>.median`. The run date of the non-`deduct` regime summaries was not checked.
2. **The Mashaba verdict's figure.** The verdict is rated on `1 - realistic_given_none` [77% by subtraction, printed nowhere]. The card shows the printed `realistic_given_none` [23%] with a label stating the event. Proposed: a generated token `claim.soweto.not_realistic_given_none`, made through `stats.render` as `og_pages.coalition_figure` does.
3. **Laingsburg's own figures.** The DA's ward wins, its entitlement, the council's seats and the KDF's lost seat are words in the article. Only `hist_laingsburg_da_share` is a token. The card therefore shows Johannesburg's live figures. A Laingsburg graphic needs fixed tokens with IEC provenance (OG spec D3).
4. **Years.** "2019", "2021" (nobody-catches line and chart note), "2015" (German line) and "2021" (Laingsburg line) are typed. The German row labels and the Laingsburg headline are the page's own words, read from the page. The Laingsburg headline and the minority table label also contain "2021".
5. **The Zille FALSE card** draws `claim_half_surged` and `claim_zille_votes`, which are fixed tokens inside the page's `data-asof="2026-08-07"` passage. `og_pages.ledger_records` files every image figure as `dated: False, asof: ""`. These two are not superseded today, but production should carry the record's own `dated`/`asof` for such a figure. The alternative is the live `claim.da_alone.share` [0.1%] from the claim's "since" note.

## Owner decisions

| | decision | options |
|---|---|---|
| S1 | D1: per-claim URL | (a) `/claims/<slug>` static pages, recommended; (b) Worker rewrite on `/claims?c=<slug>` |
| S2 | where the share line goes | `og:description` + new `twitter:description` (recommended), and/or the text of a share button that articles and claims do not have today |
| S3 | live or published figures in a frozen article's share line | the lines for nobody-will-win, minority and Laingsburg use live tokens, as nobody-will-win's image already does with "Figures as of". A share line carries no date. Alternatives: date it, or use the article's pinned figures |
| S4 | `quote_short` wording | the three cuts above |
| S5 | Zille FALSE card figure | the arithmetic `claim_half_surged` (drawn), or the live `claim.da_alone.share` |
| S6 | Mashaba card figure | add the complement token (drawn as 77%), or keep the printed 23% with its label (drawn) |
| S7 | German graphic | add regime tokens, or drop the graphic and keep the headline-only image |
| S8 | Laingsburg graphic | Johannesburg's live chance (drawn), or Laingsburg's own figures once tokenised |

## Files

`BRIEF.md`, `make_mockups.py`, `mock-cards.mjs`, `specs.json` (every card spec as drawn), `share-lines.json` (each line: template, review form, resolved, character count), the eleven PNGs and `contact-sheet.png`.

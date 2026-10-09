# Item 9 implementation spec: a share image for each page

Brief: `BRIEF.md` item 9 (owner, 2026-10-09). Mock-ups: `og-design/` (generator
`make_og.mjs`, `contact-sheet.png`). Process: `QC.md` §4b. Written read-only on
2026-10-09 while another writer holds `src/levels.py`, `src/montecarlo.py`,
`src/seats.py`, `src/backtest.py`, `tests/`, `JUDGEMENT-CALLS.md` and
`MACHINERY.md`; nothing here was run against the build.

Each statement is marked **[read]** (verified by reading the named file and
line) or **[argued]** (reasoned, not checked). Section 8 lists what the owner
decides before code is written.

---

## 1. What exists today

| fact | where | status |
|---|---|---|
| Every page's `og:image` and `twitter:image` is `https://joburg.whysoserious.city/og.png`, typed once in `OG_META` | `src/build_site.py:213-225` | [read] |
| `page_og(og, title, href)` rewrites description, title, `og:url` and canonical by regex over `OG_META`; it never touches `og:image`, `og:image:alt` or `twitter:image` | `build_site.py:600-616` | [read] |
| Three callers of `page_og`: `artefact_head` (ARTEFACTS pages and articles), `shell` (render_doc pages: methodology, sources, review, corrections, support, privacy), and `/your-forecast/` | `build_site.py:523`, `:635`, `:1168` | [read] |
| `index.html` returns bare `OG_META` (the site-wide card) | `build_site.py:516-517` | [read] |
| Each ARTEFACTS page is rendered by `statlib.render(html, registry, ctx, record=seen)`; `seen` holds one mapping per token occurrence with `token`, `value`, `display` (the string the reader sees), `fmt`, `source` | `build_site.py:1146-1148`, `src/stats.py:721-737` | [read] |
| `plain_tokens` resolves tokens to bare figures for an attribute (the article share-card description) | `build_site.py:476-483` | [read] |
| Seat ranges are inline tokens `{{@seats.<CODE>.median\|p5\|p95=…}}` written by `render_sheet` from `scenarios.seat_quantiles`, and the same numbers as `data-m/-p5/-p95` attributes on the seat table rows; `build_play.py:112` already reads rows back by those attributes | `render_sheet.py:531-543`, `seat_table.py:95`, `build_play.py:112` | [read] |
| The seat axis scale is `seat_table.SEAT_SCALE` (the mock-up types `max = 150`) | `build_make.py:1317` | [read] |
| A claim's verdict is typed in `claims.toml`, and `claims_faults` refuses the build when it disagrees with `CHANCE_SCALE` applied to the chance the page prints | `render_sheet.py:38-100`, `:128-176`, `:836` | [read] |
| Claim boxes carry no `id`; the mock-up captions `/claims#1`…`#5` are not addresses on the site | `render_sheet.py:855` | [read] |
| Raster path: `src/og-raster.js` `rasterise(Resvg, svg, fonts)`; under node, `interactive/tools/render_cards.mjs` `toPNG(svg)`, which loads resvg-wasm from `worker-api/node_modules` and the faces from `src/card-fonts/` | files as named | [read] |
| `render_cards.mjs` reads `interactive/tests/share-fixture.json` at import, and `assets()` takes party colours from that fixture | `render_cards.mjs:19`, `:29-37` | [read] |
| `make_og.mjs` copies `share-card.js`'s private primitives (`esc`, `text`, `rect`, `brand`, `chip`) and says so | `make_og.mjs:24` | [read] |
| `share-card.js` is served under `/your-forecast/js/` and listed in `LIVE_WRITERS` with no region | `src/stats.py:292-295`, `build_your_forecast.py:89` | [read] |
| `/og/1/link.png` and `/og/1/story.png` are Worker routes; `/og.png` is the Worker's `FALLBACK_IMAGE` | `src/share-edge.js:11-16`, `:60` | [read] |
| `share-edge.js` rewrites the tags named in `TAGS` (`og:title`, `og:description`, `og:url`, `og:image`, `og:image:alt`, `twitter:image`) on `/your-forecast/?<forecast>` | `share-edge.js:134-156` | [read]; that its rewrite replaces whatever value is present rather than the literal `/og.png` is [argued], check before building |
| No build step calls node; `build_all.run` is the subprocess precedent | `build_all.py:35-51` | [read] |
| `site/logo.svg` and `site/logos/*.png` are tracked in git | `git ls-files` | [read] |

### The owner's badges

`audits/2026-10-07-stamp-design/owner-stamps/verdicts/`, committed in a73bd43
("for the share images"), after the mock-ups were drawn. [read]

| verdict word (`render_sheet.VERDICT_STEP`) | file | dominant fill |
|---|---|---|
| FALSE | `false.svg` | `#ff144b` |
| TRUE | `true.svg` | `#049837` |
| NEAR IMPOSSIBLE | `near-impossible.svg` | `#ba0900` |
| EXTREMELY UNLIKELY | `extremelyunlikely.svg` | `#ff2d02` |
| UNLIKELY | `unlikely.svg` | `#ff8137`, `#ffc6a5` |
| VERY LIKELY | `very-likely.svg` | `#04ce04` |
| A COIN FLIP | none | |
| QUITE LIKELY | none | |
| NEAR CERTAIN | none | |

The files are Affinity exports: DOCTYPE, `xmlns:serif`, `style="fill:…"`
attributes, viewBox about 2864 × 2533, words drawn as paths (no `<text>`, no
`<image>`). [read] Their fills are not the page's verdict colours
(`src/css/tokens.css:30`, `--v-false` … `--v-true`). [read]

`owner-stamps/prediction.webp` is a VP8X WebP with alpha, 2864 px wide. [read]
Whether resvg-wasm 2.6.2 decodes WebP is [argued: unknown].

The mock-up stamps are drawn by `make_og.mjs` `stamp()`, not the owner's files.

---

## 2. Architecture: Python resolves, node draws

One rule: **the renderer receives every figure and word as data and types
none.** The node module holds layout constants only (positions, sizes, the
kind colours).

### Files

| file | change |
|---|---|
| `src/og_pages.py` (new) | Builds one **card spec** (JSON) per page from the page's own render, calls the renderer, names the output by hash, returns the tags. Python-side layout choice: page type → layout (§3). |
| `src/og-pages.mjs` (new, not served) | `node src/og-pages.mjs <specs.json> <out-dir>`: for each spec, draws the SVG for its layout and rasterises it through `og-raster.js`; writes `<out-dir>/<slug>-<hash>.png` and prints a JSON manifest `{slug: filename}`. Its layouts are `make_og.mjs`'s five functions with every page read and every literal figure removed. |
| `src/og-raster-node.mjs` (new) or a split of `render_cards.mjs` | `toPNG(svg)` without the fixture import, so the build does not load `share-fixture.json`. `render_cards.mjs` then imports `toPNG` from it (one definition). |
| `interactive/js/share-card.js` | Export `esc`, `text`, `rect`, `brand`, `chip` (today private, copied into `make_og.mjs`). Option B in §7 keeps them private and duplicates them; the no-duplicated-logic rule argues for exporting. |
| `src/build_site.py` | `OG_META` gains an image placeholder; `page_og` gains `image` and `alt` parameters; the ARTEFACTS loop, `render_doc`/`shell` and the `/your-forecast/` assembly fill them after render (§5). Remove nothing else. |
| `src/render_sheet.py` | If per-claim pages are approved (§8, D1): emit each claim box with a stable `id` and write the per-claim page bodies. The claim box markup is otherwise unchanged. |
| `content/joburg/claims.toml` | New optional fields `slug` (stable URL part) and `quote_short` (the marked cut, replacing `make_og.mjs`'s index-keyed `SHORT` dict, which mis-assigns the moment a claim is inserted). |
| `content/joburg/articles.toml` | New optional field `og_headline` where the image's set lines differ from `title` (the mock-ups break "Nobody will win Johannesburg" from a longer title); and `og_visual` naming the article's visual (§3). |
| `src/og_badges/` or `site/stamps/` | The six badge SVGs, copied from `owner-stamps/verdicts/` with a table `BADGE = {verdict word: file}` in `render_sheet.py` beside `CHANCE_SCALE` (one list of verdict words). |
| `tests/test_og_pages.py` (new) | §6. Registering it in `tests/run_all.py` waits until the other writer has released `tests/`. |

### Order inside `build_site.main`

1. Render the page exactly as today, with `record=seen`. **[read]** this is
   where every displayed figure is already produced.
2. `og_pages.spec_for(output, html, seen, articles, claims)` builds the card
   spec: figures are taken from `seen` by token name, using `display`, so the
   image shows the string the page shows.
3. After every page is rendered, one call `og_pages.render_all(specs, out/"og-page")`
   runs node once for all specs (one wasm init) and returns the manifest.
4. Each page's head placeholder is replaced by its image URL, then
   `statlib.audit`, `scan_numbers` and the write run as today. **[argued]**
   whether `scan_numbers` flags the hex digits of a hash in a `content="…"`
   attribute is unknown. Check it first; if it does, the hash goes in a form
   the scan ignores or the scan's attribute rule is extended, and that change
   goes through `number_scan`'s own tests.

Steps 3-4 mean audit and write move after all renders. If that reorder is
judged too wide, the alternative is two passes: render once for specs, render
again with the URL. That alternative costs a second `statlib.render` per page
and nothing else. [argued]

---

## 3. Page type → layout, and each figure's source

Kind bar colours, palette, logo position, footer rule and date line are fixed
across layouts (`make_og.mjs` `frame()`). Every layout puts the headline as the
largest element, top left, cap line level with the logo.

| page | layout | headline source | visual | figures and words, each with its source |
|---|---|---|---|---|
| `/claims` | claims index (`claimsIndex`) | ARTEFACTS title for `claims.html` (`build_site.py:446-447`) | one badge per party, first claim per party in `claims.toml` order | verdict word: `claims.toml` `verdict` after `claims_faults`; party short name and colour: `render_sheet.CHIPS`/`NAMES`; speaker: `claims.toml` `speaker`; "latest tested" date: max of `claims.toml` `published` |
| one claim (needs D1) | claim (`claimCard`) | the quote: `claims.toml` `quote`, or `quote_short` when it does not fit | the owner's badge for the verdict word | party name `party_name`; speaker; outlet `outlet`; tested date `published`; logo `site/logos/<logo>.png` |
| `/nobody-will-win` | article with seat ranges | `og_headline` or `title`, `articles.toml` | seat ranges, six largest by middle | middles and ends: `seen` entries `seats.<CODE>.median/p5/p95` (or the `data-m/-p5/-p95` row attributes, as `build_play.py:112` reads them); majority line: token `majority`; "one party majority" chance: token `p_alone`; axis: `seat_table.SEAT_SCALE`; band wording ("9 of 10 simulations"): from the quantiles `scenarios.seat_quantiles` uses, as a named constant there, not typed; published date: `articles.toml` `date`; "figures as of": token `generated_date` |
| `/laingsburg-2021` | article with vote and seat bars | as above | two 100 % bars | the mock-up TYPES the IEC's WC051 votes and seats. Not buildable as drawn: either tokens are added for them (source `law/sources/iec-lge2021-seat-calculation-detail-wc051-laingsburg.pdf`, registered in `stats.toml` as fixed with provenance) or the image drops the bars (D3) |
| the other three articles | article | as above | not designed (D3) | |
| `/forecast` | forecast (`forecastMap`) | `OG_TITLE` (`build_site.py:209`), one definition; the mock-up types "Who governs Johannesburg?" | the page's ward map, contested wards striped as geometry (`stripedMap`), taken from the rendered page's map SVG | tokens `p_anc_largest`, `p_da_largest`, `generated_date`, `council_size`; vote date: `election.toml` `election_date` |
| `/your-forecast/` | interactive (`interactive`) | `build_your_forecast.OG_TITLE` or a declared `og_headline` | a solid map | ward calls: the mock-up uses the share fixture's reader A. The build must not ship fixture calls as if they were a prediction. Options: our published prediction's calls (STYLE.md rule 11: then it is labelled as our prediction), or an unfilled map (D4). Council size and date as `/forecast` |
| `/`, `/commentary`, render_doc pages | not designed | | | D2 |

**Not to be carried over from `make_og.mjs`:** the `page()` reads of built
HTML, the `token()` scrape of `data-current`, `SHORT`, `LB`, `max = 150`,
`maj = 136`, "270 seats", "vote on 4 November 2026", "Published 8 August 2026",
the per-code ink choices for KDF and PA, and `assets()`'s fixture colours
(party colours come from `render_sheet.CHIPS`). [read: each is a literal in
`make_og.mjs`]

Glyphs: the card faces are Latin-1 subsets (`src/card-fonts/`, file names
`*-Latin1.ttf`). [read] A quote with a character outside Latin-1 renders as a
missing glyph with no error. [argued] The spec builder refuses a string with a
character no card face covers.

---

## 4. Regeneration and naming

- The image is rendered on every build. The file name is
  `<slug>-<first 12 hex of sha256 of the SVG string>.png`. A changed figure,
  word, layout or badge changes the SVG and therefore the URL; a crawler's
  cache of the old URL is then irrelevant. [argued: X and Facebook key their
  card caches by image URL]
- Hashing the SVG, not the spec, means a renderer change also renames. Fonts
  and the resvg version are not in the SVG; a font file change does not rename.
  Including `sha256` of the font files and resvg's version in the hash input
  closes that. [argued]
- The build writes the current set into `<out>/og-page/` and deletes every
  other file there, so the directory holds exactly what pages reference.
- Directory name: `/og-page/`, not `/og/`, because `/og/1/…` is a Worker route
  and `/og.png` its fallback. [read] Before building, confirm that
  `share-edge.js`'s route matcher does not catch `/og-page/` and that the
  Worker's root-city path handling serves it for `joburg`. [argued]
- `site/og.png` stays as the Worker fallback and the image of any page D2
  leaves undesigned.
- A failure in the node step (missing `worker-api/node_modules`, a resvg
  error, a missing badge) stops the build. It never leaves the previous image
  or `og.png` in place silently. Running `npm ci` in `worker-api/` becomes a
  build prerequisite, stated in `build_site.py`'s docstring.

## 5. Tags per page

`OG_META` keeps its shape; `page_og` writes, for every page with an image:

```
<meta property="og:image" content="https://joburg.whysoserious.city/og-page/<slug>-<hash>.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="<headline>. <one-line description of the visual>">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="<same URL>">
```

`page_og`'s existing self-check (`out.count(url) != 2`) is extended to assert
the image URL appears exactly twice (`og:image`, `twitter:image`) and the alt
was rewritten. The alt text carries the same figures as the image, from the
same `seen` entries. `share-edge.js`'s per-forecast rewrite on
`/your-forecast/?…` must still replace these tags; it matches by tag name.
[read for `TAGS`; argued for the replacement behaviour]

---

## 6. Tests

`tests/test_og_pages.py`. Each scan-shaped test meets CLAUDE.md §4's four
parts: right population, it looked (two-sided bound), it can see (a constructed
violation caught and quiet again when reverted), constructed input.

1. **Every page has its own image, and every image has a page.** Build into a
   temporary `--out`. Population: the pages `build_site` writes (ARTEFACTS ∪
   render_doc outputs ∪ `/your-forecast/`), computed from those tables, and
   asserted equal to the set scanned. Forward: each page's `og:image` and
   `twitter:image` are equal, name a file in `<out>/og-page/`, and that file's
   PNG header reads 1200 × 630. Reverse: every file in `og-page/` is referenced
   by exactly one page. Bound: the number of distinct images lies between the
   number of designed pages and that number plus the claims count. Constructed:
   delete one PNG from a built tree, and add an unreferenced one; both caught,
   both quiet when restored.
2. **Every figure in an image is the page's figure.** For each spec, every
   figure field equals the `display` of the `seen` entry it names. Population:
   the figure fields of each layout, listed by the layout, asserted equal to
   the fields compared. Constructed: alter one spec figure; caught; reverted;
   quiet. Plus a literal scan of `src/og-pages.mjs` with
   `stats.SCRIPT_FORBIDDEN`'s data-block pattern, so a typed array of figures
   cannot enter the renderer.
3. **The name moves with the content.** On a constructed spec: change one
   figure, the hash changes; revert, it returns. Change nothing, two renders
   give identical bytes. (Regenerate, never compare mtimes.)
4. **Badges, both directions.** Every verdict word in `VERDICT_STEP` either
   has a file in `BADGE` or is in the declared missing set D5 decides; every
   file in the badge directory is in `BADGE`; the two populations asserted
   equal to what was scanned. Constructed: remove one entry, caught; restore,
   quiet. And: a claim whose verdict has no badge makes `og_pages` refuse (or
   take D5's fallback), tested on a constructed claim.
5. **Tags.** `page_og` on a constructed page writes all six tags; a malformed
   `OG_META` makes it refuse.
6. **Glyph coverage.** A constructed quote with a character outside the faces
   is refused.

The first implementation checkpoint (QC §4b step 4) is one `toPNG` call on one
owner badge embedded as `brand()` embeds the logo: it settles whether resvg
renders the Affinity `style="fill:…"` attributes, before any layout code is
ported. A second is one `toPNG` on `prediction.webp`, or its PNG conversion.

## 7. Check tier (QC §4b)

- **Option A (recommended): export the primitives from `share-card.js`.** A
  served module the interactive share cards use changes, so the tier is
  **interactive behaviour**: §6's module, `site_assets`, `site_structure`,
  `number_scan`, the share-card node tests by file, `render_cards.mjs` (its
  output compared by eye against the committed screenshots), `yf_jump_check`,
  the site build to `--out`, screenshots of five tag-bearing pages and of every
  generated PNG.
- **Option B: duplicate the primitives in `og-pages.mjs`.** Tier is
  **cosmetic**, but it breaks the one-definition rule; not recommended.
- No model run and no full suite: no `src/` module `run_model` imports changes
  and no published figure changes. `render_sheet.py` changes only if D1 is
  approved and only in markup and page emission.

## 8. Owner decisions

| | decision | why it is needed |
|---|---|---|
| D1 | **How a claim gets its own image.** A crawler reads one `og:image` per document and ignores the fragment, so `/claims#3` shows `/claims`'s image [argued, standard crawler behaviour]. Options: (a) a page per claim, `/claims/<slug>`, holding that claim's box and a link to all claims; (b) a Worker rewrite of `TAGS` on `/claims?c=<slug>`, as `share-edge.js` does for `/your-forecast/`. (a) is static and indexable; (b) adds an edge route. | The brief requires a per-claim image; nothing today can carry one. |
| D2 | **Home, `/commentary`, and the render_doc pages** (methodology, sources, review, corrections, support, privacy): keep `og.png`, or get a layout (e.g. the forecast layout for the home page). | The brief says "each page" and names four types. |
| D3 | **Article visuals.** Laingsburg: add tokens for the IEC WC051 figures, or drop the bars. The other three articles have no designed visual. | The mock-up types the Laingsburg figures. |
| D4 | **The interactive's map.** Our prediction's calls (labelled as our prediction), or an unfilled map. | The mock-up shows the share fixture's reader A, which is not a real prediction. |
| D5 | **Missing badges: A COIN FLIP, QUITE LIKELY, NEAR CERTAIN.** The EFF claim in `EFF-CLAIM-DRAFT.md` would be NEAR CERTAIN. A verdict moves when its chance crosses a band edge, so any claim can land on a missing word after a model run. Options: the owner draws the three; the build refuses a claim without a badge; or it falls back to the drawn stamp (`make_og.mjs` `stamp()`) for those words only. | The approved mock-ups used drawn stamps; the badges arrived after. |
| D6 | **Badge colours.** Use the files' own fills, or recolour to the page's `--v-*` steps so the image's badge matches the page's verdict pill. | They differ today. |
| D7 | **Where the prediction stamp (`prediction.webp`) goes.** No layout in the brief or the mock-ups uses it; the interactive layout is the candidate. | Committed "for the share images" with no stated place. |
| D8 | **Whether the interactive tier (Option A) is acceptable** for a change the brief tiers as cosmetic. | §7. |

## 9. Risks

- **Node becomes a build dependency.** A machine without
  `worker-api/node_modules` cannot build the site. The build refuses rather
  than shipping `og.png`.
- **Hash in an attribute vs the number scan** (§2 step 4). Unknown until run.
- **Audit and write move after all renders** (§2). A failure in the image step
  now stops a build that would previously have written the HTML.
- **Badge rendering.** Affinity `style=` fills and a 2864-unit viewBox inside
  resvg are untested [argued]; the first checkpoint settles it.
- **WebP in resvg-wasm 2.6.2** is unknown; convert to PNG at asset preparation
  if it fails (Pillow is already a dependency of `prep_logos.py` [read: it
  writes PNGs; the import itself not re-read]).
- **The striped map's source.** `forecastMap` slices the map SVG out of the
  built page by searching for `<pattern`. In the build the spec builder takes
  the map from the rendered page in memory; a change to the map's markup can
  break the slice with no error. A test asserts the extracted map has as many
  ward paths as the ward count `render_map` reports.
- **`/your-forecast/` with a forecast in its query** must keep its per-forecast
  image; a page default that `share-edge.js` fails to replace would put the
  generic interactive image on every shared reader forecast.
- **Fonts' Latin-1 subset**: names and quotes with characters outside it.

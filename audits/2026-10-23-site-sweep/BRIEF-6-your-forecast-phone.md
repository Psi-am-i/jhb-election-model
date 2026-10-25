# Brief 6: /your-forecast on phones, the buttons, and the site's width

Owner's message, 2026-10-25, with screenshots. Branch `site-sweep-1`. A writer
makes the edits; I review the diff; then the publish build and UAT. Every
reader-facing word below is the owner's; **add no other words** (memory
`no-unapproved-reader-words`). If an edit seems to need a word this brief does
not give (an aria-label, a title, a hint), stop and list it in the report with
your proposed text; do not write it.

Sources: `interactive/` (built into `site/your-forecast/` by
`src/build_your_forecast.py`), `src/build_play.py`, `src/build_site.py`,
`site/css/site.css` is BUILT from its source; find the source and edit that.

## Part A. The page header on /your-forecast (phone widths, up to 640px)

The header holds "Published forecast" and, once the reader changes anything,
the purple "Your changes" block. Owner: "optimise the space".

1. **Parties along the top, using every line.** At phone widths the party
   chips flow across the full width with no wasted space at line ends; the
   "Published forecast" label and "Majority 136" do not take a line of their
   own if they can share one.
2. **"Your changes" underneath, full width.** The purple block sits under the
   published row, spans the full width, and shows each party's seats with its
   ▲/▼ change as the wide layout does now (the ▲1 / ▼1 marks), plus the
   settings line ("Your changes: Black African turnout +3.5 points; …; +1
   more") the page already writes.
3. **A tiny map in the header.** A small copy of the reader's ward map
   (current calls, the page's own colours). On mouse-over it grows; on a
   click or tap it scrolls the page to the full ward map. It is live: it
   reflects every ward call. **It is a LIVE-region write**: register it with
   the region-writer scan (`your-forecast.html` lines 36-43, `make.js` lines
   9-18, `stats.LIVE_WRITERS`) so the scanner test stays green; one module
   writes it. Draw it from the existing ward paths (`ward_paths.json`), not a
   second copy of the geometry. Needs an accessible name: propose one in the
   report.
4. **Gaps.** At phone widths the large empty gaps (after section 1's
   introduction, before "Most seats:", around the ward map) go; sections sit
   at the page's normal paragraph spacing. Find the cause (min-height, fixed
   height, a reserved LIVE region) and say what it was.

## Part B. Calling the wards

5. **The instruction**, at every screen size much bigger and bold, and
   reading exactly: "Choose a party below, then tap or drag across wards to
   give them ward wins." It replaces the current hint
   ("Choose a party, then tap or drag across wards to give them to it.",
   `make.js` near line 585). The other hint state ("Giving wards to X. Tap
   or drag across wards.") stays as it is.
6. **Remove the compass sectors**: the North / East / South / West area
   selector and its hint "Areas are compass sectors drawn from the ward
   boundaries, not the City's regions." (`your-forecast.html` near lines
   239-246) and the code only they use. Keep the map's N arrow.

## Part C. The buttons

7. "Share this prediction" becomes "Share My Prediction". Grep every
   reader-visible instance (page, share dialog, share card, OG text, tests)
   and list them in the report; change the button text; list the others for
   me to decide.
8. "Analyse my prediction" in a different colour from Share My Prediction,
   same shape and size. Use the site's existing accent or secondary token;
   no new colour value.
9. **Both buttons side by side, under the council block**, each inside a box
   styled like the step boxes, its existing caption underneath the button:
   Analyse with "Our badge for your prediction, your map ward by ward, and
   each party's seats and vote."; Share with "Your map, your seats, our badge
   for your prediction, and a sealed link." The "4 See how likely it is"
   heading and "17 predictions sealed so far." line stay with their buttons.
   On phones they stack, full width.

## Part D. Site-wide

10. **"Follow us on X"** under "Support Our Work" in the header, at the same
    size and style, same link (`build_site.X_URL`). The footer link stays.
11. **Width.** The page content's maximum width matches the header and
    footer's, on every page (no wide side indents on a large screen).
    Reading-width text blocks may stay narrower inside it; say which you
    kept narrow and why.
12. **Home page, the "Your prediction" card** (and the forecast card beside
    it): the button centred in its column, with space between the last text
    and the button.
13. **The map key** ("Solid: one party wins the ward…", "Stripes: …", "Tap a
    ward for its numbers."): each swatch sits next to its own sentence, the
    two entries on separate lines when they do not fit on one, and "Tap a
    ward for its numbers." left-aligned under them. On every page that draws
    the key.

## Not in this brief

- The "Where each party's votes come from" chart (OWNER-DECISIONS item 40),
  the ward/list vote control (item 41) and a phone-only instruction
  (item 42): do not touch.

## Limits

- No forecast number changes; no `montecarlo.py`, no re-emit, no writes under
  `data/`.
- Targeted tests: the interactive's suite (`interactive/tests`), and
  `tests/run_all.py -k site_structure -k home_page -k site_assets -k
  number_scan -k og_pages -k stat_sources -k publication_ledger -k
  quarantine` plus any module that pins a string you change. No whole suite.
- Look at it: screenshots at 375px, 640px and 1440px of /your-forecast (top,
  map, vote, buttons), the home page and one article with the map key, from a
  local preview on port 8801 (never 8765). Save them under
  `audits/2026-10-23-site-sweep/brief6-shots/` and list them.
- One commit per part. Do not run `revive_retire.py --apply`,
  `build_site.py --publish`, or deploy.
- Do not sub-delegate. Report: each change with before and after, the cause
  of the gaps, every word you needed and did not write, test output, commits,
  screenshots.

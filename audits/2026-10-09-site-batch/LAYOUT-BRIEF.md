# Brief: layout notes of 2026-10-10 (owner, after the local preview)

QC.md §4b. Draft for the owner's approval; nothing runs before it.

## Items

1. **Two-name share card.** Owner: few readers will share someone else's
   forecast; it might work with celebrities, set up as an "X vs Y" matchup,
   and it should say the result comes on election day. This release: remove
   the two-name card from the share choices. Backlog: an "X vs Y" matchup
   card. *Tier:* interactive.
2. **Home page.**
   a. "What this is" moves to the right; the articles list goes on its left.
   b. The map and party totals become a simplified version, not a copy of
      the forecast page's, with a clear link to the detailed forecast.
   c. A big, obvious **PREDICT THE ELECTION YOURSELF** button (the title link
      is not obvious).
   *Tier:* cosmetic (figures stay tokens; the simplified map uses the same
   draws).
3. **Your Forecast page.** Heading "Your Forecast"; the subheadline above it
   removed. Share buttons and "Analyse my forecast" become large, prominent
   buttons in place of the brown slabs. *Tier:* interactive.
4. **Footer notes** set in two columns. *Tier:* cosmetic.
5. **Commentary.** Opening an item shows other items from the same list
   under the article, so a reader moves between items without going back.
   *Tier:* cosmetic.
6. **One layout across pages.** The toolbar is identical on every page; the
   party-claims page's toolbar width and text-block width apply to every
   page. Your Forecast and other map pages may be wider where needed, by one
   shared wider width. The Your Forecast layout must not shift. *Tier:*
   cosmetic plus the interactive's node tests and `yf_jump_check`.

## Out of scope
Any forecast number; the model; the "X vs Y" card itself.

## Open
- Article share images: remove, or move the headline down (owner's line).
- FALSE badge: owner re-export, or redraw the flattened spikes in our copy.

## Process (owner, 2026-10-10: "I want the layout work done right now")
Approved. No mock-up stage: the owner reviews in the local preview. Two
writers in parallel, split by file ownership:
- **Writer S (site):** items 2, 4, 5 and 6 for every page `build_site.py`
  builds. Owns `src/build_site.py`, `src/render_home.py`, `src/render_sheet.py`
  page assembly, `content/`, `docs-public/`, `site/css/` sources and
  `tokens.css`. Defines the shared widths as CSS custom properties in
  `tokens.css`: `--page-width` (the party-claims page's toolbar/page width),
  `--text-width` (its text-block width), `--wide-width` (map pages, one value),
  and the one toolbar markup/CSS.
- **Writer I (interactive):** items 1, 3 and the Your Forecast half of item 6.
  Owns `interactive/` and `src/build_make.py`/`build_your_forecast.py` page
  markup. Uses the three custom properties and the shared toolbar as defined
  by writer S (names fixed above); does not edit `tokens.css` or `site.css`.
- Each writer: write, self-check (imports, a scratch build), commit, report;
  diff review; then targeted checks; preview rebuilt for the owner.

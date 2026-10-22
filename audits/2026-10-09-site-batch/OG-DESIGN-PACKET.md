# Item 9 packet: a share image for each page (mock-ups only)

One front-end designer. **Write only to `audits/2026-10-09-site-batch/og-design/`.**
Mock-ups only; nothing in `site/`, `src/` or `interactive/` is edited. Do not
sub-delegate. If you serve pages, use port 8802 (8801 is in use, and 8765 is
never to be used).

Read `CLAUDE.md`, `STYLE.md` (rule 11: forecast, prediction, result),
`audits/2026-10-09-site-batch/BRIEF.md` item 9, and the owner's screenshot
`owner-shots/03.29.10.png`: the generic logo image with a small title. Also read:
- the share-card pipeline (`interactive/js/share-card.js`, `src/og-raster.js`,
  `interactive/tools/render_cards.mjs`, `interactive/tools/card_fonts.mjs`);
- the pages (`site/claims.html`, `site/nobody-will-win.html`, the other article
  pages, `site/forecast.html`, `site/index.html`);
- the owner's stamps (`audits/2026-10-07-stamp-design/owner-stamps/`).

Produce 1200×630 PNGs, rendered through the real raster path
(`render_cards.mjs`' `toPNG` with the card fonts), not a browser screenshot, so
what you show is what the pipeline can make:
1. **Claims page:** the headline "The parties' claims, tested", large, plus a
   strip of the five verdicts.
2. **One per claim, all five:** the quote (shortened only where it must be,
   marked), who said it, the verdict as a stamp, and a small date line.
3. **Two articles:** "Nobody will win Johannesburg" and one other. Headline large,
   plus one visual from that article (a map cut, a seat bar, or the article's
   headline figure).
4. **The forecast page:** headline, plus the striped map or the seat ranges.
5. **The interactive:** "Make your prediction", plus a visual.

Show them together as a contact sheet of how a feed of these would look side
by side. The owner wants posts that do not all look the same, so vary layout
by page type while keeping the type, palette and logo consistent.

Figures in the mock-ups may be today's values taken from the built pages'
`data-current` attributes, each labelled in a caption as such. The build will
take them from tokens. Look at every PNG before reporting. Return the file list
and one paragraph on the system: what varies and what is fixed.

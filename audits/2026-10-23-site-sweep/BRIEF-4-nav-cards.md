# Brief 4: the nav break, the share cards, the phone layout

Owner, 2026-10-24, with screenshots: "Please remove the forced break in our
menu items. i.e after party claims" and "it looks like all our social share
cards have had their images deleted. That cannot happen in future. The cards
should be dated "as of [date]" and left alone." Branch `site-sweep-1`; runs
after the suite fixes, before the next UAT upload. A writer makes the edits;
I review the diff.

## 1. The nav

`src/build_site.py` `nav_for` renders the items in two `navgroup` spans split
after `NAV_FIRST_GROUP_ENDS`, which forces a line break after "party claims".
Render one group; the items wrap only where the width makes them. Remove
`NAV_FIRST_GROUP_ENDS` and any CSS or test that exists only for the split.
Check the header at desktop and phone widths.

## 2. Share images are never deleted

**Cause.** `og_pages.render_all` deletes every file in `site/og-page/` that
the current build does not name ("so it holds exactly what pages name").
Each build gives a changed card a new hashed name, so every earlier card's
address stops resolving. A post shared before then (the ANC claim card,
posted 19 October, image `claim-anc-absolute-authority-oodpfkhobkjd.png`,
deleted 22 October) shows no image.

- `render_all` writes new images and deletes nothing. A file of the same
  name is never overwritten with different bytes: refuse instead.
- Restore every image ever committed under `site/og-page/` and since deleted,
  from git history, byte for byte (`git log --diff-filter=D`); report the
  count and confirm each restored file's blob hash equals the deleted one.
- A test: plant an old image in a temporary out dir, run the image step,
  assert the old file is still there and unchanged; and a check (build or
  `deploy_check`) that every `site/og-page/*.png` ever committed is present.
- Records: the docstring and MACHINERY.md say images are kept forever.

## 3. Each card is dated

Each card prints "as of <date>", the date its figures were published, in
the "24 October 2026" form, from the same date the page prints (no typed
date). Placement: the card's existing small text line; show me a rendered
card of each layout (forecast, claims, claim, article, interactive) before
committing. These are the only new words.

## 4. Your prediction, phone layout

Owner, 2026-10-24: "on mobile layout for your Prediction - In the first
section Changing Our forecast, the first thing should be the map and party
table. They are last. The order is right in Your Prediction." In "Adjust our
forecast" (`#adjust`), the DOM order is `.pl-controls` then
`.pl-resultscol`; the desktop media query in `interactive/css/play.css` sets
them side by side, and at phone width they stack in DOM order, so the map and
the party table come after every control. At phone width, put
`.pl-resultscol` first, matching the "Make your own prediction" section. Keep
the desktop layout and the sticky controls unchanged; check that nothing
sticky covers the results at phone width, and that tab order still follows
what the reader sees (if `order` alone would break it, move the markup).
Show me screenshots at 390 px and at desktop width.

## 5. The council bar's words (owner item 37)

In `src/render_map.py`, the bar label "The full council — {council} seats, the
most typical simulation" becomes "The full council, {council} seats: the
simulation closest to every party's median" ({council} stays computed), and
the caption sentence "The bar shows the whole council, ward and list seats
together, in the most typical simulation." becomes "The bar shows the whole
council, ward and list seats together, in the simulation closest to every
party's median seat count." Owner's words, 2026-10-24; nothing else changes.
Re-render the map region of `forecast-sheet.html`.

## Limits

No forecast number changes; no writes under `data/`. Targeted tests
(`-k og -k site_structure -k build_site -k deploy`); no publish, deploy, push
or sub-delegation.

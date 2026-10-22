# Items 1, 2 and 4 packet: front-end design options (mock-ups only)

One front-end designer. **Write only to `audits/2026-10-09-site-batch/design/`.**
Do not edit `site/`, `interactive/`, `src/` or any CSS in place. Mock-ups are
standalone HTML files that link or copy the site's real CSS tokens and fonts
(`site/css/`, `site/fonts/`, IBM Plex), plus PNG screenshots at 375 px and
1440 px. Use Playwright from
`/Users/simondavis/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs`.
Serve on port 8801 if you need a server, never 8765. Do not sub-delegate.

Read:
- `CLAUDE.md`;
- `STYLE.md`, including rule 11: forecast, prediction, result. "Make your own
  forecast" becomes prediction language;
- `audits/2026-10-07-prediction-restructure/BRIEF.md`. Phase 2 moves the levers
  onto `/forecast`; a reader's own entry is "Your prediction" on
  `/your-prediction/`;
- `site/your-forecast/index.html` and `interactive/css/your-forecast.css` (the
  current sections);
- `site/index.html` (the home page);
- the owner's screenshots in `audits/2026-10-09-site-batch/owner-shots/`:
  - 01.06.55: the purple "Your changes" bar;
  - 01.07.01: the "N wards change their most likely winner" line;
  - 01.42.48: the call-to-action box on the home page.

## Item 1: a callout box for the forecast levers

The owner's words: "these two sections top and bottom of forecast are great
but hidden. Put them together in a call out box which has a nice layout. 1.
what user changed. 2. what actually moved. and put that purple box at the top
and bottom of the forecast."

Design one box with two parts:
- **What you changed:** the lever settings, as today's bar lists them.
- **What moved:** the wards whose most likely winner changed, as today's line
  lists them, plus whatever else the page already computes that moved (seat
  middles, chances). Read `interactive/js/play*.js` for what exists. Invent no
  new statistic.

Include "Back to the forecast". The box appears at the top and at the bottom of
the forecast section. Show it with no changes (hidden or a quiet state, you
choose and justify), with one change, and with many changes (long lists).

## Item 2: the same for the prediction

What the reader changed from our prediction (wards repainted, votes moved) and
what that does to the council (seats per party, largest party, majority), using
what `make.js` already computes. Propose the wording. The owner has not worked
it out, so give two wording options.

## Item 4: the call to action, redesigned

The owner: "this needs a flashy call to action redesign. can front end
designer give us some options?"

Give three distinct options, from restrained to bold, each in prediction
language. Each keeps the substance:
- you can make your own prediction;
- it is sealed with the time;
- it is ranked against the result;
- privacy in one line.

At least one option uses the stamps (`audits/2026-10-07-stamp-design/` holds
the owner's SVGs). Keep the site's palette and type. No stock imagery.

## Return

The file list (HTML and PNG), one paragraph per option on its trade-offs, and
any wording that needs the owner's approval. Typed figures are not allowed in
the mock-ups except as obvious placeholders.

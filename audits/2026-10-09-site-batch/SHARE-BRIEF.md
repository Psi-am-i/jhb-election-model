# Brief: sharing on every page (owner, 2026-10-11)

QC.md §4b. Owner, after showing the live site: "need more share sheets with
images or something for all articles and party claims. Party claims shares
them all... not one by one. And we need to add 'share' button to pretty much
every page."

## Items

1. **One claim, one share.** Each party claim gets its own address
   (`/claims/<slug>`), a static page built by `build_site.py` holding that
   claim's card (quote, who said it, verdict stamp, the figure that decides
   it) with a link back to all claims. Each gets its own share image: the
   quote large, the owner's verdict stamp, the party logo, the speaker
   (OG spec D1 settled as "a page per claim"). The claims page links each
   claim to its page. The image figures are the page's own tokens.
2. **A share button on every page** (home, forecast, claims, each claim,
   each article, commentary, methodology and the other documents, Your
   Forecast keeps its own). One component, placed in one position on every
   page (by the page title), opening one share sheet: the page's share image
   shown, Share… (Web Share API where available), WhatsApp, X, copy link,
   download image. The interactive's existing sheet is the model; one
   definition of the sheet, reused, not a second copy.
3. **Article share images** stay as built (headline, date); the sheet in
   item 2 shows them.

## Out of scope
The model; forecast numbers; the reader card's badge (investigated
separately); the X-vs-Y card.

## Checks
Interactive tier: page modules, number scan, node tests by file, scratch
build, screenshots of the sheet on three page types at 375 and 1440, each
claim page and its image. Whole suite once before the release.

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

## Process
Design mock-ups for items 2, 3 and 6 first (screenshots of the proposed
layout), owner approves, then code, diff review, checks, preview.

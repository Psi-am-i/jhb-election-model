# Brief: Joburg over time, an animated results map (owner, 2026-10-13)

QC.md §4b. Owner's direction 2026-10-13: "yeah that would be really nice
actually... go for it." The design points below are his, except where marked
"agent's choice".

## What it is
An animated map of who won each Johannesburg ward at every election since
2000. These are results maps: what happened, never a forecast or a
prediction (STYLE.md rule 11). Nothing from the model is used.

## Placement (owner)
- A small version on the home page.
- A new menu item and page, "Joburg over time", with the full version.

## The map (owner)
- Party colours exactly as the site uses now. A bolder colour means a
  stronger win.
- Strength is the winner's share of the valid vote in the ward.
- **Bands (agent's choice):** under 40%, 40-50%, 50-60%, 60-75%, 75%+, from
  palest to boldest. One definition, declared in JUDGEMENT-CALLS.md as a
  presentation call.
- **A key** showing each party's logo and colour, for the parties that win
  at least one ward in the frames shown.
- **Controls:**
  - click or Enter runs and stops the animation;
  - Left and Right arrows step one election at a time;
  - a frame changes every 0.75 s by default, with slower and faster options.
- **Reduced motion:** with `prefers-reduced-motion`, nothing plays on its
  own; stepping still works.
- **The year and election** are shown large on each frame, e.g. "2016 · local
  election" or "2019 · national election".

## Timelines (owner)
Local elections are the default timeline:
- 2000, 2006 and 2011, 2016, 2021.
- 2026 is added after the result.

National elections are an option, as either one combined timeline or a
separate one, chosen by a switch:
- 1999 (the file is marked approximate);
- 2004, 2009, 2014, 2019 and 2024.

## Data (agent's choice of method, owner approved the approximation)
1. **Elections with their own ward geometry:**
   - 2011 on the 2011 wards (from `data/raw/geo/wards2011_SA.gdb.zip`,
     Johannesburg only);
   - 2016 on `wards2016_JHB.geojson`;
   - 2021 on `wards2020_JHB.geojson`;
   - 2026 later, on `wards2026_JHB.geojson`.

   Aggregate each file by its own `Ward` column.
2. **2000 and 2006 local, and 1999, 2004 and 2009 national** have no ward
   geometry of their own:
   - re-count each voting district (`VD_Number`) into the 2011 ward that
     carries that district number, and draw on the 2011 wards;
   - 99% of the 2000 and 2006 districts exist in 2011 (645 of 652 and 723 of
     727); report every unplaced district and its votes;
   - where a 2011 district is split across wards, assign it by
     `montecarlo.ward_parts` or the 2011 file's own district-to-ward rows,
     and say which.

   A visible note on those frames: "Re-counted onto the 2011 wards; the
   boundaries then were different."
3. **National elections:** take each file's `Ward` column where that ward
   numbering matches a geometry we hold:
   - 2014 on the 2011 wards;
   - 2019 on the 2016 wards;
   - 2024 on the 2020 wards.

   Otherwise use the district method in 2. The winner is the party with the
   most national-ballot votes in the ward.
4. **Local elections:** the ward winner is the winner of the ward ballot.
5. **Party names:** map through `src/parties.canonical`. Parties that merged
   or renamed (for example the DP and NNP into the DA) are shown under the
   name they stood as that year, with the colour of their successor only if
   the site already does so. List every mapping used.
6. **Checks, in the build's tests:**
   - for each election, the sum of ward votes equals the file's total minus
     the unplaced votes, stated;
   - every ward in a frame's geometry has a winner or is marked no-data;
   - the winner counts per party match a direct count from the raw file.
7. **Size:** simplify the geometry and precompute one compact JSON per
   election. The home version loads lazily.

## Constraints
- No model code or forecast numbers are touched.
- Follow the site's existing conventions: build_site, tokens, STYLE.md,
  fonts, tests tiered per QC §4b.
- Must work at phone width and with the keyboard; the map has an accessible
  text alternative (for example a table of ward counts per party per year).

## Checks
- The data tests above.
- The keyboard controls in a node test or headless check.
- A screenshot of the home version and the page at desktop and phone width.
- The whole suite once.
- Then a UAT Version URL.

Promotion to live is the owner's.

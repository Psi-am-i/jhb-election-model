# Item 7 packet: animated Johannesburg election maps

One agent. **Read-only for the repository except this directory**
(`audits/2026-10-09-site-batch/maps/`). Do not run `src/montecarlo.py` as a
script, `compare_history`, `build_site` or anything that writes `data/`,
`site/`, `content/` or `publications/`. In-process `run_model` calls are allowed,
with output only to this directory. Use `.venv/bin/python`. Do not sub-delegate.

Read `CLAUDE.md` (§1 and §3), `STYLE.md` rule 11 and `src/render_map.py` (how the
forecast map draws contested-ward stripes: `ward_call`, `toss_bands`).

1. **Forecast maps.** For each past Johannesburg target the model forecasts,
   only from data before that election (2011, 2016, 2021, which have emitted
   pools; check), run `run_model` in-process the way
   `compare_history.run_city_year` sets it up (its default draw count), and draw
   the forecast map exactly as `/forecast` draws it: each ward's likely winner,
   with stripes for contested wards and the same colours and thresholds
   (import `render_map`'s functions; do not copy them). Also draw the published
   2026 forecast map from `data/processed` (the same as the live page).
2. **Real winners' maps.** For each election with Johannesburg ward boundaries
   in `data/raw/geo/` (`wards2011_JHB`, `wards2016_JHB`, `wards2020_JHB` for 2021,
   `wards2026_JHB`), draw the actual ward winners from the cleaned IEC files.
   Read them with `backtest.actual_result`, or the shared reader it uses.
3. **Two GIFs plus a side-by-side.**
   - `forecast.gif`: the forecast years in order, with 2026 last.
   - `results.gif`: the real years in order.
   - `side-by-side.gif`: forecast and result per year.

   Each frame carries the year and a one-line label: "Forecast made from data
   before the <year> election" or "Result, <year>". Use party colours from
   `build_play.roster()`. Ward boundaries change between elections; each frame
   uses its own year's boundaries. Use a still frame of about 2 seconds,
   phone-friendly sizing, and file sizes stated.
4. **Notes for the owner:** for each year, how many wards changed winner from
   the previous result, and the forecast's correct-call count against the
   result. Each figure states where it came from.

Return: the file list with sizes, the per-year notes, and anything you could not
do and why.

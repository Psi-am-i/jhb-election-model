# Tshwane: what exists, what is missing, the shortest path (2026-10-06)

A read-only survey of the repository on 2026-10-06 (owner: "make a to do list to
see if we can do Tshwane relatively quickly"). Nothing was run. File paths are
where each fact was read; re-check them before acting, the tree moves.

**Gate first.** `TODO.md` (other metros) says other cities wait until the
Johannesburg interactive is finished, Tshwane as a "ward and seat predictor with
headline numbers only", and not to start acquiring rolls before then. The owner
decides whether that gate is open now that Johannesburg is live.

## What exists

- `cities/tshwane.toml`: identity, structure, map block, newsdesk block. Its
  header says SKELETON: the judgements are Johannesburg's copied as placeholders
  and nothing may be published until each is reviewed. `structure.registered`
  is the 2021 roll.
- `judgements/tshwane-{2011,2016,2021,2026}.toml`. The 2026 file has party stubs
  with empty `parent`s and no `[roster]`.
- `data/processed/tshwane/`: pool specs 2011, 2016, 2021, 2026 (2026 with
  `roster_source: "projected"`), fold parameters, VD concordance, VD-ward 2026,
  turnout per year.
- Raw inputs: LGE 2000-2021 and NPE 1999-2024 results for TSH, seat calculation
  reports 2011-2021, ward and VD boundaries including 2026, the Gauteng certified
  candidates PDF (`data/raw/nominations/lge2026_certified_candidates_GP.pdf`),
  Gauteng by-elections.
- One recorded 2026 run: `audits/2026-09-28-seed-survival/results/tshwane-2026.json`.
- Backtest rows for Tshwane 2011, 2016, 2021 in `data/processed/history.md`.
- Worker routing for `<city>.whysoserious.city` (`src/worker.js`), a portal card
  per `cities/*.toml` (`src/build_portal.py`).

## Gaps, with the artefact that shows each done

### Inputs
1. **Certified roster (M).** `[roster]` in `judgements/tshwane-2026.toml` parsed
   from the Gauteng PDF (method: `SOURCES.md`, certified list; no parser in
   `src/` yet). Done: `inputs_preflight.py --strict --city tshwane --target
   2026` roster row OK, PDF ward set equals `vd_ward_2026.csv`, re-emitted spec
   says `declared`.
2. **2026 ward roll snapshot (S).** `archive/iec-registration-<date>/tshwane_ward_registration_<date>.csv`,
   read in a browser (CLAUDE.md §4b). Done: preflight roll row OK.
3. **`structure.registered` (S).** Find what reads it; update or confirm display-only.
4. **By-election deltas and gamma_recent for tshwane/2026 (S, optional).**
   Without them the model falls back silently.
5. **A Tshwane 2026 poll (owner).** None registered; `PLAN-TO-LIVE.md` holds
   metro readings back until after November.

### Model
6. **Judgement review of `cities/tshwane.toml` (M).** Scalars, VF+ as a
   first-class party, Defenders of the People, entrant parents, PA. Done: the
   SKELETON header removed, each call in `JUDGEMENT-CALLS.md`, a MODEL-LOG entry.
7. **Seat allocator on Tshwane's councils (S).** `validate_seats.py --city
   tshwane` for 2011, 2016, 2021 reproduces the IEC councils; record the run.
8. **Re-emit and run (S).** `pools.py --city tshwane --target 2026 --emit`, then
   `montecarlo.py --city tshwane --target 2026`. Done:
   `data/processed/tshwane/2026/forecast_summary.json`, `seat_draws.csv`.
9. **Portal path (S, silent).** `build_portal.py` reads
   `city.processed/forecast_summary.json`; Tshwane 2026 output goes to
   `data/processed/tshwane/2026/`. Done: the portal reads the target's processed
   directory, and a test builds a live Tshwane card from a fixture.
10. **`fold.py` reads Johannesburg's concordance (S, backtest only).**

### Site
11. **`content/tshwane/` (M)** if the full site is built: stats, home, articles,
    claims, election.
12. **Johannesburg hard-coding in the build (M):** `build_site.py` defaults
    (`--stats`, and `--out site`, which would overwrite Johannesburg),
    `site_text.py`, `build_interactive.py`, `render_home.py` (ANC/DA race), the
    Johannesburg prose in the model-doc pages and templates.
13. **Ward map (S):** `render_map.py --city tshwane`, check `rotate_deg`.
14. **Number review (S):** `content/tshwane/NUMBERS-REVIEW.md`.

### Interactive (leave out at first)
15. **Your forecast per city (L):** the build, `export_draws`, the Pyodide copies,
    share cards, seals and the entries database are Johannesburg's.

### Deploy
16. **`deploy_check` is single-city (S/M):** any `site/tshwane/*.html` would block
    the Johannesburg deploy. Done: it reads every city's review; a two-city test.
17. **Route and DNS (S):** a `custom_domain` entry in `wrangler.toml` and the DNS
    record.
18. **Portal numbers are not scanned (S):** `TODO.md`.

## Risks

1. The roster: the Gauteng PDF is the only source, there is no parser, and
   `complete = true` deletes every party it omits.
2. Unreviewed judgements and a weaker backtest (uniform swing beats the model on
   seats at Tshwane 2011 and 2016, `history.md`); no poll.
3. Plumbing never exercised for a second city, where the failures are silent and
   one Worker, one `site/` and one deploy gate serve both cities.

## Shortest path to a minimal page (headline numbers and seats)

Gate confirmed → roster (1) → roll (2) → preflight → bounded judgement pass (6)
and allocator check (7) → re-emit and run (8) → portal path (9) → a single-page
builder writing `site/tshwane/index.html` from `forecast_summary.json` and
`seat_draws.csv` with its own `content/tshwane/stats.toml` → number review (14)
→ multi-city `deploy_check` (16) → route and DNS (17) → UAT.

Leaves out: the interactive and sharing, methodology and review pages (link to
Johannesburg's), claims and articles, polls, coalition outputs. The page says
the forecast has no poll and lightly reviewed judgements.

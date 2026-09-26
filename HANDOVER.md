# Handover — current state and the nomination-day runbook

⛔ **THIS FILE CARRIES WHAT IS TRUE NOW.** Superseded banners are in
`HANDOVER-ARCHIVE.md` and are not maintained; durable findings are in
`MODEL-LOG.md`, which is append-only and dated. `CLAUDE.md` sends every session
here first, so anything stale in this file is read as an instruction.

> ## ⛔ STATE AT 2026-09-26 — THE TYPED-FIGURE GATE MEASURES ZERO BLOCKING IN A
> ## SCRATCH BUILD, AND NOTHING HAS BEEN PUBLISHED. INTERACTIVE: 3 OF 4 DECIDED.
>
> **Live pages are still the 31 August build.** Nothing was deployed or
> re-emitted this evening, and no forecast number moved.
>
> **Tidied.** Two sessions (Atlas, Scout) had worked this branch unaware of each
> other. Both checkouts are now at the same `remediation` head. Scout's stale
> uncommitted edits from 14 Sep (deleted `HANDOVER.md` / `PLAN-TO-LIVE.md` /
> `LAUNCH-THE-REVIEW.md`, a trimmed `POLLING.md`, an empty `agent-os/`) are
> **stashed on Scout, not dropped** — `git stash list` there, *"scout 2026-09-14
> local deletions"*; the owner decides whether any of it was meant. Four
> never-ending `pgrep` wait-loops on Atlas were killed. The two 24 Sep banners
> are in `HANDOVER-ARCHIVE.md`.
>
> ⚠️ **Scout cannot run anything**: no `.venv`, and its gitignored `data/` is
> ten days stale. Run the model, the suite and every measurement on **Atlas**.
>
> **Suite, full, Atlas: 770 passed, 2 failed, 18 skipped, no PARTIAL banner**
> (2026-09-25, wall clock 1008.6 s, after the home-page tests; the 24 Sep run at
> `4667fd7` was 761/2/18). The two failures are the standing ones, both in
> `test_pool_bounds`: the 2011 DA-in-White impossible weights and Mangaung
> 2016's pool rates summing to `[1, 1, 0, 1]`. The 24 Sep evening commit was
> documents and an audit folder only.
>
> ⛔ **The previous banner's item 1 was FALSE and nothing was changed for it.**
> It said `/nobody-will-win` did not exist. It does: `build_site.ARTEFACTS` has
> cut it from `forecast-sheet.html` since `5064975`, and it carries both
> `#nobody-catches` and `#minority`. `forecast.html` also forwards any anchor it
> lacks to that page. The owner's `articles.toml` hrefs are correct as they
> stand. ⚠️ The owner said *"point the hrefs at forecast"* on the strength of
> that false claim; it was not done, because the page already exists and
> `forecast#…` would redirect straight back to it. **Confirm with him.**
>
> **NEXT, in order. The pool-input window is PARKED behind its pre-registration;
> attention moves to the interactive and polling (owner, 2026-09-25).**
>
> ## A. THE INTERACTIVE — decided, and the first measurement is done
>
> **A1. ✅ Pyodide speed, measured 2026-09-25 (MODEL-LOG §1.260).** `run_model`
> called directly (never `montecarlo.py` — a bare run overwrites that city-year's
> forecast artefacts and `data/**` is gitignored), Johannesburg 2026, seed
> 20261104, no `run_dir`, BLAS pinned with
> `VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
> MKL_NUM_THREADS=1` because Pyodide is single-threaded:
> **fixed cost 14.79 s, 21.6 ms per draw, 300 draws = 21.3 s native.**
> The two figures this file used to carry as contradictory were CPU-across-threads
> against wall clock; the browser's 55 ms per draw is 2.5x native, an ordinary
> WASM penalty.
>
> **A2. ✅ MEASURED 2026-09-26 (MODEL-LOG §1.264), and it moved the problem.**
> Pyodide under **Node**, not a browser — same V8 WASM engine, but file reads go
> through NODEFS at disk speed, so this is a FLOOR for a browser. Fixed cost
> **25.06 s**, **48.3 ms** per draw, 300 draws **39.6 s** extrapolated; the
> spike's 55 ms was 14% high and nothing rests on the difference. A lever change
> that re-enters only the draw loop is **14.5 s**.
> ⛔ **The constraint is no longer speed. One run opens 75 files totalling
> 141 MB** under `data/` — nationwide VD-level CSVs at 4-9 MB each, read for a
> Johannesburg forecast. A page cannot ship that, so §9b's "the engine ships"
> needs a route: prune the inputs, precompute the fixed stage into JSON, or serve
> the fixed stage's output as an artefact. Only the third keeps "the page runs
> the real model" literally true. `openpyxl` is also a hard dependency of the run
> path (`pools.read_census` on the census `.xlsx`), not in Pyodide's core set,
> and parsing that spreadsheet is a large share of the 25 s.
> The harness is committed this time, at
> `audits/2026-09-26-pyodide-timing/measure.mjs` — the spike it replaces was lost
> by being left in a scratchpad. Run it with `npm install pyodide` beside it.
>
> **A3. Owner decision, 2026-09-26 (PUBLISHING-BACKLOG §9b):** the engine ships
> and the wait is handled in the page — a progress display carrying trivia from
> the model's own record rather than a spinner. Three constraints follow: the
> fixed cost is paid once at load and not per lever change (a design that
> re-enters the model each time turns 16 seconds into 35); every trivia figure is
> a token, not typed into the page script; the draw count stays at 300 and the
> page says its band is wider than the published 5,000-draw one.
>
> **A4. Then §9a's three model mechanisms**, which are model changes and come
> before the page: per-pool turnout applied AFTER the IPF (the only placement
> measured to move shares), the DA-share-among-Black-Africans slider with its
> range taken from the record rather than from the DA's claim, and per-poll
> selection. Each needs a pre-registration, a blind review, a JUDGEMENT-CALLS row
> and a 2026 liveness test, and all three go into ONE re-emit window.
>
> **A5. Undesigned, and the owner's** (§9a): how a reader's hand-built forecast is
> rated, given that the joint chance of 135 hand-picked ward winners is below one
> in any number of draws the page can run; and whether a leaderboard may store
> readers' forecasts, which §10 refused on the grounds that a stored forecast is a
> reader's political statement held on our infrastructure.
>
> ## B. POLLING — three items, all recorded, none started
>
> **B1. The trust ceiling is the owner's choice** (E = 3.0pp against >= 5pp), and
> the research behind it is now in
> `audits/2026-09-24-interactive-round1/poll-research/REPORT.md`: a third
> Johannesburg poll exists and is NOT in `polls.json` — Ipsos Khayabus,
> June-July 2026 fieldwork, released 4 September, ANC 31 / DA 28 / ASA 14 / EFF 8
> / MK 6 / PA 3 / Other 7 / DK 3, no published n, +-5.57 max MoE implying n ~= 310
> under SRS. Verified from the primary PDF. It is June-July fieldwork, not
> September, and the DA figure is 28, not the 27 reported elsewhere.
>
> **B2. A live defect: a poll with no `n` is priced MORE precise than SRF**
> through the `POLL_HOUSE_SD` fallback. That is backwards — an undisclosed sample
> size should widen, not narrow — and it is live in the code whether or not the
> poll channel is on.
>
> **B3. What must not be taken on trust.** Admitting any poll is a register change
> and goes through `polling.screen`. The per-house RMS table in that report is an
> agent's arithmetic over several secondary inputs and must be re-derived before
> any of it becomes a constant; Nelson Mandela Bay 2016 disagrees with
> `POLL_RMS_ERROR_2016`'s own provenance (agent 0.2 / 1.7 / 1.5 against
> polling.py's 3.9 / 2.7 / 0.9) and is unresolved. The finding that bears on the
> design: Ipsos is the only house with a scored Johannesburg reading, and SRF —
> the only house admitted at 2026 — has no scored local-election reading at all.
>
> ## C. THE POOL-INPUT WINDOW — AUTHORISED ON HONESTY (owner, 2026-09-26)
>
> *"lets go for more honest and wrap this up."* The window ships under
> `ITERATING.md`'s rule that a more honest model ships even when a headline score
> worsens. MODEL-LOG §1.263 records what it claims and what it does not: a flat
> score is the EXPECTED result, because the model's error is in the level and this
> is structure — panel PR vote MAE 3.15pp against ward vote MAE 2.98pp with the
> modal ward winner right in 96.76% of wards. The pre-registered nulls stand.
>
>
> `prereg/2026-09-25-pool-input-repairs.md` fixes what the emit may conclude
> before it runs. POOLS-REEMIT-QUEUE entries 30-33 carry the four changes.
> MODEL-LOG §1.255-§1.261 carry the evidence. The blind review is
> `audits/2026-09-25-pool-inputs/brief-pollster.md`, committed before it ran.
>
> **C1. The first item is a MEASUREMENT, not a repair:** how much of the emitted
> composition survives the per-draw IPF re-fit, written into the `--run-dir`
> trace per city-year and per party. It prices everything else on the seed side,
> and if little survives, entries 32 (the composition half) and 33 are deferred.
>
> **C2. Three nulls are pre-registered**, so a flat result is not a failure: the
> seat headline should not move for established parties (the centres are imposed
> through the IPF column margin); ward calls should not improve materially (the
> panel calls 2,120 of 2,191 wards, and Cape Town has the worst pool split on the
> panel while calling 342 of 343 with the three lowest Briers); and the one-party
> selection should survive every repair.
>
> **C3. The standing warning.** Enlarging the White pools may turn
> `test_no_emitted_composition_weight_is_arithmetically_impossible` green while
> the mechanism behind it is untouched: a pool composition carried across a level
> change with nothing coupling the two. All 14 cases in that scan are the DA,
> none at a 2021 target, every one where the DA grew since its fitting year. Live
> exposure: the joburg 2026 spec puts 83.6% of the DA's vote in a White pool that
> is exhausted at a DA citywide share of 38.9%, against 25.45% in 2021.
>
> **C4. A hard zero is a floor, not a measurement** (§1.261, owner's question
> 2026-09-26). The 2021 Johannesburg spec emits the PA at exactly 1.0 Coloured,
> which asserts it won 45.6% of every Coloured vote in the city and zero votes
> from anybody else. 245 of 3,417 member cells are exactly zero and 37
> party-city-years are single-pool across 19 of 24 specs. The fix already exists
> and fires only on infeasibility, which is why the live 2026 spec is spread and
> the 2021 one is a corner. Entry 33.
>
> **Superseded numbering below.** Items 1 and 2 are done; 3 is A above.
>
> 1. ✅ **DONE 2026-09-25 (atlas-claude).** Palace: diary
>    `diary_jhb_election_model_20260925_002025241464_98cd12b936b8`, drawers
>    `drawer_jhb_election_model_decisions_7e0bc936d29b2d6a66ef636d` (§9a) and
>    `…_findings_5ea60f9c604ae60fa6731d43` (the poll research, with the
>    report's caveats carried verbatim). Memory: the `/nobody-will-win` case
>    appended to `an-unticked-box-is-not-evidence`, and a new
>    `interactive-is-a-prediction-game` pointer.
> 2. ✅ **DONE 2026-09-25 — `tests/test_home_page.py`, nine tests, registered in
>    `run_all.MODULES`.** The four minimum items are covered: the regions
>    (regenerate the real page over a sentinel and see which ones move — the
>    survivors must be exactly the map regions, named by `render_map` and
>    `hex_cartogram`'s own constants), "everyone else" taken per simulation
>    (constructed `seat_draws.csv` whose columns deliberately do not sum to the
>    council, so the three wrong answers all differ from the right one),
>    exactly one `lead` (0 and 2 refuse, 1 runs first), and the typed-figure
>    gate. The lede's wording-by-number is covered too, each band on its
>    exclusive edge.
>    ⚠️ **What the item said was true and misleading.** No module *imports*
>    `render_home`, but `test_published_page.py:185` already regenerated it and
>    checked its tokens, and `index.html` is in `build_site.ARTEFACTS`, so the
>    build's audit already reached the page.
>    Two things moved with it: `build_site.audit_configs` was extracted so the
>    audit settings have ONE definition (the test is the first caller outside
>    the build, MACHINERY.md), and `render_home`'s `ENTRY_POINTS` exemption was
>    deleted — a test imports it now, so the exemption exempted nothing.
> 2b. ⛔ **FOUND WHILE DOING IT, AND IT IS ON THE DEPLOY PATH:
>    `build_site.py --publish` WILL REFUSE as the tree stands.** Typed figures
>    on three pages are `BLOCKS` rows in `content/joburg/NUMBERS-REVIEW.md`
>    (read its `blocking=` token, not a figure copied here; measure it with a
>    `build_site.py --out <scratch>` build, not by grepping the committed file).
>    ✅ **TEN ROWS BECAME TWO.** Every one cleared was the same defect — a
>    figure typed into prose beside the code that computes it — and not one was
>    cleared with a whitelist row:
>    * the seats note's `90%`, on BOTH pages, is `scenarios.BAND`; it is now the
>      tokens `home.band` / `seats.band`;
>    * `claims.toml` said "at least 30 of the ANC's usual wards" while
>      `render_sheet` counted that scenario with a literal `>= 30`. It is
>      `render_sheet.WALL_FLIPS` now, rendered as `claim.da_alone.wall_flips`,
>      so an edit to one can no longer leave the sentence describing a different
>      scenario from the number beside it;
>    * `corrections.md`'s five were not model figures at all — they record what
>      the published page showed on 2026-09-23, so that passage is now wrapped
>      as the dated statement it is. ⚠️ **They must never become tokens**: a
>      token recomputes, and the sentence would then describe today's page
>      rather than the one the correction is about.
>    ⛔ **MEASURED AGAIN 2026-09-26 (atlas-claude): THERE WERE THREE ROWS, NOT
>    TWO, AND ALL THREE NOW CLEAR.** `build_site.py --out <scratch>` stamps
>    `blocking=0`. What was there:
>    * the election date, twice — one register row matched on neither page.
>      Its `context` was the pre-24-September masthead wording. It is now the
>      substring both mastheads share, `City of Johannesburg · 4 November 2026`,
>      which clears index and forecast from ONE row. `classify()` in `stats.py`
>      matches on `value` + `context` only, so the row's `page` field is
>      informational and nothing parses it.
>      ⚠️ **The row's `source` was wrong and was corrected in the same edit.**
>      The IEC did not proclaim the date; the COGTA Minister, Velenkosini
>      Hlabisa, announced it on 7 August 2026 and the IEC welcomed it.
>      `reviewed` was set to 2026-09-26 — **that is the owner's attestation and
>      he has not yet confirmed it.**
>    * a THIRD row that the banner above could not have known about: `four`, in
>      "The same votes under four seat laws", added to `home.html` by this
>      branch's own last commit `c450f8e`. It counted `overhang_regimes.RULES`
>      plus ours — a figure typed beside the code that computes it. The prose
>      now states no count: "our seat law and Germany's of 2000, 2015 and 2023".
>    ✅ **REAL BUILD RUN, AND THE DEPLOY GATE IS GREEN** (`5455b6f`):
>    `deploy_check: ✓ site/ matches its number review`, committed review stamped
>    `blocking=0`. The rebuild moved three files — the review, `site/index.html`
>    and `site/changes.json` — so the seat-laws sentence is the only
>    page-visible change. Tests re-run after it, 6 of 56 modules, 14 passed:
>    home_page, published_page, site_text, number_scan, stat_freshness,
>    model_index. **Nothing is published and nothing is deployed**: the build was
>    a dry run and the ledger is untouched.
>    ⚠️ **`site/portal.html` SHIPS AND IS NOT SCANNED.** `build_portal.py` writes
>    it, the review's `built-pages` stamp does not list it, and `deploy_check`
>    therefore never looks at it — so the typed-figure gate covers eight of the
>    nine pages in `site/`. It is stale as well as unscanned; this build did not
>    touch it. Not fixed here, and it is the same hole `deploy_check` exists to
>    close. §11 has the detail.
> 2c. **Regenerate `MODEL-INDEX.md` BEFORE the suite run you intend to quote,
>    not after.** It joins the registers, so a new public constant or an
>    `ENTRY_POINTS` change moves it and `test_model_index` fails on a file
>    nobody edited — and since regenerating is itself an edit, finding it at the
>    end costs the whole run again. It cost two runs on 2026-09-25. Now in
>    `QC.md` §4 with the other preconditions.
> 3. **Interactive: measure Pyodide speed FIRST.** The notes disagree: ~55 ms per
>    draw in the browser (~17 s for 300 draws) in one, ~35 s of CPU per 300
>    draws natively in another. The spike's code was never committed. Whether
>    "300 draws per change" is even possible decides the page's design.
> 4. **The interactive's model mechanisms** (PUBLISHING-BACKLOG §9, now §9a):
>    per-pool turnout (level + differential, after the IPF), the DA-share-among-
>    Black-Africans control, and per-poll selection. Each gets a pre-registration,
>    a blind review, a JUDGEMENT-CALLS row and a 2026 liveness test, and all of
>    them go into one re-emit window.
> 5. **Carried from the earlier banner, still open:**
>    - the **small-party draw fix** (the within-pool Dirichlet gives micro seeds
>      a spike at zero; backtest seated-parties PIT 0.83; Johannesburg 2021
>      seated 18 parties, per the IEC seat report). Scripts are in
>      `audits/2026-09-24-interactive-round1/small-party-tail/`;
>    - a poll with no n is priced MORE precise than SRF (`POLL_HOUSE_SD`
>      fallback), a live defect;
>    - the register VALUE guard, then the `/judgement-calls` page;
>    - the owner-authorised re-emit window, which must regenerate
>      `build_validation` (the public table is the 11 Aug run, truncated at 12
>      parties);
>    - owner review, then `build_site.py --publish --reason … --change-class …`,
>      then `env -u CLOUDFLARE_API_TOKEN npx wrangler deploy`;
>    - ✅ **the ledger has its baseline** (2026-09-26, `191465d`, owner's rule in
>      PUBLISHING-BACKLOG §12: *"change must always be against previously
>      published number"*). The live site is FOUR pages carrying 27 tokens and
>      it is the **7 August** build, not the 31 August one — every page stamps
>      `data-when="2026-08-07"`, and `/forecast`, `/about`, `/corrections` and
>      `/nobody-will-win` 404 there. Those pages are archived with their sha256
>      at `archive/live-2026-08-07/`; do not re-save or re-fetch them, the hash
>      is the row identity. The build now reports 4 material moves, 23 unmoved
>      and 291 new.
>
> **Owner decisions, interactive** — recorded in `PUBLISHING-BACKLOG.md` §9a,
> in his words. **Decided:** a DA-among-Black-Africans slider; turnout as overall
> plus per pool; ward calls carried into votes, so **the interactive is now a
> prediction game** (hand-pick every ward and the PR vote, share it, have it
> rated by the model, scored after the election).
>
> **Still his:**
> - the poll trust ceiling;
> - whether a "competition" may store readers' forecasts, which would break
>   §10's URL-only rule;
> - how a forecast is rated (see §9a: a literal joint chance is always ~0);
> - the social preview card;
> - whether §A4 / §A43 are resolved;
> - whether micro-party reach is read from the declared 2026 ward slates.
>
> **Polls, answered for the owner** (`audits/2026-09-24-interactive-round1/poll-research/REPORT.md`):
> - A third Johannesburg poll exists and is NOT in `polls.json`: **Ipsos,
>   June–July 2026 fieldwork**, released 4 Sep. ANC 31 / DA 28 / ASA 14 /
>   EFF 8 / MK 6 / PA 3 / Other 7 / DK 3; no published n, ±5.57 ⇒ ≈310.
>   Verified from the primary PDF. It is not September fieldwork, and DA is 28,
>   not 27 as reported elsewhere.
> - Ipsos is the only house with a scored Johannesburg reading. SRF has no
>   scored local-election reading at all.
> - An unverified IOL report ties SRF to a former DA staffer.
> ## ⛔ STATE AT 2026-09-23 — THE WINDOW IS TAKEN AND THE SITE IS BUILT. NOT DEPLOYED.
>
> **The live pages are still the 31 August build.** Everything below is built,
> committed and pushed, and nothing is published. The owner reviews, then
> `build_site.py --publish --reason … --change-class …`, then `wrangler deploy`.
>
> **THE CANONICAL MEASUREMENT, and the only figure anything may be quoted from
> until the next window** (MODEL-LOG §1.253):
>
> ```
> seat_abs_err_coherent=733/@2ac4c1eb/1000d/pools:7264a929/rows=24
> ```
>
> 24 city-years, 1,000 draws, seed 20261104, clean tree. 17.2% over uniform
> swing, 46.1% over prior-LGE-noise. The freeze was re-taken after it at 1,500
> draws, clean, with all nine environment switches recorded.
>
> **What went into the window:** §1.249, the entrant spread like the city rather
> than a quarter into every pool (ultra review 2 on PR #16 — one nit, fixed);
> and §1.252, the declared ward slates reaching the contestation correction,
> against `prereg/2026-09-23-declared-ward-slates.md`, all six predictions held.
> 27 specs, one key `pools_sha 7264a92947ba4529`. Pre-emit set archived at
> `archive/pools-preemit-2026-09-21/`.
>
> ⚠️ **THE HEADLINE MOVED AND THE OWNER HAS NOT SEEN IT YET.** The ANC is now
> fractionally ahead of the DA on median seats (67 to 66) and "largest party" is
> a dead heat (47.2% / 47.3%). The live page says the DA leads. The PA gains
> 4.71 mean seats from the declared slates alone (§1.252), and the `[0, 2]` clip
> absorbs 21.6% of that correction — its unclipped ward/PR ratio is 2.551.
>
> **Two things were found dead and fixed, both predating this work:**
> * `build_portal` raised `KeyError: 'subdomain'` for every metro ingested on
>   2026-09-01, so `build_all` stopped one step BEFORE the site — which is part
>   of why nothing has rebuilt since 31 August.
> * `montecarlo` swallowed any error in the pool-geography step, so a missing
>   `openpyxl` silently produced a different forecast (§1.250). Latent: it fired
>   on no city-year in the project venv.
>
> **Suite:** whatever `tests/run_all.py` prints. As of this banner the standing
> failures are the 2011 DA-in-White impossible seeds (three, down from four —
> §1.249 fixed Mangaung 2016) and Mangaung 2016's pool rates summing to
> [1, 1, 0, 1]. ⚠️ **And two date-stamp failures that only appear the day AFTER
> a build**: each reader edition stamps today's date, so `test_published_page`
> fails on any later day. It is a test defect, not a page defect, and the
> proposed fix is to stamp the date the CONTENT last changed.
>
> **Still queued, deliberately not in this window:** POOLS-REEMIT-QUEUE entries
> 19, 20, 27 and 28. Entry 27 is the two Cape Town renames the owner confirmed
> on 2026-09-16; it is not number-neutral and needs its own pre-registration.
>
> **The interactive** is decided and not started: it runs the real model in the
> browser (Pyodide, measured bit-identical), and three of its reader controls
> need new model mechanisms. PUBLISHING-BACKLOG §9 has the decisions.
>
> The banners this one supersedes are in `HANDOVER-ARCHIVE.md`. They are not
> maintained and several of their claims are false today.


> ## 📋 NOMINATION-DAY RUNBOOK — Johannesburg, 16 September 2026
>
> Prepared 2026-09-16 **before** the list landed, so the day is a data drop and
> not a code change. Pre-registration: `prereg/2026-09-16-declared-roster-at-
> nomination.md` — read it first; §5 fixes the reporting rule in advance.
>
> **What the paste actually switches on.** Not just contestation. A declared
> roster makes `emit_pools` CONSTRUCT the arrival group for the first time at
> 2026 (`pools.py:6047-6049` builds it only `if roster_source in ("published",
> "declared")`), changes which parties the off-ballot drop removes, and makes
> `contestation_expand` inert (`levels.py:751`). The arrival channel is the one
> to watch, not the PA's slate.
>
> **⛔ THE EMIT IS THE ONLY CHECK OF THE ROSTER, AND THAT IS BY DESIGN.**
> `resolve_roster` and the off-ballot drop run inside `emit_pools`
> (`pools.py:5528`), which `main` reaches only under `--emit`, and `pools.py`
> has **no `--out-dir`** — so there is no way to exercise the roster path
> end-to-end without writing the real spec. Do not build a pre-flight that
> re-derives the known-party set: that duplicates `resolve_roster` and this
> project bars a second definition. **A refused emit writes nothing** — the
> refusal raises before `main`'s `write_text` (`:6268`) — so the cost of a bad
> paste is one ~97s fit, not a corrupted artefact. Let it refuse.
>
> **Rehearsed 2026-09-16, and what it proved (and did not):**
> * The READER works. `pools.declared_roster` parsed a 60-party block (the 57
>   real 2021 CoJ ballot names plus three unseen), canonicalised it, and
>   defaulted `complete` to False. Runs in seconds, no fit.
> * Its unknown-key refusal is MUTATION-PROVEN: `parties` → `partys` on the live
>   block gives *"[roster] … carries ['partys'], which nothing reads"*, and the
>   file reverts byte-exact. ⚠️ The first attempt at this mutation reported the
>   detector BLIND — it had hit the commented-out template at line 72 instead of
>   the live block at 209. A probe bug, not a finding; check which occurrence you
>   are mutating.
> * **NOT rehearsed, and not rehearsable: everything from `resolve_roster`
>   onward** — the drop ceiling, the arrival-group construction, the unknown-name
>   refusal. Those are emit-time, per the paragraph above.
>
> **The steps.**
>
> 1. Paste the IEC list into `[roster]` in `judgements/joburg-2026.toml`
>    (template at the top of that file). `complete = true` ONLY if it is the
>    whole ballot; bare boolean, never quoted.
>
>    ⛔ **PASTE THE UNION OF THE WARD AND PR SETS, NOT THE PR SET.**
>    `contesting_parties`' docstring defines the roster as *"who is on the ballot
>    at the target"*, and the result files it is modelled on carry both ballots.
>    Measured on the certified list: **75 parties have PR lists, 80 contest
>    wards, and the union is 82** — so a PR-only paste with `complete = true`
>    deletes a party that is genuinely standing. The United Democratic Movement
>    is the worked example: it contests **wards in Johannesburg and files no PR
>    list**, and it holds a 2024 baseline, so a PR-only roster deletes a real
>    party's pool mass. Extract both, union them, paste that.
> ⛔ **DO NOT LAND THE TWO CONFIRMED CAPE TOWN ALIASES TONIGHT.** The owner
> confirmed `CCC = NCC` and `CAPE PARTY = CAPE INDEPENDENCE PARTY` on
> 2026-09-16, and they are queued as entry 27 — **not** because they are
> unimportant but because they are **not number-neutral**: measured, they add a
> θ observation in all eight metros and move the 2026 arrival-group total. They
> need a full window *and* a measured panel, and folding them into tonight would
> entangle the published forecast with an unmeasured model change. Tonight is
> the roster paste and nothing else.
>
> 2. Two-spec re-emit — **not** the 27-spec window:
>
>        .venv/bin/python src/pools.py --city joburg --target 2026 --emit
>        .venv/bin/python src/pools.py --city joburg --target 2026 --simulation --emit
>
> ⛔ **THE CERTIFIED LIST SPELLS FOUR PARTIES DIFFERENTLY FROM THE FILES THEIR
> BASELINES COME FROM. THE FIX IS IN THE PASTE, AND IT IS STILL A TWO-SPEC
> NIGHT.** (Corrected 2026-09-16, second pass: an earlier version of this block
> said the day was a FULL 27-spec WINDOW because the fix had to be an alias in
> `parties.py`. **That was wrong.** `[roster] parties` is a hand-written list
> that `declared_roster` canonicalises, so writing the spelling the model already
> recognises resolves it with **no code change**, no `deps_sha` move, and the
> two-spec re-emit the judgement template describes. An alias is the DURABLE fix
> — the 4 November result file will carry the IEC's new string and the ingest
> path will hit this again — but that is an ordinary window later, with queue
> entry 19, not tonight.)
>
> | the IEC's 2026 string | canonicalises to | the baseline file says | which is |
> |---|---|---|---|
> | `UMKHONTO WESIZWE PARTY` | `UMKHONTO_WESIZWE_PARTY` | `UMKHONTO WESIZWE` | `MK` |
> | `VRYHEIDSFRONT PLUS \| FREEDOM FRONT PLUS` | `VRYHEIDSFRONT_PLUS_FREEDOM_FRONT_PLUS` | `VRYHEIDSFRONT PLUS` | `VFPLUS` |
>
> **⛔ WHAT A `[party.X]` TABLE WOULD DO HERE, AND WHY SUBSTITUTION IS NOT THE
> SAME THING.** `pools.py`'s refusal message warns that a `[party.X]` table turns
> a party that HAS a baseline into a phantom entrant sized from the arrival
> record, while `complete = true` deletes the real one — the ActionSA failure
> with the sign reversed. Substitution avoids both: the name resolves to the
> party's OWN code, so it keeps its baseline and nothing is deleted. **Write the
> left column, not the IEC's string:**
>
> | write this in `[roster]` | resolves to | instead of the IEC's | which would resolve to |
> |---|---|---|---|
> | `UMKHONTO WESIZWE` | `MK` | `UMKHONTO WESIZWE PARTY` | `UMKHONTO_WESIZWE_PARTY` |
> | `VRYHEIDSFRONT PLUS` | `VFPLUS` | `VRYHEIDSFRONT PLUS \| FREEDOM FRONT PLUS` | `VRYHEIDSFRONT_PLUS_FREEDOM_FRONT_PLUS` |
> | `THE ORGANIC HUMANITY MOVEMENT` | `THE_ORGANIC_HUMANITY_MOVEMENT` | `ORGANIC HUMANITY MOVEMENT` | `ORGANIC_HUMANITY_MOVEMENT` |
> | `CHANGE` | `CHANGE` | `CHANGE PARTY` | `CHANGE_PARTY` |
>
> **Record the four substitutions in the judgement file as a comment beside the
> roster**, naming the IEC string each one replaces: the paste is then no longer
> a verbatim copy of the certified list, and the next reader must be able to see
> that and check it.
>
> ⚠️ **The last two are judgement, not arithmetic.** A definite article and a
> trailing "PARTY" are the likeliest renamings in the list, but nothing proves
> `CHANGE PARTY` is the `CHANGE` of 2021 — check both against the IEC's party
> register before pasting. The first two are certain.
>
> **Four more pairs scored as near-matches and are NOT renamings** — the
> Azanian People's Organisation, the African People's Convention and the Congress
> of the People each carry their own history and appear independently, and the
> People's Consent Party and Service Delivery Party have no history at all, so
> they are new parties. Do not substitute them.
>
> ⚠️ **AND THE SCAN THAT WAS MEANT TO FIND THESE DID NOT.** A similarity pass
> over canonical codes reported ONE break and missed both, because an alias
> collapses a long name to a two-letter code (`MK`) and no string metric sees
> `UMKHONTO_WESIZWE_PARTY` as close to it. They were found by checking the two
> known aliased parties BY NAME. **Check the alias targets explicitly; a fuzzy
> scan over codes cannot do it.**
>
> 3. **If it refuses on an unknown name** (`pools.py:5362`): check the spelling
>    against `parties.py` FIRST. A real party under an unfamiliar IEC spelling is
>    far likelier than a new one, and "fixing" it with a `[party.X]` table turns
>    a party that has a baseline into a phantom entrant — the ActionSA failure
>    with the sign reversed. **Decided in advance (P2): use a `[party.X]` table
>    in the judgement file, NOT `parties.ALIASES`** — the alias route is
>    `parties.py`, an emit dependency, so it moves `deps_sha` and invalidates all
>    27 specs, turning a two-spec night into a full window. Queue entry 19 is the
>    alias change and stays un-landed for the same reason.
> 4. **EXPECT `complete = true` TO REFUSE, AND KNOW WHICH NUMBER IT IS READING.**
>    The ceiling is measured against `prior_local` — the **fitting year's (2021)
>    citywide shares** — not the 2024 baseline. Approximated from the certified
>    list before the night (summing 2021 PR rows by canonical code, which is a
>    LOOSER set than the `deliberate` subset the run actually charges, so read it
>    as an over-estimate):
>
>    | roster as pasted | parties dropped | share of the 2021 PR vote | vs 1.5% ceiling |
>    |---|---|---|---|
>    | union of ward+PR, no aliases | ~30 | **~3.1%** | refuses |
>    | union of ward+PR, **with the two aliases** | ~29 | **~1.8%** | still refuses |
>
>    The remainder is genuine: parties that stood in 2021 and are not standing in
>    2026 (GOOD is the largest at ~0.33% of the 2021 PR vote, then Party of
>    Action, Abantu Batho Congress, DOP, Black First Land First). So the refusal
>    is the guard doing its job on a real deletion, not a sign of a half-typed
>    list.
>
>    ✅ **THE OWNER CONFIRMED THE 27, 2026-09-16: they are not running.** So
>    `confirm_drop = true` is authorised for this paste, and the refusal — when
>    it fires — is to be acknowledged rather than investigated again. ⛔ The
>    authorisation is for THIS list and this deletion set: it is a statement
>    about 27 named parties, not a standing permission, and a re-paste that
>    changes the set needs it re-confirmed. Do not raise the ceiling, and do not
>    carry `confirm_drop = true` into a later window unexamined.
>
>    ⚠️ **The same measurement against the 2024 baseline is the proof that the
>    aliases matter: 14.2% dropped without them, 1.1% with.** That ~13-point gap
>    is MK plus VF Plus — i.e. without the aliases the certified roster deletes
>    MK's entire baseline, and only the ceiling stands between that and a
>    published forecast.
> 5. Check the emit diff: `roster_source` is now `declared`, `arrival_group` is
>    non-null (it was null), and the drop list is read BY NAME.
> 6. `.venv/bin/python src/build_all.py --city joburg --model --regimes`, nothing
>    else touching the tree. This is the slow step and it runs the site audits.
> 7. Fix only what the build names — `publication.retire` with a reason, or date
>    a historical claim. **No `--allow-*` flags.**
> 8. `src/declares.py --verify`, then `tests/run_all.py -k published_page -k
>    stat_freshness -k publication_ledger -k build_all`.
> 9. Freeze, `build_site.py --publish …`, commit, push `atlas`, then
>    `env -u CLOUDFLARE_API_TOKEN npx wrangler deploy`. **Verified 2026-09-16:
>    wrangler authenticates as psi@whysoserious.club via OAuth. The bare
>    `npx wrangler whoami` FAILS** — a stale `CLOUDFLARE_API_TOKEN` placeholder
>    is exported in the environment, so the `env -u` prefix is load-bearing, not
>    decoration.
>
> **Checked while preparing this, so nobody re-checks it:** the 2026 ward map is
> real and is the 2026 delimitation — `data/processed/vd_ward_2026.csv`, written
> by `build_concordance.py` from `data/raw/geo/vds2026_JHB.geojson` (MDB
> `VotingDistricts2026_Final`, ward identity from its own `WardNo`), and
> `render_map.py` draws `wards2026_JHB.geojson`. So a `[roster.wards]` paste will
> not refuse for want of a ward map. The `vd_ward_*` CSVs show `✗` in
> `declares.py` because every CSV intermediate does — a structural hole excluded
> from `--verify`'s denominator — and they are covered instead by
> `test_intermediates_are_current`, which regenerates them into a purged scratch
> root. **Nothing to fix there.**

---

**Everything superseded now lives in `HANDOVER-ARCHIVE.md`** — the dated state
banners, the 2026-08-29 session's "what to do next", its executed
pre-registrations and its own errata. That file is NOT maintained and several
of its claims are known false today. Durable findings are in `MODEL-LOG.md`,
append-only and dated; process rules are in `CLAUDE.md` and `QC.md`.

This file is the CURRENT state and the runbook, and nothing else. A superseded
instruction here is not history, it is a false premise delivered with the
authority of the rules — which is why it was moved rather than annotated.

# Handover — current state and the nomination-day runbook

⛔ **THIS FILE CARRIES WHAT IS TRUE NOW.** Superseded banners are in
`HANDOVER-ARCHIVE.md` and are not maintained; durable findings are in
`MODEL-LOG.md`, which is append-only and dated. `CLAUDE.md` sends every session
here first, so anything stale in this file is read as an instruction.

> ## ⛔ STATE AT 2026-09-24 — SITE REBUILT AGAIN, STILL NOT DEPLOYED. INTERACTIVE DESIGNED, AWAITING OWNER.
>
> Live pages are still the 31 August build. Commits since 23 Sep (remediation,
> atlas, NOT pushed): `5064975` home page + /forecast (leads with the forecast)
> + /nobody-will-win (the 31 Aug article), one site theme (dark, sun/moon), map
> switch everywhere; `ea3d34a` one "Others" definition (`scenarios.others_per_draw`),
> median/range seat columns, bigger claim logos, cartogram test on constructed
> input; `d38d57c` MODEL-LOG §1.254 + 12 register rows amended + judgement_sheet
> parser fixed. Suite at d38d57c: 761 passed, 2 failed (the two standing ones).
>
> **Settled:** the 723→733 window "drop" is seed noise (4 seeds: 734 vs 735
> mean). §1.249 stays. By-elections: a fresh IEC fetch is byte-identical; no
> Gauteng contest after 2026-02-25.
>
> **NEXT, in order** (PUBLISHING-BACKLOG §11 has the site list):
> 1. **Small-party draw fix** — the within-pool Dirichlet gives micro seeds a
>    spike at zero plus rare chunks (median drawn share ~500x below real
>    first-timers) AND starves established small parties; backtest seated-parties
>    PIT 0.83, 10/24 rows above the 95th pct (model UNDER-seats). JHB 2021 seated
>    18 (IEC seat report), not 12. Spec: each small/new party its own share draw
>    from measured history (first-timers by ward reach), vote shares only.
>    Pre-register, blind review, then change. Owner question open: read reach
>    from the declared 2026 ward slates? Measurement scripts:
>    Scout scratchpad `tail/`, atlas `/tmp/smalltail_*`.
> 2. **Poll with no n is priced MORE precise than SRF** (polling.py fallback
>    POLL_HOUSE_SD) — live defect, both review passes agree; fix.
> 3. Register VALUE guard (spec in the 24 Sep audit), then `/judgement-calls`
>    (owner: live calls + plain intro + full register collapsed, all current).
> 4. Re-emit window: owner authorised. Must include regenerating
>    `build_validation` — the public "about the model" table is the 11 Aug run
>    AND truncated at 12 parties per city (JHB sums to 264 of 270).
> 5. Owner review → `build_site.py --publish --reason … --change-class …` →
>    `env -u CLOUDFLARE_API_TOKEN npx wrangler deploy`.
>
> **Interactive: designed, reviewed blind, four owner decisions open** —
> (1) mixing control: geography-only γ, or a direct "DA share among Black African
> voters" slider (review); (2) turnout ranges: level + differential from the
> record (review) vs the design's (a)/(b); (3) polls: trust ceiling 3.0pp vs
> ≥5pp, and add the Sept Ipsos CoJ poll to polls.json first; (4) ward calls:
> winners only vs carried into votes. Agreed by both: turnout shift goes AFTER
> the IPF (backlog §9's placement is wrong); best/worst = conditioning on the
> published 5,000 draws only. Also for the owner: mark §A4/§A43 ⚪ resolved?
> Page architecture (Pyodide timing unmeasured = decisive risk; ward overrides
> re-seat exactly) is in the palace drawer of 24 Sep.
>
> Leftover on atlas: four never-ending `pgrep` wait-loops from an earlier
> session (they match their own command line); harmless, not this session's.

> ## ⛔ STATE AT 2026-09-24 — THE HOME PAGE IS BUILT. STILL NOT DEPLOYED.
>
> **Everything below the 23 September banner still holds** — the window, the
> canonical measurement, the freeze. This banner adds what happened after it.
>
> **The home page is the landing page now.** `home.html` → `index.html`; the
> forecast sheet → `/forecast`. Built from the current run, layout A with the
> large map and colour-separated sections (PUBLISHING-BACKLOG §10). The heading
> leads on the coalition and its STRENGTH is chosen by the measurement, not
> typed — see `render_home._lede`.
>
> **⚠️ THE NEXT THREE THINGS, in order:**
>
> 1. **The article page does not exist.** The owner edited
>    `content/joburg/articles.toml` on 2026-09-24 so three entries point at
>    `nobody-will-win` (and `nobody-will-win#nobody-catches`,
>    `#minority`). Nothing builds that page yet — the anchors currently live on
>    the forecast sheet. Either build the article as its own page and move those
>    sections into it, or point the hrefs back at `forecast#…`. **The build does
>    not check internal links, so this will ship broken if nobody looks.**
> 2. **The home page has no tests.** Everything else on the site has a guard;
>    this page has none. At minimum: its regions regenerate, its figures are
>    tokens rather than typed numbers, the "everyone else" row is taken per
>    simulation, and exactly one article carries `lead`.
> 3. **The full suite has not run since the home page landed.** Only the six
>    modules the work touched were run (published_page, number_scan, build_all,
>    site_text, standalone, model_index) — all green.
>
> **Then:** the owner reviews, `build_site.py --publish --reason … --change-class`
> (append-only, needs the owner's words), and `env -u CLOUDFLARE_API_TOKEN npx
> wrangler deploy`.
>
> **Open questions the owner has not answered yet:** whether the pool-seed fix
> ships given it costs 10 coherent seats on the panel (§1.253 — it removes an
> impossible assumption, and ITERATING says more honest usually ships); and what
> a social preview card shows for a reader's own forecast (§10).
>
> **SITE-TEXT.md** is waiting for the owner's language edits; `src/site_text.py
> --apply` writes them back to source and refuses any edit that changes a figure.

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

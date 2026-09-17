# Handover — current state and the nomination-day runbook

⛔ **THIS FILE CARRIES WHAT IS TRUE NOW.** Superseded banners are in
`HANDOVER-ARCHIVE.md` and are not maintained; durable findings are in
`MODEL-LOG.md`, which is append-only and dated. `CLAUDE.md` sends every session
here first, so anything stale in this file is read as an instruction.

> ## ⛔ STATE AT 2026-09-16 — THE WINDOW WAS TAKEN. NOMINATION DAY IS TODAY.
>
> **The emit below HAPPENED.** The 27 pre-emit specs were archived at
> `be28a19` (`archive/pools-preemit-2026-09-14/`), the window was taken, and the
> canonical measurement was re-taken on a clean tree at `cf707e3` — read that
> commit message for the run's identity, and quote numbers from it, never from a
> banner. Both staleness guards cleared. `MODEL-INDEX.md` landed at `73eec0f`,
> generated from the tree and regenerated-and-compared by its own test.
>
> **⛔ SIX SUITE FAILURES PREDATE 2026-09-17 AND ARE NOT RECORDED ELSEWHERE.** All
> read artefacts from the 14-15 Sep window; none touches 2026. Each is a real
> defect, not noise:
> * `test_the_documented_figures_match_the_committed_artefact` — ITERATING.md
>   rule 8 says ranks 1-3 n = 63; `history.json` says 72.
> * `test_the_standing_refusals_figures_match_the_artefact` — §A38's PA mean and
>   median disagree with the artefact.
> * `test_no_emitted_composition_weight_is_arithmetically_impossible` — 2011/2016
>   specs seed parties to draw more votes than a pool casts (Buffalo City and Cape
>   Town 2011 DA/White, Mangaung 2016 AIC/Indian, …).
> * `test_the_three_known_things_hold_at_once` — Mangaung 2016 pool rates sum to
>   [1, 1, 0, 1]: a pool lost its voters.
> * `test_the_relabel_ablation_actually_withholds_the_label` — score 6.9450 with
>   and without the label: the switch does not reach the score.
> * `test_the_freeze_records_every_environment_switch` — `HELD_BACK_OFF` and
>   `JHB_SCORE_NO_RELABEL` are not in the freeze.
>
> **NIGHT OF 2026-09-16 — RUNBOOK STEPS 1-8 DONE, STEP 9 HELD FOR THE OWNER.**
> The certified list is pasted (`6c6bdfd`), the SACP is sized by hand
> (`JUDGEMENT-CALLS §L13`, `aa7dcd5`), both 2026 specs are re-emitted, and
> `build_all --model --regimes` built the site. The Zille claim is now dated as
> history (step 7). The publish checks pass. **Not done: freeze, `--publish`,
> push, deploy.** The live pages are still the 31 August build. Before
> deploying, the owner reads the SACP result and the dated Zille intro.
> `declares.py --verify` still exits 1, on three artefacts that predate this
> pass: `joburg/2021` and `capetown/2021` `forecast_summary.json` (strays from
> bare runs on 5 and 10 Sep, not read by the site), `validation_2021.json`
> (§1.216), and `forecast_frozen.json`, which the step-9 freeze replaces.
> Open, not queued: at every metro's 2011 spec the ballot is known but no
> newcomer is seeded, so the generic ENTRANT slot carries their votes.
>
> The banners this one supersedes — 2026-09-14 back to 2026-08-29 — are in
> `HANDOVER-ARCHIVE.md`. They are not maintained and several of their claims are
> false today; read them as a record of what was believed on their dates, never
> as instructions.

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

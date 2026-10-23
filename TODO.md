# What is left to do

Three lists. Nothing is deleted from them; items move to **Done** with a date
and stay visible.

⛔ **For list 1, whether something changes a published number is NOT a reason to
delay it.** The measure is whether the model is defensible, not whether today's
output matches yesterday's. A change that makes the forecast less flattering and
more defensible is a change that ships.

---

# 0 · THE FREEZE — the plan until the model is frozen (owner, 2026-09-28)

**Decided 2026-09-28: F3 + F5 only, freeze 1 October.** F4 waits until after the election. F6 was deferred by F2.

**Rule.** Launching the interactive freezes the model: after launch, any change
to how the model draws invalidates readers' saved forecasts. Target:
**1 October 2026**. **In:** pool repairs and mergers. **Out until after the
election:** independents, the level error.

The interactive no longer gates the freeze. It re-weights the published draws
(`audits/2026-09-28-interactive-architecture/`), so only F1 must land before
the freeze. The rest of it is built afterwards on the frozen model.

**Order.** One step at a time, each finished before the next starts. Each step
names what exists when it is done.

| # | step | done when | est. |
|---|---|---|---|
| F1 ✅ 28 Sept `bfa5d2b` | Record each draw's pool turnouts (not a draw change) | `tests/test_draw_record.py`: all `*draws` arrays identical with recording on and off at seed 20261104, and published seats byte-equal | ½ day |
| F2 ✅ 28 Sept, MODEL-LOG §1.268 | Measure how much of the emitted pool seed survives the per-draw IPF (pool prereg D1). **Result: it survives whole, but C3's composition side and C4 move no seats, so F6 is deferred.** The `--run-dir` stage was not built | a `--run-dir` stage per city-year and party, and a MODEL-LOG § with the number. It decides whether C3 and C4 are in | ½ day |
| F3 🔧 implemented, not yet re-emitted (MODEL-LOG §1.269, §1.275) | C1 conservation: no spec drops a declared pool (queue 30) | prereg P1 holds by arithmetic on every emitted spec; test in `test_pool_bounds` | ½ day |
| F4 | C2 unidentified pool levels, partial pooling (queue 31) | prereg P2: Cape Town Indian/Asian below 5% of the roll at all three cycles, eThekwini within 2 points | 1–2 days ⚠️ the hard one |
| F5 🔧 implemented, not yet re-emitted (MODEL-LOG §1.275) | Mergers: search the panel for a measurable merger, else a 🔴 judgement row; `Merger` beside `Split` in `pools.py` | JUDGEMENT-CALLS row or a measured retention; the merger prereg's RISE prediction checkable | 1 day |
| F6 ⏸ deferred by F2 | C3 and C4, only if F2 says they matter (queue 32, 33) | prereg P3; the single-pool count falls from 37 | 0–1 day |
| F7 | Blind review of F3–F6, brief committed before it runs | brief in `audits/`, findings applied or taken to the owner | ½ day |
| F8 ✅ 29 Sept, MODEL-LOG §1.279 | One re-emit of every spec (backup first; timed) | `declares.py --verify` shows no `~` on specs; suite run | hours |
| F9 ✅ 29 Sept, MODEL-LOG §1.280 | Measure against both preregistrations; write it up | MODEL-LOG § scoring every P, including what failed | ½ day |
| F10 ✅ 29 Sept, MODEL-LOG §1.281 (owner: F3–F5 modules only) | **Mechanism census** (PUBLISHING-BACKLOG §15, replacing §13 as the gate): three mutations per claimed mechanism, claims written first; the full line-by-line night (§13) runs afterwards as a background audit | a committed harness and a survivor report, read | 1 day + a night |
| F11 ✅ 30 Sept, MODEL-LOG §1.282 (deploy: owner) | Owner review, then `build_site.py --publish`. **This is the freeze** | the live forecast is the frozen model | ½ day |

**Honest total: about 6–8 working days, which lands around 6–8 October, not
1 October.** Two ways to meet the 1st: drop F4 and F6 (C1 and mergers only, the
other pool repairs after the election), and shorten F10 to the modules F3–F5
touched. The owner chooses.

**Pending the IEC roster: two ActionSA mergers** (owner decided on
2026-09-29 to declare them for completeness). The Azanian Independent Community
Movement and the Creatives Congress Movement (IOL, 2026-01-26) appear in no IEC
file for any city and on no roster, so their only spelling is the press
spelling. A declaration keyed on it would never fire if the IEC spells the
party differently, and nothing would say so. Both hold zero votes, so the
declaration changes no number. Declare each with `parties.canonical(<IEC
name>)` once the certified roster arrives; the edit plan is in the agent's
report, recorded in MODEL-LOG when applied.

**Independent review gates (owner, 2026-09-29).** A review sits where a
mistake is expensive to undo. Each brief is committed before the review runs,
gives evidence and questions rather than the lead's conclusion, and forbids the
reviewer from delegating.

| gate | before | what is reviewed | why here |
|---|---|---|---|
| **R1** | F8 re-emit | the model diff (F3, F5, the ActionSA declarations) against its specs. **Candidate for an owner-triggered ultra review** | the re-emit rewrites every spec; a bug means redoing the emit and every measurement after it |
| **R2** | F9 scoring | that the scoring script measures exactly what each prereg named, checked before any number is seen | a prereg is scored once; wrong-quantity scoring has happened twice here |
| **R3** | F10 census | the census claims file | a wrong claim misreads a live mechanism as broken or a dead one as fine |
| **R4** | F11 publish | changed pages, the ledger and the change reasons, blind (as 2026-09-27) | public, and it is the freeze |
| **R5** | sign-in going live | a security and privacy review of `worker-api/`, plus a real-browser test on phone and desktop | personal data in a political category; legal and reputational cost |
| **R6** | 4 November | the reader-scoring rule and code, run on 2021 as if it were 2026 | a rule written after the result is not a rule |

No gate on the lever wiring or the draw export: their tests compare with the
published run bit for bit, so a mistake there fails loudly.

**After the freeze: the interactive**, `audits/2026-09-28-interactive-architecture/PLAN.md`
S2–S6, about 5 days: export the draws, the Atlas grid, `reweight.py`, sectors,
the page.

---

# 1 · The model — is it right?

## Open, in the order I would take them

**The out-of-sample round (`rounds/2026-10-23-out-of-sample/PLAN.md`).** Owner
items 28 and 29 (2026-10-23). Step 0 is built and held unpublished on branch
`step0-withdraw` (cb08153; reverted off `site-sweep-1` in b6469c3, whose 62
ledger retirements must never be merged): the owner said on 2026-10-23
"Nothing gets published except tooltips about what the pages used to say and
the zille card". The quarantine copies were moved to the Trash on 2026-10-23
(owner: copies "can be deleted for now"); the in-sample originals are still in
the project and are handled by the legacy-files plan below.
Next: step 4 (stop gap), step 5.1 (freeze by 31 October), then steps 1-3.

**Next plan: legacy and stale files and instructions across the project folder**
(owner, 2026-10-23: "We can revist legacy files and legacy or stael fiels and
instructions throught the project folder as the next plan"). Inventory every
file and instruction that is legacy, stale or contradicted, including the
in-sample score originals (`OWNER-DECISIONS-ANSWERED` 32 lists them), and
propose for each: keep, relabel, move or delete. Owner decides the deletions.
Known entries so far: `data/processed/fold5_parameters.csv` (no fit_status
column, cannot be refitted under the default options, its only reader
`--fit-from 5` now refused; `declares.py --verify` shows it ✗).

**Pre-freeze arms (OWNER-DECISIONS-ANSWERED 31, 2026-10-23).** Johannesburg
2026, paired with the current forecast: by-election terms off; γ from the
2019→2021 fit; γ from both fits pooled. Pre-register under `prereg/`, run
outside `data/` with the worker count capped (owner: "please leave some cpu
available"), one old-vs-new report each in `reports/model-changes/`, then a new
owner item for what is frozen. Before 31 October. **Run 2026-10-23**: MODEL-LOG §1.333, five reports in
`reports/model-changes/2026-10-23-prefreeze-*`; waits on OWNER-DECISIONS 33.
If G2 or GP is frozen, `export_interactive.py:158` (fold 1 hard-coded) must
follow. Fix DATA-QUALITY 21 in `run_model` if BF or later is frozen.

**Freeze settings (OWNER-DECISIONS-ANSWERED 33, 2026-10-23).** Pooled γ, the
placeholder fix and the ActionSA call withdrawn, Johannesburg 2026 only.
Pre-registration `prereg/2026-10-23-freeze-settings.md`. Sequence: writer
(code and tests) → review → `backup_ignored.py` → `inputs_preflight --strict`
→ fold files and pooled file → `width_record.py --emit` → canonical run →
`overhang_regimes.py` → `freeze.py` → `export_draws.py` (three cells, `--index`)
→ `citywide_table.py --city joburg --target 2026` → `render_map.py` and
`hex_cartogram.py` (the build refuses maps from an older run) →
old-vs-new report → UAT → owner's yes → freeze hash by 31 October. Whole suite
once on the settled tree, at a time the owner chooses (CPU).

**ActionSA's level, later** (owner: "we cna deal with that later"). The call
of 21 October (§SJ2) is withdrawn; whether ActionSA's model-own level needs
a different treatment is open.

**Site text for the withdrawn ActionSA call** (needed before the freeze UAT;
site brief under QC.md §4b, owner's approval). `content/joburg/stats.toml`
`judgement_asa_support` (sources `judgement:joburg-2026:party.ASA.support`,
which no longer exists) and the `[[audit.fixed]]` 17.6% entry on methodology;
`content/joburg/model-claims.toml` claim `actionsa-judged-level`; the
methodology and forecast Limits passages that state 17.6%; the docstring
example at `src/stats.py:65`. Live text was true when published, so it gets
a dated "Since then" note, not a correction (publication convention).
Left by step 0: `reports/model-changes/build_report.py` reads the quarantined
`history.json`, so it cannot run until a forward-chained one exists; the
in-sample banner in `reports/model-changes/template.html` comes out then.


**Independents cannot win anything, and the model is charged for it.**
`IND` is on the certified ballot and on our roster, and has no pool membership,
so no simulation can seat an independent. Independents took 11,904 votes in
Johannesburg in 2021 — 0.645%, tenth of 57 parties, above the African
Independent Congress — and 52 council seats nationally. In the backtest the
model hands their seats to parties and takes the error. Registered as an
assumption on 2 September and unactioned since. Pre-registration written;
testable out of sample against eThekwini 2011 and 2016, where independents won
wards.

**A merged party's vote is deleted instead of transferred.**
The roster drops 29 parties. Two of the three largest merged into parties that
ARE on the ballot — GOOD into RISE Mzansi (RISE is the Gauteng ballot party),
Forum 4 Service Delivery into ActionSA — and their vote vanishes rather than
moving. It matters most for RISE, which did not contest Johannesburg in 2021 and
is therefore sized as an arrival, the model's weakest area, while the 6,773
votes of the party it merged with are thrown away. Splits already work this way
in reverse, with a measured fraction; mergers need the same with a retention
factor below 1.

**The largest-party headline is decided by a tie-break.**
`np.argmax` awards every DA/ANC tie to the DA because the DA has the higher mean.
Sole largest: ANC 47.20%, DA 45.52%, tied 1.82% — 91 draws. Published as
47.34% / 47.20%, which prints as "47% / 47%" and fires the "dead heat" sentence.
Split the ties evenly and the ANC leads 48.1 to 46.4 and that sentence does not
fire. It is one rule applied asymmetrically to two figures in the largest type
on the site.

**The roster is a newspaper count.**
82 parties, typed from reporting that contradicts itself (82 in three outlets,
75 in two, all citing the same certification). `complete = true` licenses
deleting 27 parties. The IEC publishes no per-municipality list anywhere
reachable — every path checked and recorded at the flag itself. **The list has
to be requested from the IEC.** Count stays at 82 until it arrives.

**The validation table describes itself wrongly.**
`/about` says "every party that won a seat in 2021, in every city" over a table
of the largest few, and prints a total computed over all parties beneath rows
that do not add to it. The code fix is written; applying it needs the artefact
regenerated, which is the first item on this list.

**The baseline field excludes the honest opponent.**
Three baselines are used and the README says a fourth — the roster-aware uniform
swing — is "the honest opponent at 2021". The published "+37% better" is against
the weaker field.

**A published sentence contradicts a registered decision.**
`/forecast` says "every party on the IEC's certified ballot is named in the
simulations". Independents are on that ballot and are excluded by decision. This
is a correction, not a rewording. *(Owner: add, leave for now.)*

## Done

* **The backtest score moved; it was not an implementation error.** Total error
  over eight cities 213.9 → 224.1. Commit `f33528f` (14 Aug) stopped the 2021
  backtest sizing ActionSA from a split three years after the election; 213.9
  was contaminated. Blind review: `audits/2026-09-27-backtest-difference/`.
  Republished as a bugfix. *(27 Sept)*
* **The arrows pointed the wrong way** — four figures frozen as "published 31
  August" came from a build that was never deployed; three showed a rise where
  the published number had fallen. Re-sourced to the publication ledger, arrows
  recomputed, correction filed, and a test now refuses a frozen figure that does
  not cite the ledger and match it. *(27 Sept)*
* **Two medians were quoted against each other** — 118 across all simulations
  against 144 among those where the coalition wins, both called "median". Both
  now named. *(26 Sept)*
* **A range printed over one simulation** — "34 – 34 seats" now collapses to a
  single figure and its source says how many draws it covers. *(27 Sept)*

---

# 2 · The interactive — what it needs to go live

## Decided

* **Seat-law comparison first.** Four laws, already computed at the full 5,000
  draws, no browser engine needed. The data now ships as `site/regimes.json`.
* **Controls that survive measurement:** the seat law, how much support moves
  within a pool, and how much weight by-elections carry. Per-VD turnout noise and
  ward-local by-elections were dropped — measured at 0.01 and 0.04 seats.
* **Polls:** a row per poll with its caveat, a toggle each, one trust slider from
  no effect to taking the poll as the outcome, the spread between houses shown,
  the average as one option. Our own trust is zero, which is what we publish.
* **Turnout** by population group and by area. The geography exists; the grouping
  is a choice between derived compass sectors and the City's official regions.
* **Scoring a reader's map:** their percentile in the distribution of
  draw-to-draw distances, not a probability — independent per-ward marginals
  would rank the model's own best guess above 95% of the maps it actually draws.
* **A reader's controls never touch the published forecast.**

## Open

* **Methodology says Stats SA "holds" home language by ward (found 2026-10-22).**
  `docs-public/methodology.md` and `content/joburg/model-claims.toml` say it is held
  and "we have requested it". Stats SA (Magakwe Kgope, 24 August 2026, the owner's
  Gmail): language data "is not available at Ward level". Correct the sentence under
  a QC.md §4b brief; the Stats SA outreach note links this page.
* **The input route is not settled.** See `INPUT-ROUTE.md`. The question is not
  only size but whether each route still lets a lever act at the right point in
  the model.
* **What the page shows before a reader touches anything**, given that a
  300-draw default is the first 300 of the published 5,000 and prints different
  headline percentages.
* **Turnout by group and by area has to be built** — it does not exist.
* **The poll dial has to be built.** It is a new parameterisation, not a
  relabelling of the existing one.
* **No browser measurement exists.** The timing we have is Node, explicitly a
  floor.
* **Validation of a shared forecast** — a link carrying 135 ward calls, a PR
  vector and lever positions is untrusted input and nothing bounds it.
* **What happens to the coalition table, the ward map and the tested claims**
  when a lever moves.
* **The judgement calls have no published surface** since the sheet was
  withdrawn as unreadable.
* **Readers make the judgement calls** (owner, 2026-10-21: after go-live, a
  new site feature with a brief first). One control offered for every party,
  redrawn from the published simulations in the browser. OWNER-DECISIONS
  item 10.
* **Sign-in, redesigned** (owner, 2026-10-21, held for later): readers sign in
  with X or another account and the site keeps no credentials; their contact
  details are sealed inside their entry, readable by the operators only in
  named circumstances where a key is received. The built `worker-api/` stores
  email addresses and needs reworking to this before any sign-in goes on.
  OWNER-DECISIONS item 11.
* **The share badge's bands** (owner, 2026-10-21: went live with the bands
  as they are). Re-record `tests/test_reweight.py`'s badge table on the 21
  October simulations and measure why a same-sized move from our prediction
  now scores lower. OWNER-DECISIONS item 13.
* **The splinter split** (owner, 2026-10-21: live at 35%, measure after
  go-live). Re-measure `SPLINTER_PARENT_WEIGHT` (JUDGEMENT-CALLS §F6), with
  the population-group question in the brief: "It seems incorrect as it
  stands in a country so divided by population group." OWNER-DECISIONS item 6.

## Done

* Pyodide speed measured; the constraint is the input size, not the draw rate.
* Effect sizes measured; two candidate controls deleted.
* Seat-law data lifted out of gitignored storage into the site bundle.

---

# 3 · Everything else

**From OWNER-DECISIONS answered 2026-10-23** (in order of the owner's priority):
* **Site sweep, brief 1 (first):** redraw the ward map; fix the factual errors on live pages; a correction entry for each error that was live; dated amendments on the claim cards. `audits/2026-10-23-site-sweep/FINDINGS.md`.
* **Site sweep, brief 2:** the tone sweep ("This Model"; Your Prediction for one scenario, Forecast for a range); STYLE.md brought up to date with the rules now only in memory; a test that scans body text.
* **GitHub:** push everything, after a scan of the full history for secrets and personal data (addresses, phone numbers).
* **Cities fingerprint (item 19):** narrow it in one re-emit window; Johannesburg must reproduce exactly.
* **Tshwane (item 20):** two briefs (roll-to-ward assignment; the Tshwane page with its ward map and UI), and a by-election pre-registration.
* **Claims (item 22):** a Baloyi 2-3% card; a dated Morero line on the ANC card; check Baloyi's MK-growth claim before any card.

**Other metros (owner, 2026-09-29): only after the Johannesburg interactive is
finished.** Not a full site per metro: a ward and seat predictor with headline
numbers only. **Tshwane is the second**, and the only one planned. Its gaps for
a 2026 forecast (`src/inputs_preflight.py --strict --city tshwane --target
2026`) are the voters' roll and the certified roster; it already has a 2026
spec and judgements file. Do not start acquiring rolls before Johannesburg's
interactive is done.

**Owner, 2026-10-19: Tshwane launches after Johannesburg is live.** A third gap
for that launch: Tshwane has no by-election deltas file, so its forecast reads
no by-elections. `src/byelections.py --city tshwane` has never been run; the
raw file already holds its contests. Pre-register before building it (it moves
Tshwane's forecast).

**Before the election**

* **Post-election scoring must be frozen before 4 November** — seat count per
  party, correct party by ward, correct ward-versus-PR allocation, scored
  identically for readers and for us. Still needs the result-ingest path and the
  party-name mapping, and the IEC spells four Johannesburg parties differently
  from our own files.

**Publishing**

* ~~Six commits are unshipped~~ — deployed and verified live 27 Sept
  (`fbb829e`).
* The portal page ships without being scanned by the number gate.

**The newsdesk**

* ~~Moved to its own private repository~~ — `~/projects/atlas-jhb-model-newsdesk`
  (`Psi-am-i/jhb-model-newsdesk`), 27 Sept. Its rules are its `CLAUDE.md`; the
  two-`CLAUDE.md` collision is gone. Routine `joburg-daily-newsdesk` repointed
  and its prompt reduced to "follow `CLAUDE.md`".
* ~~Close the 13 `newsdesk/*` PRs~~ — closed 28 Sept with a pointer; the `newsdesk/*`
  branches deleted from GitHub the same day, after each was checked
  byte-identical to its copy in the new repo.
* **Owner, open:** remove the routine's five connectors (Gmail, Drive,
  Calendar, Cloudflare, Claude Code Remote) in the routine settings. The API
  would not clear them. Claude Code Remote is what let it schedule its own
  follow-up routines.
* After changing polls, claims or articles here, run its `bin/sync-context.sh`.

**Data**

* The IEC's per-voting-district 2026 registration is not published; only ward
  level is. Worth requesting alongside the roster.
* The IEC's own page gives two city totals 613 apart, unreconciled.
* Tshwane is missing both its roll and its roster.

**Housekeeping**

* **Discard list reviewed 27 Sept; deletion not yet done** (the agent's delete
  was blocked by the permission check, so the owner runs it):
  - `splinter-rule-and-historical-tail` — safe. Its tip tree is identical to
    `efa06f7` on `remediation` ("tree identical to splinter-rule-…"), so all
    content survives as a squash. Its 56 commits have no patch-equivalent on
    `remediation`, so tag it before deleting to keep the per-commit history.
  - `atlas/…` tip `a5e8c5d` (WIP, 2 Sep) — safe. Its four files diff empty
    against `af054e3` on the splinter branch, whose content reached
    `remediation` via `efa06f7`.
  - Scout's 14-Sep stash — not reviewed: Scout offline on 27 Sept.
  - The site was published from `remediation`, which is not on the list.
* ~~Commits are unpushed to Atlas~~ — `remediation` pushed to `atlas` 27 Sept.
  GitHub `origin` is not pushed (see the two-`CLAUDE.md` item).

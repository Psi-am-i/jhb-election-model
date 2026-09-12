# Document integrity — findings inventory, 2026-09-10

Commissioned after the owner's diagnosis: *"some very old cruft inside them that
keeps pulling us towards a centre that is not there."*

**Status key:** ✅ verified by re-derivation · ⚠️ reported by a reviewer, NOT yet
verified · 🔧 fixed in this batch.

---

## A. `CLAUDE.md` — stale claims in the auto-loaded rules file  ✅ 🔧

Loaded into every session, so each of these was a false premise injected into all
downstream work.

| line | claimed | actual |
|---|---|---|
| `:134`, `:175`, `:271` | panel is **16** city-years | **24** |
| `:127` | **26** specs | **27** |
| `:274` | **four** standalone modules | **five** (its own test names five) |
| `:184` | "38 tests… 13 + 22" | 13 + 22 = 35 |
| `:232-239` | `k*` 0.62/2.48/1.70/1.76, RMS 1.77, mean 1.64 | unverified; removed as a claim |
| `:243` | "three ultra reviews" | a decrementing count |
| `:266`, `:309` | "~14 min", "3x speedup" | moving quantities |

**Fixed** by rewriting to mechanism-only with a new rule §0 banning numbers.

## B. `ITERATING.md:1135` — the bar file is stale AND mislabelled  ✅

Claims coherent seat error **707**, margin **20.1%**. Measured today at HEAD:
**725 / 18.1%** with the free arrival relabel, **743 / 16.0%** without — and 2026
gets no label, so **16.0% is the figure that applies to the live forecast**.
~~"707" was the *marginal* statistic carrying the *coherent* name.~~
⛔ **RETRACTED 2026-09-10 (pollster review).** That diagnosis was an inference
stamped ✅. The marginal is **709**, and 707/20.1% are consistent with each other
((885−707)/885), so 707 is a figure from a different tree state. The stale bar
stands; the story of *why* was invented. `history.json` was also taken at 1000
draws on a dirty tree, so part of 707→725 may be Monte Carlo noise.

## C. Citation rot  ✅

82 citations pair a `file.py:NNN` with a named symbol. Measured by distance from
the cited line to the nearest occurrence:

| | count |
|---|---|
| accurate (≤5 lines) | 22 |
| drifted but findable (6–25) | 18 |
| **wrong region (>25)** | **34** |
| **dead — symbol absent from that file** | **8** |

Concentrated in three files:

| file | cites | bad | live? |
|---|---|---|---|
| `DUPLICATION-AUDIT.md` | 39 | 20 | historical (dated in its title) |
| `audits/BATCH-PLAN-2026-09-02.md` | 17 | 11 | **claims "the one that governs"** — spent |
| **`MACHINERY.md`** | **7** | **6** | **live** |

Worst single: `MACHINERY.md:739` discusses `arrival_group_spec` and cites
`montecarlo.py`. It lives at **`src/pools.py:3758`** — wrong module.

**Instrument note:** the first detector reported 60/82 using a ±5 window. Hand
spot-checks showed it conflated a 9-line offset inside the right comment block
with a 190-line miss. The distance buckets above are the third revision.

## D. Documents describing mechanisms the code no longer has  ✅

| where | claims | reality |
|---|---|---|
| `docs-public/methodology.md:277` | "a single unreplicated house is **capped at half the blend**" | `montecarlo.py:4538` — "THE CAP IS DELETED"; `_cap = 1.0` under the default `SIGMA_TWO_TERM` |
| same, `:278` | "**the cap binds today**… the cap is what stands between that house and the published forecast" | nothing stands there |
| same, `:279` | polls "moved the DA from **83 to 77** seats" | polls move the DA **68 → 79** — inverted sign, ~2× magnitude |
| same, `:280` | "we publish the forecast with polls and without, **side by side**" | published nowhere |
| `site/index.html:576` | "polling introduced… **only as levers bounded by history**" | `poll_credence: 1.0`, `poll_paths: "all"` in the published artefact |
| `site/index.html:614` | "Polling (**SRF, Ipsos**) spans the scenario lever only" | only SRF has a Johannesburg-2026 metro poll (`polls.json`); Ipsos's entries are 2016/2021 national and a 2025 metros-wide wave. ⚠️ *Corrected 2026-09-10:* the evidence first cited here — a `metro_poll` scenario key — is `None` in both forecast artefacts; it is a `note_constant`, not a scenario key |

**Dated cause:** the "83 to 77" sentence was written 2026-08-23 (`210a8ae`); the
cap was deleted 2026-08-24 (`2fae2d1`). The sentence was never updated.

## E. Derived-artefact staleness  ✅ 🔧 (MODEL-LOG §1.222)

26 of 104 processed CSVs did not match what the code produces; seven cities
scored 2021 on a turnout projection predating the pre-2011 ingest. Refreshed;
measured effect on the 24-city-year seat table was **exactly zero**.
`fold5_parameters.csv` is **not reproducible by any invocation available today**
and is kept and flagged. `turnout.csv` still carries **no artefact key**.

## F. Reviewer claims NOT yet verified  ⚠️

Two blind pollster reviews raised these; I have re-derived none of them and they
must not be repeated as fact until someone does.

1. `SD_FLOOR = 0.15` binds on ANC/DA/EFF/MK (~82% of ballot mass) and does double
   duty as both draw width and the poll-blend denominator; sweeping it across its
   own registered range moves the DA's poll weight 0.37 → 0.76.
2. `site/about.html` — titled "How we know the model works" — is built from an
   artefact flagged `in_sample: True` on all eight cities, 400 draws, 12-party
   truncated.
3. The defect-rate decomposition of the 222 `MODEL-LOG` findings (both reviewers
   produced one; they disagree on the verdict).
4. ~~`freeze.py:158` raises `ValueError` when `compare_history --json` points
   outside the repo, discarding a completed panel run.~~ ✅ 🔧 **Confirmed by the
   pollster and fixed 2026-09-11** — `freeze._dirty_excluding` drops
   out-of-repo paths. Guarded by
   `test_an_output_outside_the_repository_does_not_discard_the_run`, and the
   pre-fix expression was shown to raise on the same probe path.
5. Two of the eight live suite failures are model defects, not documentation.
6. MK's prior band and the rupture-mixture argument (§1.201 / §1.205).
7. Coverage/PIT width figures on the `reference` population.

## G. Open questions for the owner

* Does `ITERATING.md` get the §0 treatment — the bar stated as a *comparison*
  plus the command that settles it, carrying no figure at all?
* Does `~/CLAUDE.md` (global, all projects) get the same claim-stripping? Its
  claims are infrastructure, not forecast.
* `DUPLICATION-AUDIT.md` and `BATCH-PLAN-2026-09-02.md` are spent. Retire them to
  a dated archive, or repair their citations?

---

## H. The pollster's work list, and where it stands (2026-09-11)

The pollster reviewed this inventory blind on 2026-09-10 and returned a ranked
work list. Its output file lived in a session temp directory that no longer
exists; the list is persisted here so it is not lost twice. ⚖️ owner judgement ·
🔧 mechanical · 📏 blocked on a measurement not yet taken.

Its central correction of this inventory: **rank by whether a false statement
can change a number, or what someone believes about one — not by how often the
document is read.** `CLAUDE.md`'s stale counts changed nothing; the register
rows pinned to the 16-panel are the only written defence of live parameters.

| # | item | kind | status |
|---|---|---|---|
| 1 | `docs-public/methodology.md` claims a poll cap that is deleted, and a side-by-side publication that does not exist | ⚖️ wording | ✅ **RESOLVED 2026-09-12, and not by a reword.** The owner took the polls OUT of the forecast (§1.225), so the section now says so, dated, with the measurement as pinned tokens. The side-by-side sentence is gone — it promised something that never existed. ⚠️ `site/methodology.html` is NOT rebuilt: doing so publishes the polls-off headline. |
| 2 | `ITERATING.md` bar: stale, and the label-free arm (what 2026 is scored like) is not persisted | 📏 | ⛔ **RE-DIAGNOSED 2026-09-12 — IT WAS NEVER WAITING ON A SETTLED TREE. IT IS WAITING ON A REPAIR.** `test_the_relabel_ablation_actually_withholds_the_label` is red and says the switch is INERT: *"6.9450 with the label, 6.9450 without"*. So `JHB_SCORE_NO_RELABEL=1` withholds nothing and the label-free panel cannot be measured at all until it reaches `calibration_columns` and both `score_seats` calls, not only `relabel_run`. Every previous write-up of this item, including this session's, said "needs a run on a settled tree" — that was wrong and cost three sessions of it sitting in a queue as though it were merely unrun. The with-label panel is now taken twice (§1.225). |
| 3 | `JUDGEMENT-CALLS.md` rows whose evidence is the 16-panel | 📏 + ⚖️ | 🔧 **tagged [16-panel]** (header note + six rows); re-measurement open — owner picks the order |
| 4 | `freeze._dirty_excluding` raised on an out-of-repo `--json` | 🔧 | ✅ **fixed + test** |
| 5 | §0 redirected the spec count to a document typing the same count | 🔧 | ✅ queue says "every spec" and points at its own `find` command; `CLAUDE.md` §0 names the command |
| 6 | `CLAUDE.md` "MODEL-LOG is the only file where a measurement is written as a number" contradicts its own routing table | ⚖️ | ✅ **RESOLVED 2026-09-12 by the owner**, and the rule he gave is stronger than either option put to him: *a number lives where it was generated; everywhere else POINTS at it — you do not copy it, you fetch it.* `JUDGEMENT-CALLS.md` is not an exception but the rule's own case: nothing derives a judgement call, so it has no upstream to point at and must state the value explicitly. |
| 7 | `README.md` "sixteen city-years" | 🔧 | ✅ — and its "wins in most, on both cycles" was dropped: `history.json` has 2011 at 4W 3L 1T against uniform swing, which is not "most" |
| 8 | `ITERATING.md` cites `compare_history.py:1221` for `relabel_run` | 🔧 | ✅ cited by name |
| 9 | `ITERATING.md` "the baseline is now 548.05 on 24" | 🔧 | ✅ figure dropped, points at `history.json` / §1.215 |
| 10 | `MACHINERY.md` citation rot | 🔧 | ✅ all line cites replaced by symbols (0 remain) |
| 11 | `POOLS-REEMIT-QUEUE.md` citation rot (not in the original inventory) | 🔧 | ✅ 0 remain |
| 12 | "sixteen city-years" as live claims elsewhere | 🔧 | ✅ `MACHINERY.md`, `ARCHITECTURE.md`, `AGENT-PLAN.md`; `PLAN-TO-LIVE.md` given a dated banner instead of a rewrite |
| 13 | `history.json` taken dirty at 1000 draws | 🔧 | partly — two 1000-draw panels were run serially on 2026-09-12 with nothing overlapping, and both are recorded with their tokens (§1.225). The tree was still dirty (`@1d9a0e1d+dirty`), so a CLEAN run is still owed after this batch commits. |
| 14 | `forecast_frozen.json` (1500d, 28 Aug) vs `forecast_summary.json` (5000d, 31 Aug, matches the site) — both called "the forecast" | ⚖️ which is the freeze | ✅ **ANSWERED 2026-09-12, and the owner's premise was half wrong.** He kept it as "a snapshot of what we published" but believed the model itself was not snapshotted. It was: the freeze records commit `82c61e1` clean, and `pools.py` there re-hashes to the recorded `dbdf171344ffd5f0`. The 28 Aug model is recoverable from git; the emitted SPEC FILES and raw inputs are not (`data/**` is gitignored, and the inputs were refreshed in §1.222). The two artefacts also agree on **every headline seat median** — they differ in the tails, not the forecast. |
| 15 | `CLAUDE.md` "`--run-dir` changes no number": `test_chain` asserts artefact identity, not draw identity | ⚖️ | ✅ **CLOSED 2026-09-12 by making the claim true**, not by softening it. `test_passing_a_run_directory_changes_no_drawn_number` runs the model twice on one seed and compares drawn seats AND drawn shares (a share can move without crossing a quota). The same wrong citation was in `test_levers_are_live` — which passes a `run_dir` into the baseline every lever verdict is measured against — and in `run_model`'s own docstring. All three now name the test that asserts it. |
| 16 | `site/index.html` "levers bounded by history"; "Polling (SRF, Ipsos)" | 🔧 after #1 | open |
| 17 | `BATCH-PLAN-2026-09-02.md` claims "the one that governs" for a landed batch | ⚖️ | ✅ **DONE 2026-09-12** — owner chose archive + stub. Moved to `archive/`, banner added saying its unticked boxes are not outstanding work, stub left in `audits/`. |

**Left deliberately:** three line cites in dated documents
(`ARCHITECTURE.md:129`, `AGENT-PLAN.md:142`, `:166`) describe a formula that no
longer exists in that form; `MODEL-LOG.md`'s own cites are append-only history.

**Negative results from the review — do not re-hunt:** `§1.x` cross-references
resolve (one apparent dangle is `CLAUDE.md §4.4`); doc-to-file references
resolve; the site's "5,000 simulations" is correct.

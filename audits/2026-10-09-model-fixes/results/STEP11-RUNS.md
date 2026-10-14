# Step 11 run record: the arm builds, before any arm run (2026-10-10)

Written and committed before the first arm run, per `reviews/STEP11-WRITER-BRIEF.md`
item 1. Specification: `prereg/2026-10-10-model-correction-batch.md` with every
amendment (A1-A13).

- **HEAD (W):** `e70116beab50e643868d3d7a179c558282f5da5a`. `src/` at W is `src/`
  at 8c1ca90 (the commits after it touch tests and documents only).
- Machine: Atlas, 8 cores, 16 GB; `.venv/bin/python` 3.13.4, numpy 2.5.1.
- Arm trees live outside the repository, under this session's scratch directory
  (`.../scratchpad/arms/<tree>`). Raw outputs go to `data/arms/step11/<arm>/`
  in the real tree (gitignored). The recipe scripts, the arm diffs and the
  harness are committed under `results/harness/`.

## 1. Arm trees: diff sha256 and tree hash

Tree hash: `find src -type f -name '*.py' | LC_ALL=C sort | xargs cat | shasum -a 256`,
first 16 hex. Diff sha256: `git diff <base> -- src | shasum -a 256`.

| arm | built as | diff base | diff sha256 (full) | lines | tree hash | prereg's value |
|---|---|---|---|---|---|---|
| A | `git archive 597ec38` | — | — | — | `7a0d39ae11e41fce` | same |
| B0 | `git archive 954086b` | — | — | — | `0983a6f0b3fbf0aa` | same |
| B6 | clone at 597ec38 + recipe 3.1 | 597ec38 | `9ed8630ee0f952f6f3109c0cea537ada1c5b34c510cef3719d7a0090181b7803` | 236 | `0ea073d69372edb7` | same (diff `9ed8630ee0f952f6…`, 236) |
| B8 | clone at 597ec38 + recipe 3.2 with A6 | 597ec38 | `eea149ebfa4043141a7c4bb772d033776fa907d4dcaaaff05faf0d9106bb5dba` | 341 | `d2b3afbdb9bfa09d` | same (diff `eea149ebfa404314…`, 341) |
| C16 | clone at W + recipe 3.3 | W | `e5fbb23b953343f045e1fba64fea30d62d55df349ccde5c6be63e4cf1570a043` | 361 | `70788004167673cc` | recomputed (A13); at acbd9f8 it was `e2ab33c6ebdd48d6` |
| C | C16 + recipe 3.4 | W | `2a55b91f1319118d3481b64a74e8c50df42a3b2c6ed1db8e337d06cb8947dc7f` | 372 | `7e14119858a16c06` | recomputed; at acbd9f8 `33acd90bb91ba1a2` |
| B | C + recipe 3.5 | W | `609ab638063d4b143ac317cb1bafad7f288d302370602bd8fc2f3c23ee80168f` | 390 | `232b6fe93bff4b50` | recomputed; at acbd9f8 `a4574cf3542727e9` |
| E (and D, D0) | `git archive W` | — | — | — | `bb771e9bad1d514d` | recomputed; at acbd9f8 `ddb9a6d3714ae29a` |

**Check of the W-based recipes.** Each was first applied, by the same scripts,
to a clone at `acbd9f8`: C16 gave `git diff acbd9f8 -- src` sha256
`81d681500680923d…` (361 lines) and tree `e2ab33c6ebdd48d6`; C gave
`618f9e961bf9d4a2…` and `33acd90bb91ba1a2`; B gave `d39643bc448d055d…` and
`a4574cf3542727e9`; `git archive acbd9f8` gave `ddb9a6d3714ae29a`. All equal §3's
values. At W, each arm's diff against W equals its diff against acbd9f8 at
acbd9f8 line for line once `@@` offset lines and `index` lines are removed
(compared with `diff`; identical for C16, C and B).

**Two facts the recipes did not state.**
- **B6 (recipe 3.1).** Cutting the `theirs` side at `slate_coverage`'s
  `return out` with no blank line after it gives 235 lines and sha256
  `2e0d65f81b3b9205…`. The stated `9ed8630ee0f952f6…` (236 lines) is produced
  with one blank line kept after `return out` at the end of `levels.py`. The
  stated hash is taken as the authority, as A6 does for B8; the difference is
  one trailing newline and no code.
- **C16 (recipe 3.3) and `git apply --check`.** §3 and A13 say a recipe that
  fails `git apply --check` on W stops the arm. `git apply --check -R` of
  cdcf517 fails on W (`patch failed: src/montecarlo.py:2698`), and fails
  identically at `acbd9f8`, where the prereg built it: the recipe is a
  `--3way` application with one conflict, which §3.3 names and resolves. At W
  the 3-way application gives the same single conflict at the same lines
  (2839-2957) as at acbd9f8, and the stated resolution reproduces the
  prereg's own hash at acbd9f8 (above). 6074382's reverse applies cleanly at
  W (`--check` passes). The arm is built and run; this is reported here and in
  the results for the reviewer to judge.

Scripts: `harness/recipe/select_hunks.py` (hunk split of
`git show 2933c2e -- src/levels.py src/montecarlo.py`; B6 hunks 3,4,8,9,10,16;
B8 hunks 0,1,2,5,6,7,8,11,12,13,14,15,17,18), `resolve_b8.py`,
`resolve_c16.py`, `switch_c.py`, `switch_b.py`. Each arm's full `src` diff:
`harness/arm-diffs/<arm>.src.diff`.

## 2. Data in each tree

- `data/processed`: a copy (`rsync -a`) of the real tree's, then every
  `pools_*.json` deleted (27 per tree), and `bye_value.json` and
  `group_share_record.json` deleted. `data/raw`: a symlink to the real tree's
  `data/raw` (not read-only at the filesystem; checked after the runs with
  `find data/raw -newer <marker>`, marker taken 10:35 SAST before the first
  emit). `.venv`: a symlink to the real tree's.
- **A:** `data/arms/A-specs-pre-batch/` copied in; `shasum -a 256 -c SHA256SUMS`
  in the tree: 27/27 OK. One `pools_sha`, `c70b8fc5bcd79279`.
- **B0, B6, B8, B, C, C16, E:** each emitted its own specs with
  POOLS-REEMIT-QUEUE.md step 2's loop (`harness/recipe/emit_loop.sh`, 27
  commands, `PYTHONHASHSEED=0`): 27 issued, 27 on disk, all newer than the
  marker, every loop exit 0. `pools_sha`: B0, B6, B8 `c70b8fc5bcd79279` (27 of
  27); B, C, C16, E `a58f884b337a7735` (27 of 27). Seven loops ran at once.
- `group_share_record.py --emit` in B, C, C16, E. `bye_value.py --emit` in E:
  under 1%: 34 pairs, weight 0.000; 1% and over: 35 pairs, weight 0.000.
- E's 27 specs, `group_share_record.json` and `bye_value.json` are
  byte-identical to the real tree's window emit (2d73de7).
- B, C and C16 hold no `bye_value.json`: their runs set `w_bye=0.4`, which
  skips the file (`run_model`: `if bye and scenario["w_bye"] is None`); a run
  that read it would refuse. A, B0, B6 and B8 hold neither record (their code
  reads neither).

**Proven current, before any run** (`tests/run_all.py`, in each tree;
`data/processed` sha256 listing identical before and after the tests in every
tree):

| tree | `-k chain`: `test_every_emitted_pool_spec_carries_a_current_artefact_key` | `test_the_specs_on_disk_agree_with_the_constructed_one` | A4's three `test_stage_inputs` tests | rest of `-k chain` |
|---|---|---|---|---|
| A | ok | (not in 597ec38-based trees) | — | 64 passed, 0 failed |
| B0, B6, B8 | ok | — | — | 64 passed, 0 failed each |
| B, C, C16 | ok | ok (passed, not skipped) | ok, ok, ok | 61 passed, 3 failed each: `test_the_forecast_runs_and_fills_the_council`, `test_the_model_is_reproducible_from_its_seed`, `test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`, each `SystemExit: …bye_value.json is missing` (a 2026 run with no `w_bye` override, in a tree that deliberately has no file) |
| E | ok | ok | ok, ok, ok | 64 passed, 0 failed |

## 3. Seeds and draws

- Panel: the 24 city-years `compare_history.runnable` returns (asked in each
  tree, recorded in `data/arms/step11/<arm>/runnable.json`), 1,000 draws,
  `compare_history.run_city_year(..., seed=None)`, so `DEFAULTS["seed"]` =
  20261104 in every tree. Each city-year in its own process.
- Johannesburg 2026: 5,000 draws, `DEFAULTS["seed"]` (20261104), the scenario
  `load_scenario` builds after `apply_city`.
- `PYTHONHASHSEED=0` for every process (asserted by the harness).
- Overrides: B, C, C16, D `--set w_bye=0.4` (panel and 2026); D0
  `--set w_bye=0`; A, B0, B6, B8, E none.

## 4. Commands

Every run is one process:

    cd <tree> && PYTHONHASHSEED=0 .venv/bin/python \
      <repo>/audits/2026-10-09-model-fixes/results/harness/arm_run.py \
      --mode panel --city <city> --year <year> --draws 1000 [--set w_bye=…] \
      --out <repo>/data/arms/step11/<arm>/<city>-<year>
    cd <tree> && PYTHONHASHSEED=0 .venv/bin/python …/arm_run.py \
      --mode forecast --city joburg --year 2026 --draws 5000 [--set w_bye=…] \
      --out <repo>/data/arms/step11/<arm>/joburg-2026
    cd <tree> && PYTHONHASHSEED=0 .venv/bin/python …/arm_run.py \
      --mode rule_a --city <city> --year <year> \
      --out <repo>/data/arms/step11/<arm>/rule_a-<city>-<year>      # A, B0

The extra 2026 runs in E's tree (P12, P19), 5,000 draws:

    … --mode forecast --city joburg --year 2026 --draws 5000 --move-aside group_share_record.json
    … --mode forecast --city joburg --year 2026 --draws 5000 --set bye_weight_mode=inverse_variance
    … --mode forecast --city joburg --year 2026 --draws 5000 --module-set montecarlo.BYE_MIN_WEIGHT=1.0

All of them are issued by `harness/run_jobs.py <arms root> <repo>/data/arms/step11 7`
(seven processes at once; the moved-aside run alone, after every other job).

`arm_run.py` installs the §2 tie classifier (a wrapper around
`montecarlo.allocate`) and a draw counter (a wrapper around
`montecarlo.allocate_with_overhang`), both delegating unchanged, captures every
drawn array from the `ModelRun` before `relabel_run`, writes the run's trace
(`run_dir`) and asserts `_pools_stale` is null and one
`allocate_with_overhang` call per draw. `rule_a` mode executes the tree's own
`audits/2026-10-07-prediction-restructure/backtest/rule_a.py` unchanged through
`runpy`. The spec comparison (E1-E4) is `harness/spec_diff.py`.

## 5. The real tree before the runs

sha256 listing digests (`find <dir> -type f | sort | xargs shasum -a 256 | shasum -a 256`,
first 16), compared again after the runs: `data/processed` 151 files
`46eacfb2a56bbb47`; `site/` 125 `db12116add3d10b6`; `content/` 10
`9de858760fea0038`; `publications/` 1 `fafaca0958b51a0f`; `prereg/` 19
`676fbc84b4bdd0bc`; `src/` 210 `4c8e54b082b08a54`; `tests/` 167
`76cae1d840adeca9`; `data/arms/A-specs-pre-batch/` 28 `9aaa2ea06513abc1`.
`git status`: clean apart from this results directory.

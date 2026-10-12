"""Step 11 job runner: every arm run as its own process, N at a time.

    .venv/bin/python run_jobs.py <arms root> <out root> <workers> [arm ...]

<arms root>/<tree>/ are the arm trees; each job runs `arm_run.py` (beside this
file) with the tree as working directory and PYTHONHASHSEED=0, writing to
<out root>/<arm>/<label>/. A job whose meta.json exists is skipped (resume).
The panel population is `compare_history.runnable` asked in each tree, for
every city in `compare_history.CITIES`; it is recorded in
<out root>/<arm>/runnable.json.
"""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARM_RUN = HERE / "arm_run.py"
arms_root, out_root, workers = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
only = set(sys.argv[4:])

W04 = ["w_bye=0.4"]
# arm: (tree, panel overrides, forecast overrides, rule_a?)
ARMS = {
    "A":   ("A",   [], [], True),
    "B0":  ("B0",  [], [], True),
    "B6":  ("B6",  [], [], False),
    "B8":  ("B8",  [], [], False),
    "B":   ("B",   W04, W04, False),
    "C":   ("C",   W04, W04, False),
    "C16": ("C16", W04, W04, False),
    "D":   ("E",   W04, W04, False),
    "D0":  ("E",   ["w_bye=0"], ["w_bye=0"], False),
    "E":   ("E",   [], [], False),
}
EXTRA = [  # (arm label, tree, label, args)
    ("E", "E", "joburg-2026-gsrecord-aside",
     ["--move-aside", "group_share_record.json"]),
    ("E", "E", "joburg-2026-inverse-variance",
     ["--set", "bye_weight_mode=inverse_variance"]),
    ("E", "E", "joburg-2026-bye-min-weight-1",
     ["--module-set", "montecarlo.BYE_MIN_WEIGHT=1.0"]),
]
PY = "/Users/simondavis/projects/atlas-jhb-election-model/.venv/bin/python"


def runnable(tree: Path) -> list[tuple[str, str]]:
    code = ("import sys,json; sys.path.insert(0,'src'); import cityconfig,"
            "compare_history as CH\n"
            "out=[]\n"
            "for s in CH.CITIES:\n"
            "    ok,_r=CH.runnable(cityconfig.use(s)); out += [[s,y] for y in ok]\n"
            "print(json.dumps(out))")
    r = subprocess.run([PY, "-c", code], cwd=tree, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONHASHSEED="0"), check=True)
    return [tuple(x) for x in json.loads(r.stdout.strip().splitlines()[-1])]


jobs = []
for arm, (tree, pset, fset, rule_a) in ARMS.items():
    if only and arm not in only:
        continue
    t = arms_root / tree
    (out_root / arm).mkdir(parents=True, exist_ok=True)
    pop = runnable(t)
    (out_root / arm / "runnable.json").write_text(json.dumps(pop))
    sets = lambda s: sum((["--set", x] for x in s), [])
    jobs.append((arm, t, "joburg-2026", ["--mode", "forecast", "--city", "joburg",
                                         "--year", "2026", "--draws", "5000"] + sets(fset)))
    for city, year in pop:
        jobs.append((arm, t, f"{city}-{year}", ["--mode", "panel", "--city", city,
                                                "--year", year, "--draws", "1000"] + sets(pset)))
        if rule_a:
            jobs.append((arm, t, f"rule_a-{city}-{year}",
                         ["--mode", "rule_a", "--city", city, "--year", year]))
for arm, tree, label, extra in EXTRA:
    if only and arm not in only:
        continue
    jobs.append((arm, arms_root / tree, label,
                 ["--mode", "forecast", "--city", "joburg", "--year", "2026",
                  "--draws", "5000"] + extra))
# the 5,000-draw forecasts first: they are the longest
jobs.sort(key=lambda j: 0 if "2026" in j[2] else 1)
# a moved-aside file is shared state inside E's tree: run that job alone,
# after every other job in E's tree has finished
aside = [j for j in jobs if "--move-aside" in j[3]]
jobs = [j for j in jobs if "--move-aside" not in j[3]]


def run(job):
    arm, tree, label, a = job
    out = out_root / arm / label
    if (out / "meta.json").exists():
        return arm, label, "skipped", 0.0
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with (out / "log.txt").open("w") as log:
        r = subprocess.run([PY, str(ARM_RUN), *a, "--out", str(out)], cwd=tree,
                           stdout=log, stderr=subprocess.STDOUT,
                           env=dict(os.environ, PYTHONHASHSEED="0"))
    status = "ok" if r.returncode == 0 else f"FAILED rc={r.returncode}"
    print(f"{time.strftime('%H:%M:%S')} {arm:4s} {label:34s} {status} "
          f"{time.time() - t0:.0f}s", flush=True)
    return arm, label, status, time.time() - t0


print(f"{len(jobs) + len(aside)} jobs, {workers} at once", flush=True)
with ThreadPoolExecutor(max_workers=workers) as ex:
    results = list(ex.map(run, jobs))
for j in aside:
    results.append(run(j))
failed = [r for r in results if r[2].startswith("FAILED")]
print(f"done: {len(results)} jobs, {len(failed)} failed")
for r in failed:
    print("FAILED", r[0], r[1])

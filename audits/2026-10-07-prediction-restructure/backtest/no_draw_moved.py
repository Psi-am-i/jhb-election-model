"""One-off proof that recording the vote arrays moved no draw (SPEC-A §3).

Runs `run_model` at joburg 2026, the published seed, 200 draws, once in a
pre-change tree and once in this tree, each in its own interpreter under
`montecarlo.HASH_SEED`, and compares every `*draws` field of the two
`ModelRun`s. Passes when every field the old run has is equal in the new one
and the only new fields are `pr_vote_draws` and `ward_vote_draws`.

    mkdir /tmp/pre-a && git archive 322bcde | tar -x -C /tmp/pre-a
    ln -s "$PWD/data" /tmp/pre-a/data      # gitignored: both trees read one data/
    # 322bcde is HEAD when slice A was written, before any of its edits
    PYTHONHASHSEED=0 .venv/bin/python audits/2026-10-07-prediction-restructure/backtest/no_draw_moved.py /tmp/pre-a/src

The whole tree is extracted because `cityconfig` and the model find `cities/`
and `data/` relative to their own files. Both trees read the same inputs;
`run_model` only reads them, and this writes only into a temporary directory. The result goes into MODEL-LOG §1.291.
"""
import os
import pickle
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
CHILD = r'''
import argparse, pickle, sys
sys.path.insert(0, sys.argv[1])
import cityconfig, montecarlo as M
city = cityconfig.use("joburg"); target = cityconfig.use_target("2026"); M.apply_city(city)
scenario = M.load_scenario(argparse.Namespace(config=None, set=[], draws=200,
                                              seed=int(M.DEFAULTS["seed"]),
                                              city="joburg", target="2026"))
run = M.run_model(target, scenario, verbose=False)
fields = {n: getattr(run, n) for n in dir(run) if n.endswith("draws") and not n.startswith("_")}
pickle.dump(fields, open(sys.argv[2], "wb"))
'''


def fields_of(src: Path, out: Path) -> dict:
    env = dict(os.environ, PYTHONHASHSEED="0")
    subprocess.run([sys.executable, "-c", CHILD, str(src), str(out)], cwd=REPO,
                   env=env, check=True)
    with out.open("rb") as fh:
        return pickle.load(fh)


def same(a, b) -> bool:
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        return np.array_equal(np.asarray(a), np.asarray(b))
    return a == b


def main(pre_src: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        old = fields_of(Path(pre_src), Path(tmp) / "old.pkl")
        new = fields_of(REPO / "src", Path(tmp) / "new.pkl")
    differ = sorted(n for n in old if not same(old[n], new.get(n)))
    added = sorted(set(new) - set(old))
    print("fields compared:", sorted(old))
    print("differ:", differ)
    print("new fields:", added)
    ok = not differ and added == ["pr_vote_draws", "ward_vote_draws"]
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))

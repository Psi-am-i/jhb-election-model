"""``src/bye_value.py`` — the by-election value test (BRIEF item 19, SPEC R2.4).

G23: the test can see an increment. On constructed pairs, where the outcome's
residual is exactly half the by-election delta the class is admitted at a
slope of 0.5; where the residual is independent of the delta the
5th-percentile gain is at or below 0 and the weight is 0; with 9 pairs the
class is "not measurable" whatever the data say. Every input in those tests is
a literal or a seeded draw; nothing is read from disk.

Beside G23, the pieces the test is built from, each pinned by hand arithmetic:
the hold-out by metro identity (a metro's own pairs never enter its fit, also
when the bootstrap draws it twice), the floored slope, the size class and its
edge, the PR conversion, the trusted ward/PR ratio and the per-contest weight.

One test reads the real archive (``build``, about 12 s): the artefact states
the cross-ballot caveat, its counts add up, and each pair's class is its 2021
list share's. G25, the no-look-ahead guard, is in ``tests/test_temporal.py``.

Run:
    ./.venv/bin/python tests/test_bye_value.py
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import bye_value as BV  # noqa: E402
import byelections as BY  # noqa: E402
import levels  # noqa: E402


METROS = ("m1", "m2", "m3", "m4", "m5", "m6")


def _pairs(n_per_metro: int, cls: str, residual, seed: int = 7) -> list[dict]:
    """Constructed pairs: ``delta_pr`` drawn from a seeded normal, ``e`` from
    ``residual(delta, rng)``, two contests each."""
    rng = np.random.default_rng(seed)
    out = []
    for m in METROS:
        for _ in range(n_per_metro):
            d = float(rng.normal(0.0, 0.05))
            out.append({"metro": m, "class": cls, "delta_pr": d,
                        "e": float(residual(d, rng)), "contests": 2})
    return out


def test_an_exact_half_increment_is_found_and_admitted():
    """G23 (a). ``e = 0.5·δ`` exactly: every leave-one-metro-out slope is 0.5,
    the gain is positive in every resample, and the class weight is the
    all-metro slope, 0.5."""
    pairs = _pairs(3, "at_or_over", lambda d, _r: 0.5 * d)
    out = BV.evaluate(pairs, resamples=200)
    c = out["at_or_over"]
    assert c["pairs"] == 18
    assert math.isclose(c["slope_all_metros"], 0.5, rel_tol=1e-12)
    assert all(math.isclose(w, 0.5, rel_tol=1e-12)
               for w in c["w_leave_one_metro_out"].values())
    assert c["G"] > 0 and c["G_percentile"] > 0, c
    assert c["verdict"] == "admitted"
    assert math.isclose(c["weight"], 0.5, rel_tol=1e-12)
    # the other class has no pair: not measurable, weight 0
    assert out["under"]["pairs"] == 0
    assert out["under"]["verdict"] == "not measurable"
    assert out["under"]["weight"] == 0.0


def test_a_residual_independent_of_the_delta_earns_no_weight():
    """G23 (b). ``e`` drawn independently of ``δ``: the 5th-percentile gain
    is at or below 0 and the weight is 0."""
    pairs = _pairs(3, "under", lambda _d, r: r.normal(0.0, 0.05), seed=11)
    c = BV.evaluate(pairs, resamples=500)["under"]
    assert c["pairs"] == 18
    assert c["G_percentile"] <= 0.0, c
    assert c["verdict"] == "no measurable gain"
    assert c["weight"] == 0.0


def test_nine_pairs_are_not_measurable_even_when_the_increment_is_exact():
    """G23 (c). Below the 10-pair floor the class takes 0 whatever the data
    say; at 10 the same exact increment is admitted."""
    nine = _pairs(3, "at_or_over", lambda d, _r: 0.5 * d)[:9]
    c = BV.evaluate(nine, resamples=200)["at_or_over"]
    assert c["pairs"] == 9
    assert c["verdict"] == "not measurable" and c["weight"] == 0.0
    ten = _pairs(3, "at_or_over", lambda d, _r: 0.5 * d)[:10]
    assert BV.evaluate(ten, resamples=200)["at_or_over"]["verdict"] == "admitted"


def test_the_bootstrap_is_reproducible_from_its_seed():
    """Same seed, same percentile; another seed, generally another one."""
    pairs = _pairs(2, "under", lambda _d, r: r.normal(0.0, 0.05), seed=3)
    a = BV.evaluate(pairs, resamples=300, seed=1)["under"]["G_percentile"]
    b = BV.evaluate(pairs, resamples=300, seed=1)["under"]["G_percentile"]
    c = BV.evaluate(pairs, resamples=300, seed=2)["under"]["G_percentile"]
    assert a == b
    assert a != c


def test_a_metro_is_held_out_by_identity_including_its_bootstrap_copies():
    """Metro A carries ``e = δ`` (slope 1); B and C carry ``e = 0``. A's
    weight is fitted on B and C only, so it is 0, also when A is drawn twice:
    a copy of A in A's fit set would make it positive. B's fit includes both
    copies of A. Hand arithmetic: with δ = (0.1, 0.2) in every metro, B's
    fit set is A, A, C: Σeδ = 2·(0.01 + 0.04) = 0.10, Σδ² = 3·0.05 = 0.15,
    so w_(−B) = 2/3."""
    d = np.array([0.1, 0.2])
    groups = [("A", d.copy(), d.copy()), ("A", d.copy(), d.copy()),
              ("B", np.zeros(2), d.copy()), ("C", np.zeros(2), d.copy())]
    g, w = BV.lomo_gain(groups)
    assert w["A"] == 0.0
    assert math.isclose(w["B"], 2 / 3, rel_tol=1e-12)
    assert math.isclose(w["C"], 2 / 3, rel_tol=1e-12)
    # G by hand: A's pairs (twice) keep |e| = 0.3 each copy (w = 0);
    # B's and C's go from |0| to |0 − (2/3)·δ| = 0.2 each: G = (0 − 0.4)/8.
    assert math.isclose(g, -0.4 / 8, rel_tol=1e-12)


def test_the_slope_is_through_the_origin_and_floored_at_zero():
    e = np.array([0.02, -0.01])
    d = np.array([0.04, -0.02])
    assert math.isclose(BV.slope(e, d), 0.5, rel_tol=1e-12)
    assert BV.slope(-e, d) == 0.0                 # negative relation: floored
    assert BV.slope(e, np.zeros(2)) == 0.0        # no variation in δ


def test_the_size_class_edge_is_one_percent_and_names_no_party():
    assert BY.BYE_CLASS_EDGE == 0.01
    assert BY.size_class(0.0) == "under"
    assert BY.size_class(0.0099999) == "under"
    assert BY.size_class(0.01) == "at_or_over"
    assert BY.size_class(0.5) == "at_or_over"
    assert BY.SIZE_CLASSES == ("under", "at_or_over")


def test_the_pr_conversion_divides_by_a_trusted_ratio_and_adds_otherwise():
    assert BY.delta_pr(0.04, None) == 0.04
    assert BY.delta_pr(0.04, 2.0) == 0.02
    assert BY.delta_pr(-0.03, 0.5) == -0.06


def test_the_trusted_ward_pr_ratio_has_its_threshold_and_its_clip():
    """Above a PR share of 0.001 only, clipped to [lo, hi]; over ``parties``
    when given."""
    wc = {"A": 0.30, "B": 0.0009, "C": 0.01, "D": 0.25}
    pc = {"A": 0.10, "B": 0.0009, "C": 0.10, "D": 0.20}
    got = levels.trusted_ward_pr(wc, pc, 0.5, 2.0)
    assert got == {"A": 2.0, "C": 0.5, "D": 1.25}
    assert levels.trusted_ward_pr(wc, pc, 0.5, 2.0, parties=["D"]) == {"D": 1.25}


def test_one_contest_carries_the_weight_and_delta_the_docstring_states():
    """``weight = exp(−age/τ)·√votes·ρ`` and ``delta = share_bye − share_base``
    on one constructed contest, by hand."""
    votes = {"W1": {"X": 60, "Y": 40}, "W2": {"X": 20, "Y": 80}}
    registered = {"W1": 200, "W2": 200}
    contests = {("2023-05-29", "W1"): {"X": 30, "Y": 70}}
    day = date(2024, 5, 29)
    found = BY.weighted_deltas(contests, votes, registered, day, 18.0, "2021")
    city = {"X": 80 / 200, "Y": 120 / 200}
    rho = 1.0 - 0.5 * (abs(0.6 - city["X"]) + abs(0.4 - city["Y"]))
    w = math.exp(-12.0 / 18.0) * math.sqrt(100) * rho
    assert math.isclose(found["weight_sum"]["X"], w, rel_tol=1e-12)
    assert math.isclose(found["weighted"]["X"] / found["weight_sum"]["X"],
                        0.30 - 0.60, rel_tol=1e-12)
    assert found["skipped"] == []
    missing = BY.weighted_deltas({("2023-05-29", "W9"): {"X": 1}}, votes,
                                 registered, day, 18.0, "2021")
    assert missing["skipped"] == [("W9", "2023-05-29")]


def test_the_real_artefact_states_its_caveat_and_its_counts_add_up():
    """On the archive: the cross-ballot caveat is in the artefact, the
    population is the pair list's length and the two classes partition it,
    each pair's class is its 2021 list share's, each pair has a positive list
    share at one of the two elections, and the weights are the classes'.
    """
    payload = BV.build()
    assert "Cross-ballot" in payload["caveat"]
    assert "2024 provincial ballot" in payload["caveat"]
    pairs = payload["pairs"]
    assert payload["population"] == len(pairs) > 0
    assert sum(payload["classes"][c]["pairs"]
               for c in BY.SIZE_CLASSES) == len(pairs)
    for p in pairs:
        assert p["class"] == BY.size_class(p["s2021"]), p
        assert p["s2021"] > 0 or p["actual"] > 0, p
        assert math.isclose(p["e"], p["actual"] - p["B"], abs_tol=1e-15)
        if p["s2021"] <= 0:
            assert p["B"] == 0.0, p
    assert payload["weights"] == {c: payload["classes"][c]["weight"]
                                  for c in BY.SIZE_CLASSES}
    assert payload["artefact_key"] == BY.bye_value_key(
        tuple(payload["artefact_key"]["ward_pr_clip"]))



# The scratch leg of the key test, run with the scratch tree as the working
# directory and its own copy of src/ first on the path, so every path the key
# reads resolves inside the scratch tree. Prints one JSON object.
_KEY_PROBE = r"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))
import byelections as BY
import montecarlo as M
here = Path(".").resolve()
clip = (M.WARD_PR_RATIO_MIN, M.WARD_PR_RATIO_MAX)
out = {"src": str(Path(BY.__file__).resolve().parent.parent) == str(here),
       "files": [str(f.relative_to(here)) for f in BY.bye_value_files()]}
art = here / "data" / "processed" / BY.BYE_VALUE
art.parent.mkdir(parents=True, exist_ok=True)
art.write_text(json.dumps({"artefact_key": BY.bye_value_key(clip),
                           "weights": {c: 0.0 for c in BY.SIZE_CLASSES}}))

def read():
    try:
        M.read_bye_value(art)
        return "accepted"
    except SystemExit as exc:
        return str(exc)

def edit(rel):
    # replace the symlink (or file) with a copy that differs in one byte
    p = here / rel
    data = bytearray(p.read_bytes())
    p.unlink()
    data[-1] ^= 1
    p.write_bytes(bytes(data))
    data[-1] ^= 1
    return p, bytes(data)

out["fresh"] = read()
for rel in (sys.argv[1], "cities/joburg.toml"):
    p, original = edit(rel)
    out["edited " + rel] = read()
    p.write_bytes(original)
    out["reverted " + rel] = read()
print(json.dumps(out))
"""


def _scratch_tree(root: Path) -> None:
    """``root`` holding a copy of ``src/`` and ``cities/``, and links to the
    raw election and by-election files (each election file its own link, so
    one can be replaced by an edited copy without touching the original)."""
    shutil.copytree(ROOT / "src", root / "src",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "cities", root / "cities")
    for sub in ("config", "judgements"):
        if (ROOT / sub).exists():
            shutil.copytree(ROOT / sub, root / sub)
    raw = root / "data" / "raw"
    (raw / "elections").mkdir(parents=True)
    for f in (ROOT / "data" / "raw" / "elections").iterdir():
        (raw / "elections" / f.name).symlink_to(f)
    (raw / "byelections").symlink_to(ROOT / "data" / "raw" / "byelections")


def test_the_key_covers_the_raw_election_files_and_the_city_files():
    """Fix row 3 of the M4 review. ``bye_value_key`` carries the raw election
    files ``B``, the outcome and the θ record are read from
    (``bye_value_files``) and every ``cities/*.toml``. In a scratch tree (a
    copy of ``src/`` and ``cities/``, links to the raw files; no file under
    this repository's ``data/`` is written): an artefact stamped with the
    scratch tree's key is accepted by ``montecarlo.read_bye_value``; one byte
    changed in a raw election file ``theta_record`` reads, and then in
    ``cities/joburg.toml``, each makes it refuse, naming the field that
    moved; each reverted, it is accepted again.

    The population: ``bye_value_files`` is every calendar election with a
    result template up to the outcome, in every metro, scanned against a
    construction from the calendar here, both ways."""
    import cityconfig
    built = [Path(f).name for f in BY.bye_value_files()]
    want = sorted(cityconfig.CALENDAR[y].results.replace("{CODE}", c)
                  for y, e in cityconfig.CALENDAR.items()
                  if e.results and int(y) <= int(BV.OUTCOME)
                  for c in levels.METRO_CODES)
    assert sorted(built) == want
    on_disk = [f for f in BY.bye_value_files() if f.exists()]
    scanned(on_disk, of=want, low=1.0, high=1.0, what="raw election files "
            "on disk", denominator="calendar elections up to the outcome x metros")
    edited = "data/raw/elections/" + cityconfig.CALENDAR["2016"].results.replace(
        "{CODE}", "JHB")
    with tempfile.TemporaryDirectory(prefix="bye_value_key_") as tmp:
        root = Path(tmp)
        _scratch_tree(root)
        env = dict(os.environ, PYTHONHASHSEED="0")
        done = subprocess.run([sys.executable, "-c", _KEY_PROBE, edited],
                              cwd=root, capture_output=True, text=True,
                              timeout=600, env=env)
        assert done.returncode == 0, done.stderr[-3000:]
        got = json.loads(done.stdout.strip().splitlines()[-1])
    assert got["src"], "the probe imported this repository's src/, not the copy"
    assert edited in got["files"]
    assert got["fresh"] == "accepted", got["fresh"]
    for rel, field in ((edited, "election_files_sha"),
                       ("cities/joburg.toml", "cities_sha")):
        assert "is stale" in got["edited " + rel] and field in got["edited " + rel], (
            rel, got["edited " + rel])
        assert got["reverted " + rel] == "accepted", (rel, got["reverted " + rel])

if __name__ == "__main__":
    raise SystemExit(run_module(globals()))

"""The draw file the interactive re-weights holds the published draws, exactly.

Build step S2 of `audits/2026-09-28-interactive-architecture/PLAN.md`.
`src/export_draws.py` runs the model under all four seat laws and writes one
binary file plus a manifest. The page shows these draws as the published
forecast when no control is moved, so the file must BE the published draws,
not a re-derivation that happens to look like them.

What this module proves, at the published city-year, seed and draw count (read
from `forecast_summary.json`, not typed here), by running the export itself:

1. SEATS. Rebuilt from the file, `seat_draws.csv` and the three
   `regime_{rule}_seat_draws.csv` are byte-equal to the published files, and
   `ward_draws.csv` likewise from the ward block.
2. CONSERVATION. In every draw under every law the party columns plus OTHER
   sum to the council, and OTHER is zero because every seat-winning party has
   its own column (an absence-shaped check: CLAUDE.md §4's four parts are
   below it).
3. THE FILE DECLARES ITSELF. The manifest's `artefact_key` carries every field
   `declares.py` requires of a run, each one a real value.
4. SIZE. Under PLAN.md's budget gzipped.
5. THE REFUSALS SEE. On constructed runs: laws that do not share their draws
   or their centres, a draw whose seats miss its council, and a file whose
   manifest disagrees with it are each refused, and the refusal goes quiet
   when reverted.
6. THE S6 FIELDS (`audits/2026-09-30-interactive-s6/SPEC-v2.md`, lane E).
   `model_sha256` recomputes from `model_modules`, which holds the model and
   not the exporter or the re-weighter, and moves with any one module's bytes;
   `published_run` names the ledger's newest run (and, on a constructed
   ledger, picks the newest row and reports a spec that differs); `centres`
   are keyed like the seat blocks and refused when metro polls move them
   after the traced stage.
7. BOTH BALLOTS (2026-10-08, SPEC-A G2/G5). The `ward_vote` and `list_vote`
   blocks are, cell for cell, the integers `run_model`'s seat law read, on
   the run's whole universe; rule A on the unpacked file equals rule A on the
   run; the `combined_share` refusal is lifted and never sits beside the
   blocks (`export_draws.ballot_faults`).

The served copy of the file, `site/draws/`, is checked by
`tests/test_served_draws.py`, not here: this module checks what the export
WRITES, that one what the site SERVES.

⚠️ Check 1 holds while the published files are what the code produces. When
the published forecast is regenerated from a changed model, both sides move
together and it stays green; when the model changes and the forecast is NOT
regenerated, it fails, which is the published tree going stale, not the export
breaking. Say which before repairing anything (CLAUDE.md §1).

The export runs four full models in parallel, so this module takes minutes.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import declares  # noqa: E402
import export_draws as E  # noqa: E402
import reweight as R  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
SUMMARY = PROCESSED / "forecast_summary.json"
#: PLAN.md build step S2's budget for the file, gzipped.
BUDGET_GZIP_BYTES = 1_500_000
PUBLISHED = {"deduct": PROCESSED / "seat_draws.csv",
             **{r: PROCESSED / f"regime_{r}_seat_draws.csv"
                for r in ("expand", "level", "cap")}}

_STATE: dict = {}


def _published_run() -> tuple[int, int]:
    """The seed and draw count the published forecast declares."""
    summary = json.loads(SUMMARY.read_text())
    return int(summary["scenario"]["seed"]), int(summary["_draws"])


def _export() -> dict:
    """Run the export once at the published seed and draws; cache the result."""
    if _STATE:
        return _STATE
    seed, draws = _published_run()
    tmp = tempfile.TemporaryDirectory(prefix="export_draws_test_")
    out = Path(tmp.name) / "out"
    done = subprocess.run(
        [sys.executable, str(ROOT / "src" / "export_draws.py"),
         "--city", "joburg", "--target", "2026",
         "--seed", str(seed), "--draws", str(draws), "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True, timeout=5400,
        env=dict(os.environ))
    if done.returncode != 0:
        raise AssertionError(f"the export failed:\n{done.stderr[-4000:]}")
    manifest = json.loads((out / "manifest.json").read_text())
    blob = (out / "base.bin").read_bytes()
    _STATE.update(tmp=tmp, out=out, manifest=manifest, blob=blob,
                  arrays=R.unpack(blob, manifest), seed=seed, draws=draws)
    return _STATE


# -- reconstruction of the published files from the export -------------------

def seat_csv_bytes(arrays: dict, manifest: dict, law: str) -> bytes:
    """`seat_draws.csv` as `montecarlo.main` writes it, from the draw file.

    `main` ranks the WHOLE universe by mean seats with a stable sort and writes
    the first thirteen. The file keeps the seat-winning parties in universe
    order, and a party with no seat in any draw has mean zero and sorts after
    them, so the same stable sort over the file's parties gives the same
    columns whenever at least thirteen parties win a seat.
    """
    parties = manifest["parties"]
    seats = arrays[f"seats/{law}"].astype(np.int64)
    council = arrays[f"council/{law}"].astype(np.int64)
    means = {p: seats[:, j].mean() for j, p in enumerate(parties)}
    top = sorted(parties, key=lambda p: -means[p])[:13]
    col = {p: j for j, p in enumerate(parties)}
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["draw", "threshold", "council_size"] + top)
    for i in range(seats.shape[0]):
        writer.writerow([i, council[i, 0], council[i, 1]]
                        + [seats[i, col[p]] for p in top])
    return buf.getvalue().encode("utf-8")


def ward_csv_bytes(arrays: dict, manifest: dict) -> bytes:
    """`ward_draws.csv` as `montecarlo.main` writes it, from the draw file."""
    block = next(b for b in manifest["blocks"] if b["name"] == "ward_winner")
    codes = manifest["ward_parties"]
    winners = arrays["ward_winner"]
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(["draw"] + block["columns"])
    for i in range(winners.shape[0]):
        writer.writerow([i] + [codes[c] for c in winners[i]])
    return buf.getvalue().encode("utf-8")


# -- 1: the seats are the published seats -------------------------------------

def test_the_export_ran_the_published_seed_and_draws():
    st = _export()
    key = st["manifest"]["artefact_key"]
    assert (key["seed"], key["draws"]) == (st["seed"], st["draws"])
    for law, path in PUBLISHED.items():
        if law == "deduct":
            continue
        declared = json.loads(path.with_name(f"regime_{law}_summary.json")
                              .read_text())["scenario"]
        assert (int(declared["seed"]), int(declared["draws"])) == (
            st["seed"], st["draws"]), (
            f"{path.name} was published at another seed or draw count, so no "
            f"export can reproduce it")
    assert st["manifest"]["laws"] == list(E.LAWS)


def test_every_published_seat_file_is_reproduced_byte_for_byte():
    st = _export()
    differ = [law for law, path in PUBLISHED.items()
              if seat_csv_bytes(st["arrays"], st["manifest"], law)
              != path.read_bytes()]
    assert not differ, (
        f"{[PUBLISHED[law].name for law in differ]} not reproduced from the "
        f"draw file. If the model changed since they were published, the "
        f"published tree is stale; if not, the export is wrong.")
    scanned(len(PUBLISHED), of=len(E.LAWS), low=1.0, high=1.0,
            what="seat files compared", denominator="the four seat laws")


def test_the_published_ward_winners_are_reproduced_byte_for_byte():
    st = _export()
    assert ward_csv_bytes(st["arrays"], st["manifest"]) == \
        (PROCESSED / "ward_draws.csv").read_bytes()


def test_a_changed_seat_or_ward_is_caught_and_the_check_then_goes_quiet():
    st = _export()
    arrays = dict(st["arrays"])
    law = "level"
    good = arrays[f"seats/{law}"]
    bad = good.copy()
    # a party the published file carries: its first party column
    with PUBLISHED[law].open(encoding="utf-8", newline="") as handle:
        first = next(csv.reader(handle))[3]
    bad[7, st["manifest"]["parties"].index(first)] += 1
    arrays[f"seats/{law}"] = bad
    assert seat_csv_bytes(arrays, st["manifest"], law) != \
        PUBLISHED[law].read_bytes()
    arrays[f"seats/{law}"] = good
    assert seat_csv_bytes(arrays, st["manifest"], law) == \
        PUBLISHED[law].read_bytes()

    good = arrays["ward_winner"]
    bad = good.copy()
    bad[3, 5] = (bad[3, 5] + 1) % len(st["manifest"]["ward_parties"])
    arrays["ward_winner"] = bad
    assert ward_csv_bytes(arrays, st["manifest"]) != \
        (PROCESSED / "ward_draws.csv").read_bytes()
    arrays["ward_winner"] = good
    assert ward_csv_bytes(arrays, st["manifest"]) == \
        (PROCESSED / "ward_draws.csv").read_bytes()


# -- 2: conservation, and no seat-winning party folded into OTHER -------------

def _other_seated_draws(arrays: dict, laws) -> list[tuple[str, int]]:
    """(law, draw) where OTHER holds a seat: a seat-winner lost its column."""
    other = []
    for law in laws:
        seats = arrays[f"seats/{law}"]
        other += [(law, int(i)) for i in np.flatnonzero(seats[:, -1] > 0)]
    return other


def _council_misses(arrays: dict, laws) -> list[tuple[str, int]]:
    out = []
    for law in laws:
        seats = arrays[f"seats/{law}"].astype(np.int64)
        council = arrays[f"council/{law}"].astype(np.int64)[:, 1]
        out += [(law, int(i)) for i in np.flatnonzero(seats.sum(axis=1) != council)]
    return out


def test_every_draw_sums_to_its_council_and_other_holds_no_seat():
    st = _export()
    arrays, manifest = st["arrays"], st["manifest"]
    laws = manifest["laws"]
    # 0. the right population: every law's block, every draw, and OTHER last
    assert all(f"seats/{law}" in arrays for law in E.LAWS)
    for law in laws:
        block = next(b for b in manifest["blocks"] if b["name"] == f"seats/{law}")
        assert block["columns"] == manifest["parties"] + ["OTHER"]
    # 1. it looked: every draw under every law
    examined = sum(arrays[f"seats/{law}"].shape[0] for law in laws)
    scanned(examined, of=st["draws"] * len(E.LAWS), low=1.0, high=1.0,
            what="law-draws examined", denominator="draws x seat laws")
    assert _other_seated_draws(arrays, laws) == []
    assert _council_misses(arrays, laws) == []
    # the file holds a real party list: some but not all of the columns carry
    # seats in the median draw
    seats = arrays["seats/deduct"]
    seated = int((np.median(seats[:, :-1], axis=0) > 0).sum())
    scanned(seated, of=len(manifest["parties"]), low=0.05, high=0.95,
            what="parties seated in the median draw",
            denominator="the file's seat-winning parties")

    # 2. it can see, and goes quiet on revert
    good = arrays["seats/cap"]
    bad = good.copy()
    bad[11, -1] += 1
    probe = dict(arrays, **{"seats/cap": bad})
    assert _other_seated_draws(probe, laws) == [("cap", 11)]
    assert _council_misses(probe, laws) == [("cap", 11)]
    probe["seats/cap"] = good
    assert _other_seated_draws(probe, laws) == []
    assert _council_misses(probe, laws) == []


def _constructed_runs(draws: int = 6) -> dict:
    """Three tiny runs, one per law, over four parties. Nothing observed."""
    rng = np.random.default_rng(1)
    universe = ["A", "B", "C", "Z"]
    turnouts = rng.uniform(0.3, 0.6, size=(draws, 2))
    ward_votes = rng.integers(1, 50_000, size=(draws, 4)).astype(np.int64)
    list_votes = rng.integers(1, 50_000, size=(draws, 4)).astype(np.int64)
    winners = rng.integers(0, 2, size=(draws, 3))
    runs = {}
    for k, law in enumerate(("deduct", "expand", "cap")):
        seats = np.zeros((draws, 4), dtype=np.int64)
        seats[:, 0] = 5 + k
        seats[:, 1] = 3
        seats[0, 2] = 1          # C wins one seat, once: it keeps a column
        council = seats.sum(axis=1)
        runs[law] = {"universe": universe, "wards": ["w1", "w2", "w3"],
                     "pool_names": ["p", "q"], "seats": seats,
                     "thresholds": council // 2 + 1, "council_sizes": council,
                     "ward_winners": winners.copy(),
                     "ward_votes": ward_votes.copy(), "list_votes": list_votes.copy(),
                     "pool_turnouts": turnouts.copy(),
                     "centres": {"A": 0.4, "B": 0.3, "C": 0.2, "Z": 0.15},
                     "poll_paths": "off"}
    return runs


def test_the_build_puts_every_seat_winner_in_a_column_and_the_rest_in_other():
    runs = _constructed_runs()
    blob, manifest = E.build(runs)
    manifest["draws"] = runs["deduct"]["seats"].shape[0]
    arrays = R.unpack(blob, manifest)
    assert manifest["parties"] == ["A", "B", "C"]      # Z never seated
    assert manifest["ward_parties"] == ["A", "B"]
    assert _other_seated_draws(arrays, runs) == []
    # both ballots on the WHOLE universe: the never-seated Z keeps its own
    # column, nothing is summed into OTHER, and the integers are exact
    cols = {b["name"]: b["columns"] for b in manifest["blocks"]}
    assert cols["ward_vote"] == cols["list_vote"] == ["A", "B", "C", "Z"]
    assert np.array_equal(arrays["ward_vote"], runs["deduct"]["ward_votes"])
    assert np.array_equal(arrays["list_vote"], runs["deduct"]["list_votes"])
    assert "pr_share" not in arrays
    assert np.array_equal(arrays["pool_turnout"], runs["deduct"]["pool_turnouts"])
    # the centres: the seat columns' keys, OTHER summing the never-seated Z
    centres = manifest["centres"]
    assert list(centres["values"]) == ["A", "B", "C", "OTHER"]
    assert centres["values"]["OTHER"] == 0.15 and centres["absent"] == []
    assert "combined_share" not in manifest and manifest["vote_blocks"] == E.VOTE_BLOCKS


def test_the_centres_are_refused_when_they_are_not_the_drawn_centres():
    runs = _constructed_runs()
    blob, manifest = E.build(runs)
    assert "values" in manifest["centres"]
    for run in runs.values():
        run["poll_paths"] = "all"
    _, manifest = E.build(runs)
    assert manifest["centres"].get("refused") is True
    assert "values" not in manifest["centres"]
    # a seat-winner with no centre is named, never given a zero
    for run in runs.values():
        run["poll_paths"] = "off"
        run["centres"] = {"A": 0.4, "B": 0.3, "Z": 0.15}
    _, manifest = E.build(runs)
    assert manifest["centres"]["absent"] == ["C"]
    assert "C" not in manifest["centres"]["values"]


# -- 5: the refusals see ------------------------------------------------------

def test_laws_that_do_not_share_their_draws_are_refused_and_then_accepted():
    runs = _constructed_runs()
    assert E.shared_draw_differences(runs) == []
    kept = runs["cap"]["pool_turnouts"]
    runs["cap"]["pool_turnouts"] = kept + np.where(
        np.arange(kept.size).reshape(kept.shape) == 3, 1e-9, 0.0)
    assert E.shared_draw_differences(runs) == ["cap:pool_turnouts"]
    try:
        E.build(runs)
    except SystemExit as exc:
        assert "did not share their draws" in str(exc)
    else:
        raise AssertionError("a law with different draws was not refused")
    runs["cap"]["pool_turnouts"] = kept
    assert E.shared_draw_differences(runs) == []
    E.build(runs)
    # the centres precede the law, so a law with other centres is refused too
    kept = runs["expand"]["centres"]
    runs["expand"]["centres"] = dict(kept, B=kept["B"] + 1e-12)
    assert E.shared_draw_differences(runs) == ["expand:centres"]
    runs["expand"]["centres"] = kept
    assert E.shared_draw_differences(runs) == []


def test_a_draw_that_misses_its_council_is_refused():
    runs = _constructed_runs()
    runs["expand"]["council_sizes"] = runs["expand"]["council_sizes"].copy()
    runs["expand"]["council_sizes"][2] += 1
    try:
        E.build(runs)
    except SystemExit as exc:
        assert "do not sum to its council" in str(exc)
    else:
        raise AssertionError("a draw whose seats miss its council was accepted")
    runs["expand"]["council_sizes"][2] -= 1
    E.build(runs)


def test_a_file_that_disagrees_with_its_manifest_is_refused():
    runs = _constructed_runs()
    blob, manifest = E.build(runs)
    manifest["draws"] = runs["deduct"]["seats"].shape[0]
    R.unpack(blob, manifest)
    for broken_blob, broken_manifest in (
            (blob[:-1], manifest),
            (blob, dict(manifest, format="something-else")),
            (blob, dict(manifest, draws=manifest["draws"] + 1))):
        try:
            R.unpack(broken_blob, broken_manifest)
        except R.Refused:
            continue
        raise AssertionError("a draw file that disagrees with its manifest was read")



def test_the_combined_share_refusal_is_lifted_and_never_both():
    """G5: the build's manifest carries both vote blocks and no refusal;
    ``ballot_faults`` complains about a refusal beside the blocks and about a
    missing block, and is quiet on the clean manifest again."""
    runs = _constructed_runs()
    _, manifest = E.build(runs)
    assert E.ballot_faults(manifest) == []
    both = dict(manifest, combined_share={"refused": True})
    assert any("lifted it" in f for f in E.ballot_faults(both))
    one = dict(manifest, blocks=[b for b in manifest["blocks"] if b["name"] != "list_vote"])
    assert any("list_vote block is missing" in f for f in E.ballot_faults(one))
    stepped = dict(manifest, blocks=[dict(b, dtype="<f8") if b["name"] == "ward_vote" else b
                                     for b in manifest["blocks"]])
    assert any("not stored as whole votes" in f for f in E.ballot_faults(stepped))
    assert E.ballot_faults(manifest) == []
    # and the build itself refuses a run whose two ballots are not on one roster
    import copy
    broken = copy.deepcopy(runs)
    for run in broken.values():
        run["ward_votes"] = run["ward_votes"][:, :3]
    try:
        E.build(broken)
    except (SystemExit, ValueError):
        pass
    else:
        raise AssertionError("a ward block on three of four parties was accepted")


def test_the_vote_blocks_are_run_model_s_integers_and_rule_a_agrees():
    """G2: the served blocks are, cell for cell, the integers ``run_model``'s
    seat law read, and rule A on the unpacked file equals rule A on the run:
    the calls, both vote dicts, the pool and the council. Constructed
    violation: two list-vote columns swapped in the file move rule A's votes;
    reverted, they agree again. In-process at a small draw count; needs the
    fixed hash seed that run_all.py sets."""
    import montecarlo as M
    import prediction
    from seats import eligible_parties, lot_identity
    if os.environ.get("PYTHONHASHSEED") != str(M.HASH_SEED):
        from _support import skip
        skip(f"PYTHONHASHSEED is {os.environ.get('PYTHONHASHSEED')!r}, not "
             f"{M.HASH_SEED!r}: export_draws._run_law refuses to run without it. "
             f"Run through tests/run_all.py, which sets it.")
    seed, _draws = _published_run()
    r = E._run_law("deduct", "joburg", "2026", 40, seed)
    blob, manifest = E.build({"deduct": r})
    arrays = R.unpack(blob, manifest)
    cols = {b["name"]: b["columns"] for b in manifest["blocks"]}
    assert cols["ward_vote"] == cols["list_vote"] == r["universe"]
    assert np.array_equal(arrays["ward_vote"], r["ward_votes"])
    assert np.array_equal(arrays["list_vote"], r["list_votes"])
    scanned(arrays["list_vote"].shape[0], of=40, low=1.0, high=1.0,
            what="draws compared", denominator="draws run")

    # the run's identity for the seeded lot (ModelRun.lot), as the build names it
    lot = lot_identity("joburg", "2026", seed)
    run_pred = prediction.rule_a(r["ward_winners"], r["universe"], r["wards"],
                                 r["ward_votes"], r["list_votes"], r["universe"],
                                 lot=lot)

    def served(list_block):
        return prediction.rule_a(arrays["ward_winner"], manifest["ward_parties"],
                                 cols["ward_winner"], arrays["ward_vote"],
                                 list_block, cols["list_vote"], lot=lot)
    file_pred = served(arrays["list_vote"])
    assert file_pred == run_pred
    assert set(eligible_parties(file_pred["ward_votes"], file_pred["list_votes"])) == \
        set(eligible_parties(run_pred["ward_votes"], run_pred["list_votes"]))
    assert prediction.seats_of(file_pred, M.COUNCIL, lot=lot) == \
        prediction.seats_of(run_pred, M.COUNCIL, lot=lot)

    # it can see: the two largest list columns swapped
    means = arrays["list_vote"].astype(np.int64).mean(axis=0)
    a, b = (int(j) for j in np.argsort(-means)[:2])
    swapped = np.array(arrays["list_vote"], copy=True)
    swapped[:, [a, b]] = swapped[:, [b, a]]
    assert served(swapped)["list_votes"] != run_pred["list_votes"]
    assert served(arrays["list_vote"]) == run_pred

# -- 3 and 4: the manifest declares, and the file fits ------------------------

def test_the_manifest_carries_every_field_declares_requires_of_a_run():
    st = _export()
    key = st["manifest"]["artefact_key"]
    required = declares.KINDS["run"].required
    missing = [f for f in required if not declares._declared(key.get(f))]
    assert not missing, f"artefact_key lacks {missing}"
    # `_declared` accepts any non-empty dict, so the commit string itself is
    # checked: "<unavailable>" (no git checkout) fails here
    assert len(key["git"]["commit"]) == 40, key["git"]
    assert len(key["code_sha256"]) == 64
    assert set(key["config"]) == set(E.LAWS)
    assert {key["config"][law]["overhang_rule"] for law in E.LAWS} == set(E.LAWS)
    # the pool spec the file was made from is the one on disk now
    import cityconfig
    import freeze
    assert key["inputs"] == freeze.pool_artefact_keys(cityconfig.use("joburg"))
    # and the strength judgements it ran with (step-6 item 3)
    assert declares.manifest_judgements_lie(key) is None, \
        declares.manifest_judgements_lie(key)


def test_the_manifest_declares_the_judgements_and_a_forecast_must():
    """Step-6 item 3, constructed (no export run): the manifest carries the
    one strength-judgement hash the laws applied, laws that disagree are
    refused, and `declares.manifest_judgements_lie` fails a forecast manifest
    that declares none, passes it with the live hash, and passes a backtest
    manifest with none."""
    import montecarlo as M
    sc = {k: M.DEFAULTS[k] for k in ("draw_law", "apply_judgements")}
    live = M.live_judgements_sha("joburg", "2026", dict(M.DEFAULTS))
    runs = {law: {"judgements_applied_sha": live} for law in E.LAWS}
    assert E.judgements_declaration(runs) == live
    try:
        E.judgements_declaration(dict(runs, cap={"judgements_applied_sha": "0"}))
    except SystemExit as exc:
        assert "different strength judgements" in str(exc)
    else:
        raise AssertionError("laws with different judgements were accepted")
    key = {"city": "joburg", "target": "2026", "config": {"deduct": sc},
           "judgements_applied_sha": live}
    assert declares.manifest_judgements_lie(key) is None
    assert "declares no strength-judgement hash" in (
        declares.manifest_judgements_lie(dict(key, judgements_applied_sha=None))
        or "")
    assert declares.manifest_judgements_lie(key) is None
    assert declares.manifest_judgements_lie(
        dict(key, target="2021", judgements_applied_sha=None)) is None


def test_the_model_hash_is_the_model_s_import_closure_and_recomputes():
    st = _export()
    key = st["manifest"]["artefact_key"]
    modules = key["model_modules"]
    # the manifest names no directory (E.PRIVATE_KEYS); the export ran this tree's src/
    assert not set(E.PRIVATE_KEYS) & set(key), sorted(key)
    src = ROOT / "src"
    # 0. the right population: the model's own module is in it, and neither
    # the exporter nor the page's re-weighter (imported only by `build`)
    assert "montecarlo.py" in modules
    assert "export_draws.py" not in modules and "reweight.py" not in modules
    # 1. it looked: a closure, not the whole directory and not one file
    scanned(len(modules), of=len(list(src.glob("*.py"))), low=0.02, high=0.9,
            what="modules in the model's import closure",
            denominator="the .py files in the source directory")
    assert key["model_sha256"] == E.files_sha256(src / m for m in modules)
    assert key["model_sha256"] != key["code_sha256"]
    # 2. it can see: the hash moves with any one module's bytes
    with tempfile.TemporaryDirectory() as tmp:
        copies = []
        for m in modules:
            (Path(tmp) / m).write_bytes((src / m).read_bytes())
            copies.append(Path(tmp) / m)
        assert E.files_sha256(copies) == key["model_sha256"]
        copies[0].write_bytes(copies[0].read_bytes() + b"\n")
        assert E.files_sha256(copies) != key["model_sha256"]


def test_the_manifest_names_the_ledger_s_latest_run():
    st = _export()
    import publication
    rows = publication.history("joburg", root=ROOT / "publications")
    newest = max(rows, key=lambda r: r.published_at)
    run = st["manifest"]["published_run"]
    assert run["model_run_id"] == newest.model_run_id
    assert run["published_at"] == newest.published_at
    assert run["pool_artefact_keys"] == newest.provenance["pool_artefact_keys"]
    assert run["inputs_match_ledger"] is (
        st["manifest"]["artefact_key"]["inputs"] == run["pool_artefact_keys"])


def test_published_run_reads_the_newest_row_and_compares_the_inputs():
    """On a constructed ledger: the newest `published_at` wins, whatever the
    file order, and a spec key that differs from the row's is reported."""
    keys = {"pools_2026.json": {"pools_sha": "aaa"}}

    def row(run_id: str, when: str) -> str:
        return json.dumps({
            "token": "t", "value": 1, "display": "1", "fmt": None,
            "source": "s", "model_run_id": run_id, "run_at": when,
            "as_of": when, "published_at": when, "change_class": None,
            "reason": None, "movement": "new", "schema": 1,
            "provenance": {"pool_artefact_keys": keys}})

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "x").mkdir()
        (Path(tmp) / "x" / "ledger.jsonl").write_text(
            row("r-new", "2026-09-02T00:00:00Z") + "\n"
            + row("r-old", "2026-09-01T00:00:00Z") + "\n")
        got = E.published_run("x", keys, root=Path(tmp))
        assert got["model_run_id"] == "r-new"
        assert got["inputs_match_ledger"] is True
        got = E.published_run("x", {"pools_2026.json": {"pools_sha": "bbb"}},
                              root=Path(tmp))
        assert got["inputs_match_ledger"] is False
        assert E.published_run("absent", keys, root=Path(tmp))[
            "model_run_id"] is None


def test_the_manifest_centres_are_the_trace_s_and_combined_share_is_lifted():
    st = _export()
    manifest = st["manifest"]
    centres = manifest["centres"]
    assert list(centres["values"]) == manifest["parties"] + ["OTHER"]
    assert centres["absent"] == []
    values = np.array(list(centres["values"].values()))
    assert np.all(values >= 0) and np.all(np.isfinite(values))
    # levels, not shares: some party carries a real level, none is all of it
    top = max(centres["values"], key=centres["values"].get)
    assert 0.05 < centres["values"][top] < 0.95, top
    assert "combined_share" not in manifest
    assert manifest["vote_blocks"] == E.VOTE_BLOCKS
    assert E.ballot_faults(manifest) == []


def test_the_file_is_within_the_budget_gzipped():
    st = _export()
    size = len(gzip.compress(st["blob"], compresslevel=9))
    print(f"  base.bin {len(st['blob']):,} bytes, {size:,} gzipped")
    assert size <= BUDGET_GZIP_BYTES, f"{size:,} bytes gzipped"


def test_votes_and_turnouts_are_what_the_model_drew():
    st = _export()
    arrays, manifest = st["arrays"], st["manifest"]
    blocks = {b["name"]: b for b in manifest["blocks"]}
    assert "pr_share" not in blocks and not any("step" in b for b in blocks.values())
    for name in ("ward_vote", "list_vote"):
        assert np.dtype(blocks[name]["dtype"]).kind == "u", name
        assert np.all(arrays[name].astype(np.int64).sum(axis=1) > 0), name
    spec = json.loads((PROCESSED / "pools_2026.json").read_text())["pools"]
    block = next(b for b in manifest["blocks"] if b["name"] == "pool_turnout")
    assert set(block["columns"]) == set(spec)
    t = arrays["pool_turnout"]
    for j, name in enumerate(block["columns"]):
        lo, _, hi = spec[name]["turnout"]
        assert np.all((t[:, j] > lo) & (t[:, j] < hi)), name
        assert np.std(t[:, j]) > 0, name


def test_the_reported_bye_weight_is_the_one_blended_centres_applied():
    """G26 (BRIEF item 19). For every row of the real
    ``byelection_party_deltas.csv``, the weight the index reports equals the
    one ``blended_centres`` gave that party, carried every step the export
    carries it: ``30_centres``' ``bye_weight`` in a run directory, read by
    ``_bye_weight_from_trace``, put in the manifest by ``build``, written as
    the published cell's ``manifest.json``, read back by ``write_index`` and
    reported in ``index.json``'s ``byelection`` rows. Constructed sizes put
    parties in both classes and constructed class weights (0.2, 0.7) differ,
    so a report that ignored the class, or used a typed weight, would
    disagree; a step that dropped the weight reports ``None``. Both
    directions: every row but ``UNKNOWN`` is reported, and every weighed party
    is a row. The runs are constructed (``_constructed_runs``); no model run.
    """
    import montecarlo as M
    bye_path = PROCESSED / "byelection_party_deltas.csv"
    with open(bye_path, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)]
    parties = [r["party"] for r in rows if r["party"] != "UNKNOWN"]
    scanned(parties, of=rows, low=0.5, high=1.0, what="by-election rows "
            "weighed", denominator="rows of byelection_party_deltas.csv")
    bye = {r["party"]: (float(r["weight_sum"]), float(r["weighted_delta"]))
           for r in rows if r["party"] != "UNKNOWN"}
    base = {p: 0.05 for p in parties}
    prior = {p: (0.004 if i % 2 else 0.05) for i, p in enumerate(parties)}
    scenario = {"w_bye": None, "level_shrink": 0.0,
                "spine_level": {p: 0.05 for p in parties},
                "_bye_value": {"weights": {"under": 0.2, "at_or_over": 0.7}}}

    class _Trace:
        def __init__(self, root):
            self.root = root

        def put(self, name, value=None, **_kw):
            (self.root / f"{name}.json").write_text(json.dumps(value))
            return value

    saved = M.PLAN_BOUNDS
    M.PLAN_BOUNDS = {}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            M.blended_centres(scenario, base, prior, bye, trace=_Trace(Path(tmp)))
            carried = E._bye_weight_from_trace(Path(tmp))
    finally:
        M.PLAN_BOUNDS = saved
    applied = scenario["_bye_weight"]
    assert {applied[p]["class"] for p in applied} == {"under", "at_or_over"}
    # through the export: build's manifest, the published cell's manifest.json
    # on disk, and write_index's read of it
    runs = _constructed_runs()
    for run in runs.values():
        run["bye_weight"] = carried
    _blob, data = E.build(runs)
    import cityconfig
    city, target = cityconfig.active().slug, cityconfig.target().year
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = dict(data, artefact_key={
                "config": {"deduct": {"w_bye": None}}, "overrides": [],
                "code_sha256": "c", "draws": 6, "seed": 1,
                "city": "joburg", "target": "2026"})
            (root / "manifest.json").write_text(json.dumps(manifest))
            index = E.write_index(root)
            assert json.loads((root / "index.json").read_text()) == index
    finally:
        cityconfig.use(city)
        cityconfig.use_target(target)
    report = index["byelection"]
    assert [r["party"] for r in report] == parties
    assert set(applied) == set(parties)
    for r in report:
        assert r["class_weight"] == applied[r["party"]]["weight"], r
        assert r["size_class"] == applied[r["party"]]["class"], r
    # it can see: a report built from a weight the model did not apply differs
    wrong = {p: {"weight": 0.4, "class": "under"} for p in carried}
    assert any(r["class_weight"] != applied[r["party"]]["weight"]
               for r in E.byelection_index(bye_path, wrong))



def _cell_manifest(w_bye, bye_weight=None) -> dict:
    """A constructed cell manifest: only the fields ``index_cell`` reads."""
    m = {"artefact_key": {"config": {"deduct": {"w_bye": w_bye}},
                          "overrides": [] if w_bye is None else [f"w_bye={w_bye}"],
                          "code_sha256": "c", "draws": 10, "seed": 1}}
    if bye_weight is not None:
        m["bye_weight"] = bye_weight
    return m


def test_the_cells_order_and_compare_by_effective_weight_not_w_bye():
    """Fix row 2 of the M4 review (BRIEF item 19). The published cell's
    ``w_bye`` is ``None``; its weight is the per-party class weights in its
    manifest's ``bye_weight``. On constructed manifests: the index orders the
    cells by that effective weight, the published cell in the middle, and
    ``build_play.bye_ends`` labels the override cells at either end by their
    side of it. Three cases: class weights strictly inside (0.2, 0.7); every
    class weight 0, which ties the published cell with the "not at all" cell;
    every class weight 1, the tie at the other end. A cell exported before
    item 19 (no ``bye_weight``, numeric ``w_bye``) is ordered by its
    ``w_bye``. No file and no model run."""
    import build_play
    over = lambda w: {"A": {"weight": w, "class": "override"},  # noqa: E731
                      "B": {"weight": w, "class": "override"}}
    for under, at_or_over in ((0.2, 0.7), (0.0, 0.0), (1.0, 1.0)):
        published = _cell_manifest(None, {
            "A": {"weight": under, "class": "under"},
            "B": {"weight": at_or_over, "class": "at_or_over"}})
        # deliberately listed out of order
        cells = [E.index_cell(_cell_manifest(1, over(1.0)), "w_bye-1"),
                 E.index_cell(published, "."),
                 E.index_cell(_cell_manifest(0, over(0.0)), "w_bye-0")]
        assert cells[1]["w_bye"] is None
        assert cells[1]["bye_weight_range"] == [min(under, at_or_over),
                                                max(under, at_or_over)]
        ordered = [c["path"] for c in E.order_bye_cells(cells)]
        assert ordered == ["w_bye-0", ".", "w_bye-1"], (under, ordered)
        ends = [(label, c["path"]) for label, c in
                build_play.bye_ends(E.order_bye_cells(cells))]
        assert ends == [("Fully", "w_bye-1"), ("Not at all", "w_bye-0")], ends
    # an index written before item 19: no range, ordered by w_bye
    old = [{"path": p, "w_bye": w} for p, w in
           (("w_bye-1", 1), (".", 0.4), ("w_bye-0", 0))]
    assert [c["path"] for c in E.order_bye_cells(old)] == ["w_bye-0", ".", "w_bye-1"]
    assert E.bye_weight_range(None, 0.4) == [0.4, 0.4]
    assert E.bye_weight_range({}, None) == [0.0, 0.0]
    # a "no record" party's 0 is its rule, not the cell's weight (§A60)
    norec = {"A": {"weight": 1.0, "class": "override"},
             "N": {"weight": 0.0, "class": "no record"}}
    assert E.bye_weight_range(norec, 1.0) == [1.0, 1.0]
    assert E.bye_weight_range({"N": norec["N"]}, 1.0) == [1.0, 1.0]
    assert E.bye_weight_range({"N": dict(norec["N"], **{"class": "override"})},
                              1.0) == [0.0, 0.0]
    # it can see: ordering by w_bye, as before the fix, cannot order the
    # published cell at all
    try:
        sorted(cells, key=lambda c: c["w_bye"])
    except TypeError:
        pass
    else:
        raise AssertionError("w_bye ordered a cell whose w_bye is None")

if __name__ == "__main__":
    raise SystemExit(run_module(globals()))

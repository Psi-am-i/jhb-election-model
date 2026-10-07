"""The draw files the site SERVES are the published forecast, and say which run.

S6 lane E (`audits/2026-09-30-interactive-s6/SPEC-v2.md`; review finding B3:
"the served `site/draws/` is tested by nothing"). `tests/test_export_draws.py`
checks what `src/export_draws.py` writes into a scratch directory; this module
checks the committed bytes under `site/draws/`, which are what a reader's
browser downloads. It runs no model, so it is cheap.

What it proves, on the base cell (the one with no lever override):

1. SEATS. `seat_draws.csv` and the three `regime_{rule}_seat_draws.csv`, and
   `ward_draws.csv`, rebuilt from the served `base.bin` with the rebuilders of
   `test_export_draws` (one definition), are byte-equal to the published files.
2. WARD PROBABILITIES. `ward_winner_probs.csv` is reproduced from the ward
   block: every ward, every party's Jeffreys `p_win` at the file's four
   decimals, and the winner wherever the top count is unique. The `dist`
   ordering is compared as a set, not a string: `main` orders it with an
   unstable sort and ties exist.
3. SUMMARY. `forecast_summary.json`'s per-party `median`, `p5`, `p95` and
   `ward_wins_mean`, its `threshold_median`, `_draws` and seed. The party set
   is the summary's own (its membership rule is not re-derived here).
   `p_excessive_*`, the coalition tables and `structural` need the overhang
   flags or `coalitions.py`, which the file does not carry: NOT CHECKED.
4. EVERY CELL. Each cell `index.json` lists exists and every cell under
   `site/draws/` is listed (both directions); each unpacks against its
   manifest and every draw's seats sum to its council under every law.
5. THE RUN. Each cell's manifest `published_run.model_run_id` names the
   ledger's newest model run (the id's `r-<content>` part: the run's
   artefacts; the commit after it changes with every publish of the same run,
   owner 2026-10-07) and its pool specs are that run's (`inputs_match_ledger`), and
   each carries `model_sha256`. A cell exported before S6 carries neither and
   FAILS with the instruction to re-export — it does not skip, because the
   cell is on disk and stale, which is a finding.
6. NOTHING PRIVATE SHIPS (deploy review 2026-09-30, F2/F3). No served manifest
   carries `export_draws.PRIVATE_KEYS` or an absolute path, and every poll in
   `index.json` carries the reader caveat from `content/joburg/poll-caveats.toml`,
   not the register's working note. A constructed manifest with a path, and an
   index with the register's caveat, are each caught and go quiet when reverted.
7. THE CHECKS SEE. One flipped byte inside a compared seat column breaks
   check 1, a changed ward column breaks check 2 and a changed summary median
   breaks check 3, each quiet when reverted; a manifest with the wrong run id, or
   none, breaks check 5 and goes quiet when reverted. In memory only: nothing
   here writes under `site/`.

Skips loudly, per test, when `site/draws/` is absent.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip  # noqa: E402

import reweight as R  # noqa: E402
from test_export_draws import (PROCESSED, PUBLISHED, SUMMARY,  # noqa: E402
                               _council_misses, seat_csv_bytes,
                               ward_csv_bytes)

DRAWS = ROOT / "site" / "draws"
WARD_PROBS = PROCESSED / "ward_winner_probs.csv"
REEXPORT = ("re-export every cell (`src/export_draws.py --out <scratch>` per "
            "cell, then `--index`) and commit the result to site/draws/")

_STATE: dict = {}


def _served() -> dict:
    """index.json, every cell's manifest and blob, and the base cell's arrays."""
    if not DRAWS.is_dir():
        skip(f"{DRAWS} is absent: the served draw files are not in this tree, "
             f"so nothing the site serves can be checked")
    if _STATE:
        return _STATE
    index = json.loads((DRAWS / "index.json").read_text())
    cells = {}
    for cell in index["cells"]:
        where = DRAWS / cell["path"]
        cells[cell["path"]] = {
            "manifest": json.loads((where / "manifest.json").read_text()),
            "blob": (where / "base.bin").read_bytes(),
            "entry": cell}
    base = [p for p, c in cells.items() if not c["entry"]["overrides"]]
    assert len(base) == 1, f"expected one cell with no override, got {base}"
    b = cells[base[0]]
    _STATE.update(index=index, cells=cells, base=base[0],
                  manifest=b["manifest"], blob=b["blob"],
                  arrays=R.unpack(b["blob"], b["manifest"]))
    return _STATE


# -- 1: seats -----------------------------------------------------------------

def _unmatched_seat_files(arrays: dict, manifest: dict) -> list[str]:
    return [PUBLISHED[law].name for law in PUBLISHED
            if seat_csv_bytes(arrays, manifest, law) != PUBLISHED[law].read_bytes()]


def test_the_served_seats_are_the_published_seat_files_byte_for_byte():
    st = _served()
    assert st["manifest"]["laws"] == list(PUBLISHED), st["manifest"]["laws"]
    differ = _unmatched_seat_files(st["arrays"], st["manifest"])
    assert not differ, (
        f"the served base.bin does not reproduce {differ}. If the forecast was "
        f"re-run since the cells were exported, the served files are stale: "
        f"{REEXPORT}.")


def test_the_served_ward_winners_are_the_published_ward_draws():
    st = _served()
    assert ward_csv_bytes(st["arrays"], st["manifest"]) == \
        (PROCESSED / "ward_draws.csv").read_bytes()


# -- 2: ward probabilities ----------------------------------------------------

def _ward_prob_differences(arrays: dict, manifest: dict) -> list[str]:
    """Wards whose published `p_win`s the served ward block does not give."""
    block = next(b for b in manifest["blocks"] if b["name"] == "ward_winner")
    codes = manifest["ward_parties"]
    winners = arrays["ward_winner"].astype(np.int64)
    draws = winners.shape[0]
    with WARD_PROBS.open(encoding="utf-8", newline="") as handle:
        published = {row["ward"]: row for row in csv.DictReader(handle)}
    if set(published) != set(block["columns"]):
        return [f"ward sets differ: published-only "
                f"{sorted(set(published) - set(block['columns']))}, served-only "
                f"{sorted(set(block['columns']) - set(published))}"]
    out = []
    for j, ward in enumerate(block["columns"]):
        counts = np.bincount(winners[:, j], minlength=len(codes))
        # `montecarlo.main`'s `_p_win`: the Jeffreys posterior mean
        mine = {codes[k]: f"{(c + 0.5) / (draws + 1.0):.4f}"
                for k, c in enumerate(counts) if c > 0}
        row = published[ward]
        theirs = dict(item.split(":") for item in row["dist"].split("|"))
        if mine != theirs or row["p_win"] != max(mine.values(), key=float):
            out.append(ward)
            continue
        top = np.flatnonzero(counts == counts.max())
        if len(top) == 1 and row["winner"] != codes[top[0]]:
            out.append(ward)
    return out


def test_the_served_ward_block_reproduces_ward_winner_probs():
    st = _served()
    block = next(b for b in st["manifest"]["blocks"] if b["name"] == "ward_winner")
    scanned(len(block["columns"]), of=len(WARD_PROBS.read_text().splitlines()) - 1,
            low=1.0, high=1.0, what="wards compared",
            denominator="ward_winner_probs.csv's rows")
    assert _ward_prob_differences(st["arrays"], st["manifest"]) == []


# -- 3: the summary -----------------------------------------------------------

def _summary_differences(arrays: dict, manifest: dict, summary: dict) -> list[str]:
    seats = arrays["seats/deduct"].astype(np.int64)
    council = arrays["council/deduct"].astype(np.int64)
    winners = arrays["ward_winner"].astype(np.int64)
    parties, codes = manifest["parties"], manifest["ward_parties"]
    draws = seats.shape[0]
    out = []
    if summary["_draws"] != draws or summary["_draws"] != manifest["draws"]:
        out.append("_draws")
    if int(summary["scenario"]["seed"]) != int(manifest["artefact_key"]["seed"]):
        out.append("seed")
    if summary["threshold_median"] != int(np.median(council[:, 0])):
        out.append("threshold_median")
    for party, published in summary["parties"].items():
        if party not in parties:
            out.append(f"{party}: in the summary, not a column of the file")
            continue
        s = seats[:, parties.index(party)]
        wins = int((winners == codes.index(party)).sum()) if party in codes else 0
        mine = {"median": float(np.median(s)),
                "p5": float(np.percentile(s, 5)),
                "p95": float(np.percentile(s, 95)),
                "ward_wins_mean": wins / draws}
        out += [f"{party}.{k}" for k, v in mine.items() if published[k] != v]
    return out


def test_the_served_seats_reproduce_the_published_summary():
    st = _served()
    summary = json.loads(SUMMARY.read_text())
    scanned(len(summary["parties"]), of=len(st["manifest"]["parties"]),
            low=0.02, high=0.9, what="summary parties compared",
            denominator="the file's seat-winning parties")
    assert _summary_differences(st["arrays"], st["manifest"], summary) == []


# -- 4: every cell ------------------------------------------------------------

def test_every_cell_is_indexed_unpacks_and_sums_to_its_council():
    st = _served()
    listed = {c["path"] for c in st["index"]["cells"]}
    on_disk = {(m.parent.relative_to(DRAWS).as_posix() or ".")
               for m in DRAWS.rglob("manifest.json")}
    assert listed == on_disk, (f"index-only {sorted(listed - on_disk)}, "
                               f"disk-only {sorted(on_disk - listed)}")
    assert st["index"]["paired"] is False
    for path, cell in st["cells"].items():
        arrays = R.unpack(cell["blob"], cell["manifest"])
        laws = cell["manifest"]["laws"]
        assert _council_misses(arrays, laws) == [], path
        assert cell["manifest"]["artefact_key"]["overrides"] == \
            cell["entry"]["overrides"], path


# -- 5: the run each cell stands for ------------------------------------------

def _ledger_newest() -> dict:
    import publication
    rows = publication.history("joburg", root=ROOT / "publications")
    assert rows, "the Johannesburg ledger is empty"
    row = max(rows, key=lambda r: r.published_at)
    return {"model_run_id": row.model_run_id,
            "pool_artefact_keys": (row.provenance or {}).get("pool_artefact_keys")}


def _model_run(run_id) -> str | None:
    """The model run in a `publication.run_identity` id, `r-<content>-<commit>[-dirty]`:
    its `r-<content>` part. Two publications of one run differ only after it."""
    m = re.fullmatch(r"(r-[0-9a-f]{12})-[0-9a-z]+(?:-dirty)?", run_id or "")
    return m.group(1) if m else None


def _run_problems(manifests: dict[str, dict], newest: dict) -> list[str]:
    """Cells that do not say they are the ledger's newest model run, and why."""
    out = []
    for path, manifest in manifests.items():
        run = manifest.get("published_run")
        key = manifest.get("artefact_key", {})
        if not run or "model_sha256" not in key:
            out.append(f"{path}: no published_run/model_sha256 (exported "
                       f"before S6)")
        elif _model_run(run.get("model_run_id")) is None or \
                _model_run(run.get("model_run_id")) != _model_run(newest["model_run_id"]):
            out.append(f"{path}: run {run.get('model_run_id')!r}, ledger "
                       f"{newest['model_run_id']!r}")
        elif key.get("inputs") != newest["pool_artefact_keys"]:
            out.append(f"{path}: pool specs are not the ledger run's")
    shas = {m.get("artefact_key", {}).get("model_sha256")
            for m in manifests.values()}
    if len(shas) > 1:
        out.append(f"the cells were drawn by {len(shas)} different models")
    return out


def test_every_served_cell_is_the_ledger_s_newest_run():
    st = _served()
    manifests = {p: c["manifest"] for p, c in st["cells"].items()}
    problems = _run_problems(manifests, _ledger_newest())
    assert not problems, (
        "the served cells do not name the published run:\n  "
        + "\n  ".join(problems) + f"\nRE-EXPORT NEEDED: {REEXPORT}.")


# -- 6: nothing private ships --------------------------------------------------

#: An absolute path on a Unix or Windows machine, or a home directory, at the
#: start of a JSON string or after a space, bracket, = or : inside one ("built
#: at /Users/..."); a URL's own path segments are not matched.
_PATH = re.compile(r'(?:^|[\s"\'(=:])(?:/(?:Users|home|private|tmp|var)/|[A-Za-z]:\\\\|~/)')


def _private_problems(manifests: dict[str, dict], index: dict) -> list[str]:
    import export_draws as E
    import polling

    out = []
    for path, manifest in manifests.items():
        leaked = set(E.PRIVATE_KEYS) & set(manifest.get("artefact_key", {}))
        if leaked:
            out.append(f"{path}: artefact_key carries {sorted(leaked)}")
        if _PATH.search(json.dumps(manifest)):
            out.append(f"{path}: an absolute path")
    if _PATH.search(json.dumps(index)):
        out.append("index.json: an absolute path")
    register = {p["id"]: p.get("caveat") for p in polling.load(ROOT / "polls.json")}
    want = {p["id"]: p["caveat"] for p in E.reader_polls(
        [{k: v for k, v in p.items() if k != "caveat"} for p in index["polls"]], "joburg")}
    for poll in index["polls"]:
        if poll.get("caveat") != want[poll["id"]]:
            out.append(f"index.json: poll {poll['id']} does not carry its reader caveat")
        if register.get(poll["id"]) and poll.get("caveat") == register[poll["id"]]:
            out.append(f"index.json: poll {poll['id']} carries the register's note")
    return out


def test_nothing_private_is_served():
    st = _served()
    manifests = {p: c["manifest"] for p, c in st["cells"].items()}
    # it looked: every cell, and every poll the page offers
    assert len(manifests) == len(st["index"]["cells"]) >= 1
    assert st["index"]["polls"], "index.json offers no poll, so no caveat was checked"
    assert _private_problems(manifests, st["index"]) == []


def test_a_served_path_or_working_note_is_caught_then_quiet():
    import polling
    st = _served()
    manifests = {p: json.loads(json.dumps(c["manifest"])) for p, c in st["cells"].items()}
    index = json.loads(json.dumps(st["index"]))
    first = next(iter(manifests))
    manifests[first]["artefact_key"]["code_dir"] = "/Users/someone/src"
    found = _private_problems(manifests, index)
    assert any("code_dir" in f for f in found) and any("absolute path" in f for f in found), found
    del manifests[first]["artefact_key"]["code_dir"]
    assert _private_problems(manifests, index) == []
    # a path in the middle of a string is caught too, and a URL is not
    index["note"] = "built at /Users/someone/src from C:\\work"
    assert _private_problems(manifests, index) == ["index.json: an absolute path"]
    index["note"] = "see https://example.org/var/tmp/Users/x"
    assert _private_problems(manifests, index) == []
    index["note"] = st["index"]["note"]
    register = {p["id"]: p for p in polling.load(ROOT / "polls.json")}
    poll = next(p for p in index["polls"] if register[p["id"]].get("caveat"))
    kept = poll["caveat"]
    poll["caveat"] = register[poll["id"]]["caveat"]
    assert len(_private_problems(manifests, index)) == 2
    poll["caveat"] = kept
    assert _private_problems(manifests, index) == []


# -- 7: the checks see --------------------------------------------------------

def test_a_flipped_byte_in_a_served_seat_column_is_caught_then_quiet():
    st = _served()
    manifest = st["manifest"]
    block = next(b for b in manifest["blocks"] if b["name"] == "seats/deduct")
    with PUBLISHED["deduct"].open(encoding="utf-8", newline="") as handle:
        first = next(csv.reader(handle))[3]    # a party the file publishes
    item = np.dtype(block["dtype"]).itemsize
    at = (int(block["offset"])
          + (block["columns"].index(first) * manifest["draws"] + 7) * item)
    bad = bytearray(st["blob"])
    bad[at] ^= 0x01
    arrays = R.unpack(bytes(bad), manifest)
    assert _unmatched_seat_files(arrays, manifest) == [PUBLISHED["deduct"].name]
    bad[at] ^= 0x01
    assert bytes(bad) == st["blob"]
    assert _unmatched_seat_files(R.unpack(bytes(bad), manifest), manifest) == []


def test_a_changed_ward_or_summary_figure_is_caught_then_quiet():
    st = _served()
    arrays, manifest = dict(st["arrays"]), st["manifest"]
    good = arrays["ward_winner"]
    bad = good.copy()
    bad[:40, 3] = (bad[:40, 3] + 1) % len(manifest["ward_parties"])
    arrays["ward_winner"] = bad
    assert _ward_prob_differences(arrays, manifest) != []
    arrays["ward_winner"] = good
    assert _ward_prob_differences(arrays, manifest) == []

    summary = json.loads(SUMMARY.read_text())
    party = next(iter(summary["parties"]))
    summary["parties"][party]["median"] += 1
    assert _summary_differences(arrays, manifest, summary) == [f"{party}.median"]
    summary["parties"][party]["median"] -= 1
    assert _summary_differences(arrays, manifest, summary) == []


def test_a_wrong_or_missing_run_id_is_caught_then_quiet():
    st = _served()
    newest = _ledger_newest()
    good = json.loads(json.dumps(st["manifest"]))
    good["published_run"] = {"model_run_id": newest["model_run_id"]}
    good["artefact_key"]["model_sha256"] = "0" * 64
    good["artefact_key"]["inputs"] = newest["pool_artefact_keys"]
    assert _run_problems({"c": good}, newest) == []
    wrong = json.loads(json.dumps(good))
    wrong["published_run"]["model_run_id"] = "r-not-the-published-run"
    assert len(_run_problems({"c": wrong}, newest)) == 1
    # another model run is caught; the same run published again (a new commit
    # after it) is not
    head = _model_run(newest["model_run_id"])
    assert head, newest["model_run_id"]
    other_run = json.loads(json.dumps(good))
    other_run["published_run"]["model_run_id"] = "r-" + ("0" if head[2] != "0" else "1") * 12 + "-abcdef12"
    assert len(_run_problems({"c": other_run}, newest)) == 1
    republished = json.loads(json.dumps(good))
    republished["published_run"]["model_run_id"] = head + "-0badc0de-dirty"
    assert _run_problems({"c": republished}, newest) == []
    missing = json.loads(json.dumps(good))
    del missing["published_run"]
    assert "exported before S6" in _run_problems({"c": missing}, newest)[0]
    stale = json.loads(json.dumps(good))
    stale["artefact_key"]["inputs"] = {}
    assert len(_run_problems({"c": stale}, newest)) == 1
    other = json.loads(json.dumps(good))
    other["artefact_key"]["model_sha256"] = "1" * 64
    assert _run_problems({"c": good, "d": other}, newest) == [
        "the cells were drawn by 2 different models"]
    assert _run_problems({"c": good, "d": good}, newest) == []


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))


# -- the page's fingerprint of the draws is the served draws' -----------------

def _fingerprint_problem(forecast: dict, manifest: bytes, blob: bytes) -> str | None:
    """Why /your-forecast/'s forecast.json does not name the served draws, or
    None. The seat Worker answers a card only when the caller's draws_sha256
    is the draws it fetched (worker-api/seats-py/src/entry.py), so a mismatch
    turns every link preview into the generic image (2026-10-07: the manifests
    were re-exported and the page was not rebuilt)."""
    import hashlib
    have = hashlib.sha256(manifest + blob).hexdigest()
    want = forecast.get("draws_sha256")
    if want != have:
        return (f"site/your-forecast/forecast.json draws_sha256 {want!r} is not "
                f"the served draws' {have!r}: rebuild the site (build_site.py) "
                f"after any change to site/draws/")
    return None


def test_the_page_names_the_served_draws_and_a_stale_name_is_caught():
    forecast = json.loads((ROOT / "site" / "your-forecast" / "forecast.json").read_text(encoding="utf-8"))
    manifest = (ROOT / "site" / "draws" / "manifest.json").read_bytes()
    blob = (ROOT / "site" / "draws" / "base.bin").read_bytes()
    assert manifest and blob, "the served draws are empty"
    assert _fingerprint_problem(forecast, manifest, blob) is None, _fingerprint_problem(forecast, manifest, blob)
    # it can see: a manifest changed by one byte is caught, and reverted is quiet
    assert _fingerprint_problem(forecast, manifest + b" ", blob)
    assert _fingerprint_problem(forecast, manifest, blob) is None

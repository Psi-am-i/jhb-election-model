"""Export the published run's draws for the interactive: one binary file and its manifest.

    .venv/bin/python src/export_draws.py --out /tmp/draws
    .venv/bin/python src/export_draws.py --laws deduct --out /tmp/draws

Build step S2 of ``audits/2026-09-28-interactive-architecture/PLAN.md``
(INTEGRATION.md §3a). The page re-weights these draws (``src/reweight.py``)
instead of re-running the model, so the file must hold, per draw, everything a
control weights by and everything a figure is computed from:

* **seats** for every seat-winning party plus ``OTHER``, under each of the four
  seat laws (``deduct``, the statute, and the three counterfactuals of
  ``src/overhang_regimes.py``), with each law's majority threshold and council
  size;
* **ward winners**, one code per ward;
* **ward votes** and **list votes**, each party's whole votes on the ward
  ballot and on the list (PR) ballot, exactly the integers ``run_model``'s seat
  law read in that draw (``ModelRun.ward_vote_draws`` and ``pr_vote_draws``),
  with the run's WHOLE universe as columns: every party under its own code,
  none summed into ``OTHER`` and none dropped. Rule A
  (``src/prediction.py``) reduces them to our prediction; a list share is
  ``reweight.list_shares`` of the list block;
* **pool turnouts**, ``ModelRun.pool_turnout_draws`` (MACHINERY.md, "Per-draw
  pool turnouts").

"Seat-winning" is a rule, the same for every party: a party that takes at least
one seat in at least one draw under at least one law gets its own column; every
other party is summed into ``OTHER``. ``OTHER`` seats are therefore zero by
construction and are written anyway, so the page can check that each draw's
columns sum to its council.

⛔ IT CALLS ``run_model`` AND NEVER ``montecarlo.main``
======================================================

``main`` writes the published forecast's files into ``data/processed``, and a
bare ``python src/montecarlo.py`` or ``overhang_regimes.py`` run overwrites the
site's inputs (``overhang_regimes.py``'s docstring is the incident). This module
writes only to ``--out`` and refuses an ``--out`` inside ``data/``. Each seat
law runs in its own process under ``montecarlo.HASH_SEED``, as ``main`` does,
and the export refuses to run without it: a random hash seed reorders float
summations at machine epsilon (MODEL-LOG §1.104). An exact tie at the last
seat no longer depends on it: since 2026-10-09 the seeded lot draws it under
the run's identity (``seats.lot_order``, JUDGEMENT-CALLS §Q6), where until then
it fell to the dict's order and so to the hash seed.

What the export asserts before it writes
========================================

* **The draws are shared across seat laws.** Pool turnouts, both vote blocks
  and ward winners are stored ONCE, which is only honest if the four runs drew them
  identically — the seat law acts after every random draw. The export compares
  them array for array and refuses if they differ, because a weight computed on
  one law's draws would then not carry to another by draw index (PLAN.md §7).
* **The inputs did not move under it.** The pool specs' artefact keys are read
  before the first run and after the last; a re-emit in between
  (``CLAUDE.md`` §3) is a refusal, not a footnote.
* **Every draw's seats sum to its council**, per law.
* **Both ballots are in the file and nothing refuses them**
  (:func:`ballot_faults`): both vote blocks present, integer, on the same
  columns, and no ``combined_share`` refusal beside them.

The manifest
============

``manifest.json`` carries the block table :func:`reweight.unpack` needs (names,
dtypes, offsets, column names), the party codes of the ward block, and an
``artefact_key`` with the fields ``declares.py`` requires of a run: ``git``,
``draws``, ``seed``, ``env`` (``freeze.resolved_switches``), ``inputs`` (the
pool specs' keys), ``time``, plus ``code_sha256`` over every ``.py`` file in the
source directory the model was actually imported from — the commit alone does
not describe a tree with uncommitted modules in it — and ``config``, the
scenario levers each law ran with.

Four fields answer S6 (``audits/2026-09-30-interactive-s6/SPEC-v2.md``, lane E):

* ``artefact_key.model_sha256`` and ``artefact_key.model_modules`` — WHICH MODEL
  drew these numbers. ``code_sha256`` covers this file too, so an edit to the
  exporter changed it and no cell could ever match a published run (review
  B3). The model's import closure is determined DYNAMICALLY: in each worker,
  after ``run_model`` returns, every entry of ``sys.modules`` whose file is a
  ``.py`` in the source directory, minus ``export_draws.py`` itself (matched by
  file path, so the spawn child's ``__mp_main__`` alias is caught), unioned
  over the laws — a non-statute rule may import what ``deduct`` does not. The
  worker imports nothing of this module's before the model (``reweight`` is
  imported lazily in :func:`build`), so everything in the closure was imported
  by the model's set-up or by ``run_model``. ``model_modules`` lists the file
  names, so the hash can be recomputed with :func:`files_sha256`.
* ``published_run`` — the ledger's latest run (``publications/<city>/
  ledger.jsonl`` via :func:`publication.history`, the row with the newest
  ``published_at``): its ``model_run_id``, ``published_at`` and
  ``pool_artefact_keys``, and ``inputs_match_ledger``, whether the pool specs
  this export ran on are the ones that run recorded. RECORDED, NOT ENFORCED
  HERE: an export before a publication is legitimate; the gate is
  ``tests/test_served_draws.py``, which checks the served cells against the
  ledger.
* ``centres`` — each party's DETERMINISTIC blended centre, the level the draws
  scatter around, so a lever's effect can be shown without draw noise (review
  F3). ``ModelRun`` does not carry it, so it is read from the run's own trace
  (``run_model(..., run_dir=...)``, stage ``30_centres``, ``after_shrink``),
  which changes no drawn number
  (``test_chain.py::test_passing_a_run_directory_changes_no_drawn_number``).
  Keyed like the seat blocks: the file's parties, then ``OTHER`` summing the
  rest. They are ``blended_centres``' citywide LEVELS, not shares: nothing
  normalises them to one before the draw does, so their sum is not one and a
  page must compare a cell's centre with another cell's centre, never with a
  drawn share. The centres must agree across laws (the law acts after them) or the
  export refuses. Stage 30 is the drawn centre only while metro polls are not
  blended in afterwards (``poll_paths != "all"``); under ``"all"`` the field
  is a stated refusal, not a number.
* ``vote_blocks`` — what the two vote blocks are (:data:`VOTE_BLOCKS`). The
  ``combined_share`` refusal this field replaces was lifted on 2026-10-08:
  ``run_model`` now records each draw's whole votes per ballot, so the
  combined tally is ``seats.eligible_parties(ward_vote, list_vote)`` per draw,
  computed by whoever needs it from the file and never stored here
  (MODEL-LOG §1.291).

What the manifest and the index do NOT carry
============================================

Both are served with the page (``site/draws/``), so neither may carry a path
on the machine that exported them or a note written for the model's authors
(deploy review 2026-09-30, F2/F3):

* ``artefact_key`` names the source directory by nothing but its modules'
  file names (``model_modules``); ``code_dir``, the absolute path it once
  carried, is gone. :data:`PRIVATE_KEYS` lists it, and ``--index`` removes it
  from a manifest written before the change (:func:`public_manifest`), which
  rewrites the JSON only, never ``base.bin``.
* Each poll in ``index.json`` carries its READER caveat, from
  ``content/<city>/poll-caveats.toml``, in place of the register's own
  ``caveat`` (:func:`reader_polls`); a poll with no reader caveat stops the
  index.

Storage choices, stated because they lose information: seats, thresholds and
councils are unsigned integers of the smallest width that holds the largest
value (exact); ward winners are one byte per ward (exact); ward and list votes
are unsigned integers of the narrowest width (exact); pool turnouts are
float64, exactly ``ModelRun.pool_turnout_draws``. No stepped (rounded) block
remains: the PR share block, stored to a step of 1e-5, was dropped for the
list votes it is derived from (owner, 2026-10-08), which also keeps the file
under the size budget. ``tests/test_export_draws.py`` checks the seat columns
byte for byte against the published CSVs.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

# `reweight` is imported inside `build`, not here: the spawn workers import this
# module before the model, and `model_sha256` is the closure of what the model
# imported. A module-level import would put the page's re-weighter into the
# model's identity (or, filtered out by name, hide it the day the model starts
# importing it).

#: The trace stage the deterministic centres are read from, and its key.
CENTRES_STAGE = ("30_centres", "after_shrink")

#: What the manifest says the two vote blocks are (module docstring).
VOTE_BLOCKS = {
    "unit": "whole votes",
    "columns": "the run's universe; no party summed or dropped",
    "source": ("ModelRun.ward_vote_draws and pr_vote_draws: the integers "
               "run_model's seat law read"),
    "combined": "seats.eligible_parties(ward_vote, list_vote) per draw; not stored",
}

#: The four seat laws, statute first. `deduct` is `montecarlo.DEFAULTS`'s
#: `overhang_rule`; the other three are `overhang_regimes.RULES`.
LAWS = ("deduct", "expand", "level", "cap")


def files_sha256(paths) -> str:
    """sha256 over ``paths``, by file name and content, in name order.

    One recipe for both hashes in the manifest: ``code_sha256`` over every
    ``.py`` file in the source directory, ``model_sha256`` over the model's
    import closure (``artefact_key.model_modules``).
    """
    h = hashlib.sha256()
    for path in sorted((Path(p) for p in paths), key=lambda q: q.name):
        h.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def _code_sha256(src: Path) -> str:
    """sha256 over every ``.py`` file in ``src``, by name and content."""
    return files_sha256(src.glob("*.py"))


def model_closure(src: Path) -> list[str]:
    """The ``.py`` files in ``src`` this process has imported, minus this one.

    Called in a worker after ``run_model`` returns, so it is the model's import
    closure (see the module docstring). Matched by resolved file path: the
    spawn child imports this file as ``__mp_main__`` when it ran as a script.
    """
    src = src.resolve()
    me = Path(__file__).resolve()
    names = set()
    for module in list(sys.modules.values()):
        f = getattr(module, "__file__", None)
        if not f:
            continue
        path = Path(f).resolve()
        if path.parent == src and path.suffix == ".py" and path != me:
            names.add(path.name)
    return sorted(names)


def _bye_weight_from_trace(run_dir: Path) -> dict[str, dict]:
    """Stage ``30_centres``' ``bye_weight``: the weight ``blended_centres``
    gave each party with by-election evidence, and its class or
    ``"override"`` (BRIEF item 19). Taken from the run, so the report cannot
    differ from what the model applied."""
    trace = json.loads((run_dir / f"{CENTRES_STAGE[0]}.json").read_text())
    return {p: {"weight": float(v["weight"]), "class": str(v["class"])}
            for p, v in (trace.get("bye_weight") or {}).items()}


def _centres_from_trace(run_dir: Path) -> dict[str, float]:
    """Stage ``30_centres`` of a trace: each party's deterministic centre."""
    stage, key = CENTRES_STAGE
    trace = json.loads((run_dir / f"{stage}.json").read_text())
    if "__unserialisable__" in trace:
        raise SystemExit(f"the trace could not record {stage}: "
                         f"{trace['__unserialisable__']}")
    return {p: float(v) for p, v in trace[key].items()}


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), capture_output=True, text=True,
                              check=True, cwd=Path.cwd()).stdout.strip()
    except Exception:                                    # noqa: BLE001
        return "<unavailable>"


def _run_law(rule: str, city_slug: str, year: str, draws: int, seed: int,
             overrides: tuple[str, ...] = ()) -> dict:
    """One full run under one seat law. Returns plain arrays, in a worker process.

    The same order of set-up as ``montecarlo.main``: city, target, then
    ``apply_city`` (council size is per year), then the scenario.
    """
    import cityconfig
    import montecarlo as M

    if os.environ.get("PYTHONHASHSEED") != str(M.HASH_SEED):
        raise SystemExit(f"PYTHONHASHSEED is {os.environ.get('PYTHONHASHSEED')!r}, "
                         f"not montecarlo.HASH_SEED {M.HASH_SEED!r}: a tied last "
                         f"seat would be a coin flip. Run this module as a "
                         f"script, which re-executes under the fixed seed.")
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    # `overrides` are the lever-grid cells (PLAN.md S3; owner 2026-09-29:
    # `w_bye` only). A cell with any override is a counterfactual, like a
    # non-statute seat law: it never stands for the published run.
    extra = [] if rule == "deduct" else [f"overhang_rule={rule}"]
    args = argparse.Namespace(
        config=None, draws=draws, seed=seed,
        set=(list(overrides) + extra) or None,
        counterfactual=rule != "deduct" or bool(overrides))
    scenario = M.load_scenario(args)
    config = {k: scenario[k] for k in sorted(M.DEFAULTS) if k in scenario}
    config = json.loads(json.dumps(config, default=str))
    # The trace is the only route the deterministic centres have out of
    # `run_model` (`ModelRun` does not carry them); it changes no drawn number.
    with tempfile.TemporaryDirectory(prefix="export_draws_trace_") as trace_dir:
        run = M.run_model(target, scenario, verbose=False, run_dir=trace_dir)
        centres = _centres_from_trace(Path(trace_dir))
        bye_weight = _bye_weight_from_trace(Path(trace_dir))
    src = Path(M.__file__).resolve().parent
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws],
                     dtype=np.int64)
    return {
        "rule": rule,
        "config": config,
        "universe": universe,
        "wards": list(run.wards),
        "seats": seats,
        "thresholds": np.asarray(run.thresholds, dtype=np.int64),
        "council_sizes": np.asarray(run.council_sizes, dtype=np.int64),
        "ward_winners": np.asarray(run.ward_winner_draws),
        "ward_votes": np.asarray(run.ward_vote_draws),
        "list_votes": np.asarray(run.pr_vote_draws),
        "pool_turnouts": np.asarray(run.pool_turnout_draws, dtype=float),
        "pool_names": list(run.pool_turnout_names),
        "centres": centres,
        "bye_weight": bye_weight,
        "poll_paths": scenario.get("poll_paths", M.DEFAULTS["poll_paths"]),
        "model_file": str(Path(M.__file__).resolve()),
        "model_modules": model_closure(src),
    }


def _uint(array: np.ndarray) -> np.dtype:
    """The narrowest unsigned integer type that holds every value exactly."""
    if array.size and array.min() < 0:
        raise ValueError("a count is negative")
    top = int(array.max()) if array.size else 0
    for dt in (np.uint8, np.uint16, np.uint32):
        if top <= np.iinfo(dt).max:
            return np.dtype(dt)
    raise ValueError(f"{top} does not fit an unsigned 32-bit integer")


def shared_draw_differences(runs: dict[str, dict]) -> list[str]:
    """Which per-draw inputs differ between laws. Empty means they may be stored once."""
    first = runs[next(iter(runs))]
    differ = []
    for rule, run in runs.items():
        for key in ("universe", "wards", "pool_names"):
            if run[key] != first[key]:
                differ.append(f"{rule}:{key}")
        for key in ("ward_winners", "ward_votes", "list_votes", "pool_turnouts"):
            a, b = run[key], first[key]
            if a.shape != b.shape or a.dtype != b.dtype or not np.array_equal(a, b):
                differ.append(f"{rule}:{key}")
        # the deterministic centres come before any draw, so before the law
        if run.get("centres") != first.get("centres"):
            differ.append(f"{rule}:centres")
    return differ


def centres_block(runs: dict[str, dict], parties: list[str]) -> dict:
    """The manifest's ``centres``: stage 30's centres on the file's columns.

    Keyed ``parties + ["OTHER"]``, OTHER summing every centre not in
    ``parties``. A seat-winning party with no centre is listed under
    ``absent`` rather than given a zero. Under ``poll_paths == "all"`` the
    metro poll blend moves the centres after stage 30, so the block is a
    refusal.
    """
    first = runs[next(iter(runs))]
    stage, key = CENTRES_STAGE
    source = f"run_model trace, stage {stage}, {key}"
    if first.get("poll_paths") == "all":
        return {"refused": True, "source": source,
                "reason": "poll_paths is 'all': metro polls move the centres "
                          "after stage 30, so it is not the drawn centre"}
    centres = first["centres"]
    values = {p: centres[p] for p in parties if p in centres}
    values["OTHER"] = float(sum(v for p, v in centres.items()
                                if p not in parties))
    return {"source": source, "values": values,
            "absent": [p for p in parties if p not in centres]}


def build(runs: dict[str, dict]) -> tuple[bytes, dict]:
    """The draw file and the manifest's data half, from one run per law.

    Refuses if the laws' shared draws differ, or if any draw's seats do not
    sum to its council.
    """
    import reweight

    differ = shared_draw_differences(runs)
    if differ:
        raise SystemExit(f"the seat laws did not share their draws ({differ}); "
                         f"weights cannot cross laws by draw index")
    first = runs[next(iter(runs))]
    universe = first["universe"]
    draws = first["seats"].shape[0]

    won = np.zeros(len(universe), dtype=bool)
    for run in runs.values():
        won |= run["seats"].max(axis=0) > 0
    parties = [p for p, w in zip(universe, won) if w]
    keep = np.flatnonzero(won)
    rest = np.flatnonzero(~won)
    columns = parties + ["OTHER"]

    blocks = []
    for rule, run in runs.items():
        seats = np.column_stack([run["seats"][:, keep],
                                 run["seats"][:, rest].sum(axis=1)])
        if not np.array_equal(seats.sum(axis=1), run["council_sizes"]):
            raise SystemExit(f"{rule}: a draw's seats do not sum to its council")
        blocks.append((f"seats/{rule}", seats.astype(_uint(seats)), columns))
        council = np.column_stack([run["thresholds"], run["council_sizes"]])
        blocks.append((f"council/{rule}", council.astype(_uint(council)),
                       ["threshold", "council_size"]))

    codes = sorted(set(np.unique(first["ward_winners"]).tolist()))
    ward_parties = [universe[j] for j in codes]
    lookup = np.full(len(universe), -1, dtype=np.int64)
    lookup[codes] = np.arange(len(codes))
    winners = lookup[first["ward_winners"]]
    blocks.append(("ward_winner", winners.astype(_uint(winners)), first["wards"]))

    # both ballots on the run's whole universe: no party summed, none dropped
    wv, lv = np.asarray(first["ward_votes"]), np.asarray(first["list_votes"])
    blocks.append(("ward_vote", wv.astype(_uint(wv)), universe))
    blocks.append(("list_vote", lv.astype(_uint(lv)), universe))
    blocks.append(("pool_turnout", first["pool_turnouts"], first["pool_names"]))

    blob, table = reweight.pack(blocks)
    data = {
        "format": reweight.FORMAT,
        "draws": int(draws),
        "laws": list(runs),
        "parties": parties,
        "ward_parties": ward_parties,
        "blocks": table,
        "centres": centres_block(runs, parties),
        "bye_weight": first.get("bye_weight") or {},
        "vote_blocks": VOTE_BLOCKS,
    }
    faults = ballot_faults(data)
    if faults:
        raise SystemExit("the draw file's ballots are not sound: " + "; ".join(faults))
    return blob, data


def ballot_faults(manifest: dict) -> list[str]:
    """Everything wrong with a manifest's two ballots, as sentences. Empty means sound.

    Both ``ward_vote`` and ``list_vote`` must be present, stored as integers,
    on identical columns; and the ``combined_share`` refusal the blocks lifted
    must not sit beside them (lifted and refused at once).
    """
    blocks = {b["name"]: b for b in manifest.get("blocks", [])}
    out = []
    present = [n for n in ("ward_vote", "list_vote") if n in blocks]
    for name in ("ward_vote", "list_vote"):
        if name not in blocks:
            out.append(f"the {name} block is missing")
        elif np.dtype(blocks[name]["dtype"]).kind not in "iu" or "step" in blocks[name]:
            out.append(f"the {name} block is not stored as whole votes "
                       f"({blocks[name]['dtype']})")
    if len(present) == 2 and blocks["ward_vote"]["columns"] != blocks["list_vote"]["columns"]:
        out.append("the ward_vote and list_vote blocks have different columns")
    if "combined_share" in manifest:
        out.append("the manifest carries a combined_share refusal beside the "
                   "vote blocks that lifted it" if present else
                   "the manifest carries a combined_share refusal and no vote blocks")
    return out


#: ``artefact_key`` fields that describe the exporting machine, not the run.
#: Never written; :func:`public_manifest` removes them from an older manifest.
PRIVATE_KEYS = ("code_dir",)


def public_manifest(manifest: dict) -> dict:
    """``manifest`` without :data:`PRIVATE_KEYS` in its ``artefact_key``.

    Everything else, the hashes and the block table included, is kept as it
    is, so the draw file it describes is unchanged and still unpacks.
    """
    key = {k: v for k, v in manifest["artefact_key"].items()
           if k not in PRIVATE_KEYS}
    return {**manifest, "artefact_key": key}


#: Where each city's reader-facing poll caveats are (one file per city).
POLL_CAVEATS = Path(__file__).resolve().parents[1] / "content" / "{city}" / "poll-caveats.toml"


def reader_polls(polls: list[dict], city_slug: str,
                 caveats_path: Path | None = None) -> list[dict]:
    """The page's polls with the register's ``caveat`` replaced by the reader's.

    The register's ``caveat`` (``polls.json``) is a working note and does not
    ship. Every other field is kept: ``reweight.poll_trust_sd`` prices a poll
    from them. Refuses, naming them, when a poll has no reader caveat.
    """
    import tomllib

    path = caveats_path or Path(str(POLL_CAVEATS).format(city=city_slug))
    table = (tomllib.loads(path.read_text(encoding="utf-8")).get("caveats", {})
             if path.is_file() else {})
    missing = [p["id"] for p in polls if not str(table.get(p["id"], "")).strip()]
    if missing:
        raise SystemExit(f"no reader caveat in {path} for poll(s) {missing}: the "
                         f"register's own caveat is a working note and does not "
                         f"ship. Add one per poll, in the reader's language.")
    return [{**{k: v for k, v in p.items() if k != "caveat"},
             "caveat": table[p["id"]]} for p in polls]


def published_run(city_slug: str, inputs: dict, root: Path | None = None) -> dict:
    """The ledger's latest run, and whether ``inputs`` are the specs it recorded.

    Read through :func:`publication.history`; "latest" is the row with the
    newest ``published_at``. Recorded, not enforced (module docstring).
    """
    import publication

    root = (Path(__file__).resolve().parents[1] / "publications"
            if root is None else root)
    rows = publication.history(city_slug, root=root)
    if not rows:
        return {"model_run_id": None,
                "reason": f"no ledger rows under {root / city_slug}"}
    row = max(rows, key=lambda r: r.published_at)
    keys = (row.provenance or {}).get("pool_artefact_keys")
    return {"model_run_id": row.model_run_id,
            "published_at": row.published_at,
            "run_at": row.run_at,
            "pool_artefact_keys": keys,
            "inputs_match_ledger": keys == inputs,
            "source": f"publications/{city_slug}/ledger.jsonl, newest "
                      f"published_at"}


def export(city_slug: str, year: str, draws: int, seed: int, out: Path,
           laws: tuple[str, ...] | None = None, jobs: int | None = None,
           overrides: tuple[str, ...] = ()) -> dict:
    """Run each law, build the file, write ``base.bin`` and ``manifest.json`` to ``out``.

    ``laws`` defaults to :data:`LAWS`, resolved here at call time rather than
    bound as a default argument, so a caller who rebinds ``LAWS`` reaches the
    call (``tests/test_ipf_feasibility.py``, CLASS 13).
    """
    import cityconfig
    import freeze

    laws = LAWS if laws is None else tuple(laws)
    out = out.resolve()
    data_root = (Path.cwd() / "data").resolve()
    if out == data_root or data_root in out.parents:
        raise SystemExit(f"--out {out} is inside {data_root}: the export never "
                         f"writes into the published tree")
    unknown = [law for law in laws if law not in LAWS]
    if unknown:
        raise SystemExit(f"unknown seat law(s) {unknown}; the four are {LAWS}")

    city = cityconfig.use(city_slug)
    keys_before = freeze.pool_artefact_keys(city)
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=jobs or len(laws), mp_context=ctx) as pool:
        futures = {law: pool.submit(_run_law, law, city_slug, year, draws, seed,
                                    tuple(overrides))
                   for law in laws}
        runs = {law: futures[law].result() for law in laws}
    keys_after = freeze.pool_artefact_keys(city)
    if keys_after != keys_before:
        raise SystemExit("the pool specs changed while the export ran (a re-emit "
                         "landed); nothing was written. Re-run on a settled tree.")

    blob, manifest = build(runs)
    src = Path(runs[laws[0]]["model_file"]).parent
    modules = sorted(set().union(*(runs[law]["model_modules"] for law in laws)))
    manifest["published_run"] = published_run(city_slug, keys_before)
    manifest["artefact_key"] = {
        "git": {"commit": _git("rev-parse", "HEAD"),
                "dirty": bool(_git("status", "--porcelain", "--", "src"))},
        "code_sha256": _code_sha256(src),
        "model_sha256": files_sha256(src / m for m in modules),
        "model_modules": modules,
        "city": city_slug,
        "target": year,
        "draws": int(draws),
        "seed": int(seed),
        "env": freeze.resolved_switches(),
        "inputs": keys_before,
        "config": {law: runs[law]["config"] for law in laws},
        "overrides": list(overrides),
        "time": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "base.bin").write_bytes(blob)
    (out / "manifest.json").write_text(json.dumps(public_manifest(manifest), indent=1),
                                       encoding="utf-8")
    return {"out": str(out), "bytes": len(blob),
            "gzip_bytes": len(gzip.compress(blob, compresslevel=9)),
            "manifest_bytes": (out / "manifest.json").stat().st_size}


def write_index(root: Path) -> dict:
    """``root/index.json``: every exported cell under ``root``, read from the
    cells' own manifests, so the page loads one file to learn the grid.

    A cell's manifest that still carries a :data:`PRIVATE_KEYS` field is
    rewritten without it first (:func:`public_manifest`); its ``base.bin`` is
    not opened. The polls carry their reader caveats (:func:`reader_polls`).

    The cells are listed from least to most by-election weight
    (:func:`order_bye_cells`), each with its ``bye_weight_range`` (the least
    and greatest weight its run gave any party, :func:`bye_weight_range`) and
    its ``bye_order``. ``w_bye`` stays the cell's override, ``None`` for the
    published cell, whose weight is per class (BRIEF item 19); the page and
    ``build_play`` order and compare by the range, never by ``w_bye``.

    ⚠️ THE CELLS ARE NOT PAIRED (measured 2026-09-30, MODEL-LOG §1.283): a
    `w_bye` override shifts the random stream after the first few draws, so
    draw i of one cell is not draw i of another. A weight computed on one
    cell's draws must never be applied to another's; the index says so.
    """
    cells = []
    published_bye_weight: dict = {}
    for manifest in sorted(root.rglob("manifest.json")):
        whole = json.loads(manifest.read_text())
        if manifest.parent == root:
            published_bye_weight = whole.get("bye_weight") or {}
        if any(k in whole["artefact_key"] for k in PRIVATE_KEYS):
            # a manifest written before PRIVATE_KEYS: the JSON is rewritten,
            # base.bin is not touched
            whole = public_manifest(whole)
            manifest.write_text(json.dumps(whole, indent=1), encoding="utf-8")
        cells.append(index_cell(whole,
                                manifest.parent.relative_to(root).as_posix() or "."))
    if len({c["code_sha256"] for c in cells}) > 1:
        raise SystemExit("the cells were exported by different code; re-export "
                         "them together so the page compares like with like")
    # The page and /play/ show the cells in this order (one definition:
    # `order_bye_cells`), each carrying its position.
    cells = order_bye_cells(cells)
    for i, c in enumerate(cells):
        c["bye_order"] = i
    # The poll set the page offers, selected here at build time by the one
    # definition (`reweight.page_polls`), so the browser need not import the
    # model to apply the screening rules. Records carry `asof`.
    import cityconfig
    import reweight
    first = json.loads(sorted(root.rglob("manifest.json"))[0].read_text())["artefact_key"]
    cityconfig.use(first["city"])
    polls = reader_polls(reweight.page_polls(cityconfig.use_target(first["target"])),
                         first["city"])
    # The by-election evidence the page shows beside the w_bye control
    # (DESIGN-decided §11): the model's own input file, with whether each
    # party reaches `montecarlo.BYE_MIN_WEIGHT` (the same rule for every
    # party). `UNKNOWN` is not a party and is left out (review F20).
    import montecarlo
    bye_path = Path(montecarlo.__file__).resolve().parents[1] / "data/processed/byelection_party_deltas.csv"
    byelection = byelection_index(bye_path, published_bye_weight)
    index = {"cells": cells, "paired": False, "polls": polls,
             "byelection": byelection,
             "byelection_min_weight": montecarlo.BYE_MIN_WEIGHT,
             "note": "cells are independent samples; weights do not carry "
                     "across cells by draw index"}
    (root / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    return index


def index_cell(manifest: dict, path: str) -> dict:
    """One cell's row in ``index.json``, from its manifest."""
    key = manifest["artefact_key"]
    w_bye = key["config"]["deduct"].get("w_bye")
    return {
        "path": path,
        "overrides": key.get("overrides", []),
        "w_bye": w_bye,
        "bye_weight_range": bye_weight_range(manifest.get("bye_weight"), w_bye),
        "code_sha256": key["code_sha256"],
        # absent from a cell exported before S6; test_served_draws says so
        "model_sha256": key.get("model_sha256"),
        "published_run": (manifest.get("published_run") or {}).get(
            "model_run_id"),
        "draws": key["draws"],
        "seed": key["seed"],
    }


def bye_weight_range(bye_weight: dict | None, w_bye) -> list[float]:
    """A cell's effective by-election weight: ``[least, greatest]`` over the
    weights its run gave each party (the manifest's ``bye_weight``, BRIEF item
    19).

    The published cell has ``w_bye = None`` and per-party class weights, which
    differ between classes when the measured weights do, so one number cannot
    stand for it; the range can, and it is a single point for an override cell
    (every party at the override). A manifest with no ``bye_weight`` was
    exported before item 19, when ``w_bye`` was the one weight for every party,
    and its range is that point. A derived cell whose run weighed no party
    gave by-elections no weight: ``[0, 0]``.
    """
    weights = [float(v["weight"]) for v in (bye_weight or {}).values()]
    if weights:
        return [min(weights), max(weights)]
    if w_bye is not None:
        return [float(w_bye), float(w_bye)]
    return [0.0, 0.0]


def order_bye_cells(cells: list[dict]) -> list[dict]:
    """The by-election cells from least to most weight, the one order the page
    and ``build_play`` use.

    Sorted by :func:`bye_weight_range` (least weight, then greatest), never by
    ``w_bye``, which is ``None`` for the published cell. A cell with no
    ``bye_weight_range`` (an index written before the field) is read from its
    ``w_bye``. On a tie the published cell (``"."``) sits between the cells
    either side of it: an override of 0 before it, any other override after,
    so with every class weight at 0 the "not at all" cell still comes first and
    the published one stays in the middle.
    """
    def key(c: dict):
        lo, hi = c.get("bye_weight_range") or bye_weight_range(None, c["w_bye"])
        tie = 1 if c["path"] == "." else (0 if c["w_bye"] == 0 else 2)
        return (lo, hi, tie, c["path"])
    return sorted(cells, key=key)


def byelection_index(bye_path: Path, bye_weight: dict) -> list[dict]:
    """The by-election rows the page shows beside the ``w_bye`` control.

    One per party in the model's input file (``UNKNOWN`` is not a party,
    review F20): its contests, weight sum and weighted delta, whether it
    reaches ``montecarlo.BYE_MIN_WEIGHT`` (the same rule for every party), and
    beside that its ``class_weight`` and ``size_class`` (BRIEF item 19): the
    weight the published run's ``blended_centres`` gave it, read from that
    run's trace via the cell manifest (``bye_weight``), ``None`` for a party
    the run did not weigh.
    """
    import csv
    import montecarlo
    rows = []
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row["party"] == "UNKNOWN":
                    continue
                given = bye_weight.get(row["party"]) or {}
                rows.append({
                    "party": row["party"], "contests": int(row["contests"]),
                    "weight_sum": float(row["weight_sum"]),
                    "weighted_delta": float(row["weighted_delta"]),
                    "reaches_model": float(row["weight_sum"]) >= montecarlo.BYE_MIN_WEIGHT,
                    "class_weight": given.get("weight"),
                    "size_class": given.get("class")})
    return rows


def main(argv: list[str] | None = None) -> int:
    import cityconfig
    import montecarlo as M

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    parser.add_argument("--draws", type=int, default=None,
                        help="default: montecarlo.DEFAULTS, the published count")
    parser.add_argument("--seed", type=int, default=None,
                        help="default: montecarlo.DEFAULTS, the published seed")
    parser.add_argument("--laws", nargs="+", default=list(LAWS), choices=LAWS)
    parser.add_argument("--jobs", type=int, default=None)
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="a lever-grid cell, e.g. --set w_bye=0 (PLAN.md S3); "
                             "recorded in the manifest")
    parser.add_argument("--index", type=Path, default=None, metavar="ROOT",
                        help="write ROOT/index.json from the cells under ROOT "
                             "and exit")
    parser.add_argument("--out", type=Path, default=None,
                        help="default: a new scratch directory")
    args = parser.parse_args(argv)
    if args.index:
        print(json.dumps(write_index(args.index), indent=1))
        return 0
    city = cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))
    draws = args.draws or int(M.DEFAULTS["draws"])
    seed = args.seed or int(M.DEFAULTS["seed"])
    out = args.out or Path(tempfile.mkdtemp(prefix="export_draws_"))
    report = export(city.slug, target.year, draws, seed, out,
                    tuple(args.laws), args.jobs, tuple(args.set))
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    # Before anything else, as `montecarlo`'s own guard does: this may replace
    # the process with one under the fixed hash seed, which the workers inherit.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import montecarlo
    montecarlo.fix_hash_seed()
    raise SystemExit(main())

"""Results night: rank every sealed forecast against the result (owner, 2026-10-03).

Every successful seal is stored as one entry in the D1 database ``joburg-entries``
(``src/share-edge.js`` ``storeEntry``, ``migrations/0001_entries.sql``). Each
sealed forecast is one entry, even when one person sealed several. This module
scores every entry against the actual result and writes the leaderboard
artefact that ``build_site`` publishes as ``/leaderboard/`` once
``content/<city>/leaderboard.toml`` says ``published = true``
(:mod:`build_leaderboard`).

ONE DEFINITION OF THE SCORE. Each entry is scored by
:func:`score_forecasts.score` and ordered by :func:`score_forecasts.rank`, the
competition's order (``JUDGEMENT-CALLS.md`` §N4): seat error, then ward calls
correct, then list-ballot vote error. The result is read by
:func:`score_forecasts.ingest_result`, the scorer's loader: it is the one that
returns the list-ballot shares the third key needs (``backtest.actual_result``
returns seats and ward winners only).

TIES (``JUDGEMENT-CALLS.md`` §N7). The vote error is rounded once, to
``VOTE_DP`` decimals, before ranking: the board ranks on the figure it
prints. Entries equal on all three keys are placed by the earlier seal;
entries sealed in the same second, by seal id. Every entry gets its own
place: :func:`score_forecasts.rank` orders the ties this way already, and the
place is the position in that order.

EVERY ENTRY IS LISTED. The artefact carries every row; the page lists them
all, and a reader finds their own by its link.

AFTER PUBLICATION (``JUDGEMENT-CALLS.md`` §N8). ``--drop <seal id>`` removes
an entry from the written board on a reader's request, and ``--anonymise``
replaces every name with "Anonymous #" and the start of the seal id, at the
ninety-day deletion. Both edit ``content/<city>/leaderboard.json`` in place,
with no export: removing an entry from a total order leaves the others in
order, so the places are renumbered and nothing is re-scored. The board is
gitignored (``.gitignore``) so a name removed from it is not kept in git.

AN ENTRY THAT CANNOT BE SCORED STOPS THE RANKING, as :func:`score_forecasts.rank`
does: an entry made under a context (roster, wards, total vote) with no
forecast.json given is named, as is one the seat law cannot seat. Nothing is
left out in silence. An earlier context's forecast.json is in git:
``git show <commit>:site/your-forecast/forecast.json > <file>``.

The owner's steps, on results night
===================================

1. Export the entries (wrangler.toml, the ENTRIES note)::

       npx wrangler d1 execute joburg-entries --remote --json \\
         --command "SELECT seal_id, sealed_at, label, model_ref, context_ref, state, forecast FROM entries" \\
         > ~/joburg-entries.json

2. Ingest the result (``src/ingest_lge.py``) to its cleaned VD file, then::

       .venv/bin/python src/rank_entries.py --entries ~/joburg-entries.json \\
         --result data/raw/elections/lge2026_JHB_vd_party_clean.csv \\
         --forecast site/your-forecast/forecast.json

   It writes ``content/joburg/leaderboard.json``. With the IEC's seat table
   on disk it is compared with the computed council; a disagreement stops
   the run until ``--seat-source`` names one.

3. Set ``published = true`` in ``content/joburg/leaderboard.toml`` and build
   the site.

On a reader's request, after publication::

       .venv/bin/python src/rank_entries.py --drop <seal id>

At the ninety-day deletion (wrangler.toml, the ENTRIES note)::

       npx wrangler d1 execute joburg-entries --remote --command "DELETE FROM entries"
       rm ~/joburg-entries.json
       .venv/bin/python src/rank_entries.py --anonymise

then build and deploy the site.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import score_forecasts as S

REPO_ROOT = Path(__file__).resolve().parents[1]
EDGE = REPO_ROOT / "src" / "share-edge.js"
#: How many characters of the seal id identify an entry on the leaderboard
#: (a reader's link finds its row by them) and in an anonymous entry's name.
#: The leaderboard's script reads ID_CHARS from the artefact.
ID_CHARS, ANON_CHARS = 12, 6
#: The decimals of the vote error the leaderboard prints and ranks on
#: (JUDGEMENT-CALLS.md §N7). The page reads it from the artefact.
VOTE_DP = 1


def entry_columns() -> list[str]:
    """The entry's columns, read from their one definition (share-edge.js
    ``ENTRY_COLUMNS``)."""
    m = re.search(r"export const ENTRY_COLUMNS = \[([^\]]*)\];", EDGE.read_text(encoding="utf-8"))
    if not m:
        raise SystemExit("src/share-edge.js no longer declares ENTRY_COLUMNS")
    return re.findall(r'"([a-z_]+)"', m.group(1))


def load_export(path) -> list[dict]:
    """The rows of a ``wrangler d1 execute --json`` export (a list of
    ``{"results": [...]}``), or a bare list of rows. Every row must carry
    exactly the entry's columns."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list) and data and isinstance(data[0], dict) and "results" in data[0]:
        if not all(block.get("success", True) for block in data):
            raise ValueError(f"{path}: the export reports a failed query")
        rows = [r for block in data for r in block["results"]]
    elif isinstance(data, list):
        rows = data
    else:
        raise ValueError(f"{path}: not a wrangler d1 --json export or a list of rows")
    cols = set(entry_columns())
    bad = [r.get("seal_id") for r in rows if set(r) != cols]
    if bad:
        raise ValueError(f"{len(bad)} row(s) do not carry exactly the columns {sorted(cols)}: {bad[:5]}")
    ids = [r["seal_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("a seal id appears twice in the export")
    return rows


def anonymous(seal_id: str) -> str:
    return "Anonymous #" + seal_id[:ANON_CHARS]


def entry_name(row: dict) -> str:
    """The label the reader typed, or "Anonymous #" and the seal id's start."""
    return row["label"] or anonymous(row["seal_id"])


def sealed_iso(seconds: int) -> str:
    return datetime.fromtimestamp(int(seconds), tz=timezone.utc).isoformat().replace("+00:00", "Z")


def rank_entries(rows: list[dict], forecasts: dict[str, dict], result: dict, *,
                 seat_source: str | None = None) -> dict:
    """The leaderboard artefact for ``rows`` against ``result``.

    ``forecasts`` maps a context_ref to its forecast.json (its ``schema``).
    Returns ``{"result", "entries", "wards", "id_chars", "vote_dp", "rows":
    [{place, id, name, seat_error, wards_called, list_vote_error,
    sealed_at}]}``, rows in place order, the vote error rounded to
    ``VOTE_DP`` decimals and ranked as rounded. Refuses (ValueError) an entry under a context with no forecast.json,
    and, through :func:`score_forecasts.rank`, any entry that cannot be scored.
    """
    missing = sorted({r["context_ref"] for r in rows} - set(forecasts))
    if missing:
        named = {c: [r["seal_id"] for r in rows if r["context_ref"] == c][:5] for c in missing}
        raise ValueError(f"entries under context(s) with no forecast.json given: {named}. "
                         f"Pass that context's forecast.json with --forecast.")
    scores = {r["seal_id"]: S.score(json.loads(r["forecast"]), forecasts[r["context_ref"]]["schema"],
                                    result, seat_source=seat_source)
              for r in rows}
    for s in scores.values():
        if s.get("ok"):
            s["list_vote_error"] = round(s["list_vote_error"], VOTE_DP)
    by_id = {r["seal_id"]: r for r in rows}
    order = S.rank(scores, saved_at={r["seal_id"]: int(r["sealed_at"]) for r in rows})
    wards = {s["wards"] for s in scores.values()}
    if len(wards) > 1:
        raise ValueError(f"entries are scored over different ward counts: {sorted(wards)}")
    out = []
    for place, (_shared, ident, _key) in enumerate(order, start=1):
        s, r = scores[ident], by_id[ident]
        out.append({"place": place, "id": ident[:ID_CHARS], "name": entry_name(r),
                    "seat_error": s["seat_error"], "wards_called": s["wards_called"],
                    "list_vote_error": s["list_vote_error"],
                    "sealed_at": sealed_iso(r["sealed_at"])})
    if len({row["id"] for row in out}) != len(out):
        raise ValueError(f"two entries share the first {ID_CHARS} characters of their seal id")
    return {"_about": "Written by src/rank_entries.py. Do not edit.",
            "result": {"city": result["city"], "target": result["target"],
                       "seat_source": seat_source or "computed"},
            "entries": len(out), "wards": wards.pop() if wards else 0,
            "id_chars": ID_CHARS, "vote_dp": VOTE_DP, "rows": out}


def edit_board(board: dict, *, drop=(), anonymise: bool = False) -> dict:
    """``board`` without the entries whose seal id (whole, or its first
    ID_CHARS characters) is in ``drop``, places renumbered; with
    ``anonymise``, every name replaced by "Anonymous #" and the id's start.
    Refuses an id that names no entry."""
    want = {d.strip()[:ID_CHARS] for d in drop if d.strip()}
    have = {r["id"] for r in board["rows"]}
    unknown = sorted(want - have)
    if unknown:
        raise ValueError(f"no entry on the board has the seal id(s) {unknown}")
    rows = [dict(r) for r in board["rows"] if r["id"] not in want]
    for place, r in enumerate(rows, start=1):
        r["place"] = place
        if anonymise:
            r["name"] = anonymous(r["id"])
    return {**board, "entries": len(rows), "rows": rows}


def main(argv=None) -> int:
    import cityconfig
    import official_seats

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entries", type=Path, help="the wrangler d1 --json export")
    ap.add_argument("--result", type=Path, help="the cleaned IEC VD-level result file")
    ap.add_argument("--forecast", type=Path, action="append",
                    help="a forecast.json; one per context the entries were sealed under")
    ap.add_argument("--drop", action="append", default=[], metavar="SEAL_ID",
                    help="remove this entry from the board (a reader's request); repeatable")
    ap.add_argument("--anonymise", action="store_true",
                    help="replace every name on the board (the ninety-day deletion)")
    ap.add_argument("--target", default="2026")
    ap.add_argument("--aliases", type=Path, help="JSON {IEC name: roster spelling}, if the IEC respells one")
    ap.add_argument("--seat-source", choices=S.SEAT_SOURCES)
    ap.add_argument("--out", type=Path, default=None,
                    help="default: content/<city>/leaderboard.json")
    cityconfig.add_city_argument(ap)
    args = ap.parse_args(argv)
    slug = cityconfig.use(args.city).slug
    out = args.out or REPO_ROOT / "content" / slug / "leaderboard.json"
    ranking = (args.entries, args.result, args.forecast)
    if not any(ranking):
        if not (args.drop or args.anonymise):
            ap.error("give --entries, --result and --forecast to rank, or --drop / --anonymise to edit the board")
        board = edit_board(json.loads(out.read_text(encoding="utf-8")), drop=args.drop,
                           anonymise=args.anonymise)
        out.write_text(json.dumps(board, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{board['entries']} entries on the board -> {out}")
        return 0
    if not all(ranking):
        ap.error("ranking needs --entries, --result and --forecast together")
    forecasts = {}
    for f in args.forecast:
        data = json.loads(f.read_text(encoding="utf-8"))
        forecasts[data["context_ref"]] = data
    aliases = json.loads(args.aliases.read_text(encoding="utf-8")) if args.aliases else None
    official = official_seats.read(cityconfig.active().code, int(args.target))
    result = S.ingest_result(args.result, city=slug, target=args.target,
                             roster=S.certified_roster(slug, args.target), aliases=aliases,
                             official=official)
    board = rank_entries(load_export(args.entries), forecasts, result, seat_source=args.seat_source)
    board = edit_board(board, drop=args.drop, anonymise=args.anonymise)
    out.write_text(json.dumps(board, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ranked {board['entries']} entries -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

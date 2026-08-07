"""Assemble forecast-interactive.html from the template and the data packs.

The page must be fully self-contained (no fetches), so the ward-level data
pack and the Python reference run are injected as literals. Re-run this after
any pipeline re-run so the page and the Python model stay in step:

    python src/export_interactive.py && python src/build_interactive.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import stats as statlib


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path,
                        default=Path("src/interactive_template.html"))
    parser.add_argument("--data", type=Path,
                        default=Path("data/processed/interactive_data.json"))
    parser.add_argument("--summary", type=Path,
                        default=Path("data/processed/forecast_summary.json"))
    parser.add_argument("--out", type=Path, default=Path("forecast-interactive.html"))
    args = parser.parse_args(argv)

    html = args.template.read_text(encoding="utf-8")
    registry_path = Path("content/joburg/stats.toml")
    if registry_path.exists():
        registry = statlib.load_registry(registry_path)
        ctx = statlib.load_context(args.data.parent)
        html, drift, unresolved = statlib.render(html, registry, ctx)
        if unresolved:
            raise SystemExit("unresolved stats in the interactive template: "
                             + ", ".join(sorted(set(unresolved))))
        if drift:
            print(statlib.drift_report(drift))
    data = json.loads(args.data.read_text(encoding="utf-8"))

    reference = None
    if args.summary.exists():
        summary = json.loads(args.summary.read_text(encoding="utf-8"))
        reference = {
            "parties": {p: {"median": round(v["median"])}
                        for p, v in summary["parties"].items()
                        if p in ("DA", "ANC", "EFF", "MK", "ASA", "PA")},
            "threshold_median": summary["threshold_median"],
            "p_excessive_any": summary["p_excessive_any"],
            "structural": summary["structural"],
        }

    html = html.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    html = html.replace("/*__REF__*/null", json.dumps(reference, separators=(",", ":")))
    args.out.write_text(html, encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

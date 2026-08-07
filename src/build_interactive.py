"""Assemble forecast-interactive.html from the template and the data packs.

The page must be fully self-contained (no fetches), so the ward-level data
pack and the Python reference run are injected as literals. Re-run this after
any pipeline re-run so the page and the Python model stay in step:

    python src/export_interactive.py && python src/build_interactive.py
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import cityconfig
import stats as statlib


def city_constants(city) -> str:
    """The JS mirror of the model's constants, generated from the config.

    These used to be hand-typed in the template alongside the Python
    originals — four copies of the same numbers, which had already drifted
    (a dead POLLING_SPAN=4 sat opposite polling_span=8.0). Generating them
    makes drift impossible and makes the browser engine city-agnostic.
    """
    j = city.judgements
    sc = j.get("scalars", {})
    bounds = {k: list(v) for k, v in city.plan_bounds.items()}
    ind = {k: list(v) for k, v in j.get("individual_theta", {}).items()}
    blocs = city.blocs
    theta = j.get("theta_mode", {})
    # the browser draws bloc shifts from (low, high); the mode is derived
    anc_shift = sc.get("anc_bloc_shift", [])
    da_shift = sc.get("da_bloc_shift", [])
    lines = [
        "// GENERATED from cities/%s.toml — do not hand-edit" % city.slug,
        "const BOUNDS=%s;" % json.dumps(bounds),
        "const IND_THETA=%s;" % json.dumps(ind),
        "const F_OTHER=%s;" % json.dumps(list(sc.get("f_other", [0.7, 1.3, 2.0]))),
        "const ANC_SHIFT=[%g,%g], DA_SHIFT=[%g,%g];" % (
            anc_shift[0], anc_shift[-1], da_shift[0], da_shift[-1]),
        "const BLOC_ANC=%s, BLOC_DA=%s;" % (
            json.dumps(list(blocs["ANC_BLOC"])), json.dumps(list(blocs["DA_BLOC"]))),
        "const THETA_BOSA=%g;" % theta.get("BOSA", 0.80),
    ]
    return "\n".join(lines)


def default_cfg(city) -> str:
    """The slider defaults, from the same config the Python model reads."""
    j = city.judgements
    sc = j.get("scalars", {})
    theta = j.get("theta_mode", {})
    ind = j.get("individual_theta", {})
    cfg = {
        "thetaANC": theta.get("ANC"), "thetaDA": theta.get("DA"),
        "thetaEFF": theta.get("EFF"), "thetaMK": theta.get("MK"),
        "thetaASA": theta.get("ASA"),
        "thetaPA": (ind.get("PA") or [None, None, None])[1],
        "wBye": sc.get("w_bye"), "blocLeak": sc.get("bloc_leak"),
        "pollPick": "", "pollWeight": 0.5,
        "alphaANC": sc.get("alpha_anc"), "alphaDA": sc.get("alpha_da"),
        "mkRatio": j.get("ward_pr_ratio_overrides", {}).get("MK"),
        "paUplift": sc.get("pa_contestation_uplift"),
        "turnoutANC": sc.get("turnout_tilt_anc"),
        "turnoutDA": sc.get("turnout_tilt_da"),
        "turnoutBlend": sc.get("turnout_pattern_blend"),
        "turnoutNoise": sc.get("turnout_noise_sd"),
        "entrantProb": sc.get("entrant_prob"),
        "entrantMode": (sc.get("entrant_share") or [0, 0.04, 0])[1],
    }
    missing = [k for k, v in cfg.items() if v is None]
    if missing:
        raise SystemExit(f"{city.slug}: config is missing {missing}")
    return json.dumps(cfg)


def apply_slider_defaults(html: str, cfg_json: str, city) -> str:
    """Point each slider's value/min/max at the config, not a typed literal."""
    cfg = json.loads(cfg_json)
    bounds = city.plan_bounds
    ranges = {"thetaANC": bounds.get("ANC"), "thetaDA": bounds.get("DA"),
              "thetaEFF": bounds.get("EFF"), "thetaMK": bounds.get("MK"),
              "thetaASA": bounds.get("ASA")}
    ind = city.judgements.get("individual_theta", {})
    if "PA" in ind:
        ranges["thetaPA"] = (ind["PA"][0], ind["PA"][2])

    def fix(match: re.Match) -> str:
        tag, sid = match.group(0), match.group(1)
        if sid in cfg:
            tag = re.sub(r'value="[^"]*"', 'value="%g"' % cfg[sid], tag)
        rng = ranges.get(sid)
        if rng:
            tag = re.sub(r'min="[^"]*"', 'min="%g"' % rng[0], tag)
            tag = re.sub(r'max="[^"]*"', 'max="%g"' % rng[1], tag)
        return tag

    return re.sub(r'<input type="range" id="(\w+)"[^>]*>', fix, html)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path,
                        default=Path("src/interactive_template.html"))
    parser.add_argument("--data", type=Path,
                        default=Path("data/processed/interactive_data.json"))
    parser.add_argument("--summary", type=Path,
                        default=Path("data/processed/forecast_summary.json"))
    parser.add_argument("--out", type=Path, default=Path("forecast-interactive.html"))
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)

    html = args.template.read_text(encoding="utf-8")
    city = cityconfig.load(getattr(args, "city", None))
    cfg_json = default_cfg(city)
    html = html.replace("/*__CITY_CONSTS__*/", city_constants(city))
    html = html.replace("/*__DEFAULT_CFG__*/null", cfg_json)
    html = apply_slider_defaults(html, cfg_json, city)
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

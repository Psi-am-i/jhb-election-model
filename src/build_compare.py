"""Build a side-by-side review page for a document rewrite.

The rewrite process (agreed 2026-08-04): the canonical technical documents
stay verbatim (and live on GitHub); the site gets reader editions written for
the public. Nothing is ever lost, so review is about whether the new page is
good — judged section by section against the original.

This script renders that judgement surface: an unlisted page at
site/drafts/<name>.html pairing original sections (left) with the proposed
reader edition (right), numbered so verdicts can be as terse as
"1–4 yes, 5 no, 6 yes but drop the last sentence".

Usage:
    python src/build_compare.py sources
"""

from __future__ import annotations

import argparse
from pathlib import Path

import markdown

# per-document spec: source files and the section pairing.
# headings are matched on their ## text; "" means the pre-heading intro.
SPECS = {
    "sources": {
        "original": "SOURCES.md",
        "proposed": "docs-public/sources.md",
        "title": "Sources — rewrite review",
        "pairs": [
            ("Purpose of the page", [""], [""]),
            ("The access story", ["Access constraints (learned the hard way)", "Election IDs"],
             ["Public records, deliberately hard to reach"]),
            ("The election results", ["National & provincial elections (VD-level, provincial ballot)",
                                      "Local government elections (VD-level, ward + PR ballots)"],
             ["The election results themselves"]),
            ("Boundaries and maps", ["Boundaries — MDB Spatial Knowledge Hub"], ["The maps"]),
            ("By-elections", ["By-elections — use the dashboard, not the downloads page"],
             ["By-elections"]),
            ("Census / covariates", ["Covariates"], ["People"]),
            ("What is not published", ["Historic VD boundaries — searched for, not published",
                                       "Still to acquire — needs a human"],
             ["What nobody publishes"]),
            ("Integrity of the data", ["Archive"], ["Keeping ourselves honest"]),
        ],
    },
    "methodology": {
        "original": "METHODOLOGY.md",
        "proposed": "docs-public/methodology.md",
        "title": "Methodology — rewrite review",
        "pairs": [
            ("Purpose of the page", [""], [""]),
            ("What is being predicted", ["1. What is being predicted"],
             ["How Johannesburg's council elections actually work"]),
            ("The pipeline", ["5A. How the model works, end to end"],
             ["The machinery of prediction"]),
            ("Validation", ["5. Validation results"],
             ["How we know it works — and what that does not cover"]),
            ("Corrections & the review", ["3. Corrections to the plan, with reasoning and impact"],
             ["The model was broken once, and we published the repair"],
             "The reader edition compresses this to a pointer — the full story is the Review page."),
            ("Assumptions & limits", ["6. Assumptions and limitations a reviewer should weigh"],
             ["The dials you can turn", "Limits worth knowing"]),
            ("Data provenance & traps", ["2. Data: provenance and validation",
                                         "4. Data quality problems found"], [],
             "Not carried here — this material lives on the Sources page and on GitHub."),
            ("Results", ["5B. Results"], [],
             "Not carried here — the forecast page IS the results."),
            ("Reproducibility", ["7. Reproducibility"], [],
             "Not carried here — the GitHub README covers reproduction."),
        ],
    },
    "review": {
        "original": "drafts/review-original-excerpts.md",
        "original_label": "model-review.html (verbatim excerpts)",
        "proposed": "docs-public/review.md",
        "title": "Review — rewrite review",
        "pairs": [
            ("Framing", ["Verdict"], [""]),
            ("The headline error", ["E1"], ["The error that mattered most"]),
            ("The other findings", ["E2 to E6"], ["The other five, briefly"]),
            ("What the fixes changed", ["Addendum: what the corrected model says"],
             ["What the fixes changed"]),
            ("What remains open", ["Addendum: still open"],
             ["What the review could not fix"]),
            ("Why publish", [], ["Why publish this at all"],
             "New section — no original counterpart; the argument for publishing the audit."),
        ],
    },
}

STYLE = """
  :root{
    --paper:#fbfbfa; --paper-2:#f2f3f1; --rule:#d9dbd6; --rule-soft:#e7e8e4;
    --ink:#1a1d1b; --ink-2:#4a4f4b; --ink-3:#767b76;
    --accent:#a8621f; --accent-soft:#f0e2d5; --good:#2f6d4a;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
    --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --paper:#141715; --paper-2:#1c201d; --rule:#333833; --rule-soft:#282d29;
      --ink:#eceee9; --ink-2:#b6bcb6; --ink-3:#868d86;
      --accent:#d9954f; --accent-soft:#3a2a1a; --good:#6fb98a;
    }
  }
  *{box-sizing:border-box;margin:0;}
  a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px;}
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);
    font-size:14.5px;line-height:1.6;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1200px;margin:0 auto;padding:28px 24px 80px;}
  .kicker{font-size:11px;font-weight:650;letter-spacing:.16em;text-transform:uppercase;
    color:var(--accent);margin-bottom:8px;}
  h1{font-family:var(--serif);font-weight:600;font-size:clamp(26px,4vw,36px);
    line-height:1.12;margin-bottom:10px;}
  .howto{background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);
    padding:12px 16px;font-size:13.5px;color:var(--ink-2);margin:14px 0 26px;}
  .pair{margin:34px 0;}
  .pairhead{display:flex;align-items:baseline;gap:12px;margin-bottom:10px;}
  .num{font-family:var(--mono);font-size:15px;font-weight:700;color:var(--accent);
    border:1.5px solid var(--accent);border-radius:50%;width:30px;height:30px;
    display:flex;align-items:center;justify-content:center;flex:none;}
  .pairhead h2{font-family:var(--serif);font-weight:600;font-size:20px;}
  .duo{display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start;}
  @media (max-width:900px){.duo{grid-template-columns:1fr;}}
  .col{border:1px solid var(--rule-soft);padding:14px 18px;min-width:0;}
  .col.orig{background:var(--paper-2);}
  .col.prop{border-left:3px solid var(--good);}
  .collabel{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;
    text-transform:uppercase;color:var(--ink-3);margin-bottom:10px;}
  .col.prop .collabel{color:var(--good);}
  .col h1,.col h2{font-family:var(--serif);font-size:17px;border:none;margin:12px 0 4px;padding:0;}
  .col p{margin:8px 0;}
  .col ul,.col ol{margin:8px 0;padding-left:18px;}
  .col li{margin:4px 0;}
  .col code{font-family:var(--mono);font-size:.85em;background:var(--paper);
    border:1px solid var(--rule-soft);border-radius:3px;padding:.05em .3em;}
  .col.orig code{background:var(--paper-2);}
  .col pre{background:var(--paper);border:1px solid var(--rule-soft);border-radius:4px;
    padding:10px 12px;overflow-x:auto;font-size:12px;margin:10px 0;}
  .col .tw{overflow-x:auto;}
  .col table{border-collapse:collapse;width:100%;font-size:12.5px;margin:10px 0;}
  .col th{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);
    text-align:left;padding:0 10px 5px 0;border-bottom:1px solid var(--rule);}
  .col td{padding:6px 10px 6px 0;border-bottom:1px solid var(--rule-soft);vertical-align:top;}
  .colophon{font-family:var(--mono);font-size:11px;color:var(--ink-3);
    border-top:1px solid var(--rule);padding-top:12px;margin-top:40px;}
"""


def sections(path: Path) -> dict[str, str]:
    """Split a markdown file into {## heading: chunk}; '' is the intro."""
    out: dict[str, list[str]] = {"": []}
    current = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            out[current] = []
        elif line.startswith("# ") and current == "":
            continue  # drop the H1; the pair header carries context
        else:
            out.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def render(chunk: str) -> str:
    html = markdown.markdown(chunk, extensions=["tables", "fenced_code", "smarty"])
    return html.replace("<table>", '<div class="tw"><table>').replace(
        "</table>", "</table></div>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("doc", choices=sorted(SPECS))
    parser.add_argument("--out-dir", type=Path, default=Path("site/drafts"))
    args = parser.parse_args(argv)
    spec = SPECS[args.doc]

    orig = sections(Path(spec["original"]))
    prop = sections(Path(spec["proposed"]))

    blocks = []
    for i, pair in enumerate(spec["pairs"], 1):
        label, orig_keys, prop_keys = pair[:3]
        note = pair[3] if len(pair) > 3 else ""
        left = "\n<hr>\n".join(render(orig[k]) for k in orig_keys if k in orig)
        right = "\n".join(render(prop[k]) for k in prop_keys if k in prop)
        if not right and note:
            right = f"<p><em>{note}</em></p>"
        if not left and note:
            left = f"<p><em>{note}</em></p>"
        blocks.append(f"""
<div class="pair">
  <div class="pairhead"><span class="num">{i}</span><h2>{label}</h2></div>
  <div class="duo">
    <div class="col orig"><div class="collabel">Original — {spec.get("original_label", spec["original"])}</div>{left}</div>
    <div class="col prop"><div class="collabel">Proposed reader edition</div>{right}</div>
  </div>
</div>""")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{spec["title"]}</title>
<style>{STYLE}</style>
</head>
<body>
<div class="wrap">
  <div class="kicker">Draft for review · unlisted</div>
  <h1>{spec["title"]}</h1>
  <div class="howto">The original stays canonical (on GitHub) whatever happens here — this
  review decides only what the <em>website</em> says. Reply with verdicts by number, as terse
  as you like: <b>"1–4 yes, 5 no, 6 yes but drop the last sentence."</b></div>
{"".join(blocks)}
  <div class="colophon">Generated by src/build_compare.py · not linked from the site ·
  original: {spec["original"]} · proposed: {spec["proposed"]}</div>
</div>
</body>
</html>
"""
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"{args.doc}.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB, {len(blocks)} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

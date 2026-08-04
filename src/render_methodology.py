"""Render METHODOLOGY.md as methodology.html in the project's house style.

Same principle as render_sheet.py: the styled artefact is generated from the
canonical source, never hand-copied, so it cannot go stale. Re-run after any
METHODOLOGY.md edit:

    python src/render_methodology.py

The page is fully self-contained (inline CSS, no external assets), responsive,
theme-aware (light/dark), and carries the same typography as
forecast-sheet.html / model-review.html.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

import markdown

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
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);
    font-size:15px;line-height:1.62;-webkit-font-smoothing:antialiased;}
  .sheet{max-width:780px;margin:0 auto;padding:32px 24px 80px;}

  .kicker{font-size:11px;font-weight:650;letter-spacing:.16em;text-transform:uppercase;
    color:var(--accent);margin-bottom:10px;}
  h1{font-family:var(--serif);font-weight:600;font-size:clamp(28px,4.6vw,40px);
    line-height:1.12;letter-spacing:-.012em;text-wrap:balance;margin:0 0 10px;}
  .dateline{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--mono);
    font-size:11.5px;color:var(--ink-3);border-top:1px solid var(--rule);
    border-bottom:1px solid var(--rule);padding:9px 0;margin:14px 0 8px;}
  .dateline b{color:var(--ink-2);font-weight:600;}

  h2{font-family:var(--serif);font-weight:600;font-size:24px;line-height:1.2;
    letter-spacing:-.006em;margin:42px 0 4px;padding-top:18px;
    border-top:1px solid var(--rule);}
  h2:first-of-type{border-top:none;padding-top:0;}
  h3{font-family:var(--serif);font-weight:600;font-size:18px;line-height:1.3;margin:28px 0 2px;}
  p{margin:10px 0;max-width:70ch;}
  ul,ol{margin:10px 0;padding-left:20px;max-width:68ch;
    display:flex;flex-direction:column;gap:5px;}
  strong{font-weight:650;}
  em{font-style:italic;}
  hr{border:none;border-top:1px solid var(--rule-soft);margin:26px 0;}
  a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px;}

  code{font-family:var(--mono);font-size:.86em;background:var(--paper-2);
    border:1px solid var(--rule-soft);border-radius:3px;padding:.08em .34em;}
  pre{background:var(--paper-2);border:1px solid var(--rule-soft);border-radius:5px;
    padding:13px 15px;overflow-x:auto;margin:14px 0;line-height:1.5;}
  pre code{background:none;border:none;padding:0;font-size:12.5px;color:var(--ink-2);}

  .tablewrap{overflow-x:auto;margin:14px 0;}
  table{border-collapse:collapse;width:100%;font-size:13.5px;}
  th{font-family:var(--sans);font-size:10.5px;font-weight:650;letter-spacing:.1em;
    text-transform:uppercase;color:var(--ink-3);text-align:left;
    padding:0 12px 7px 0;border-bottom:1px solid var(--rule);vertical-align:bottom;}
  td{padding:8px 12px 8px 0;border-bottom:1px solid var(--rule-soft);
    vertical-align:top;color:var(--ink-2);}
  td:first-child{color:var(--ink);}
  td code, th code{white-space:nowrap;}

  blockquote{border-left:2px solid var(--accent);background:var(--paper-2);
    padding:10px 16px;margin:14px 0;color:var(--ink-2);}
  blockquote p{margin:6px 0;}

  .colophon{font-family:var(--mono);font-size:11px;line-height:1.65;color:var(--ink-3);
    border-top:1px solid var(--rule);padding-top:12px;margin-top:48px;}

  @media print{
    body{background:#fff;color:#000;font-size:10pt;}
    .sheet{max-width:none;padding:0;}
    h2{break-after:avoid;} h3{break-after:avoid;}
    table,blockquote,pre{break-inside:avoid;}
  }
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("METHODOLOGY.md"))
    parser.add_argument("--out", type=Path, default=Path("methodology.html"))
    args = parser.parse_args(argv)

    text = args.source.read_text(encoding="utf-8")

    # The file opens with an H1 and a status line; lift them into a masthead.
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    body_md = "\n".join(lines[1:])
    status = ""
    match = re.search(r"^\*\*(.+?)\*\*\n(Status.+?)$", body_md, re.M)
    if match:
        subtitle, status = match.group(1), match.group(2)
        body_md = body_md.replace(match.group(0), "", 1)
    else:
        subtitle = ""

    html_body = markdown.markdown(
        body_md, extensions=["tables", "fenced_code", "smarty"]
    )
    # Wide tables must scroll inside their own container, not the page.
    html_body = html_body.replace("<table>", '<div class="tablewrap"><table>')
    html_body = html_body.replace("</table>", "</table></div>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Johannesburg 2026 Model — Methodology</title>
<style>{STYLE}</style>
</head>
<body>
<div class="sheet">
<header>
  <div class="kicker">Methodology &amp; review brief · City of Johannesburg · 4 November 2026</div>
  <h1>{title}</h1>
  <div class="dateline">
    <span><b>Subject</b> {subtitle}</span>
    <span><b>{status.split("·")[0].strip() if status else ""}</b>
          {"· ".join(status.split("·")[1:]).strip() if "·" in status else ""}</span>
  </div>
</header>
{html_body}
<div class="colophon">
  Generated from METHODOLOGY.md by src/render_methodology.py on {date.today().isoformat()} —
  the Markdown file is canonical; regenerate rather than editing this page.
  Companions: forecast-sheet.html (two-page distribution sheet) ·
  forecast-interactive.html (adjustable assumptions) ·
  model-review.html (implementation review and resolution).
</div>
</div>
</body>
</html>
"""
    args.out.write_text(page, encoding="utf-8")
    print(f"wrote {args.out} ({args.out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

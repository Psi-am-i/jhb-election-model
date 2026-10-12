"""Download every IEC report the model needs that is reachable without a browser.

Most of ``results.elections.org.za`` is Cloudflare-gated and returns 403 to
curl, but the *generated report files* are served straight through. The URL
shape is stable:

    /home/LGEPublicReports/{election}/{report}/{province}/{muni}.{ext}
    /home/NPEPublicReports/{election}/{report}/{province}/{muni}/{muni}.{ext}

Report names must be exact -- "Seat Calculation Detail" works where "Seat
Calculation" 404s. See ``SOURCES.md`` for the ones that do *not* work this way
(the bulk VD-level zips and the by-election comparison reports, both of which
need a real browser session).

Usage:
    python src/fetch_iec.py [--out-dir data/raw/elections/_reports]
"""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://results.elections.org.za/home"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Local government elections: election id -> year.
LGE_ELECTIONS = {197: 2011, 402: 2016, 1091: 2021}

# (report name, extension). The party-results CSV is the VD-level workhorse; the
# rest are cross-checks and validation targets.
LGE_REPORTS = [
    ("Downloadable Party Results", "csv"),
    ("Detailed Results", "pdf"),
    ("Seat Calculation Detail", "pdf"),
    ("Seat Calculation Detail", "xls"),
    ("Voter Turnout", "pdf"),
]

PROVINCE = "GP"
MUNI = "JHB"


def download(url: str, destination: Path, timeout: int = 120) -> tuple[bool, int, str]:
    """Fetch ``url`` to ``destination``. Returns (ok, bytes, note)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        return False, 0, f"HTTP {error.code}"
    except (urllib.error.URLError, TimeoutError) as error:
        return False, 0, str(error)

    # The portal answers a missing report with a small HTML error page and a 200.
    if payload[:15].lstrip().lower().startswith(b"<!doctype html") or payload[:6] == b"<html>":
        return False, len(payload), "HTML error page, not a report"

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return True, len(payload), ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir", type=Path, default=Path("data/raw/elections/_reports")
    )
    parser.add_argument("--province", default=PROVINCE)
    parser.add_argument("--muni", default=MUNI)
    args = parser.parse_args(argv)

    failures = 0
    for election, year in sorted(LGE_ELECTIONS.items(), key=lambda kv: kv[1]):
        for report, ext in LGE_REPORTS:
            url = (
                f"{BASE}/LGEPublicReports/{election}/"
                f"{urllib.parse.quote(report)}/{args.province}/{args.muni}.{ext}"
            )
            slug = report.lower().replace(" ", "_")
            destination = args.out_dir / f"lge{year}_{args.muni}_{slug}.{ext}"
            ok, size, note = download(url, destination)
            status = f"{size / 1000:>8.1f} kB" if ok else f"  FAILED  {note}"
            print(f"  lge{year} {report:<28s} {ext:<4s} {status}")
            failures += not ok
            time.sleep(0.4)  # the portal WAFs rapid-fire requests

    print(f"\n{'all reports fetched' if not failures else f'{failures} failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

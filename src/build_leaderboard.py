"""Build ``/leaderboard/``: every sealed forecast ranked against the result.

Hidden until the result is in. ``content/<city>/leaderboard.toml`` holds the
flag (``published``) and how many places the page lists (``top``). With the
flag off the build writes no page, removes any earlier one, and the nav has no
entry (``build_site.nav_for``). With it on, ``content/<city>/leaderboard.json``
(written by ``src/rank_entries.py``) must exist, and the build writes:

``leaderboard/index.html``
    The page: a shell with two LIVE regions and no figure, rendered, audited
    and scanned by ``build_site`` like every other page.
``leaderboard/leaderboard.json``
    The artefact, with ``top`` added.
``leaderboard/js/leaderboard.js``
    ``interactive/js/leaderboard.js``, the regions' one writer
    (``stats.LIVE_WRITERS``): it lists the first places and finds a reader's
    entry by the link they paste, or the ``s`` in the page's own address.

Its style is ``src/css/page-board.css``, in the site's one stylesheet.
"""
from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LB_DIR = "leaderboard"
LB_PAGE = f"{LB_DIR}/index.html"
#: The page's address in the nav and in og:url.
LB_HREF = f"{LB_DIR}/"
SCRIPT = REPO_ROOT / "interactive" / "js" / "leaderboard.js"
OG_TITLE = "Leaderboard: readers' forecasts against the result"
OG_DESCRIPTION = ("Every forecast sealed before polls opened, ranked against the result: "
                  "seats first, then wards called right, then the vote.")


class LeaderboardBuildError(SystemExit):
    """The page cannot be built; the message says what to do."""


def settings(city: str, content: Path | None = None) -> dict:
    """``{"published": bool, "top": int}`` from the city's leaderboard.toml;
    a city without the file has no leaderboard."""
    f = (content or REPO_ROOT / "content") / city / "leaderboard.toml"
    if not f.exists():
        return {"published": False, "top": 0}
    data = tomllib.loads(f.read_text(encoding="utf-8"))
    published, top = data.get("published"), data.get("top")
    if not isinstance(published, bool) or not isinstance(top, int) or top < 1:
        raise LeaderboardBuildError(f"{f}: `published` must be true or false and `top` a whole number")
    return {"published": published, "top": top}


def published(city: str, content: Path | None = None) -> bool:
    return settings(city, content)["published"]


def board(city: str, content: Path | None = None) -> dict:
    """The artefact rank_entries wrote, with ``top`` added. Refuses when the
    flag is on and there is no artefact."""
    f = (content or REPO_ROOT / "content") / city / "leaderboard.json"
    if not f.exists():
        raise LeaderboardBuildError(f"{f} does not exist: run src/rank_entries.py before "
                                    f"setting published = true")
    data = json.loads(f.read_text(encoding="utf-8"))
    for k in ("entries", "wards", "rows"):
        if k not in data:
            raise LeaderboardBuildError(f"{f} lacks {k!r}: not written by src/rank_entries.py")
    return {**data, "top": settings(city, content)["top"]}


BODY = """<main class="lb">
<p>Each forecast sealed before polls opened is one entry. Entries are ranked against the result:
seats per party first, then wards called right, then the vote per party on the list ballot. Equal on all three,
the earlier seal places higher. <a href="methodology">The measures</a> ·
<a href="privacy">How entries are kept</a></p>
<h2 id="lb-find">Find your forecast</h2>
<div class="lb-mine" data-live="lb-mine">
<form class="lb-form"><label>The link you shared <input type="text" inputmode="url" autocomplete="off"
spellcheck="false"></label><button class="btn" type="submit">Find it</button></form>
<p class="lb-found" role="status"></p>
<div class="lb-yours"></div>
</div>
<h2 id="lb-leaders">The leaders</h2>
<div class="lb-top" data-live="lb-top"></div>
</main>
"""


def assemble(shell, one_level_down) -> str:
    """The page's HTML, through build_site's ``shell`` (head, nav, footer),
    re-pointed one level down, with this page's script."""
    html = shell("Leaderboard", "Readers' forecasts", "<h1>Leaderboard</h1>", BODY,
                 "Ranked by src/rank_entries.py from every sealed forecast.", LB_HREF,
                 OG_DESCRIPTION)
    html = one_level_down(html)
    if html.count('<body class="pg-doc">') != 1 or html.count("</head>") != 1:
        raise LeaderboardBuildError("build_leaderboard: the shell's <head> or <body> changed")
    html = html.replace('<body class="pg-doc">', '<body class="pg-doc pg-board">')
    return html.replace("</head>", '<script type="module" src="js/leaderboard.js"></script>\n</head>')


def write_assets(out: Path, city: str, content: Path | None = None) -> list[str]:
    """Remove any earlier /leaderboard/; when published, write its data and
    script. Returns the paths written."""
    dest = out / LB_DIR
    if dest.exists():
        shutil.rmtree(dest)          # nothing survives a build that did not write it
    if not published(city, content):
        return []
    (dest / "js").mkdir(parents=True)
    (dest / "leaderboard.json").write_text(json.dumps(board(city, content), ensure_ascii=False),
                                           encoding="utf-8")
    shutil.copyfile(SCRIPT, dest / "js" / SCRIPT.name)
    return [f"{LB_DIR}/leaderboard.json", f"{LB_DIR}/js/{SCRIPT.name}"]

"""Shared readers for the turnout review. Read-only against the repo."""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path("/Users/simondavis/projects/atlas-jhb-election-model")
OUT = Path(__file__).resolve().parent
os.chdir(REPO)
sys.path.insert(0, str(REPO / "src"))

import cityconfig  # noqa: E402
import parties  # noqa: E402
import turnout  # noqa: E402

CITIES = ["buffalocity", "capetown", "ekurhuleni", "ethekwini", "joburg",
          "mangaung", "nelsonmandelabay", "tshwane"]
DATA = Path("data/raw/elections")


def lge_path(year: str) -> Path:
    return cityconfig.resolve_path(DATA / turnout.ELECTIONS[year][0])


def realised_turnout(year: str) -> dict[str, tuple[int, int]]:
    """VD -> (registered, cast) via turnout.read_turnout (higher ballot)."""
    fn, two = turnout.ELECTIONS[year]
    return turnout.read_turnout(DATA / fn, two)


def pr_votes(year: str) -> dict[str, dict[str, int]]:
    """VD -> party code -> PR ballot valid votes (list ballot)."""
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    fn, two = turnout.ELECTIONS[year]
    with lge_path(year).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if two and row.get("BallotType") != "PR":
                continue
            out[row["VD_Number"]][parties.canonical(row["sPartyName"])] += int(row["Party_Votes"])
    return out


def wstats(x, y, w):
    """Weighted slope of y on x (with intercept), robust (HC1) SE, weighted corr."""
    x = np.asarray(x, float); y = np.asarray(y, float); w = np.asarray(w, float)
    X = np.column_stack([np.ones_like(x), x])
    return wols(X, y, w)


def wols(X, y, w):
    X = np.asarray(X, float); y = np.asarray(y, float); w = np.asarray(w, float)
    w = w / w.mean()
    XtW = X.T * w
    A = np.linalg.inv(XtW @ X)
    beta = A @ (XtW @ y)
    e = y - X @ beta
    n, k = X.shape
    meat = (X.T * (w * e) ** 2) @ X
    V = A @ meat @ A * n / (n - k)
    return beta, np.sqrt(np.diag(V))


def wcorr(x, y, w):
    x = np.asarray(x, float); y = np.asarray(y, float); w = np.asarray(w, float)
    mx = np.average(x, weights=w); my = np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return cov / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))

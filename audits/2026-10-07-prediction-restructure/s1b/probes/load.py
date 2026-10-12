"""Shared loader for the B2 probes. Read-only: reads data/raw/elections and the
2026 crosswalk; writes nothing outside the scratch directory."""
import collections, csv, functools, glob, os, pickle, sys
REPO = "/Users/simondavis/projects/atlas-jhb-election-model"
sys.path.insert(0, REPO + "/src")
import parties  # noqa: E402

SCRATCH = os.path.dirname(os.path.abspath(__file__))
EL = REPO + "/data/raw/elections"
CITIES = ["BUF", "CPT", "EKU", "ETH", "JHB", "MAN", "NMA", "TSH"]
YEARS = ["2000", "2006", "2011", "2016", "2021"]


def read(city, year):
    """{vd: {ward, reg, wv: Counter(code->votes)}}, pr Counter(code), names"""
    path = f"{EL}/lge{year}_{city}_vd_party_clean.csv"
    vds = {}
    pr = collections.Counter()
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            code = parties.canonical(r["sPartyName"])
            v = int(r["Party_Votes"])
            b = r["BallotType"].strip().upper()
            if b == "WARD":
                d = vds.setdefault(r["VD_Number"].strip(), {"ward": r["Ward"].strip(),
                                   "reg": int(float(r["Registered_Population"] or 0)),
                                   "wv": collections.Counter()})
                d["wv"][code] += v
            elif b == "PR":
                pr[code] += v
    return vds, pr


@functools.lru_cache(None)
def all_data():
    cache = SCRATCH + "/cache.pkl"
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    data = {(c, y): read(c, y) for c in CITIES for y in YEARS}
    pickle.dump(data, open(cache, "wb"))
    return data


def ward_shares(vds):
    """{ward: {code: share}}, {ward: total valid ward votes}, {ward: registered}"""
    acc = collections.defaultdict(collections.Counter)
    reg = collections.Counter()
    for vd, d in vds.items():
        acc[d["ward"]].update(d["wv"])
        reg[d["ward"]] += d["reg"]
    out, tot = {}, {}
    for w, c in acc.items():
        t = sum(c.values())
        if t:
            out[w] = {p: v / t for p, v in c.items() if v}
            tot[w] = t
    return out, tot, reg


def prior_on(parts, prev_vds):
    """Prior ward-ballot shares on the target's wards. parts = [(vd, ward, part_reg)].
    Each target part takes its VD's previous votes times part_reg / (sum of
    the VD's part_reg in the target). Returns ({ward: {code: share}},
    {ward: (matched_reg, total_reg)}, {ward: previous turnout estimate})."""
    vd_tot = collections.Counter()
    for vd, w, r in parts:
        vd_tot[vd] += r
    acc = collections.defaultdict(collections.Counter)
    cov = collections.defaultdict(lambda: [0, 0])
    reg_m = collections.Counter(); cast = collections.Counter()
    for vd, w, r in parts:
        cov[w][1] += r
        d = prev_vds.get(vd)
        if d is None or not vd_tot[vd]:
            continue
        f = r / vd_tot[vd]
        for p, v in d["wv"].items():
            acc[w][p] += v * f
        cov[w][0] += r
        if d["reg"] > 0:
            reg_m[w] += r
            cast[w] += r * sum(d["wv"].values()) / d["reg"]
    out = {}
    for w, c in acc.items():
        t = sum(c.values())
        if t:
            out[w] = {p: v / t for p, v in c.items() if v}
    turn = {w: cast[w] / reg_m[w] for w in reg_m if reg_m[w]}
    return out, {w: tuple(v) for w, v in cov.items()}, turn


def parts_of(vds):
    """A held target's parts: every VD whole in its own ward (montecarlo.ward_parts' rule)."""
    return [(vd, d["ward"], d["reg"]) for vd, d in vds.items()]


def parts_2026():
    rows = list(csv.DictReader(open(REPO + "/data/processed/vd_ward_2026.csv")))
    return [(r["VD_Number"], r["Ward_2026"], int(r["part_registered"])) for r in rows]

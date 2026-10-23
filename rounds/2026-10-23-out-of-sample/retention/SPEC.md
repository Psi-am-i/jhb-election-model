# Second-election retention: specification and descriptive record (2026-10-23)

Design pass, read-only, 2026-10-23. The Johannesburg shares below were
re-derived from `data/raw/elections/lge*_JHB_vd_party_clean.csv` (PR ballot).

## Where 0.72 comes from

- **The record.** `levels.local_record` (`src/levels.py:877-905`): consecutive
  local-election pairs of list share, eight metros, both elections before the
  target, the party present at both. At 2026 it holds 292 ratios from 59 parties.
  The 2000 files of the seven metros other than Johannesburg are quarantined
  (`HELD_BACK`, `levels.py:282`).
- **The fit.** `size_centre` (`levels.py:1239-1293`): log ρ = a + b·log(share),
  with a = −0.3808 and b = −0.0308, R² about 0.04. At ActionSA's 0.1812 it gives
  0.7202.
- **Why ActionSA takes the line.** ActionSA has no ratio of its own, so
  `_shrunk` returns the line (`levels.py:1440-1445`).
- **ActionSA's centre, step by step:**
  1. Spine level: 0.18142 × 0.7202 = 13.07%.
  2. By-election level: 18.86%, from four contests. The cap holds it to
     (θ-prior high / mode) × the spine level = 16.33% (`montecarlo.py:2886-2888`).
  3. Blend at ½: 14.70% (`montecarlo.py:2967`).
  4. Size shrink: 14.48% (`compress_levels`, `montecarlo.py:3084-3148`).
  5. Shares made to add to 100%: 12.64% (`montecarlo.py:4570-4576`).

## The record: first local election → second, list share %, ratio

| party | pair | JHB | TSH | EKU | ETH | CPT | MAN | NMA | BUF |
|---|---|---|---|---|---|---|---|---|---|
| UDM ⚑ | 2000→06 | .81→.58 .72 | .55→.34 .62 | .80→.74 .93 | .33→.32 .98 | 1.58→.95 .60 | 1.02→.29 .29 | 2.40→1.16 .49 | 1.51→1.38 .92 |
| COPE | 2011→16 | 1.11→.21 .19 | .89→.22 .25 | 1.09→.28 .26 | .40→.14 .36 | 1.13→.24 .21 | 3.30→.56 .17 | 4.88→.70 .14 | 3.70→.99 .27 |
| APC | 2011→16 | .53→.16 .31 | .46→.24 .53 | .68→.27 .39 | .41→.26 .65 | .14→.07 .54 | .55→.25 .44 | .43→.16 .36 | – |
| Al Jama-ah | 2011→16 | .27→.31 1.15 | – | – | – | .35→.55 1.57 | – | – | – |
| AIC † | 2011→16 | – | – | – | – | – | – | – | 3.58→3.89 1.09 |
| EFF | 2016→21 | 10.93→10.11 .93 | 11.64→10.43 .90 | 11.10→13.27 1.20 | 3.63→10.80 2.98 | 3.12→4.15 1.33 | 8.84→11.37 1.29 | 5.03→6.40 1.27 | 8.21→12.37 1.51 |
| PA ‡ | 2016→21 | .17→2.96 17.3 | .09→.48 5.4 | .28→1.87 6.7 | – | .16→1.43 8.9 | – | .29→1.32 4.5 | – |
| NFP | 2011→16 | .82→absent | .07→absent | 1.13→absent | 4.48→absent | .07→absent | – | – | – |
| ID | 2006→11 | 1.94→absent | .94→absent | .98→absent | .92→absent | 11.02→absent | .72→absent | 2.57→absent | .66→absent |

- ⚑ UDM's seven non-Johannesburg rows come from the quarantined 2000 files.
- † AIC first stood in 2006, outside the metros. Under a per-metro "first" it
  would add 2016→21 in seven metros at 0.31–0.82.
- ‡ PA's first local election was 2016. All its 2016 shares are under 0.3%, so
  its ratios measure arrival, not retention.
- NFP was off the 2016 ballot. ID merged into the DA. GOOD and ATM first stood
  in 2021.
- Founding dates are from the design pass's own knowledge and are to be
  confirmed against the IEC party register.

**Size.** No second-election party is near ActionSA's 18%; the closest is EFF
at about 11%. The live record's 10–20% band has 7 ratios, median 1.196, three
of them EFF's. The line is nearly flat, so its value is set by the 0.5–10%
bands, whose medians are 0.535 and 0.516.

## ActionSA's 2026 centre for a given retention r

From the 21 October trace without the call, by arithmetic. Other parties'
levels do not depend on r. Draw means and widths need a run.

| r | spine | capped by-election level | blend | after shrink and making shares add to 100% |
|---|---|---|---|---|
| 0.20 (COPE) | 3.63 | 4.54 | 4.08 | 4.36 |
| 0.44 (APC) | 7.98 | 9.98 | 8.98 | 8.46 |
| 0.64 (UDM) | 11.61 | 14.52 | 13.06 | 11.49 |
| 0.72 (now) | 13.06 | 16.33 | 14.70 | 12.64 |
| 0.93 (EFF Johannesburg) | 16.87 | 18.86 | 17.86 | 14.76 |
| 1.00 | 18.14 | 18.86 | 18.50 | 15.17 |
| 1.26 (EFF pooled) | 22.86 | 18.86 | 20.86 | 16.67 |

From about r = 0.83 upward the cap does not bind.

## Limits

- The effective sample is the number of parties.
- The record splits into two groups, collapse (COPE, APC, UDM) and growth (EFF,
  AIC, Al Jama-ah, PA), so one median describes neither.
- Exits are excluded, which biases the ratios upward as a description of new
  parties.
- ActionSA's by-elections are already in its centre at ½; they are a check on
  any retention value, not more data.

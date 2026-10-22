#!/bin/sh
# Every backtest city-year with an emitted spec, then the controls.
# Usage: run_all.sh <draws>   (setup.sh must have been run first)
set -e
REPO=$(cd "$(dirname "$0")/../.." && pwd)
DRAWS=${1:-2000}
SRC=/tmp/zc_src/src; OUT="$REPO/audits/2026-09-29-zero-cells/results"
mkdir -p "$OUT"; cp /tmp/zc_src/COMMIT "$OUT/COMMIT"
cd "$REPO"
export VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
for c in joburg tshwane ekurhuleni ethekwini capetown mangaung nelsonmandelabay buffalocity; do
  for y in 2011 2016 2021; do
    if [ "$c" = joburg ]; then f=data/processed/pools_$y.json; else f=data/processed/$c/pools_$y.json; fi
    [ -f "$f" ] && echo "$c $y"
  done
done > "$OUT/panel.txt"
wc -l "$OUT/panel.txt"
xargs -P 8 -n 2 sh -c '.venv/bin/python audits/2026-09-29-zero-cells/zero_cells.py --src '"$SRC"' --city "$0" --year "$1" --draws '"$DRAWS"' --out '"$OUT"' > '"$OUT"'/"$0-$1".log 2>&1 || echo "FAILED $0 $1"' < "$OUT/panel.txt"
.venv/bin/python audits/2026-09-29-zero-cells/zero_cells.py --src "$SRC" --city joburg --year 2021 --draws 1000 --out "$OUT" --control plant > "$OUT/control-plant.log" 2>&1

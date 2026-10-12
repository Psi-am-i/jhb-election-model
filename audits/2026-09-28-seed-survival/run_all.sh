#!/bin/sh
# Re-run F2 over every emitted spec. Usage: run_all.sh <commit> <draws>
# Archives <commit>'s src/ so the live tree is never imported.
set -e
REPO=$(cd "$(dirname "$0")/../.." && pwd)
COMMIT=${1:-HEAD}; DRAWS=${2:-2000}
SRC=/tmp/seedsurv_src; OUT=/tmp/seedsurv_out
rm -rf "$SRC" && mkdir -p "$SRC" "$OUT"
(cd "$REPO" && git archive "$COMMIT" src | tar -x -C "$SRC" && git rev-parse "$COMMIT" > "$OUT/COMMIT")
cd "$REPO"
export VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
for c in joburg tshwane ekurhuleni ethekwini capetown mangaung nelsonmandelabay buffalocity; do
  for y in 2011 2016 2021 2026; do
    if [ "$c" = joburg ]; then f=data/processed/pools_$y.json; else f=data/processed/$c/pools_$y.json; fi
    [ -f "$f" ] && echo "$c $y"
  done
done | xargs -P 8 -n 2 sh -c '.venv/bin/python audits/2026-09-28-seed-survival/seed_survival.py --src '"$SRC"'/src --city "$0" --year "$1" --draws '"$DRAWS"' --out '"$OUT"' > '"$OUT"'/"$0-$1".log 2>&1 || echo "FAILED $0 $1"'
.venv/bin/python audits/2026-09-28-seed-survival/tabulate.py "$OUT"

#!/bin/zsh
# POOLS-REEMIT-QUEUE.md step 2's loop, verbatim, in the current tree.
set -e
export PYTHONHASHSEED=0
for c in joburg tshwane ekurhuleni ethekwini capetown mangaung \
         nelsonmandelabay buffalocity; do
  for y in 2011 2016 2021; do
    .venv/bin/python src/pools.py --city $c --target $y --emit
  done
done
.venv/bin/python src/pools.py --city joburg --target 2026 --emit
.venv/bin/python src/pools.py --city joburg --target 2026 --simulation --emit
.venv/bin/python src/pools.py --city tshwane --target 2026 --emit

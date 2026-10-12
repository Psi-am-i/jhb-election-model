#!/bin/zsh
cd /Users/simondavis/projects/jhb-election-model
tag=$1; src=$2
mkdir -p /tmp/f3/$tag
jobs_list=()
for c in joburg tshwane ekurhuleni ethekwini capetown mangaung nelsonmandelabay buffalocity; do
  for y in 2011 2016 2021; do jobs_list+=("$c $y"); done
done
jobs_list+=("joburg 2026" "tshwane 2026")
printf '%s\n' "${jobs_list[@]}" | xargs -P 8 -L 1 zsh -c '.venv/bin/python /tmp/f3/build_spec.py '"$src"' $0 $1 /tmp/f3/'"$tag"'/$0_$1.json'

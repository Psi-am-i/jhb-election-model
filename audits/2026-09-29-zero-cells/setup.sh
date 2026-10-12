#!/bin/sh
# Archive <commit>'s src/ to /tmp/zc_src and add ONE instrumentation hook to the
# archived montecarlo.py (never the live tree). The hook hands the draw loop's
# locals to a callback after the ward winners are taken; it reads, it does not
# write, and with no callback installed it is a no-op.
set -e
REPO=$(cd "$(dirname "$0")/../.." && pwd)
COMMIT=${1:-022f8d4}
SRC=/tmp/zc_src
rm -rf "$SRC" && mkdir -p "$SRC"
(cd "$REPO" && git archive "$COMMIT" src | tar -x -C "$SRC")
F="$SRC/src/montecarlo.py"
n=$(grep -c '^        winners = ward_tally.argmax(axis=1)$' "$F")
[ "$n" = 1 ] || { echo "anchor found $n times, expected 1"; exit 1; }
/usr/bin/sed -i '' '/^        winners = ward_tally.argmax(axis=1)$/a\
        _zc = globals().get("_ZC_HOOK")\
        if _zc is not None:\
            _zc(locals())
' "$F"
echo "$COMMIT" > "$SRC/COMMIT"
diff <(cd "$REPO" && git show "$COMMIT:src/montecarlo.py") "$F" || true

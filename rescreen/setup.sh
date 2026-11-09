#!/bin/bash
# One-time setup for the rescreen. Safe to re-run: it skips whatever is already in place.
#
#   rescreen/setup.sh
#   source rescreen/env.sh
#
# It checks out abismal at the commit the plan uses, downloads any benchmark data that is missing (cxidb 81, 61, 62 and
# HEWL from careless-examples, through each dataset's data/*/download.sh), checks that every file the runs read exists,
# checks that $PY can import abismal and TorchRef, and writes rescreen/env.sh.
#
# Optional environment:
#   PY        python to use (default: the python on PATH). Needs torch, reciprocalspaceship, gemmi and torchref 0.6.3
#   ABISMAL   an existing abismal checkout to use instead of cloning one into rescreen/abismal
#   DATA      an existing copy of the benchmark data/ tree to use instead of this repo's data/ (nothing is downloaded
#             into it; it must already hold the files listed below)
set -eu
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BENCH=$(dirname "$HERE")
COMMIT=419fae8
ABISMAL=${ABISMAL:-$HERE/abismal}
DATA=${DATA:-$BENCH/data}
PY=${PY:-$(command -v python)}

echo "== abismal at $COMMIT in $ABISMAL"
[ -e "$ABISMAL/.git" ] || git clone https://github.com/rs-station/abismal "$ABISMAL"
git -C "$ABISMAL" fetch -q origin posterior-trend-aniso || echo "(fetch failed; using the commit if the checkout already has it)"
git -C "$ABISMAL" -c advice.detachedHead=false checkout -q "$COMMIT"
git -C "$ABISMAL" log --oneline -1

echo "== data in $DATA"
FILES="hewl/reflection_data/unmerged.mtz
cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.expt
cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl
cxidb_61/reflection_data/all.stream
cxidb_62/reflection_data/all-amb-scrambled-sigfix.stream
hewl/reference_data/RTSAD_HEWL_refine_25.pdb hewl/reference_data/r-free-flags.mtz
cxidb_81/reference_data/2tli.pdb cxidb_81/reference_data/r-free-flags.mtz
cxidb_61/reference_data/5xfc_mr.pdb cxidb_61/reference_data/r-free-flags.mtz
cxidb_62/reference_data/5xfd.pdb cxidb_62/reference_data/5xfd_phases.mtz cxidb_62/reference_data/r-free-flags.mtz"
if [ "$DATA" = "$BENCH/data" ]; then
    export ABISMAL_BENCHMARKS=$BENCH
    for pair in hewl:hewl/reflection_data/unmerged.mtz \
                cxidb_81:cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl \
                cxidb_61:cxidb_61/reflection_data/all.stream \
                cxidb_62:cxidb_62/reflection_data/all-amb-scrambled-sigfix.stream; do
        ds=${pair%%:*}; f=${pair#*:}
        [ -e "$DATA/$f" ] || { echo "downloading $ds"; (bash "$DATA/$ds/download.sh"); }
    done
fi
missing=0
for f in $FILES; do [ -e "$DATA/$f" ] || { echo "MISSING $DATA/$f"; missing=1; }; done
[ $(ls "$DATA"/cxidb_81/reflection_data/figure7/*.refl 2>/dev/null | wc -l) -gt 1 ] || { echo "MISSING the full cxidb_81 figure7 set"; missing=1; }
[ $missing = 0 ] || { echo "data incomplete"; exit 1; }
echo "all data present"

echo "== python $PY"
mkdir -p "$HERE/runs"
(cd "$HERE/runs" && PYTHONPATH=$ABISMAL "$PY" -c "
import torch, gemmi, reciprocalspaceship, torchref, abismal
from abismal.command_line.abismal import main
print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), '| torchref', getattr(torchref, '__version__', '?'), '| abismal from', abismal.__file__)")

cat > "$HERE/env.sh" <<EOF
# written by rescreen/setup.sh
export ABISMAL=$ABISMAL
export BENCH=$BENCH
export DATA=$DATA
export PY=$PY
export OUT=\${OUT:-$HERE/runs}
export PATH=$HERE:\$PATH
EOF
echo "== wrote $HERE/env.sh; next: source rescreen/env.sh"

#!/bin/bash
# Measure finished rescreen runs on one CPU node: measure_runs.py on each run in parallel, one CSV per run in
# $OUT/measure/, then all of them concatenated into OUTCSV.
#
#   sbatch --export=ALL,RESCREEN=$PWD/rescreen rescreen/slurm/measure.sbatch OUTCSV RUNDIR...
#
# A run that already has $OUT/measure/<run>.csv is not measured again; delete that file to redo it.
#SBATCH -A m5149
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH -t 01:00:00
#SBATCH -J rescreen_measure
set -u
OUTCSV=$(readlink -f "$1"); shift
source "$RESCREEN/env.sh"
M=$OUT/measure; mkdir -p "$M"
cd "$OUT"   # never run python from inside the abismal checkout
export M PY RESCREEN
measure_one() {
    local run=${1%/} name; name=$(basename "$run")
    [ -s "$M/$name.csv" ] && return
    OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 $PY "$RESCREEN/measure_runs.py" "$M/$name.csv.tmp" "$run" > "$M/$name.log" 2>&1 \
        && mv "$M/$name.csv.tmp" "$M/$name.csv" || echo "measure failed: $name (see $M/$name.log)"
}
export -f measure_one
printf '%s\n' "$@" | xargs -P 48 -I{} bash -c 'measure_one {}'
$PY -c "
import sys, glob, pandas as pd
fs = sorted(glob.glob('$M/*.csv'))
pd.concat([pd.read_csv(f) for f in fs], ignore_index=True).to_csv('$OUTCSV', index=False)
print(len(fs), 'runs measured ->', '$OUTCSV')"

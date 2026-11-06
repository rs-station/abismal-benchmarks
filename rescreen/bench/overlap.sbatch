#!/bin/bash
# B. Does refinement in the training callback slow training? Four hewl trainings, one per A100, each its own bound
# task (-c 32 = 16 cores). One without refinement; three refining every epoch (--torchref-allow-overlap) at
# TORCHREF_NUM_THREADS 2, 4, 8. Compare per-epoch times in history.csv.
#SBATCH -A m5149_g -C gpu -q debug -N 1 --ntasks-per-node=4 -c 32 --gpus-per-node=4 -t 00:30:00
set -u
source $RESCREEN/env.sh
export OUT=$RESCREEN/bench/overlap_$SLURM_JOB_ID; mkdir -p $OUT
D=$DATA/hewl/reference_data
TR="--torchref-pdb $D/RTSAD_HEWL_refine_25.pdb --torchref-wavelength 1.892 --r-free-mtz $D/r-free-flags.mtz --torchref-frequency 1 --torchref-allow-overlap"
EP="--epochs 6"
export TORCH_EXTENSIONS_DIR=/tmp/torch_ext_$SLURM_JOB_ID
mkdir -p $TORCH_EXTENSIONS_DIR && cp -a ~/.cache/torch_extensions/. $TORCH_EXTENSIONS_DIR/
# load sampled every 10 s, to see how many refinements overlap
( while true; do echo "$(date +%T) $(cut -d' ' -f1-3 /proc/loadavg) workers=$(pgrep -fc _torchref_worker)"; sleep 10; done ) > $OUT/load.txt &
STAGE=train srun -n1 -c 32 --cpu-bind=cores --gpus-per-task=1 --exact $RESCREEN/run_one.sh hewl_norefine 1 $EP &
for t in 2 4 8; do
    STAGE=train TORCHREF_NUM_THREADS=$t srun -n1 -c 32 --cpu-bind=cores --gpus-per-task=1 --exact \
        $RESCREEN/run_one.sh hewl_refine$t 1 $EP $TR &
done
wait %2 %3 %4 %5
kill %1
for r in $OUT/hewl_*_s1; do
    echo "== $(basename $r)"; cut -d, -f1,2 $r/history.csv
    for d in $r/torchref_0_asu_0_epoch_*; do echo "$(basename $d) $(grep -c . $d/peaks.csv 2>/dev/null) peaks"; done
done

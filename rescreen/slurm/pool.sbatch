#!/bin/bash
# The rescreen work pool: one job, N GPU nodes, one worker task per A100, all in ONE srun step. Each worker claims runs
# from MANIFEST until none is left that fits in the remaining time (see pool_worker.sh), refining as it trains.
#
#   sbatch -N NODES -t HH:MM:SS --export=ALL,RESCREEN=$PWD/rescreen rescreen/slurm/pool.sbatch MANIFEST
#
# Re-submitting the same manifest resumes it: finished runs are skipped, and a run whose job died before it finished
# (a claim with no "done" whose job is no longer running) has its claim released and its partial output moved to
# $OUT/stale/, so it is trained again from scratch.
#
# Why one step: separate `srun` steps each take the whole job's memory by default and so run one at a time
# (rescreen/bench, 2026-11-06). A single step with one task per GPU gives every task its own GPU and 16 cores.
#SBATCH -A m5149_g
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -J rescreen_pool
set -u
MANIFEST=$(readlink -f "$1")
source "$RESCREEN/env.sh"
CLAIMS=$OUT/claims; mkdir -p "$CLAIMS" "$OUT/stale"
echo "$(date '+%F %T') pool job $SLURM_JOB_ID: $SLURM_JOB_NUM_NODES nodes ($SLURM_JOB_NODELIST), manifest $MANIFEST"

# Release stale claims: no "done", and the owning job is not this one and is no longer running.
for c in "$CLAIMS"/*/; do
    [ -d "$c" ] || continue
    c=${c%/}; run=$(basename "$c")
    [ -e "$c/done" ] && continue
    owner=$(awk '{print $2}' "$c/owner" 2>/dev/null)
    [ "$owner" = "$SLURM_JOB_ID" ] && continue
    [ -n "$owner" ] && [ -n "$(squeue -h -j "$owner" 2>/dev/null)" ] && continue
    stamp=$(date +%Y%m%d-%H%M%S)
    [ -e "$OUT/$run" ] && mv "$OUT/$run" "$OUT/stale/${run}_$stamp"
    [ -e "$OUT/$run.log" ] && mv "$OUT/$run.log" "$OUT/stale/${run}_$stamp.log"
    mv "$c" "$OUT/stale/${run}_${stamp}.claim"
    echo "released stale claim $run (owner job ${owner:-?})"
done

srun -n $((4 * SLURM_JOB_NUM_NODES)) -c 32 --cpu-bind=cores --gpus-per-task=1 \
    "$RESCREEN/slurm/pool_worker.sh" "$MANIFEST"
echo "$(date '+%F %T') pool job $SLURM_JOB_ID finished"
echo "claims: $(ls "$CLAIMS" | wc -l), done: $(ls "$CLAIMS"/*/done 2>/dev/null | wc -l), failed: $(cat "$CLAIMS"/*/done 2>/dev/null | awk '$1 != 0' | wc -l)"

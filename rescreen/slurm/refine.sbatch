#!/bin/bash
# Refine the epoch merges of up to four trained rescreen runs on one Perlmutter CPU node (128 cores).
#   sbatch rescreen/slurm/refine.sbatch LIST
# Each run gets a quarter of the node (32 cores) and refines its epochs concurrently with THREADS=8 each, so 3 epochs
# (phase 1) use 24 cores and 4 epochs (phase 2, 20 epochs) use 32. A run whose training failed refines whatever epoch
# MTZs it wrote, and its failure is in runs.log.
#SBATCH -A m5149
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 64
#SBATCH -t 01:30:00
set -u
LIST=$1
source "$RESCREEN/env.sh"
echo "$(date) job $SLURM_JOB_ID on $(hostname) refining $(wc -l < $LIST) runs from $LIST"
while IFS=$'\t' read -r name seed flags; do
    [ -n "$name" ] || continue
    STAGE=refine REFINE_PARALLEL=1 THREADS=8 srun -n1 -c 64 --cpu-bind=cores --exact \
        "$RESCREEN/run_one.sh" "$name" "$seed" &
done < "$LIST"
wait
echo "$(date) job $SLURM_JOB_ID finished"

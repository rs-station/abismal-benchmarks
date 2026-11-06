#!/bin/bash
# Train up to four rescreen runs on one Perlmutter GPU node, one run per A100, each in its own bound job step.
#   sbatch [-t HH:MM:SS] rescreen/slurm/train.sbatch LIST
# LIST holds manifest lines (name<TAB>seed<TAB>flags). Refinement is a separate CPU job (refine.sbatch); submit.sh
# chains the two. Submitted through submit.sh, which sets the account, time and log paths.
#SBATCH -A m5149_g
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -t 03:00:00
set -u
LIST=$1
source "$RESCREEN/env.sh"
echo "$(date) job $SLURM_JOB_ID on $(hostname) training $(wc -l < $LIST) runs from $LIST"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
while IFS=$'\t' read -r name seed flags; do
    [ -n "$name" ] || continue
    # $flags is unquoted on purpose: it is a list of abismal flags with no quoted arguments.
    STAGE=train srun -n1 -c 32 --cpu-bind=cores --gpus-per-task=1 --exact \
        "$RESCREEN/run_one.sh" "$name" "$seed" $flags &
done < "$LIST"
wait
echo "$(date) job $SLURM_JOB_ID finished"

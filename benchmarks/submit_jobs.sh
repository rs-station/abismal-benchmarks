################################################################################
# Submit all available benchmarks as a slurm job array
################################################################################

JOBNAME=abismal
NUM_JOBS=`ls config | wc -l`

sbatch --array=0-$((NUM_JOBS-1)) --job-name=$JOBNAME job.sh


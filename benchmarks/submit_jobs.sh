################################################################################
# Submit all available benchmarks as a slurm job array
################################################################################

JOBNAME=abismal
NUM_JOBS=`ls {config,ablations}/*.sh | wc -l`

echo "Submitting $NUM_JOBS benchmarks with slurm job array ..."
sbatch --array=0-$((NUM_JOBS-1)) --job-name=$JOBNAME job.sh
echo "Finished!"


#!/bin/bash
#SBATCH --partition=ampere
#SBATCH --account=lcls:prjlumine22
#SBATCH -N 1
#SBATCH -c 16
#SBATCH -G 1
#SBATCH --mem=96G
#SBATCH -t 0-12:00
#SBATCH -o ../log/slurm_%A_%a.out


#Set up conda env
source ../setup.sh

#0 - silent
#1 - progress bar
#2 - one line per epoch
KERAS_VERBOSITY=2
num_epochs=100

################################################################################
# Base parameters for all tests
BASE_PARAMS=(
  --normalizer=rms
  --optimizer=adam
  --mc-samples=32
  --init-scale=1.0
  --prior-distribution=wilson
  --posterior-type=structure_factor
  --posterior-distribution=foldednormal
  --keras-verbosity=$KERAS_VERBOSITY #one line per epoch
  --shuffle-buffer=10_000
  --scale-posterior-bijector=softplus
  --scale-posterior-distribution=foldednormal
  --scale-prior-distribution=lognormal
  --studentt-dof=32
  --activation=relu
  --kl-weight=1e0
  --scale-kl-weight=1e0
  --batch-size=100
  --d-model=32
  --layers=20
  --test-fraction=0.1
  --num-cpus=10
  --phenix-frequency=1
  --epsilon=1e-12
  --adam-epsilon=1e-7
  --epochs=$num_epochs
  --learning-rate=1e-3
  --beta-1=0.9
  --beta-2=0.999
)

################################################################################
# Parameters governing post-training crossvalidation run 
CCHALF_PARAMS=(
    --keras-verbosity=$KERAS_VERBOSITY #one line per epoch
)

###################################################################
# BENCHMARKCONFIG sets the important parameters for each benchmark
# by setting the following shell variables
# - INPUTS (a bash array of files)
# - EFFS (a bash array of file)
# - BENCHMARKNAME (a descriptive name of this benchmark)
# - EXPERIMENT_PARAMS (a bash array of abismal CLI params)
if [[ "$#" -gt 0 ]]; then
    echo "Loading user supplied config..."
    BENCHMARKCONFIG=$1
elif [ -n ${SLURM_ARRAY_TASK_ID} ]; then
    #Find all available benchmark config files
    ALLCONFIG=(`ls $ABISMAL_BENCHMARKS/benchmarks/config`)
    echo "Listing available configs..."
    for conf in ${ALLCONFIG[@]};do
        echo " - $conf"
    done

    echo "Choosing config from job array task ID..."

    #Select one based on the job array task id
    BENCHMARKCONFIG=$ABISMAL_BENCHMARKS/benchmarks/config/${ALLCONFIG[$SLURM_ARRAY_TASK_ID]}
else
    echo "Failed to determine config file location, exitting..."
    exit
fi


echo "Selected config .."
echo " - $BENCHMARKCONFIG"
source $BENCHMARKCONFIG

# Allow BENCHMARKCONFIG to overload OUTDIR
if [[ -z $OUTDIR ]]; then
    echo "OUTDIR is unset, using default..."
    OUTDIR=$ABISMAL_BENCHMARKS/results/job_$SLURM_ARRAY_JOB_ID/$BENCHMARKNAME
fi

echo "Time: $(date)"
echo "Running on node: $HOSTNAME"
nvidia-smi

if [[ -v EFFS ]]; then
    # Join EFFS with comma
    SAVEIFS="$IFS"
    IFS=","
    EFFS="${EFFS[*]}"
    IFS="$SAVEIFS"
    echo "Adding PHENIX configs from"
    echo " - $EFFS"
    EXPERIMENT_PARAMS+=( --eff-files $EFFS )
fi

# Prepare output dir
echo "Output will be written to..."
echo "- $OUTDIR"
mkdir -p $OUTDIR
cp $0 $OUTDIR/merge.sh

echo "Base parameters from env:"
echo "${BASE_PARAMS[@]}"

echo "Experiment parameters from env:"
echo "${EXPERIMENT_PARAMS[@]}"

if [[ -v REFERENCE_MTZ ]]; then
    echo "Setting reference mtz as: $REFERENCE_MTZ"
    EXPERIMENT_PARAMS+=( --reference-mtz=$REFERENCE_MTZ )
    CCHALF_PARAMS+=( --reference-mtz=$REFERENCE_MTZ )
fi

abismal  \
    "${BASE_PARAMS[@]}" \
    "${EXPERIMENT_PARAMS[@]}" \
    -o $OUTDIR \
    ${INPUTS[@]} 


echo "################################################################################"
echo "# Training ended... starting CChalf calculation"
echo "################################################################################"
cd $OUTDIR
checkpoint_file=`ls -t epoch_*.keras | head -1`
abismal.cchalf \
    "${CCHALF_PARAMS[@]}" \
    --sf-init epoch_0.keras \
    datamanager.yml \
    $checkpoint_file



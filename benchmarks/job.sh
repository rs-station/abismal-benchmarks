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
OUTDIR=$ABISMAL_BENCHMARKS/results/torchref/$BENCHMARKNAME

#0 - silent
#1 - progress bar
#2 - one line per epoch
KERAS_VERBOSITY=1
num_epochs=100

################################################################################
# Base parameters for all tests
ABISMAL_BASE_PARAMS=(
    --keras-verbosity=$KERAS_VERBOSITY #one line per epoch
    --num-cpus=10
    --early-stopping-criterion=KL
    --early-stopping-patience=$num_epochs
    --epochs=$num_epochs
    --anomalous
    --optimizer='Adabelief'
    --beta-1=0.9
    --beta-2=0.999
    --learning-rate=1e-3
    --adam-epsilon=1e-7
    --epsilon=1e-12
    --ff-epsilon=0.0
    --normalizer-gain=1.0
    --normalizer='activation'
    --activation='relu'
    #--jit-compile
    #--pre-activation='relu'
    --batch-normalize #commented means no instance norm
    #--gated
    #--dropout=0.9
    #--sample-reflections-per-image=8
    --init-scale=1.0
    --mc-samples=32
    --layers=5
    --d-model=256
    --batch-size=100
    --kl-weight=1e0
    --scale-kl-weight=1e0
##################################################
## Structure Factor parameterization
    --posterior-type='structure_factor'
    #--prior-distribution='auto_wilson'
    --prior-distribution='wilson'
    --posterior-distribution='foldednormal'
##################################################
## Scale parameterization
    --scale-prior-distribution='lognormal'
    --scale-posterior-distribution='foldednormal'
    --scale-posterior-bijector='softplus'
    --studentt-dof=32
    #--debug
    #--run-eagerly
    #--embed
    #--optimize-scale-prior
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
    ALLCONFIG=(`ls $ABISMAL_BENCHMARKS/benchmarks/config/*.sh`)
    echo "Listing available configs..."
    for conf in ${ALLCONFIG[@]};do
        echo " - $conf"
    done

    echo "Choosing config from job array task ID..."
    #Select one based on the job array task id
    BENCHMARKCONFIG=${ALLCONFIG[$SLURM_ARRAY_TASK_ID]}
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
    if [[ -z $SLURM_ARRAY_JOB_ID ]]; then
        SLURM_ARRAY_JOB_ID=`date +%Y%m%d`
    fi
    OUTDIR=$ABISMAL_BENCHMARKS/results/job_$SLURM_ARRAY_JOB_ID
fi
OUTDIR=$OUTDIR/$BENCHMARKNAME

echo "Time: $(date)"
echo "Running on node: $HOSTNAME"
nvidia-smi

# Refinement during training is driven by torchref: set PDBS in the benchmark
# config to a list of starting models. On anomalous data the torchref worker
# also builds an anomalous difference map and writes peaks.csv per epoch, so
# PDBS alone covers what EFFS used to do via phenix.refine + rs.find_peaks.
if [[ -v PDBS ]]; then
    # Join PDBS with comma
    SAVEIFS="$IFS"
    IFS=","
    PDBS="${PDBS[*]}"
    IFS="$SAVEIFS"
    echo "Adding torchref starting models from"
    echo " - $PDBS"
    EXPERIMENT_PARAMS+=( --torchref-pdb=$PDBS )
fi

# A fixed R-free set. Without one torchref invents a fresh random set on every
# epoch, which makes Rfree noisy and incomparable to a phenix run. RFREE_VALUE
# is the integer marking a free reflection; every r-free-flags.mtz under data/
# uses 1, and it is inferred anyway for two-valued flag columns, so configs
# only need to set it for multi-bin flag sets.
if [[ -v RFREE ]]; then
    echo "Adding fixed R-free flags from"
    echo " - $RFREE"
    EXPERIMENT_PARAMS+=( --r-free-mtz=$RFREE )
    if [[ -v RFREE_VALUE ]]; then
        EXPERIMENT_PARAMS+=( --r-free-value=$RFREE_VALUE )
    fi
fi

# Experimental wavelength, driving torchref's f'/f'' anomalous correction.
# Unset leaves torchref's default of 1.0 Angstrom.
if [[ -v WAVELENGTH ]]; then
    echo "Setting torchref wavelength to $WAVELENGTH A"
    EXPERIMENT_PARAMS+=( --torchref-wavelength=$WAVELENGTH )
fi

# EFFS (phenix.refine) is still honored for configs that have not been ported,
# such as those under benchmarks/ablations.
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

# Avoid overwriting an existing output dir by appending _N
if [[ -d $OUTDIR ]]; then
    _N=1
    while [[ -d ${OUTDIR}_${_N} ]]; do
        (( _N++ ))
    done
    OUTDIR=${OUTDIR}_${_N}
fi

# Prepare output dir
echo "Output will be written to..."
echo "- $OUTDIR"
mkdir -p $OUTDIR
cp $0 $OUTDIR/merge.sh

echo "Base parameters from env:"
echo "${ABISMAL_BASE_PARAMS[@]}"

echo "Experiment parameters from env:"
echo "${EXPERIMENT_PARAMS[@]}"

if [[ -v REFERENCE_MTZ ]]; then
    echo "Setting reference mtz as: $REFERENCE_MTZ"
    EXPERIMENT_PARAMS+=( --reference-mtz=$REFERENCE_MTZ )
    CCHALF_PARAMS+=( --reference-mtz=$REFERENCE_MTZ )
fi

cd ~/opt/abismal
git diff --output=$OUTDIR/diff.txt
cd -

abismal  \
    "${ABISMAL_BASE_PARAMS[@]}" \
    "${EXPERIMENT_PARAMS[@]}" \
    -o $OUTDIR \
    ${INPUTS[@]} 


#echo "################################################################################"
#echo "# Training ended... starting CChalf calculation"
#echo "################################################################################"
#cd $OUTDIR
#checkpoint_file=`ls -t epoch_*.keras | head -1`
#abismal.cchalf \
#    "${CCHALF_PARAMS[@]}" \
#    --sf-init epoch_0.keras \
#    datamanager.yml \
#    $checkpoint_file
#
#

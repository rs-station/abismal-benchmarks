#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source /home/kmdalton/opt/phenix-1.21.2-5419/phenix_env.sh
source ~/opt/anaconda/etc/profile.d/conda.sh
conda activate abismal

# The env above provides abismal + PHENIX but not torchref. TorchRefRunner
# launches its worker as a separate process, so point it at an interpreter that
# has torchref installed rather than trying to merge the two environments.
ABISMAL_TORCHREF_PYTHON=$HOME/micromamba/envs/abismal-torchref/bin/python
if [[ -x $ABISMAL_TORCHREF_PYTHON ]]; then
    export ABISMAL_TORCHREF_PYTHON
    echo "    ABISMAL_TORCHREF_PYTHON=$ABISMAL_TORCHREF_PYTHON"
else
    unset ABISMAL_TORCHREF_PYTHON
    echo "WARNING: no torchref interpreter found; --torchref-pdb runs will fail."
fi


# Handle ./setup.sh and source setup.sh
[[ $0 != $BASH_SOURCE ]] && 
    ABISMAL_BENCHMARKS=`dirname $BASH_SOURCE` ||
    ABISMAL_BENCHMARKS=`dirname $0` 

export ABISMAL_BENCHMARKS=`readlink -f $ABISMAL_BENCHMARKS`
echo "setting..." 
echo "    ABISMAL_BENCHMARKS=$ABISMAL_BENCHMARKS"

download_examples() {
    for script_file in $ABISMAL_BENCHMARKS/data/*/download.sh;do
        source $script_file
    done
}

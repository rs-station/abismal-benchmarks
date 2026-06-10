#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source /home/kmdalton/opt/phenix-1.21.2-5419/phenix_env.sh
source ~/opt/anaconda/etc/profile.d/conda.sh
conda activate abismal


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

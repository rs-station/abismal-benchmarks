#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source ~/tools/abismal/setup.sh

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

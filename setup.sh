#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source ~/tools/abismal/setup.sh

# Handle ./setup.sh and source setup.sh
[[ $0 != $BASH_SOURCE ]] && 
    ABISMALDIR=`dirname $BASH_SOURCE` ||
    ABISMALDIR=`dirname $0` 

export ABISMALDIR=`readlink -f $ABISMALDIR`
echo "setting..." 
echo "    ABISMALDIR=$ABISMALDIR"

download_examples() {
    for script_file in $ABISMALDIR/data/*/download.sh;do
        source $script_file
    done
}

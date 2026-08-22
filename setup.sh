#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source /home/kmdalton/opt/phenix-1.21.2-5419/phenix_env.sh
# Fall back to the standard install locations when the shell has not already
# exported these (a non-interactive shell does not source ~/.bashrc).
: "${MAMBA_EXE:=$HOME/opt/micromamba/bin/micromamba}"
: "${MAMBA_ROOT_PREFIX:=$HOME/micromamba}"
export MAMBA_EXE MAMBA_ROOT_PREFIX
eval "$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX")"
micromamba activate abismal

# abismal, DIALS and torchref all live in the `abismal` environment now, so
# --torchref-pdb runs in the interpreter this script just activated. There is no
# second environment and no ABISMAL_TORCHREF_PYTHON to point at one.
#
# The environment is still worth checking up front. The torchref worker finds
# anomalous peaks with skimage's peak_local_max, and the peak finder runs *after*
# refinement, so a missing import costs a full macrocycle set per epoch before
# anything fails. Rebuild with `pip install -e ".[dev,torchref]"` if this warns.
check_abismal_env() {
    python - <<'EOF'
from importlib.util import find_spec

missing = [m for m in ("torchref", "skimage", "dxtbx", "tensorflow")
           if find_spec(m) is None]
if missing:
    print(f"WARNING: abismal env is missing {', '.join(missing)}. "
          f"Reinstall with: pip install -e \".[dev,torchref]\"")
else:
    import numpy, tensorflow, torch
    print(f"    abismal env ok (numpy {numpy.__version__}, "
          f"tensorflow {tensorflow.__version__}, torch {torch.__version__})")
EOF
}
check_abismal_env

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

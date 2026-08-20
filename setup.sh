#!/bin/bash

#EDIT setup script location:
#Script provides abismal and PHENIX
source /home/kmdalton/opt/phenix-1.21.2-5419/phenix_env.sh
source ~/opt/anaconda/etc/profile.d/conda.sh
conda activate abismal

# The torchref worker finds anomalous peaks with skimage's peak_local_max, so
# scikit-image is a hard dependency of the peak-finding half of a --torchref-pdb
# run. It is worth checking up front: the peak finder runs *after* refinement, so
# a missing import costs a full macrocycle set per epoch before anything fails.
#
# The install is a footgun. `pip install scikit-image` on its own drags numpy up
# to 2.5, which breaks tensorflow (needs <2.1.0) and torchref (needs <2.4.0), so
# the abismal side of the benchmark stops importing. Pin numpy when installing:
#
#   micromamba run -n abismal-torchref pip install \
#       "numpy==2.0.2" "scikit-image==0.24.0"
#
# Those are the versions this benchmark suite is known good against.
TORCHREF_NUMPY_MAX="2.4.0"
check_torchref_env() {
    $ABISMAL_TORCHREF_PYTHON - "$TORCHREF_NUMPY_MAX" <<'EOF'
import sys
from importlib.util import find_spec

numpy_max = sys.argv[1]
ok = True

try:
    import numpy
except ImportError:
    print("WARNING: torchref env has no numpy.")
    ok = False
else:
    have = tuple(int(x) for x in numpy.__version__.split('.')[:3])
    want = tuple(int(x) for x in numpy_max.split('.')[:3])
    if have >= want:
        print(
            f"WARNING: torchref env has numpy {numpy.__version__}; torchref "
            f"needs <{numpy_max}. Reinstall with numpy pinned (numpy==2.0.2)."
        )
        ok = False

if find_spec("skimage") is None:
    print(
        "WARNING: torchref env has no scikit-image; anomalous peak finding "
        "will fail after refinement. Install it WITH numpy pinned:\n"
        '    pip install "numpy==2.0.2" "scikit-image==0.24.0"'
    )
    ok = False

if ok:
    import skimage
    print(f"    torchref env ok (numpy {numpy.__version__}, "
          f"scikit-image {skimage.__version__})")
EOF
}

# The env above provides abismal + PHENIX but not torchref. TorchRefRunner
# launches its worker as a separate process, so point it at an interpreter that
# has torchref installed rather than trying to merge the two environments.
ABISMAL_TORCHREF_PYTHON=$HOME/micromamba/envs/abismal-torchref/bin/python
if [[ -x $ABISMAL_TORCHREF_PYTHON ]]; then
    export ABISMAL_TORCHREF_PYTHON
    echo "    ABISMAL_TORCHREF_PYTHON=$ABISMAL_TORCHREF_PYTHON"
    check_torchref_env
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

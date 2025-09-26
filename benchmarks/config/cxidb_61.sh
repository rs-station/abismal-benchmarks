BENCHMARKNAME=cxidb_61
INPUTS=(
    $ABISMALDIR/data/cxidb_61/reflection_data/all.stream
)

EFFS=(
    $ABISMALDIR/data/cxidb_61/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.4
    --cell 53.747 71.215 91.107 90.00 90.00 90.00
    --space-group "P 2 21 21"
)

# Disable MW Prior
MULTI_WILSON_PARAMS=()

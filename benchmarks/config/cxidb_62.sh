BENCHMARKNAME=cxidb_62
INPUTS=(
    $ABISMAL_BENCHMARKS/data/cxidb_62/reflection_data/all-amb.stream
)
REFERENCE_MTZ=$ABISMAL_BENCHMARKS/data/cxidb_62/reference_data/5xfd_phases.mtz

EFFS=(
    $ABISMAL_BENCHMARKS/data/cxidb_62/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.5
    --cell 105.85 105.85 75.4595 90 90 120
    --space-group "P 65"
)

# Disable MW Prior
MULTI_WILSON_PARAMS=()

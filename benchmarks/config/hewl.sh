BENCHMARKNAME=hewl
INPUTS=(
    $ABISMAL_BENCHMARKS/data/hewl/reflection_data/unmerged.mtz
)

EFFS=(
    $ABISMAL_BENCHMARKS/data/hewl/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.7
    --steps-per-epoch=1_000
)

# Disable MW Prior
MULTI_WILSON_PARAMS=()


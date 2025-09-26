BENCHMARKNAME=hewl
INPUTS=(
    $ABISMALDIR/data/hewl/reflection_data/unmerged.mtz
)

EFFS=(
    $ABISMALDIR/data/hewl/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.7
)

# Disable MW Prior
MULTI_WILSON_PARAMS=()

steps_per_epoch=1000
#Add steps per epoch for small experiments
EXPERIMENT_PARAMS+=(
    --steps-per-epoch=$steps_per_epoch
)
CCHALF_PARAMS+=(
    --steps-per-epoch=$steps_per_epoch
)

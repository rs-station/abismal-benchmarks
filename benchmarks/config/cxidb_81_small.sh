BENCHMARKNAME=cxidb_81_small
INPUTS=(
    $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/data/figure7/by_run_t016_mr_ch/r0011/combine_experiments_t016/intermediates/t016_rg013_chunk000_reintegrated_experiments.json
    $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/data/figure7/by_run_t016_mr_ch/r0011/combine_experiments_t016/intermediates/t016_rg013_chunk000_reintegrated_reflections.pickle
)

EFFS=(
    $ABISMAL_BENCHMARKS/data/cxidb_81/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.8
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

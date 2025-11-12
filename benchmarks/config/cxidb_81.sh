BENCHMARKNAME=cxidb_81
INPUTS=(`ls $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/data/figure7/by_run_t016_mr_ch/*/*/intermediates/*_reintegrated_*.{json,pickle}`)

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

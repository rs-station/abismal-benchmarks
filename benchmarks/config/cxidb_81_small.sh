BENCHMARKNAME=cxidb_81_small
INPUTS=(
   $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.expt  
   $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl
)

EFFS=(
    $ABISMAL_BENCHMARKS/data/cxidb_81/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.8
    --steps-per-epoch=1_000
)

# Disable MW Prior
MULTI_WILSON_PARAMS=()


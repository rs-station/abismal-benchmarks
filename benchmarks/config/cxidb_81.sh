BENCHMARKNAME=cxidb_81
INPUTS=(`ls $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/figure7/*.{expt,refl}`)

EFFS=(
    $ABISMAL_BENCHMARKS/data/cxidb_81/reference_data/refine.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.8
)


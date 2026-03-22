BENCHMARKNAME=hewl_diffmap
INPUTS=(
    $ABISMAL_BENCHMARKS/data/hewl/reflection_data/unmerged.mtz
    $ABISMAL_BENCHMARKS/data/hewl/reflection_data/unmerged.mtz
    $ABISMAL_BENCHMARKS/data/hewl/reflection_data/unmerged.mtz
)

EFFS=(
    $ABISMAL_BENCHMARKS/data/hewl/reference_data/refine_no_anom.eff
)

# Dataset specific params
EXPERIMENT_PARAMS=(
    --run-eagerly
    --separate
    --dmin 1.7
    --steps-per-epoch=1_000
)


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
    ####################################################################
    # Metdata used in the original careless paper:
    # "BATCH,dHKL,Hobs,Kobs,Lobs,XDET,YDET,BG,SIGBG,LP,QE,FRACTIONCALC"
    --mtz-metadata="ROT,dHKL,Hobs,Kobs,Lobs,XDET,YDET,BG,SIGBG,LP,QE,FRACTIONCALC"
)


BENCHMARKNAME=hewl
INPUTS=(
    $ABISMAL_BENCHMARKS/data/hewl/reflection_data/unmerged.mtz
)

PDBS=(
    $ABISMAL_BENCHMARKS/data/hewl/reference_data/RTSAD_HEWL_refine_25.pdb
)

RFREE=$ABISMAL_BENCHMARKS/data/hewl/reference_data/r-free-flags.mtz
# Wavelength for torchref's f'/f'' anomalous correction (source: refine.eff)
WAVELENGTH=1.892


# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.7
    --steps-per-epoch=1_000
    ####################################################################
    # Metadata used in the original careless paper:
    # "BATCH,dHKL,Hobs,Kobs,Lobs,XDET,YDET,BG,SIGBG,LP,QE,FRACTIONCALC"
    #--mtz-metadata="ROT,dHKL,Hobs,Kobs,Lobs,XDET,YDET,BG,SIGBG,LP,QE,FRACTIONCALC"
)


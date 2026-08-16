BENCHMARKNAME=cxidb_81
INPUTS=(`ls $ABISMAL_BENCHMARKS/data/cxidb_81/reflection_data/figure7/*.{expt,refl}`)

PDBS=(
    $ABISMAL_BENCHMARKS/data/cxidb_81/reference_data/2tli.pdb
)

RFREE=$ABISMAL_BENCHMARKS/data/cxidb_81/reference_data/r-free-flags.mtz
# Wavelength for torchref's f'/f'' anomalous correction (source: 2tli.pdb REMARK 200)
WAVELENGTH=1.5418


# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.8
)


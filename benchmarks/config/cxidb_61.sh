BENCHMARKNAME=cxidb_61
INPUTS=(
    $ABISMAL_BENCHMARKS/data/cxidb_61/reflection_data/all.stream
)

PDBS=(
    $ABISMAL_BENCHMARKS/data/cxidb_61/reference_data/5xfc_mr.pdb
)

RFREE=$ABISMAL_BENCHMARKS/data/cxidb_61/reference_data/r-free-flags.mtz
# Wavelength for torchref's f'/f'' anomalous correction (source: 5xfc_mr.pdb REMARK 200)
WAVELENGTH=0.954


# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.4
    --cell 53.747 71.215 91.107 90.00 90.00 90.00
    --space-group "P 2 21 21"
    --steps-per-epoch=1_000
    #--isigi-cutoff=1.0 #match published processing
)


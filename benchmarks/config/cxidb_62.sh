BENCHMARKNAME=cxidb_62
INPUTS=(
    $ABISMAL_BENCHMARKS/data/cxidb_62/reflection_data/all-amb.stream
)
REFERENCE_MTZ=$ABISMAL_BENCHMARKS/data/cxidb_62/reference_data/5xfd_phases.mtz

PDBS=(
    $ABISMAL_BENCHMARKS/data/cxidb_62/reference_data/5xfd.pdb
)

RFREE=$ABISMAL_BENCHMARKS/data/cxidb_62/reference_data/r-free-flags.mtz
# Wavelength for torchref's f'/f'' anomalous correction (source: 5xfd.pdb REMARK 200)
WAVELENGTH=0.954


# Dataset specific params
EXPERIMENT_PARAMS=(
    --anomalous
    --dmin 1.5
    --cell 105.85 105.85 75.4595 90 90 120
    --space-group "P 65"
    #--isigi-cutoff=1.0
)


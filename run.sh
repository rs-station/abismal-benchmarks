cpu_counts=(
    8
    4
    2
    1
)

mpi_datasets=(
    cxidb_81 
    cxidb_81_small
)
non_mpi_datasets=(
    cxidb_61 
    cxidb_62 
    hewl
)

output=load_benchmark.csv

# Non-dials datasets (stream, mtz) use joblib via --nproc
for n in "${cpu_counts[@]}"; do
    #MPI benchmarks
    echo "=== MPI: n=$n datasets=${mpi_datasets[*]} ==="
    conda run --no-capture-output -n rs-benchmark mpirun -n $n python -u benchmarks/load.py --datasets "${mpi_datasets[@]}" --output $output --append
    #Non-MPI benchmarks
    #echo "=== non-MPI: nproc=$n datasets=${non_mpi_datasets[*]} ==="
    #conda run --no-capture-output -n rs-benchmark python -u benchmarks/load.py --nproc $n --datasets "${non_mpi_datasets[@]}" --output $output --append
done

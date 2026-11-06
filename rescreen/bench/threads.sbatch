#!/bin/bash
# A. TorchRef thread scaling on a CPU node (same EPYC 7763 as the GPU nodes).
#   scaling: each merge refined at 1, 2, 4, 8, 16 threads, each in its own core-bound step, all at once (62 cores)
#   crowd:   12 copies of the cx81 merge at 2 threads at once (24 cores), to see memory-bandwidth contention
#SBATCH -A m5149 -C cpu -q debug -N 1 -t 00:30:00
set -u
source $RESCREEN/env.sh
B=$RESCREEN/bench; R=$B/threads_$SLURM_JOB_ID; mkdir -p $R
WORKER=$ABISMAL/abismal/callbacks/_torchref_worker.py
export TORCH_EXTENSIONS_DIR=/tmp/torch_ext_$SLURM_JOB_ID
mkdir -p $TORCH_EXTENSIONS_DIR && cp -a ~/.cache/torch_extensions/. $TORCH_EXTENSIONS_DIR/
one() {  # tag mtz ds threads
    local tag=$1 mtz=$2 ds=$3 t=$4 X
    case $ds in
        cx81) X="--pdb $DATA/cxidb_81/reference_data/2tli.pdb --wavelength 1.2717 --r-free-mtz $DATA/cxidb_81/reference_data/r-free-flags.mtz" ;;
        hewl) X="--pdb $DATA/hewl/reference_data/RTSAD_HEWL_refine_25.pdb --wavelength 1.892 --r-free-mtz $DATA/hewl/reference_data/r-free-flags.mtz" ;;
    esac
    local d=$R/$tag; mkdir -p $d
    ( cd $d && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=$t MKL_NUM_THREADS=$t TORCHREF_NUM_THREADS=$t \
      srun -n1 -c $((2 * t)) --cpu-bind=cores --exact /usr/bin/time -f "%e s wall %U s user %M KB maxrss" \
        $PY $WORKER --mtz $mtz $X --out-dir . --device cpu --macro-cycles 5 --z-score-cutoff 5.0 \
        --adp-mode auto --adp-aniso-sigma auto --rigid-body-iter 30 > stdout.txt 2> stderr.txt
      echo "$tag $(tail -1 stderr.txt)" >> $R/times.txt )
}
cd $R
for t in 16 8 4 2 1; do
    one cx81_t$t $B/cx81_merge.mtz cx81 $t &
    one hewl_t$t $B/hewl_merge.mtz hewl $t &
done
for i in $(seq 1 12); do one crowd_cx81_t2_$i $B/cx81_merge.mtz cx81 2 & done
wait
sort $R/times.txt

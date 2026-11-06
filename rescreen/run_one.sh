#!/bin/bash
# Train one arm of the rescreen and refine its epoch 2, 5 and 10 merges (and 20 if it trained that long).
#
#   run_one.sh NAME SEED [abismal flags...]
#
# NAME starts with the dataset (hewl, cx81s, cx81, cx61, cx62), e.g. cx61_nu8; the run goes to $OUT/NAME_sSEED. The base
# configuration is applied first and the arm's flags after it, so an arm's flag overrides the base. Environment (from
# `source rescreen/env.sh`, which setup.sh writes):
#   ABISMAL   abismal checkout at 419fae8 (branch posterior-trend-aniso)
#   DATA      the benchmark data/ tree, holding {hewl,cxidb_81,cxidb_61,cxidb_62}
#   OUT       directory to write runs into
#   PY        python with abismal's dependencies and TorchRef (0.6.3)
#   THREADS   CPU threads for each refinement (default 8)
# Training uses the GPU in CUDA_VISIBLE_DEVICES; refinement runs on the CPU with the GPU hidden.
set -u
NAME=$1; SEED=$2; shift 2
DS=${NAME%%_*}
THREADS=${THREADS:-8}
STAGE=${STAGE:-all}                     # all (train, then refine), train, or refine (an already-trained run)
REFINE_PARALLEL=${REFINE_PARALLEL:-0}   # 1 refines the epochs concurrently, THREADS each
export PYTHONPATH=$ABISMAL
WORKER=$ABISMAL/abismal/callbacks/_torchref_worker.py
D81=$DATA/cxidb_81; D61=$DATA/cxidb_61; D62=$DATA/cxidb_62
case $DS in
    cx81s) IN="--anomalous --dmin 1.8 $D81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.expt $D81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl"
           PDB=$D81/reference_data/2tli.pdb; WL=1.2717; RF=$D81/reference_data/r-free-flags.mtz ;;
    cx81)  IN="--anomalous --dmin 1.8 $(ls $D81/reflection_data/figure7/*.expt $D81/reflection_data/figure7/*.refl | sort | tr '\n' ' ')"
           PDB=$D81/reference_data/2tli.pdb; WL=1.2717; RF=$D81/reference_data/r-free-flags.mtz ;;
    hewl)  IN="--anomalous --dmin 1.7 $DATA/hewl/reflection_data/unmerged.mtz"
           PDB=$DATA/hewl/reference_data/RTSAD_HEWL_refine_25.pdb; WL=1.892; RF=$DATA/hewl/reference_data/r-free-flags.mtz ;;
    cx61)  IN="--anomalous --dmin 1.5 --space-group P22121 $D61/reflection_data/all.stream"
           PDB=$D61/reference_data/5xfc_mr.pdb; WL=0.9539; RF=$D61/reference_data/r-free-flags.mtz ;;
    cx62)  IN="--anomalous --dmin 1.5 --space-group P65 --reference-mtz $D62/reference_data/5xfd_phases.mtz $D62/reflection_data/all-amb.stream"
           PDB=$D62/reference_data/5xfd.pdb; WL=0.9571; RF=$D62/reference_data/r-free-flags.mtz ;;
    *) echo "unknown dataset in $NAME"; exit 2 ;;
esac
BASE="--kl-reflection-weights exact --posterior-trend spline --scale-kl-weight 0.1"
NAME=${NAME}_s$SEED
RUN=$OUT/$NAME
mkdir -p $RUN
cd $OUT   # never run python from inside the abismal checkout: the cwd would shadow PYTHONPATH
status=0
if [ $STAGE != refine ]; then
    echo "$(date) start $NAME seed $SEED commit $(git -C $ABISMAL rev-parse --short HEAD) flags: $BASE $*" | tee -a $OUT/runs.log
    $PY -c 'import sys; from abismal.command_line.abismal import main; main(sys.argv[1:])' $IN -o $RUN $BASE "$@" --seed $SEED --verbosity 2 > $RUN.log 2>&1
    status=$?
    echo "$(date) trained $NAME exit $status" | tee -a $OUT/runs.log
fi
[ $STAGE = train ] && exit $status
refine() {
    local e=$1 d=$RUN/torchref_0_asu_0_epoch_$1
    mkdir -p $d
    (cd $d && CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=$THREADS MKL_NUM_THREADS=$THREADS TORCHREF_NUM_THREADS=$THREADS \
        $PY $WORKER --mtz $RUN/asu_0_epoch_$e.mtz --pdb $PDB --wavelength $WL --out-dir . --device cpu \
        --macro-cycles 5 --z-score-cutoff 5.0 --r-free-mtz $RF --adp-mode auto --adp-aniso-sigma auto \
        --rigid-body-iter 30 > stdout.txt 2> stderr.txt)
    echo "$(date) refined $NAME epoch $e exit $?" | tee -a $OUT/runs.log
}
for e in 2 5 10 20; do
    [ -f $RUN/asu_0_epoch_$e.mtz ] || continue
    if [ $REFINE_PARALLEL = 1 ]; then refine $e & else refine $e; fi
done
wait
echo "$(date) done $NAME" | tee -a $OUT/runs.log
exit $status

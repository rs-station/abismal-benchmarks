#!/bin/bash
# One worker of the rescreen pool: one Slurm task, one GPU, 16 cores (srun -c 32). Started by pool.sbatch.
#
#   pool_worker.sh MANIFEST
#
# Loops over the manifest (name<TAB>seed<TAB>flags, header line first), in the order the manifest lists the
# datasets' durations below (longest first), claims the next unclaimed run with an atomic mkdir in
# $OUT/claims/<run>, trains it, and repeats until nothing is left that fits in the job's remaining time.
#
# Refinement runs inside training, through abismal's TorchRef callback: every epoch, as a detached CPU subprocess
# (--torchref-frequency 1 --torchref-allow-overlap) with TORCHREF_NUM_THREADS=2. The subprocesses inherit this task's
# CPU binding, so they use its spare cores and never another run's. Measured on 2026-11-06 (rescreen/bench/): TorchRef
# gains little past 2 threads, and refining every epoch with up to 4 overlapping workers left hewl's epoch time
# unchanged (34 s). abismal waits for the last refinement before it exits, so a run's claim is done when its epochs
# are all refined.
set -u
MANIFEST=$1
source "$RESCREEN/env.sh"
CLAIMS=$OUT/claims; mkdir -p "$CLAIMS"
ME="job $SLURM_JOB_ID task $SLURM_PROCID $(hostname) $(nvidia-smi --query-gpu=uuid --format=csv,noheader | cut -c1-12)"
log() { echo "$(date '+%F %T') [$SLURM_PROCID] $*"; }

# TorchRef's C++ kernel is built in ~/.cache/torch_extensions; a private copy per task avoids lock contention there.
export TORCH_EXTENSIONS_DIR=/tmp/torch_ext_${SLURM_JOB_ID}_$SLURM_PROCID
mkdir -p "$TORCH_EXTENSIONS_DIR" && cp -a ~/.cache/torch_extensions/. "$TORCH_EXTENSIONS_DIR"/
export TORCHREF_NUM_THREADS=${TORCHREF_NUM_THREADS:-2}

# Expected wall time of one run in minutes, training plus the final refinement, with margin. Calibrated from the
# base seed-1 runs; a run is only started if this fits in the job's remaining time.
minutes() {
    case $1 in
        cx81) echo ${MIN_CX81:-240} ;; cx62) echo ${MIN_CX62:-120} ;; cx61) echo ${MIN_CX61:-120} ;;
        cx81s) echo ${MIN_CX81S:-60} ;; hewl) echo ${MIN_HEWL:-45} ;;
    esac
}
order() { case $1 in cx81) echo 0 ;; cx62) echo 1 ;; cx61) echo 2 ;; cx81s) echo 3 ;; hewl) echo 4 ;; *) echo 9 ;; esac; }
remaining_min() {  # minutes left in this job
    local l; l=$(squeue -h -j "$SLURM_JOB_ID" -o %L)
    echo "$l" | awk -F'[-:]' '{ if (NF==4) m=$1*1440+$2*60+$3; else if (NF==3) m=$1*60+$2; else m=$1; print m }'
}
torchref_flags() {
    local D
    case $1 in
        cx81s|cx81) D=$DATA/cxidb_81/reference_data; echo "--torchref-pdb $D/2tli.pdb --torchref-wavelength 1.2717 --r-free-mtz $D/r-free-flags.mtz" ;;
        cx61) D=$DATA/cxidb_61/reference_data; echo "--torchref-pdb $D/5xfc_mr.pdb --torchref-wavelength 0.9539 --r-free-mtz $D/r-free-flags.mtz" ;;
        cx62) D=$DATA/cxidb_62/reference_data; echo "--torchref-pdb $D/5xfd.pdb --torchref-wavelength 0.9571 --r-free-mtz $D/r-free-flags.mtz" ;;
        hewl) D=$DATA/hewl/reference_data; echo "--torchref-pdb $D/RTSAD_HEWL_refine_25.pdb --torchref-wavelength 1.892 --r-free-mtz $D/r-free-flags.mtz" ;;
    esac
    echo " --torchref-frequency 1 --torchref-allow-overlap"
}

# Stagger the tasks' first claims a little so they don't all hit the filesystem at once.
sleep $((SLURM_PROCID % 16))
log "worker up: $ME, manifest $MANIFEST"
n=0
while true; do
    claimed=
    left=$(remaining_min)
    while IFS=$'\t' read -r _ name seed flags; do
        run=${name}_s$seed; ds=${name%%_*}
        [ -e "$CLAIMS/$run" ] && continue
        [ "$left" -ge "$(minutes $ds)" ] || continue
        mkdir "$CLAIMS/$run" 2>/dev/null || continue     # another worker got it first
        echo "$ME $(date '+%F %T')" > "$CLAIMS/$run/owner"
        claimed=1; break
    done < <(tail -n +2 "$MANIFEST" | while IFS=$'\t' read -r name seed flags; do
                 printf '%s\t%s\t%s\t%s\n' "$(order ${name%%_*})" "$name" "$seed" "$flags"; done | sort -s -t$'\t' -k1,1n)
    [ -n "$claimed" ] || break
    log "start $run (${left} min left)"
    t0=$(date +%s)
    # $flags and the torchref flags are unquoted on purpose: plain lists of abismal flags.
    STAGE=train "$RESCREEN/run_one.sh" "$name" "$seed" $flags $(torchref_flags $ds)
    status=$?
    echo "$status $(( ($(date +%s) - t0) / 60 )) min $(date '+%F %T')" > "$CLAIMS/$run/done"
    log "end $run exit $status after $(( ($(date +%s) - t0) / 60 )) min"
    n=$((n + 1))
done
log "worker done: $n runs, $(remaining_min) min left"

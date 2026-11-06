#!/bin/bash
# Submit rescreen runs from a manifest: one GPU training job per four runs of the same dataset, each followed by a CPU
# refinement job that starts when training ends (afterany, so a failed run still gets its finished epochs refined).
#
#   rescreen/slurm/submit.sh MANIFEST [REGEX] [--dry-run]
#
# MANIFEST is a tsv like phase1.tsv (header line, then name<TAB>seed<TAB>flags). REGEX, if given, selects lines by an
# extended regex on "name<TAB>seed", e.g. '^[a-z0-9]+_base	1$' for the four base seed-1 runs. Runs whose directory
# already has a "trained" line in runs.log are skipped, so re-submitting a manifest only fills in what's missing.
# Job ids are appended to $OUT/slurm/jobs.tsv; Slurm logs go to $OUT/slurm/.
# Walltime: 3 h for cx61, cx62 and cx81, 2 h for the others (PLAN.md section 7); 20-epoch runs get double.
set -eu
RESCREEN=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export RESCREEN
source "$RESCREEN/env.sh"
MANIFEST=$1; REGEX=${2:-.}; DRY=${3:-}
[ "$REGEX" = --dry-run ] && { REGEX=.; DRY=--dry-run; }
LISTS=$OUT/slurm/lists
[ "$DRY" = --dry-run ] && LISTS=$(mktemp -d)
mkdir -p "$LISTS"
STAMP=$(date +%Y%m%d-%H%M%S)

lines=$(tail -n +2 "$MANIFEST" | awk -F'\t' -v re="$REGEX" '($1 "\t" $2) ~ re' | while IFS=$'\t' read -r name seed flags; do
    grep -q " trained ${name}_s${seed} " "$OUT/runs.log" 2>/dev/null && { echo "skip ${name}_s${seed} (already trained)" >&2; continue; }
    printf '%s\t%s\t%s\n' "$name" "$seed" "$flags"
done)
[ -n "$lines" ] || { echo "nothing to submit"; exit 0; }

for ds in $(echo "$lines" | cut -f1 | cut -d_ -f1 | sort -u); do
    case $ds in cx61|cx62|cx81) T=180 ;; *) T=120 ;; esac
    echo "$lines" | awk -F'\t' -v ds="$ds" 'index($1, ds "_") == 1' > "$LISTS/tmp_$ds"
    split -l 4 -d -a 3 "$LISTS/tmp_$ds" "$LISTS/${STAMP}_${ds}_"
    rm "$LISTS/tmp_$ds"
    for list in "$LISTS/${STAMP}_${ds}_"*; do
        t=$T; grep -q -- '--epochs 20' "$list" && t=$((2 * T))
        tag=$(basename "$list")
        if [ "$DRY" = --dry-run ]; then
            echo "would submit $tag (${t} min):"; sed 's/^/    /' "$list"; continue
        fi
        jt=$(sbatch --parsable -t $t -J rs_train_$tag -o "$OUT/slurm/train_${tag}_%j.out" \
            --export=ALL,RESCREEN="$RESCREEN" "$RESCREEN/slurm/train.sbatch" "$list")
        jr=$(sbatch --parsable -d afterany:$jt -J rs_refine_$tag -o "$OUT/slurm/refine_${tag}_%j.out" \
            --export=ALL,RESCREEN="$RESCREEN" "$RESCREEN/slurm/refine.sbatch" "$list")
        printf '%s\t%s\t%s\t%s\n' "$(date +%F_%T)" "$tag" "$jt" "$jr" >> "$OUT/slurm/jobs.tsv"
        echo "$tag: train $jt, refine $jr ($(cut -f1,2 "$list" | tr '\t\n' '_ '))"
    done
done

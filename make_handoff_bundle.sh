#!/bin/bash
# Pack what is needed to continue the abismal torch-port experiments elsewhere (e.g. Perlmutter):
#  - the two benchmark datasets (cxidb_81_small chunk, HEWL) with reference models and R-free flags
#  - every script, analysis and summary under results/ (results/ is gitignored, so these are in no repo)
#  - per-run history.csv / abismal.log and torchref peaks.csv / stdout.txt, so old runs stay usable as baselines
#  - the dof_32 epoch-100 model and MTZ (reference for the frozen-scale probe and the CC-to-converged curves)
# Model checkpoints, per-epoch MTZs and refined maps are left out (the results tree is ~530 GB).
#
#   ./make_handoff_bundle.sh [OUT.tar.gz]
set -euo pipefail
B=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$B/abismal_handoff_$(date +%Y-%m-%d).tar.gz}
cd "$B"
LIST=$(mktemp)
{
  echo data/hewl
  echo data/cxidb_81/reference_data
  echo data/cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.expt
  echo data/cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl
  find results -maxdepth 3 -type f \( -name '*.sh' -o -name '*.py' -o -name '*.md' -o -name '*.json' \
       -o -name '*.html' -o -name '*.csv' -o -name 'run*.log' -o -name '*.txt' \) -not -path '*/torchref_*'
  find results -mindepth 2 -maxdepth 3 -type f \( -name history.csv -o -name abismal.log -o -name datamanager.yml \
       -o -name mm24.csv \)
  find results -mindepth 3 -maxdepth 4 -path '*/torchref_*' -type f \( -name peaks.csv -o -name stdout.txt \)
  echo results/studentt_dof_cxidb81/dof_32/epoch_100.pt
  echo results/studentt_dof_cxidb81/dof_32/asu_0_epoch_100.mtz
  ls results/*/HANDOFF.md 2>/dev/null || true
} | sort -u > "$LIST"
tar -czf "$OUT" -T "$LIST"
echo "$(wc -l < "$LIST") paths -> $OUT ($(du -h "$OUT" | cut -f1))"
rm -f "$LIST"

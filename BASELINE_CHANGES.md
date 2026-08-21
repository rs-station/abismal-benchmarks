# Baseline changes — results before and after 2026-08-20 are not comparable

Four changes to abismal's torchref worker move the numbers this suite reports.
None is a regression; each is a correction. But a plot of banked results against
fresh ones will show steps that are measurement changes, not model changes.

## What moved, and why

**1. Anomalous peak finding replaced (gemmi flood fill -> skimage peak_local_max).**
The connected-component search merged maxima that sit within one blob and
silently dropped peaks whose blob fell under gemmi's hard 3-voxel floor.

- **hewl reports 10 sites, not 6.** Both sulfurs of all four disulfides are now
  resolved; they are 2.02-2.05 A apart and each is its own anomalous scatterer.
  The old output shows the merge in its own `dist` column: methionines landed
  0.04-0.06 A from their atom while every cysteine landed ~1.0 A away, half an
  S-S bond, because the merged blob's centroid sat at the bond midpoint.
- **Peak z-scores shift by ~0.1** from the grid change alone. `peakz` is a max
  over grid nodes and never fully converges, so it is only comparable at a fixed
  grid.

**2. Map grid sized by voxel size, not resolution.**
Was gemmi `sample_rate` (= d_min/spacing), which tied the grid to the data's
resolution: 0.392 A on cxidb_81_small but 0.331 A on hewl. Now a fixed 0.3 A
target, so a voxel means the same physical size on every dataset.

**3. Rigid-body refinement runs before the ADP macrocycles.**
Matches the phenix protocol the benchmark compares against
(`strategy = *rigid_body *individual_adp`), which this suite was configured for
but the worker never did. Worth ~0.004 on both Rwork and Rfree for
cxidb_81_small, ~0.000 for hewl -- it pays off only when the starting model is
not already in register with the data.

**4. B-factor reset now reaches anisotropic atoms.**
`reset_b_factors` set only the scalar `model.adp`; torchref keeps anisotropic
atoms in a separate `model.u` that `adp_u6()` uses instead. On hewl that left
**1112 of 1210 atoms holding their deposited ADPs** while the log announced a
flat B=20 start. Three of five benchmarks run anisotropic (hewl, cxidb_61,
cxidb_62).

This one changes a headline number: hewl's reported starting point goes
**0.1809/0.1626 -> 0.2628/0.2508**. The old figure was flattered by the
reference model's published ADPs. The converged result is unchanged
(0.1370/0.1467 -> 0.1368/0.1465), so refinement was always doing the work --
but "Initial" rows in banked runs are not a like-for-like starting point.

## Comparable across the boundary

- Converged Rwork/Rfree. cxidb_81_small 0.2050/0.2206 -> 0.2009/0.2164 is the
  rigid-body step, a real improvement, not a measurement change.
- Which sites are found on cxidb_81_small (6, unchanged).
- Everything not produced by the torchref worker: CC-half, NLL, training curves.

## Not comparable

- Any "Initial" / pre-refinement R-factor on an anisotropic dataset.
- Anomalous peak counts on hewl, cxidb_61, cxidb_62.
- Absolute peak z-scores anywhere.

## Environment

The worker now needs **scikit-image**, and it must be installed with numpy held
below 2.1: a bare `pip install scikit-image` pulls numpy 2.5 and breaks both
tensorflow (<2.1.0) and torchref (<2.4.0). Known-good: numpy 2.0.2,
scikit-image 0.24.0. `setup.sh` checks for both and warns.

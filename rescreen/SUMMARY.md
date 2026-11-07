# Rescreen phase 1: summary

Run on NERSC Perlmutter, 2026-11-06 to 07. abismal 419fae8 (`posterior-trend-aniso`), TorchRef 0.6.3 (0053149),
torch 2.13.0+cu130. 17 arms × 4 datasets × 3 seeds = 204 runs, 10 epochs each, every one finished (exit 0) and
refined at **every** epoch. Files: `phase1.csv` (one row per run and epoch), `runs.log`, `phase1/tables.md` (every
table, including the 2nd anomalous site, Wilson B, outer Fo/Fc, the epoch-5 decisions), `phase1/plots/` (every
measure by epoch, every arm), `analyze_phase1.py` (makes the tables and plots from `phase1.csv`).

**The short version.** No single change passes the §9 bar as a general win. Ev11 at ml's values is a large win on
cx81s, beating ml there on every measure, but it costs cx61 and cx62 clearly. Heavier tails than ν = 32 lose,
and a normal likelihood is very bad everywhere. More capacity (SwiGLU d256, or 10 layers) gives small gains that are
mostly the same sign across datasets. Metadata noise 0.1 and the posterior features both still help and should stay.

## How it ran

- **Check against the workstation first.** Base seed 1 on all four datasets matched `workstation_reference.csv` to
  within ±0.001 in Rfree and shell Rfree and within 0.75σ in every peak, at epochs 2, 5 and 10.
- **Launcher.** One multi-node Slurm job, one worker per A100, each claiming runs from `phase1.tsv`
  (`slurm/pool.sbatch`, `slurm/README.md`). Refinement ran during training through abismal's TorchRef callback at 2
  threads per refinement, on the training task's spare cores; it did not slow training (`slurm/README.md` has the
  measurements). This is why every epoch is refined, not just 2, 5 and 10. The settings are the callback defaults,
  identical to `run_one.sh`'s post-hoc refinement.
- **Timing on an A100 (base):** hewl 8 min, cx81s 9 min, cx61 18 min, cx62 36 min per run, refinement included. The
  204 runs took one 4-node job of 4 h.
- **Memory.** cx62 `depth10` and `swiglu256` ran out of memory on the 40 GB A100s (batch 1000; the workstation card
  has 48 GB). Those 6 runs were rerun unchanged on 80 GB A100 nodes (`-C gpu&hbm80g`), about 58 min each. Their
  failed attempts are in `runs/stale/`. Phase 2 should put cx62 and cx81 runs of the larger arms on 80 GB nodes.
- **HEWL is noisy.** Its base seed sd is 0.0021 in shell Rfree, 1.1σ in the S peak and 0.034 in CCanom (seed 1 is
  the best of the three). Differences on HEWL smaller than about 0.004 / 2σ can't be resolved with 3 seeds.

## Decisions (§9, epoch 10)

A difference counts when it exceeds twice the base seed sd and has the same sign on 3 of 4 datasets, or on both
cx81s and cx61. Full per-measure verdicts at epochs 10 and 5 are in `phase1/tables.md`.

| arm | verdict | detail (arm − base at epoch 10) |
|---|---|---|
| `nu4`, `nu8`, `nu16` | **worse** | outer CC, flat peaks and CCanom all drop (e.g. ν = 8: outer CC −0.024/−0.008/−0.013 on cx81s/cx61/cx62). Only cx81s shell Rfree improves, by at most 0.0016 (ν = 4), while cx61 and cx62 get worse by 0.001–0.009 |
| `nu64` | neutral | no shell Rfree change. cx81s improves a little (Zn flat +0.9σ, CCanom +0.006), not significant elsewhere |
| `normal` | **worse, severely** | shell Rfree +0.012 to +0.062; cx62 Se as-is peak −35σ; HEWL CCanom −0.29 |
| `ev11t` | **dataset-specific** | cx81s: shell Rfree −0.0096, outer CC +0.109, Zn flat +4.3σ, as-is +7.2σ, CCanom +0.029. cx61: shell +0.0036, outer CC −0.016. cx62: shell +0.0136, outer CC −0.044, Se flat −3.1σ. HEWL: no change |
| `ev11n` | **dataset-specific** | like `ev11t` but a little worse on every dataset; cx62 Se peaks −5 to −7σ |
| `relu128` | **worse** | shell Rfree +0.001 to +0.002 and peaks −1 to −5σ on cx81s, cx61 and cx62 |
| `relu256` | mixed | cx81s better (shell −0.0010, outer CC +0.016); cx61 and cx62 slightly worse (shell +0.0013/+0.0006, cx62 Se −1.5σ) |
| `swiglu64` | **worse** | peaks and CCanom down on 3 datasets; shell Rfree worse on cx81s and cx62 |
| `swiglu256` | mixed, mostly better | shell Rfree −0.0016 cx81s, −0.0011 cx62; peaks and CCanom up on cx61 and cx62. HEWL worse (shell +0.0026, about 1.2 base sd) |
| `depth3` | **worse** (peaks, CCanom) | small losses in flat peaks and CCanom on all four datasets |
| `depth10` | slightly better | peaks and CCanom up on all four datasets (significant on cx62, cx61 as-is and cx81s CCanom); no Rfree cost anywhere |
| `noise0` | **worse** on cx61, cx62 | shell Rfree +0.016 cx61, +0.065 cx62, and both get worse after epoch 4–5; their as-is Se peaks rise (+2.9σ, +8σ) |
| `noise0.3` | **worse** | flat peaks −3 to −10σ, CCanom −0.02 to −0.05 |
| `nopostfeat` | slightly worse | small, significant losses on cx61 and cx62 (shell +0.0007/+0.0009, flat peaks −1.4/−2.2σ); neutral elsewhere |

**For phase 2:** by the §9 rule nothing qualifies for the factorial. The candidates worth discussing are:
**Ev11** (the one big effect, but only right for cx81s at ml's fixed values, so the natural next test is a *learned*
Ev11, or Ev11 only where ml's a ≫ 1); **SwiGLU d256**; and **depth 10**. Phase 2 has not been started.

## Drift

The plan expected the cx81s base to get worse after epoch 5. In this screen it gets worse earlier, between **epoch 2
and 4**: shell Rfree 0.232 at epoch 2, 0.235 by epoch 4, flat after that (the workstation's seed 1 shows the same:
0.2324 at epoch 2, 0.2355 at epoch 5). So the 5→10 drift for the base is only −0.0004 in shell Rfree, −0.4σ as-is
and +0.2σ flat in the Zn peak; see `phase1/plots/phase1_rfree_shell.png`.

- **Ev11 removes the cx81s degradation**: shell Rfree falls steadily to 0.2255 at epoch 10, and the Zn peaks keep
  rising.
- **cx61 and cx62 are still improving at epoch 10** (base shell Rfree −0.007 and −0.027 from epoch 5 to 10), so
  phase 2's 20 epochs will matter there.
- **`noise0` reverses the cx61 and cx62 trend**: shell Rfree rises after epoch 4–5 (+0.003 and +0.009 from 5 to 10).
- **cx62 as-is Se peaks fall after epoch 5** for most arms (base −1.9σ; Ev11 and SwiGLU d256 about −4.6σ), while the
  flat peaks hold.

## Answers to the three questions

1. **Does a heavier tail or Ev11 close the cx81s gap to ml?** A heavier tail does not: ν = 4–16 lowers cx81s shell
   Rfree by at most 0.0016, still well above ml's 0.2285, and lowers cx81s outer CC, Zn peaks and CCanom; it also
   costs on cx61 and cx62. **Ev11 at ml's values does, and passes ml** on cx81s: shell Rfree 0.2255 vs 0.2285, outer
   CC 0.640 vs 0.611, Zn flat 35.1σ vs 34.3σ, Zn as-is 32.8σ vs 28.9σ, CCanom 0.249 vs 0.242 (`ev11t`; under a
   normal likelihood, `ev11n`, it is a little worse). But it costs cx61 (shell +0.0036, outer CC −0.016) and cx62
   (shell +0.0136, outer CC −0.044, Se flat −3.1σ); HEWL doesn't change.
2. **Is relu d256 better than SwiGLU d128?** Only on cx81s, and there consistently across seeds (shell −0.0010,
   outer CC +0.016), so the old cx81s result was not one lucky seed. Averaged over datasets it is not better: it is
   slightly worse on cx61 and cx62. **The effect is capacity, not unit type.** At equal width the unit type favours
   SwiGLU: relu d128 is worse than SwiGLU d128 on cx81s, cx61 and cx62. Width helps both: relu d256 beats relu d128
   (cx81s shell −0.0020, peaks +1 to +2.6σ), and SwiGLU d256 beats SwiGLU d128 on cx81s (−0.0016) and cx62 (−0.0011)
   with higher peaks on cx61 and cx62.
3. **Do metadata noise and the posterior features still help?** Yes, both. Without metadata noise cx61 and cx62
   lose badly in Rfree (+0.016, +0.065) and degrade with more training; at 0.3 the anomalous peaks fall by 3–10σ.
   0.1 stays. Removing the posterior features costs a little, consistently, on cx61 and cx62 and nothing on cx81s or
   HEWL, so they stay.

## Plots

`phase1/plots/phase1_<measure>.png`, one per measure: rows are datasets, columns are arm groups (tails, error model,
unit / width, depth, regularization). Lines are the mean over seeds, bands the seed range; base is the black line,
ml (cycle 20) the dashed line. Each row's y-axis is zoomed to epochs 2–10 of every arm except `normal`, which is
marked when it ends off scale. Measures: `rfree_shell`, `outer_cc`, `peak1_flat`, `peak1_asis` (Zn, Se, Se, S),
`peak2_flat`, `peak2_asis` (Zn2 on cx81s, Se166 on cx61), `ccanom`, `rfree`.

## Epoch-10 tables (mean ± sd over 3 seeds; ml = abismal.ml at cycle 20)

### shell Rfree (`rfree_shell`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 0.2351 ± 0.0005 | 0.1702 ± 0.0003 | 0.1490 ± 0.0001 | 0.1481 ± 0.0021 |
| nu4 | 0.2335 ± 0.0006 | 0.1774 ± 0.0004 | 0.1576 ± 0.0003 | 0.1503 ± 0.0014 |
| nu8 | 0.2340 ± 0.0009 | 0.1749 ± 0.0004 | 0.1529 ± 0.0005 | 0.1485 ± 0.0015 |
| nu16 | 0.2350 ± 0.0005 | 0.1719 ± 0.0002 | 0.1502 ± 0.0003 | 0.1481 ± 0.0020 |
| nu64 | 0.2348 ± 0.0004 | 0.1695 ± 0.0001 | 0.1490 ± 0.0001 | 0.1486 ± 0.0028 |
| normal | 0.2468 ± 0.0011 | 0.2032 ± 0.0003 | 0.1934 ± 0.0012 | 0.2096 ± 0.0246 |
| ev11t | 0.2255 ± 0.0002 | 0.1738 ± 0.0001 | 0.1626 ± 0.0003 | 0.1481 ± 0.0013 |
| ev11n | 0.2264 ± 0.0008 | 0.1730 ± 0.0001 | 0.1604 ± 0.0002 | 0.1488 ± 0.0025 |
| relu128 | 0.2361 ± 0.0006 | 0.1714 ± 0.0002 | 0.1506 ± 0.0002 | 0.1481 ± 0.0002 |
| relu256 | 0.2341 ± 0.0011 | 0.1714 ± 0.0004 | 0.1496 ± 0.0005 | 0.1480 ± 0.0004 |
| swiglu64 | 0.2369 ± 0.0003 | 0.1700 ± 0.0002 | 0.1511 ± 0.0008 | 0.1485 ± 0.0023 |
| swiglu256 | 0.2335 ± 0.0008 | 0.1705 ± 0.0001 | 0.1479 ± 0.0001 | 0.1507 ± 0.0034 |
| depth3 | 0.2364 ± 0.0003 | 0.1703 ± 0.0001 | 0.1484 ± 0.0003 | 0.1498 ± 0.0044 |
| depth10 | 0.2343 ± 0.0003 | 0.1702 ± 0.0001 | 0.1489 ± 0.0002 | 0.1484 ± 0.0010 |
| noise0 | 0.2350 ± 0.0007 | 0.1860 ± 0.0005 | 0.2140 ± 0.0016 | 0.1479 ± 0.0019 |
| noise0.3 | 0.2360 ± 0.0003 | 0.1757 ± 0.0002 | 0.1494 ± 0.0002 | 0.1498 ± 0.0012 |
| nopostfeat | 0.2354 ± 0.0005 | 0.1708 ± 0.0001 | 0.1499 ± 0.0001 | 0.1482 ± 0.0019 |
| **ml** | 0.2285 | 0.1708 | 0.1828 | 0.1479 |

### outer CC (`outer_cc`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 0.5308 ± 0.0065 | 0.8478 ± 0.0009 | 0.8645 ± 0.0001 | 0.9363 ± 0.0015 |
| nu4 | 0.5022 ± 0.0061 | 0.8334 ± 0.0017 | 0.8321 ± 0.0006 | 0.9349 ± 0.0005 |
| nu8 | 0.5070 ± 0.0075 | 0.8396 ± 0.0010 | 0.8511 ± 0.0009 | 0.9369 ± 0.0005 |
| nu16 | 0.5094 ± 0.0094 | 0.8453 ± 0.0005 | 0.8619 ± 0.0008 | 0.9365 ± 0.0010 |
| nu64 | 0.5324 ± 0.0045 | 0.8501 ± 0.0004 | 0.8633 ± 0.0002 | 0.9357 ± 0.0018 |
| normal | 0.5291 ± 0.0195 | 0.7411 ± 0.0016 | 0.7165 ± 0.0237 | 0.7320 ± 0.0565 |
| ev11t | 0.6398 ± 0.0040 | 0.8317 ± 0.0005 | 0.8202 ± 0.0005 | 0.9359 ± 0.0005 |
| ev11n | 0.6427 ± 0.0026 | 0.8330 ± 0.0011 | 0.8215 ± 0.0006 | 0.9347 ± 0.0014 |
| relu128 | 0.5348 ± 0.0108 | 0.8466 ± 0.0005 | 0.8645 ± 0.0004 | 0.9357 ± 0.0002 |
| relu256 | 0.5465 ± 0.0083 | 0.8457 ± 0.0010 | 0.8664 ± 0.0008 | 0.9353 ± 0.0007 |
| swiglu64 | 0.5068 ± 0.0030 | 0.8481 ± 0.0006 | 0.8565 ± 0.0005 | 0.9351 ± 0.0018 |
| swiglu256 | 0.5363 ± 0.0176 | 0.8480 ± 0.0004 | 0.8689 ± 0.0007 | 0.9320 ± 0.0031 |
| depth3 | 0.5132 ± 0.0027 | 0.8475 ± 0.0009 | 0.8646 ± 0.0005 | 0.9344 ± 0.0043 |
| depth10 | 0.5277 ± 0.0129 | 0.8486 ± 0.0006 | 0.8658 ± 0.0007 | 0.9361 ± 0.0012 |
| noise0 | 0.5368 ± 0.0103 | 0.8062 ± 0.0014 | 0.7715 ± 0.0028 | 0.9372 ± 0.0006 |
| noise0.3 | 0.5228 ± 0.0089 | 0.8477 ± 0.0003 | 0.8692 ± 0.0005 | 0.9343 ± 0.0015 |
| nopostfeat | 0.5299 ± 0.0090 | 0.8465 ± 0.0008 | 0.8630 ± 0.0014 | 0.9365 ± 0.0008 |
| **ml** | 0.6110 | 0.8504 | 0.8491 | 0.9332 |

### peak, flat (σ) (`peak1_flat`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 30.80 ± 0.36 | 39.50 ± 0.08 | 58.21 ± 0.16 | 18.96 ± 1.10 |
| nu4 | 27.64 ± 0.27 | 38.68 ± 0.01 | 54.69 ± 0.89 | 18.97 ± 0.71 |
| nu8 | 29.04 ± 0.36 | 39.14 ± 0.04 | 57.39 ± 0.27 | 19.13 ± 0.83 |
| nu16 | 29.74 ± 0.20 | 39.33 ± 0.05 | 57.96 ± 0.21 | 19.22 ± 0.87 |
| nu64 | 31.73 ± 0.03 | 39.58 ± 0.08 | 58.23 ± 0.12 | 18.64 ± 1.26 |
| normal | 25.83 ± 0.30 | 37.45 ± 0.05 | 41.08 ± 1.04 | 10.42 ± 2.66 |
| ev11t | 35.14 ± 0.11 | 39.21 ± 0.01 | 55.10 ± 0.43 | 19.10 ± 0.93 |
| ev11n | 32.59 ± 1.26 | 38.79 ± 0.03 | 51.35 ± 0.32 | 17.76 ± 1.53 |
| relu128 | 28.23 ± 0.05 | 37.98 ± 0.07 | 54.18 ± 0.19 | 19.29 ± 0.22 |
| relu256 | 30.43 ± 0.12 | 39.48 ± 0.04 | 56.75 ± 1.32 | 19.47 ± 0.20 |
| swiglu64 | 28.60 ± 0.15 | 38.70 ± 0.00 | 54.75 ± 1.00 | 18.54 ± 0.97 |
| swiglu256 | 31.32 ± 0.27 | 39.85 ± 0.02 | 59.03 ± 0.29 | 18.29 ± 2.05 |
| depth3 | 29.96 ± 0.18 | 39.23 ± 0.03 | 57.71 ± 0.13 | 18.20 ± 2.13 |
| depth10 | 31.37 ± 0.08 | 39.64 ± 0.08 | 58.64 ± 0.18 | 19.24 ± 0.78 |
| noise0 | 30.40 ± 0.23 | 40.18 ± 0.11 | 58.89 ± 2.54 | 18.76 ± 1.04 |
| noise0.3 | 27.62 ± 0.04 | 35.08 ± 0.03 | 48.26 ± 0.12 | 18.57 ± 1.10 |
| nopostfeat | 30.47 ± 0.10 | 38.10 ± 0.02 | 56.04 ± 0.20 | 18.86 ± 1.12 |
| **ml** | 34.33 | 39.98 | 52.22 | 19.61 |

### peak, as-is (σ) (`peak1_asis`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 25.53 ± 0.28 | 38.96 ± 0.13 | 58.44 ± 0.29 | 16.64 ± 1.69 |
| nu4 | 24.59 ± 0.29 | 39.63 ± 0.02 | 55.25 ± 0.73 | 16.36 ± 1.23 |
| nu8 | 24.96 ± 0.38 | 39.68 ± 0.05 | 57.92 ± 0.34 | 16.63 ± 1.35 |
| nu16 | 24.99 ± 0.19 | 39.28 ± 0.11 | 58.36 ± 0.37 | 16.85 ± 1.56 |
| nu64 | 25.98 ± 0.16 | 38.55 ± 0.17 | 58.16 ± 0.26 | 16.12 ± 2.36 |
| normal | 20.74 ± 0.40 | 33.76 ± 0.16 | 23.12 ± 2.29 | 8.64 ± 1.16 |
| ev11t | 32.77 ± 0.12 | 41.16 ± 0.01 | 57.52 ± 0.30 | 17.48 ± 1.45 |
| ev11n | 30.90 ± 0.76 | 40.31 ± 0.06 | 53.02 ± 0.34 | 16.00 ± 2.94 |
| relu128 | 24.52 ± 0.10 | 37.24 ± 0.03 | 53.78 ± 0.33 | 17.08 ± 0.32 |
| relu256 | 26.13 ± 0.12 | 39.35 ± 0.05 | 57.24 ± 1.23 | 17.34 ± 0.36 |
| swiglu64 | 24.21 ± 0.09 | 37.31 ± 0.11 | 54.29 ± 1.07 | 15.87 ± 1.49 |
| swiglu256 | 26.01 ± 0.38 | 39.77 ± 0.03 | 59.38 ± 0.43 | 16.35 ± 2.49 |
| depth3 | 25.03 ± 0.16 | 38.50 ± 0.11 | 57.62 ± 0.44 | 15.68 ± 2.36 |
| depth10 | 25.93 ± 0.09 | 39.26 ± 0.17 | 59.04 ± 0.22 | 17.68 ± 0.93 |
| noise0 | 25.61 ± 0.12 | 41.87 ± 0.20 | 66.41 ± 2.93 | 16.23 ± 1.36 |
| noise0.3 | 23.60 ± 0.05 | 30.50 ± 0.04 | 49.53 ± 0.22 | 16.24 ± 1.93 |
| nopostfeat | 25.46 ± 0.08 | 37.35 ± 0.05 | 56.43 ± 0.27 | 16.65 ± 1.85 |
| **ml** | 28.91 | 41.25 | 48.27 | 19.27 |

### 2nd peak, flat (σ) (`peak2_flat`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 7.58 ± 0.25 | 18.54 ± 0.09 | – | – |
| nu4 | 6.31 ± 0.44 | 18.53 ± 0.09 | – | – |
| nu8 | 6.82 ± 0.13 | 18.51 ± 0.06 | – | – |
| nu16 | 6.74 ± 0.19 | 18.53 ± 0.10 | – | – |
| nu64 | 7.50 ± 0.44 | 18.52 ± 0.15 | – | – |
| normal | 5.32 ± 0.35 | 17.28 ± 0.19 | – | – |
| ev11t | 7.59 ± 0.15 | 18.41 ± 0.04 | – | – |
| ev11n | 6.92 ± 0.27 | 18.07 ± 0.04 | – | – |
| relu128 | 6.82 ± 0.33 | 17.73 ± 0.08 | – | – |
| relu256 | 7.05 ± 0.10 | 18.49 ± 0.07 | – | – |
| swiglu64 | 6.70 ± 0.14 | 18.21 ± 0.01 | – | – |
| swiglu256 | 7.10 ± 0.20 | 18.72 ± 0.06 | – | – |
| depth3 | 7.23 ± 0.11 | 18.40 ± 0.07 | – | – |
| depth10 | 7.29 ± 0.26 | 18.63 ± 0.14 | – | – |
| noise0 | 6.92 ± 0.41 | 19.55 ± 0.19 | – | – |
| noise0.3 | 6.61 ± 0.11 | 16.22 ± 0.06 | – | – |
| nopostfeat | 6.89 ± 0.33 | 17.81 ± 0.04 | – | – |
| **ml** | 7.11 | 18.63 | – | – |

### 2nd peak, as-is (σ) (`peak2_asis`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 6.06 ± 0.28 | 20.13 ± 0.11 | – | – |
| nu4 | 5.44 ± 0.42 | 20.47 ± 0.12 | – | – |
| nu8 | 5.75 ± 0.05 | 20.36 ± 0.04 | – | – |
| nu16 | 5.41 ± 0.16 | 20.24 ± 0.12 | – | – |
| nu64 | 5.86 ± 0.34 | 20.00 ± 0.23 | – | – |
| normal | 4.48 ± 0.35 | 17.72 ± 0.33 | – | – |
| ev11t | 6.92 ± 0.15 | 20.64 ± 0.06 | – | – |
| ev11n | 6.39 ± 0.15 | 20.21 ± 0.05 | – | – |
| relu128 | 5.93 ± 0.25 | 19.13 ± 0.05 | – | – |
| relu256 | 6.00 ± 0.12 | 20.21 ± 0.11 | – | – |
| swiglu64 | 5.55 ± 0.25 | 19.50 ± 0.07 | – | – |
| swiglu256 | 5.68 ± 0.13 | 20.53 ± 0.07 | – | – |
| depth3 | 5.85 ± 0.08 | 19.94 ± 0.07 | – | – |
| depth10 | 5.71 ± 0.18 | 20.31 ± 0.26 | – | – |
| noise0 | 5.46 ± 0.32 | 21.91 ± 0.26 | – | – |
| noise0.3 | 5.52 ± 0.11 | 16.27 ± 0.16 | – | – |
| nopostfeat | 5.56 ± 0.33 | 19.11 ± 0.03 | – | – |
| **ml** | 6.32 | 20.87 | – | – |

### CCanom (`ccanom`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 0.2191 ± 0.0027 | 0.4526 ± 0.0011 | 0.3085 ± 0.0009 | 0.6395 ± 0.0342 |
| nu4 | 0.1981 ± 0.0017 | 0.4431 ± 0.0001 | 0.2908 ± 0.0048 | 0.6350 ± 0.0259 |
| nu8 | 0.2065 ± 0.0020 | 0.4482 ± 0.0004 | 0.3050 ± 0.0012 | 0.6423 ± 0.0284 |
| nu16 | 0.2116 ± 0.0020 | 0.4507 ± 0.0004 | 0.3077 ± 0.0010 | 0.6452 ± 0.0309 |
| nu64 | 0.2250 ± 0.0019 | 0.4532 ± 0.0011 | 0.3084 ± 0.0007 | 0.6299 ± 0.0386 |
| normal | 0.1849 ± 0.0014 | 0.4273 ± 0.0009 | 0.2087 ± 0.0066 | 0.3507 ± 0.0862 |
| ev11t | 0.2485 ± 0.0015 | 0.4507 ± 0.0002 | 0.2933 ± 0.0022 | 0.6427 ± 0.0327 |
| ev11n | 0.2292 ± 0.0084 | 0.4458 ± 0.0007 | 0.2724 ± 0.0017 | 0.5987 ± 0.0501 |
| relu128 | 0.2004 ± 0.0007 | 0.4346 ± 0.0011 | 0.2869 ± 0.0009 | 0.6491 ± 0.0087 |
| relu256 | 0.2164 ± 0.0016 | 0.4526 ± 0.0008 | 0.3012 ± 0.0066 | 0.6539 ± 0.0063 |
| swiglu64 | 0.2014 ± 0.0013 | 0.4423 ± 0.0001 | 0.2899 ± 0.0050 | 0.6227 ± 0.0284 |
| swiglu256 | 0.2227 ± 0.0009 | 0.4572 ± 0.0002 | 0.3133 ± 0.0017 | 0.6174 ± 0.0636 |
| depth3 | 0.2125 ± 0.0010 | 0.4492 ± 0.0004 | 0.3057 ± 0.0012 | 0.6155 ± 0.0677 |
| depth10 | 0.2248 ± 0.0016 | 0.4544 ± 0.0010 | 0.3110 ± 0.0010 | 0.6494 ± 0.0211 |
| noise0 | 0.2153 ± 0.0015 | 0.4623 ± 0.0012 | 0.3137 ± 0.0133 | 0.6327 ± 0.0317 |
| noise0.3 | 0.1962 ± 0.0006 | 0.3979 ± 0.0006 | 0.2570 ± 0.0007 | 0.6245 ± 0.0341 |
| nopostfeat | 0.2157 ± 0.0009 | 0.4359 ± 0.0001 | 0.2977 ± 0.0009 | 0.6367 ± 0.0356 |
| **ml** | 0.2416 | 0.4595 | 0.2767 | 0.6578 |

### Rfree (`rfree`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 0.2125 ± 0.0005 | 0.1632 ± 0.0003 | 0.1449 ± 0.0002 | 0.1456 ± 0.0012 |
| nu4 | 0.2113 ± 0.0003 | 0.1732 ± 0.0006 | 0.1566 ± 0.0001 | 0.1471 ± 0.0008 |
| nu8 | 0.2117 ± 0.0005 | 0.1705 ± 0.0005 | 0.1526 ± 0.0006 | 0.1461 ± 0.0010 |
| nu16 | 0.2123 ± 0.0004 | 0.1663 ± 0.0004 | 0.1484 ± 0.0006 | 0.1457 ± 0.0012 |
| nu64 | 0.2123 ± 0.0003 | 0.1617 ± 0.0004 | 0.1429 ± 0.0002 | 0.1461 ± 0.0017 |
| normal | 0.2310 ± 0.0005 | 0.1793 ± 0.0002 | 0.1583 ± 0.0012 | 0.1844 ± 0.0189 |
| ev11t | 0.2053 ± 0.0002 | 0.1651 ± 0.0001 | 0.1574 ± 0.0002 | 0.1456 ± 0.0006 |
| ev11n | 0.2064 ± 0.0006 | 0.1643 ± 0.0002 | 0.1547 ± 0.0003 | 0.1461 ± 0.0020 |
| relu128 | 0.2135 ± 0.0004 | 0.1657 ± 0.0002 | 0.1466 ± 0.0004 | 0.1460 ± 0.0004 |
| relu256 | 0.2107 ± 0.0006 | 0.1656 ± 0.0005 | 0.1458 ± 0.0006 | 0.1462 ± 0.0008 |
| swiglu64 | 0.2148 ± 0.0002 | 0.1627 ± 0.0003 | 0.1465 ± 0.0012 | 0.1457 ± 0.0011 |
| swiglu256 | 0.2108 ± 0.0004 | 0.1639 ± 0.0002 | 0.1445 ± 0.0002 | 0.1473 ± 0.0022 |
| depth3 | 0.2135 ± 0.0003 | 0.1632 ± 0.0001 | 0.1445 ± 0.0003 | 0.1470 ± 0.0026 |
| depth10 | 0.2114 ± 0.0002 | 0.1633 ± 0.0002 | 0.1448 ± 0.0001 | 0.1456 ± 0.0006 |
| noise0 | 0.2124 ± 0.0003 | 0.1679 ± 0.0002 | 0.1811 ± 0.0017 | 0.1456 ± 0.0009 |
| noise0.3 | 0.2132 ± 0.0001 | 0.1757 ± 0.0003 | 0.1515 ± 0.0003 | 0.1467 ± 0.0007 |
| nopostfeat | 0.2125 ± 0.0003 | 0.1648 ± 0.0003 | 0.1458 ± 0.0002 | 0.1457 ± 0.0011 |
| **ml** | 0.2099 | 0.1656 | 0.1809 | 0.1447 |

### Wilson B (`wilson_b`), epoch 10

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | 31.02 ± 0.02 | 25.74 ± 0.03 | 26.19 ± 0.04 | 31.59 ± 0.73 |
| nu4 | 31.69 ± 0.06 | 26.24 ± 0.02 | 27.30 ± 0.05 | 30.54 ± 0.27 |
| nu8 | 31.35 ± 0.05 | 26.02 ± 0.06 | 26.80 ± 0.02 | 30.91 ± 0.46 |
| nu16 | 31.04 ± 0.12 | 25.83 ± 0.06 | 26.40 ± 0.02 | 31.24 ± 0.56 |
| nu64 | 30.87 ± 0.15 | 25.74 ± 0.02 | 26.09 ± 0.08 | 31.83 ± 0.96 |
| normal | 23.09 ± 0.23 | 24.24 ± 0.13 | 31.34 ± 0.52 | 18.67 ± 6.86 |
| ev11t | 32.15 ± 0.01 | 25.84 ± 0.01 | 27.34 ± 0.06 | 30.41 ± 0.17 |
| ev11n | 31.99 ± 0.15 | 25.92 ± 0.00 | 27.44 ± 0.05 | 31.13 ± 0.22 |
| relu128 | 31.90 ± 0.06 | 25.83 ± 0.04 | 26.16 ± 0.02 | 32.84 ± 1.50 |
| relu256 | 32.47 ± 0.09 | 26.00 ± 0.02 | 26.29 ± 0.04 | 32.66 ± 1.44 |
| swiglu64 | 30.44 ± 0.10 | 25.57 ± 0.06 | 26.09 ± 0.03 | 31.73 ± 0.91 |
| swiglu256 | 31.36 ± 0.08 | 25.87 ± 0.02 | 26.29 ± 0.02 | 31.67 ± 0.51 |
| depth3 | 30.76 ± 0.13 | 25.81 ± 0.04 | 26.15 ± 0.06 | 32.10 ± 0.78 |
| depth10 | 31.21 ± 0.03 | 25.76 ± 0.02 | 26.19 ± 0.03 | 31.16 ± 0.11 |
| noise0 | 31.45 ± 0.12 | 21.44 ± 0.08 | 19.43 ± 0.09 | 32.09 ± 1.77 |
| noise0.3 | 31.49 ± 0.02 | 27.52 ± 0.00 | 26.68 ± 0.02 | 31.03 ± 0.43 |
| nopostfeat | 30.78 ± 0.06 | 25.55 ± 0.02 | 26.11 ± 0.04 | 31.36 ± 0.54 |
| **ml** | 25.89 | 25.35 | 17.29 | 28.61 |

## Drift tables: epoch 10 − epoch 5 (mean over seeds)

**shell Rfree**

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | -0.0004 | -0.0071 | -0.0266 | -0.0001 |
| nu4 | -0.0006 | -0.0019 | -0.0172 | -0.0008 |
| nu8 | -0.0004 | -0.0023 | -0.0183 | -0.0020 |
| nu16 | -0.0002 | -0.0044 | -0.0211 | +0.0001 |
| nu64 | +0.0003 | -0.0119 | -0.0336 | +0.0005 |
| normal | -0.0425 | -0.0675 | -0.0670 | -0.0092 |
| ev11t | -0.0011 | -0.0047 | -0.0173 | +0.0007 |
| ev11n | -0.0009 | -0.0131 | -0.0184 | -0.0067 |
| relu128 | +0.0005 | -0.0057 | -0.0231 | +0.0004 |
| relu256 | -0.0006 | -0.0054 | -0.0216 | -0.0001 |
| swiglu64 | +0.0009 | -0.0090 | -0.0306 | -0.0017 |
| swiglu256 | +0.0000 | -0.0056 | -0.0218 | +0.0007 |
| depth3 | +0.0002 | -0.0071 | -0.0261 | +0.0001 |
| depth10 | -0.0005 | -0.0070 | -0.0266 | -0.0003 |
| noise0 | -0.0004 | +0.0028 | +0.0086 | -0.0005 |
| noise0.3 | +0.0002 | -0.0072 | -0.0296 | -0.0008 |
| nopostfeat | +0.0003 | -0.0076 | -0.0267 | -0.0001 |

**peak flat**

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | +0.21 | -0.34 | +0.61 | +0.48 |
| nu4 | -0.42 | -0.01 | +0.68 | +0.43 |
| nu8 | -0.01 | -0.14 | +0.53 | +0.36 |
| nu16 | -0.21 | -0.26 | +0.37 | +0.47 |
| nu64 | +0.51 | -0.25 | +1.09 | +0.26 |
| normal | +11.21 | +9.28 | +11.52 | -0.26 |
| ev11t | +0.94 | +0.18 | -0.31 | +0.32 |
| ev11n | -0.10 | +0.79 | -1.50 | +0.52 |
| relu128 | +0.63 | +0.25 | -1.33 | +0.49 |
| relu256 | +0.37 | +0.72 | +0.62 | +0.37 |
| swiglu64 | +0.67 | +0.37 | -1.06 | +1.15 |
| swiglu256 | -0.70 | -0.58 | -1.46 | +0.32 |
| depth3 | +0.13 | -0.34 | +0.13 | +0.62 |
| depth10 | +0.07 | -0.28 | +0.82 | +0.71 |
| noise0 | +0.48 | -0.53 | +1.09 | +0.17 |
| noise0.3 | +0.12 | -0.06 | +0.47 | +0.77 |
| nopostfeat | +0.76 | -0.25 | +0.27 | +0.51 |

**peak as-is**

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | -0.38 | -0.16 | -1.87 | +0.57 |
| nu4 | -0.46 | -0.10 | -2.62 | +0.59 |
| nu8 | -0.34 | -0.11 | -2.73 | +0.57 |
| nu16 | -0.63 | -0.23 | -2.40 | +0.65 |
| nu64 | -0.30 | +0.15 | -0.67 | +0.08 |
| normal | +8.39 | +3.47 | +1.35 | +0.13 |
| ev11t | +0.73 | +0.09 | -4.66 | +0.38 |
| ev11n | -0.07 | +0.83 | -4.56 | -0.02 |
| relu128 | -0.25 | +1.50 | -3.52 | +0.50 |
| relu256 | -0.21 | +1.09 | -1.42 | +0.20 |
| swiglu64 | -0.02 | +1.14 | -3.17 | +1.72 |
| swiglu256 | -0.95 | -0.61 | -4.58 | +0.49 |
| depth3 | -0.54 | -0.25 | -2.22 | +0.78 |
| depth10 | -0.59 | +0.10 | -1.51 | +1.21 |
| noise0 | +0.27 | -0.24 | +3.48 | +0.06 |
| noise0.3 | -0.27 | +0.67 | -0.08 | +1.40 |
| nopostfeat | -0.01 | +0.15 | -1.54 | +0.59 |

**2nd peak flat**

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | +0.52 | +0.05 | – | – |
| nu4 | +0.08 | +0.24 | – | – |
| nu8 | +0.37 | +0.11 | – | – |
| nu16 | -0.05 | +0.09 | – | – |
| nu64 | +0.37 | +0.05 | – | – |
| normal | +2.85 | +3.51 | – | – |
| ev11t | +0.22 | +0.18 | – | – |
| ev11n | +0.31 | +0.44 | – | – |
| relu128 | +0.48 | +0.31 | – | – |
| relu256 | +0.25 | +0.57 | – | – |
| swiglu64 | +0.23 | +0.48 | – | – |
| swiglu256 | -0.23 | -0.11 | – | – |
| depth3 | +0.35 | +0.01 | – | – |
| depth10 | +0.37 | +0.08 | – | – |
| noise0 | +0.27 | +0.35 | – | – |
| noise0.3 | +0.23 | +0.09 | – | – |
| nopostfeat | +0.21 | +0.18 | – | – |

**2nd peak as-is**

| arm | cx81s | cx61 | cx62 | hewl |
|---|---|---|---|---|
| base | +0.24 | -0.23 | – | – |
| nu4 | -0.12 | +0.08 | – | – |
| nu8 | +0.20 | -0.06 | – | – |
| nu16 | -0.20 | -0.19 | – | – |
| nu64 | -0.06 | -0.20 | – | – |
| normal | +2.16 | +1.69 | – | – |
| ev11t | +0.18 | -0.06 | – | – |
| ev11n | +0.33 | +0.02 | – | – |
| relu128 | +0.35 | +0.61 | – | – |
| relu256 | -0.02 | +0.49 | – | – |
| swiglu64 | +0.03 | +0.58 | – | – |
| swiglu256 | -0.36 | -0.39 | – | – |
| depth3 | +0.08 | -0.24 | – | – |
| depth10 | +0.14 | -0.04 | – | – |
| noise0 | -0.06 | +0.23 | – | – |
| noise0.3 | +0.01 | +0.14 | – | – |
| nopostfeat | +0.04 | +0.07 | – | – |

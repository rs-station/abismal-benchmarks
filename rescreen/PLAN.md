# Rescreen of abismal's likelihood, error-model and scale-network settings

Written 2026-11-06 on the workstation, for the agent that will run this on NERSC Perlmutter.
Everything this plan needs is in this folder, `rescreen/` on the `rescreen` branch of abismal-benchmarks.

## Quick start

```bash
git clone -b rescreen https://github.com/rs-station/abismal-benchmarks
cd abismal-benchmarks
PY=<python with torch + torchref 0.6.3> rescreen/setup.sh   # clones abismal at 419fae8, downloads missing data, checks it all
source rescreen/env.sh
run_one.sh cx81s_base 1                                     # one run; phase 1 is every line of rescreen/phase1.tsv
```

- **Data already on Perlmutter:** add `DATA=<that data/ tree>` to the setup command and nothing is downloaded.
- **Otherwise:** `setup.sh` fetches the reflection data. cxidb 81, 61 and 62 come from cxidb.org; HEWL comes from careless-examples. That's about 50 GB. The reference models and free flags are already in this repo under `data/*/reference_data`.
- **Python environment:** the env needs torch, reciprocalspaceship, gemmi and TorchRef 0.6.3 (`pip install git+https://github.com/HatPdotS/TorchRef@0053149`). abismal itself comes from `PYTHONPATH=$ABISMAL`, which `run_one.sh` sets.

## 1. Why

On 2026-11-02 the ELBO changed in three ways:

- **Likelihood reduction:** the mean over valid observations. The per-image mean is now used only to pick the reindexing operator.
- **Structure-factor KL:** weighted by the exact `1/n_h`, with `n_h` counted in the first pass (`--kl-reflection-weights exact`).
- **Resolution trend:** a learned spline `T(d)` multiplies the predicted intensities while the KL stays on a flat scale (`--posterior-trend spline`).

Together with a scale KL weight of 0.1, this is the best configuration so far. It beats abismal.ml on cxidb_62. It ties ml on cxidb_61 and HEWL. It still trails ml on cxidb_81.

Every architecture and hyperparameter default was chosen **before** that change, under the per-image reduction with KL weight 1:

- RMS + SwiGLU, d_model 128 (Oct 20);
- Student t with ν = 32;
- metadata noise 0.1;
- posterior features in the pooled image representation.

There are three signs that these choices need checking again.

1. **The architecture ranking flipped on cxidb_81 small.** The old relu d256 network now gives the best Bayesian cx81s merge so far (Rfree 0.2101, level with ml's 0.2099). On cxidb_61 it is level with SwiGLU d128.
2. **Validation NLL no longer tracks merge quality on cx81s.**
   - relu d256 memorizes the training images most: a train−val NLL gap of 6.1, against 4.1 for SwiGLU d128. Yet it gives the best maps.
   - SwiGLU d64 barely memorizes, yet it gives the worst maps.
   - **Do not use validation NLL to pick anything in this screen.**
3. **On cx81s the merge gets worse after epoch 5** (Rfree up about 0.003, anomalous peaks down about 1–2σ). The cause is the structure factors of **weak** reflections. In the outer shell, about 2% of reflections carry 30% of the upward movement. They have I/σ ≈ 3 and usually 2 observations. They overshoot the model by about 25%.
   - This points at tail robustness: the cx81s residuals have mean z⁴/3 ≈ 21, and t with ν = 32 is close to normal.
   - It also points at the error model: ml fits Ev11 and gives better cx81s maps.

So this screen tests three groups of settings one at a time, around the current best configuration:

- likelihood tails: ν;
- the error model: Ev11 fixed at ml's values;
- the scale network: unit type, width, depth, and its regularization.

## 2. Code

- **Branch:** `posterior-trend-aniso` at **419fae8** of `rs-station/abismal`.
  - It is `torch` plus the Nov 2–6 work: per-observation NLL, KL over valid observations, the new defaults, Ev11 options, `--kl-reflection-weights`, first-pass counts, auto_wilson, `--posterior-trend`, and `--posterior-trend-aniso`.
  - The anisotropic trend is off unless asked for, so it does not affect phases 1–2.
  - `setup.sh` checks it out into `rescreen/abismal`, or into `$ABISMAL` if you set it.
- Don't change defaults on `torch` or any shared branch. Experimental knobs stay on throwaway branches. Record the commit of every run; `run_one.sh` writes it to `runs.log`.
- **TorchRef 0.6.3** is used for refinement through `abismal/callbacks/_torchref_worker.py`. It always runs on the CPU, with the GPU hidden.

## 3. Files in this folder

| file | what |
|---|---|
| `PLAN.md` | this plan |
| `setup.sh` | one-time setup (see the quick start). Writes `env.sh` |
| `run_one.sh` | trains one run, then refines its epoch 2, 5, 10 (and 20) merges. Usage: `run_one.sh NAME SEED [flags]` |
| `phase1.tsv` | the 204 phase-1 runs: `name`, `seed`, `flags` (tab-separated; empty flags = base) |
| `make_manifest.py` | regenerates `phase1.tsv`; edit it to build phase-2 manifests |
| `measures.py` | anomalous peak heights, model anomalous CC, Rfree by shell (portable copy of `reports/fiducial/measures.py`) |
| `measure_runs.py` | measures run directories and appends one CSV row per (run, epoch) |
| `edges.json` | frozen resolution shells for the measures, so numbers compare with the workstation's |
| `make_edges.py` | how `edges.json` was made (needs workstation runs; don't rerun) |
| `workstation_reference.csv` | the same measures for the base configuration (seed 1; run names `<ds>_sk0.1_s1`, epochs 2, 5, 10) and abismal.ml (run names `<ds>_l2_0`, and `cx62` for cxidb_62; the `epoch` column is ml's cycle, so compare against cycle 20) on the workstation |

`source rescreen/env.sh` sets everything `run_one.sh` and `measure_runs.py` need, and puts `rescreen/` on `PATH`:

- `ABISMAL`: the checkout at 419fae8.
- `DATA`: the benchmark `data/` tree.
- `OUT`: where to write the runs, default `rescreen/runs/` (gitignored).
- `PY`: python with abismal's dependencies and TorchRef.
- `THREADS`: refinement threads, default 8.

Two working rules:

- **Never run python from inside the abismal checkout.** The cwd shadows `PYTHONPATH`. `run_one.sh` changes into `$OUT` before it runs anything.
- `measure_runs.py` needs `ABISMAL` set too, because the measures import the TorchRef worker's grid helper.

## 4. Data

All under `$DATA`. `setup.sh` downloads anything missing and fails if any file below is absent.

| dataset | name prefix | input | reference model | wavelength (Å) | free flags |
|---|---|---|---|---|---|
| HEWL (rotation, SAD) | `hewl` | `hewl/reflection_data/unmerged.mtz`, dmin 1.7 | `hewl/reference_data/RTSAD_HEWL_refine_25.pdb` | 1.892 | `hewl/reference_data/r-free-flags.mtz` |
| cxidb_81 small (thermolysin, Zn) | `cx81s` | `cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.{expt,refl}`, dmin 1.8 | `cxidb_81/reference_data/2tli.pdb` | 1.2717 | `cxidb_81/reference_data/r-free-flags.mtz` |
| cxidb_81 full | `cx81` | every `cxidb_81/reflection_data/figure7/*.{expt,refl}`, dmin 1.8 | as cx81s | 1.2717 | as cx81s |
| cxidb_61 (SeMet, CrystFEL) | `cx61` | `cxidb_61/reflection_data/all.stream`, P22121, dmin 1.5 | `cxidb_61/reference_data/5xfc_mr.pdb` | 0.9539 | `cxidb_61/reference_data/r-free-flags.mtz` |
| cxidb_62 (SeMet, CrystFEL, P65 ambiguity) | `cx62` | `cxidb_62/reflection_data/all-amb-scrambled-sigfix.stream`, P65, dmin 1.5, `--reference-mtz cxidb_62/reference_data/5xfd_phases.mtz` | `cxidb_62/reference_data/5xfd.pdb` (the deposited model, **not** `5xfd-mr.pdb`) | 0.9571 | `cxidb_62/reference_data/r-free-flags.mtz` |

**cxidb_81 wavelength.** The data were collected at 1.2717 Å, above the Zn K edge. Some older configs say 1.5418, which is wrong. The anomalous measures depend on the wavelength.

## 5. Base configuration

`run_one.sh` adds `--kl-reflection-weights exact --posterior-trend spline --scale-kl-weight 0.1` to every run. Everything else is a branch default:

- **Training:**
  - 10 epochs × 1000 steps, batch 1000 images, lr 1e-3, 32 MC samples;
  - 10% of images held out for validation (`--test-fraction 0.1`);
  - early stopping off; on CUDA, `torch.compile` and bfloat16 on.
- **Scale network:** RMS pre-normalization, SwiGLU (gated, swish, hidden width 2/3 of d_model), d_model 128, 5 layers.
  - Its pooled image representation uses leave-one-out pooling and includes the posterior mean and standard deviation (posterior features).
  - Metadata noise 0.1.
- **Scale posterior and prior:** lognormal posterior, LogNormal(0, 1) prior, KL weight 0.1.
- **Structure factors:** folded-normal posterior on F, Wilson prior, spline trend with 16 knots.
- **Likelihood:** Student t with ν = 32 on the reported σ (no error model).

An arm's flags come after the base, so an arm can override it. For example, `--scale-kl-weight` given again wins, because argparse keeps the last value.

## 6. Phase 1: one change at a time

There are 17 arms. Each runs on 4 datasets (cx81s, cx61, cx62, HEWL) with 3 seeds (1, 2, 3), for **204 runs**. They are all listed in `phase1.tsv`; run name = `<dataset>_<arm>`, and the run directory is `<name>_s<seed>`.

| group | arm | flags | question |
|---|---|---|---|
| reference | `base` | (none) | the current best configuration. It sets the seed noise every other arm is judged against |
| tails | `nu4`, `nu8`, `nu16`, `nu64` | `--studentt-dof 4/8/16/64` | does a heavier tail stop the weak-reflection overshoot on cx81s without hurting the rest? |
| tails | `normal` | `--studentt-dof none` | the light-tail end |
| error model | `ev11t` | `--error-model ev11 --error-model-a A --error-model-b B --fix-error-model` | Ev11 held at abismal.ml's fitted a, b, under t32 |
| error model | `ev11n` | as `ev11t` plus `--studentt-dof none` | the same under a normal likelihood, which is ml's setting |
| network | `relu128`, `relu256` | `--d-model 128/256 --pre-activation relu --activation relu --no-gated --hidden-multiplier 2` | the old plain residual units, which won on cx81s at d256 |
| network | `swiglu64`, `swiglu256` | `--d-model 64/256` | SwiGLU width |
| network | `depth3`, `depth10` | `--layers 3/10` | depth |
| regularization | `noise0`, `noise0.3` | `--metadata-noise-factor 0/0.3` | metadata noise. It was tuned under the old reduction |
| regularization | `nopostfeat` | `--no-posterior-features` | posterior mean and standard deviation in the pooled image representation |

These are abismal.ml's fitted Ev11 values, as used on the workstation (`make_manifest.py` has them):

| | HEWL | cx81s | cx61 | cx62 | cx81 |
|---|---|---|---|---|---|
| a | 0.994 | 20.72 | 1.812 | 2.821 | 11.51 |
| b | 0.047 | 0.1969 | 0.3045 | 0.7809 | 0.3252 |

**Start with `base` on all four datasets, seed 1 (4 runs).**

1. Measure them.
2. Compare with `workstation_reference.csv`. Agreement within about 0.003 in Rfree and about 1σ in peaks is fine; GPUs differ, and seeds don't reproduce exactly across hardware.
3. If a dataset is far off, stop and work out why before launching the rest. A wrong file or a wrong wavelength would waste the whole screen.

## 7. Running it on Perlmutter

- **GPU:** one run per GPU. Four runs fit on a 4×A100 node.
  - On the workstation's 48 GB GPU, six of these runs shared the card comfortably, so memory isn't a constraint.
  - Turn compilation off only if it fails, and record it if you do.
- **Refinement:** `run_one.sh` refines after training, sequentially, on the CPU (`THREADS`, default 8). On a 4-GPU node, give each run a quarter of the cores.
- **Workstation timings** (10 epochs, sharing one GPU with 2–6 other runs; expect faster on an A100):

  | dataset | training | refinement (per epoch) |
  |---|---|---|
  | cx81s | 25–60 min | about 5 min |
  | cx61 | 40–110 min | about 10 min |
  | cx62 | about 1.5 h | about 10 min |
  | HEWL | 20–50 min | a few min |

  Request about 3 h per job for cx61 and cx62, and 2 h for the others.
- **Starting jobs:**
  - After submitting, confirm every job actually started: the first lines of `$OUT/<name>_s<seed>.log`, and `runs.log`.
  - Only then report anything as "running".
  - Check exit codes in `runs.log`. A training failure still leaves the log.
- **Stopping jobs:** use `scancel` by job id. Don't use `pkill -f` patterns, which can match your own shell.
- `runs.log` in `$OUT` gets one line per start, train, refine and done event, with the commit and flags.

## 8. Measuring

```bash
source rescreen/env.sh
$PY rescreen/measure_runs.py rescreen/phase1.csv $OUT/cx81s_*_s? $OUT/cx61_*_s? $OUT/cx62_*_s? $OUT/hewl_*_s?
```

This adds one row per run and refined epoch (2, 5, 10):

| column | meaning |
|---|---|
| `rfree` | Rfree after TorchRef refinement |
| `rfree_shell` | **primary measure.** The mean Rfree over 10 free-set resolution shells. Overall Rfree favours a steeper falloff; this doesn't |
| `<site>_asis`, `<site>_flat` | anomalous peak heights (σ). cx81s: `Zn`, `Zn2` (the second zinc, HOH A1002). cx61: `Se`, `Se166`. cx62: `Se`. HEWL: `S`. `asis` is the map as refined; `flat` rescales ANOM to unit RMS in every resolution shell. **Report both** |
| `ccanom` | model anomalous CC: the per-shell Pearson CC of observed ΔF against ΔF computed from the refined model, unweighted mean over 10 shells. Call it "model anomalous CC" or CCanom, not CCanom½ |
| `wilson_b` | Wilson B of the merged intensities (fit over d < 4.5 Å). ml (cycle 20) gives HEWL 28.6, cx81s 25.9, cx61 25.3, cx62 17.3, cx81 32.4. The base configuration gives HEWL 32.1, cx81s 30.9, cx61 25.7, cx62 26.2, cx81 34.5. **Lower is not automatically better**; it is reported so we can see shifts in the falloff |
| `outer_cc`, `outer_fofc` | CC and median Fo/Fc in the outermost 10% (by 1/d²) of the free set. This is the user's preferred measure of map quality |
| `val_nll`, `val_ccpred`, `train_nll`, `kl_scale`, `trend_range` | from history.csv at that epoch. For diagnosis only, **not for ranking** |

## 9. Analysis and decisions

For each dataset × arm, take the mean and standard deviation over the 3 seeds at **epoch 10**, and also at epoch 5. Then compute each arm's difference from `base`.

- **A difference counts** when it is larger than twice the base arm's seed standard deviation **and** has the same sign on at least 3 of the 4 datasets, or on both cxidb_81 small and cxidb_61 if those disagree with the rest.
  - The rank order of measures is: `rfree_shell`, then `outer_cc`, then flat and as-is peaks, then `ccanom`, then `rfree`.
  - A change that helps cx81s but costs more than one base seed SD on any other dataset is **not** a win. Report it as a dataset-specific effect.
- **Report the drift** for every arm: epoch 10 minus epoch 5 for `rfree_shell` and the peaks. On cx81s the base gets worse after epoch 5. An arm that removes that drift is interesting even if its epoch-10 numbers tie the base.
- Specific questions to answer:
  1. Does a heavier tail (ν 4–16) or Ev11 at ml's values close the cx81s gap to ml? The ml values are in `workstation_reference.csv`. Does either cost anything on cx61, cx62 or HEWL?
  2. Is relu d256 better than SwiGLU d128 on average over seeds and datasets, or was the cx81s result one lucky seed? Is the effect about the unit type (relu128 against swiglu128) or about capacity (relu256 against relu128, swiglu256 against base)?
  3. Does metadata noise still help? Do the posterior features still help?

## 10. Phase 2: combine the winners

Start this only after showing the user the phase-1 summary.

- **Arms:** a full factorial of the phase-1 changes that counted, at most three of them (≤ 8 arms).
- **Also:** the `base` arm and the best phase-1 single change, so the phase-2 numbers tie back to phase 1.
- **Datasets:** all five, including cxidb_81 full (`cx81`), which is the slowest and most important.
- **Seeds:** 3.
- **Length:** 20 epochs (`--epochs 20`; `run_one.sh` refines epoch 20 too). This shows whether any drift continues beyond epoch 10.
- **Manifest:** build it by editing `make_manifest.py`.

## 11. Optional phase 3: the anisotropic trend

`--posterior-trend-aniso {global,bins}` adds an anisotropic temperature factor to the trend:

- It is a traceless B tensor, averaged over the point group so only the components the symmetry allows can be learned.
- `global` fits one tensor; `bins` fits one per spline knot.
- The workstation is testing it on cx81s and cx61 now.

If those results are positive, the user will ask for it to be added on top of the phase-2 winner. Don't run it unprompted.

## 12. Deliverables

1. `phase1.csv` (and later `phase2.csv`) from `measure_runs.py`, plus `runs.log`.
2. `SUMMARY.md` containing:
   - a table of arm × dataset at epoch 10, as mean ± sd over seeds, for the measures in §8, with ml's values as a reference row;
   - the epoch 5→10 drift;
   - the decisions from §9;
   - answers to the three questions in §9.
3. **Plots by epoch** for every arm: shell Rfree, outer CC, the peaks (flat and as-is) and ccanom at epochs 2, 5 and 10. Show mean and seed spread, with the base arm and ml as reference lines. The user wants per-epoch plots for every new experiment.
4. Commit `phase1.csv`, `runs.log`, `SUMMARY.md` and the plots to this `rescreen` branch, then push it. The run directories under `rescreen/runs/` are large and gitignored; leave them on scratch.

Don't change any defaults or push anything to `torch`. The user decides what becomes a default.

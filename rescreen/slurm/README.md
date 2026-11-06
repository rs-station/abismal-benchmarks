# Slurm launcher for the rescreen on Perlmutter

```bash
source rescreen/env.sh
rescreen/slurm/submit.sh rescreen/phase1.tsv $'_base\t1$' --dry-run   # show the packing
rescreen/slurm/submit.sh rescreen/phase1.tsv $'_base\t1$'             # the four base seed-1 runs (PLAN.md section 6)
rescreen/slurm/submit.sh rescreen/phase1.tsv                          # everything not yet trained
```

- **Training** (`train.sbatch`, account `m5149_g`, `-C gpu -q regular`): up to four runs of one dataset per node, each
  as its own bound job step (`srun -n1 -c 32 --gpus-per-task=1 --exact`), with `STAGE=train run_one.sh`.
- **Refinement** (`refine.sbatch`, account `m5149`, `-C cpu -q regular`): one CPU node per training job, started
  `afterany` the training job. Each run gets 32 cores and refines its epochs concurrently (`STAGE=refine
  REFINE_PARALLEL=1 THREADS=8 run_one.sh`), so GPUs aren't held idle during refinement.
- **Walltime:** 3 h for cx61, cx62 and cx81, 2 h for the others; doubled when the list has `--epochs 20`.
- **Records:** `$OUT/slurm/jobs.tsv` (list, train job, refine job), Slurm logs in `$OUT/slurm/`, run events in
  `$OUT/runs.log`. Re-submitting skips any run with a `trained` line in `runs.log`; to redo a failed run, remove its
  line from `runs.log` first.
- **Stopping:** `scancel <jobid>` (ids in `jobs.tsv`); cancelling a training job still lets its refine job run.

`run_one.sh` with no `STAGE` set behaves as before (train, then refine sequentially), e.g. for an interactive node.

Smoke test (2026-11-06, debug QOS, hewl, 2 epochs × 50 steps): A100-SXM4-40GB, driver 580.178.04, torch
2.13.0+cu130 with compile on; the first epoch took about 105 s (compile), then about 2 s per 50 steps; refinement of
one epoch took about 1 min; `measure_runs.py` ran on the result.

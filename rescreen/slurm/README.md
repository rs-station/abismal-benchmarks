# Running the rescreen on Perlmutter: one job, a pool of GPU workers

Only two pending jobs per user accrue queue priority, so the screen runs as **one multi-node job** per batch of work,
not one job per run.

```bash
source rescreen/env.sh
sbatch -N 8 -t 06:00:00 -o $OUT/pool_%j.out --export=ALL,RESCREEN=$PWD/rescreen rescreen/slurm/pool.sbatch rescreen/phase1.tsv
```

- **`pool.sbatch`** (account `m5149_g`, `-C gpu -q regular`) starts one `srun` step with one task per A100
  (`-n 4N -c 32 --gpus-per-task=1 --cpu-bind=cores`), each running `pool_worker.sh`. Use ONE step: separate `srun`
  steps each take the job's whole memory by default and run one at a time.
- **`pool_worker.sh`** claims the next run from the manifest (atomic `mkdir $OUT/claims/<run>`), longest datasets
  first (cx81, cx62, cx61, cx81s, hewl), trains it with `STAGE=train run_one.sh`, and repeats. It only starts a run
  whose expected time (`MIN_<DS>` minutes; see `minutes()` in the worker) fits in the job's remaining time.
- **Refinement happens during training**, through abismal's TorchRef callback: every epoch
  (`--torchref-frequency 1 --torchref-allow-overlap`), as detached CPU subprocesses with `TORCHREF_NUM_THREADS=2`
  that inherit the task's 16-core binding. abismal waits for the last one before exiting. TorchRef's C++ kernel is
  copied to node-local `/tmp` per task. The refinement settings are the callback defaults, identical to the
  post-hoc refinement in `run_one.sh`.
- **Resuming:** re-submit the same manifest. Finished runs (`claims/<run>/done`) are skipped. A claim with no
  `done` whose job is gone is released and its partial output moved to `$OUT/stale/`. A failed run keeps its claim
  (`done` holds its exit code); to retry it, move `claims/<run>` aside.
- **Records:** `$OUT/runs.log` (start/trained lines with commit and flags), `$OUT/claims/<run>/{owner,done}`, the
  job log `$OUT/pool_<jobid>.out` (worker start/end lines with run times).
- **Backfill:** `STAGE=refine run_one.sh NAME SEED` refines a trained run's epoch 2, 5, 10 (and 20) MTZs after the
  fact, e.g. on an m5149 CPU node, if any callback refinement failed.

## Measurements behind this (2026-11-06, `rescreen/bench/`)

- **TorchRef threads** (CPU node, EPYC 7763; wall time for one refinement): cx81 merge 251/149/129/118/121 s at
  1/2/4/8/16 threads, hewl 224/151/141/125/119 s. Little gain past 2 threads. Twelve concurrent 2-thread refinements
  took 146–215 s each. Peak RSS about 2.9 GB (cx81).
- **Refinement during training** (hewl, A100, 1000 steps/epoch): 34 s/epoch with no refinement, and 34 s/epoch while
  refining every epoch at 2, 4 or 8 TorchRef threads (up to 4 overlapping refinements). The prefetch thread is not
  starved. The run ends about 1 min later, waiting for its last refinement.
- **Pool test** (debug, 1 node, 8 hewl runs × 4 epochs): four tasks at once, each 34 s/epoch, each worker took a
  second run when its first finished, all epochs refined. The first epoch of a node's first wave takes about 140 s
  (cold `torch.compile` cache in `/tmp`), later ones about 73 s.

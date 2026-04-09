#!/usr/bin/env python3
"""
Benchmark reciprocalspaceship loading performance.

Both rs.read_crystfel (stream files) and read_dials_stills use joblib for
parallelism. Control the number of workers with --nproc.

Usage
-----
# Single run at N=4
python benchmarks/load.py --nproc 4

# Sweep over process counts (appending results each time)
for n in 1 2 4 8; do
    python benchmarks/load.py --nproc $n --output load_benchmark.csv --append
done
"""

import argparse
import csv
import glob
import os
import threading
import time
import tracemalloc

import psutil
import reciprocalspaceship as rs
from reciprocalspaceship.io import read_dials_stills

from mpi4py import MPI
from mpi4py.util import pkl5

_comm_world = MPI.COMM_WORLD
MPI_RANK = _comm_world.Get_rank()
MPI_SIZE = _comm_world.Get_size()
USE_MPI = MPI_SIZE > 1
MPI_COMM = pkl5.Intracomm(_comm_world) if USE_MPI else None

DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

DATASETS = {
    "cxidb_61": {
        "type": "stream",
        "files": [os.path.join(DATA_ROOT, "cxidb_61/reflection_data/all.stream")],
    },
    "cxidb_62": {
        "type": "stream",
        "files": [os.path.join(DATA_ROOT, "cxidb_62/reflection_data/all-amb.stream")],
    },
    "cxidb_81": {
        "type": "dials",
        "files": sorted(
            glob.glob(os.path.join(DATA_ROOT, "cxidb_81/reflection_data/figure7/*.refl"))
        ),
    },
    "cxidb_81_small": {
        "type": "dials",
        "files": [
            os.path.join(
                DATA_ROOT,
                "cxidb_81/reflection_data/figure7/r0011_t016_rg013_chunk000_reintegrated.refl",
            ),
        ],
    },
    "hewl": {
        "type": "mtz",
        "files": [os.path.join(DATA_ROOT, "hewl/reflection_data/unmerged.mtz")],
    },
}


def _rss_monitor(stop_event, peak_ref, t0, heartbeat_interval=10):
    """Background thread: poll RSS every 100 ms, track the maximum, and print a heartbeat."""
    proc = psutil.Process()
    last_heartbeat = 0
    while not stop_event.is_set():
        rss = proc.memory_info().rss / 1024**2  # MB
        if rss > peak_ref[0]:
            peak_ref[0] = rss
        elapsed = time.perf_counter() - t0
        if elapsed - last_heartbeat >= heartbeat_interval:
            print(f"  still loading... {elapsed:.0f}s  RSS: {rss:.0f} MB", flush=True)
            last_heartbeat = elapsed
        time.sleep(0.1)


def load_dataset(name, dataset, nproc):
    """Load a dataset and return (ds, num_reflections)."""
    dtype = dataset["type"]

    if dtype == "stream":
        ds = rs.read_crystfel(dataset["files"][0], num_cpus=nproc)
        return ds, len(ds)

    elif dtype == "mtz":
        ds = rs.read_mtz(dataset["files"][0])
        return ds, len(ds)

    elif dtype == "dials":
        if USE_MPI:
            from reciprocalspaceship.io.dials_mpi import read_dials_stills_mpi
            data = read_dials_stills_mpi(dataset["files"], None, None, comm=MPI_COMM)
            length = 0
            if data is not None:
                for ds in data:
                    length += len(ds)
            return data,length
        else:
            backend = "joblib" if nproc > 1 else None
            ds = read_dials_stills(dataset["files"], parallel_backend=backend, numjobs=nproc)
        if ds is None:
            return None, 0
        return ds, len(ds)

    else:
        raise ValueError(f"Unknown dataset type: {dtype}")


def run_benchmark(datasets, nproc, output_csv, append):
    results = []

    if MPI_RANK == 0:
        nworkers = MPI_SIZE if USE_MPI else nproc
        print(f"\nBenchmarking {len(datasets)} dataset(s) with {nworkers} worker(s)", flush=True)
        print(f"Output: {output_csv}\n", flush=True)

    for i, (name, dataset) in enumerate(datasets.items(), 1):
        dtype = dataset["type"]
        n_files = len(dataset["files"])

        # In MPI mode, non-dials datasets have no collective operation so rank > 0
        # would race ahead and deadlock when the next dials dataset is reached.
        if USE_MPI and dtype != "dials":
            if MPI_RANK == 0:
                print(f"[{i}/{len(datasets)}] {name}  skipping (non-dials not supported in MPI mode)", flush=True)
            continue

        # Ranks > 0 only participate in the collective load; rank 0 does all monitoring.
        if USE_MPI and MPI_RANK > 0:
            from reciprocalspaceship.io.dials_mpi import read_dials_stills_mpi
            read_dials_stills_mpi(dataset["files"], None, None, comm=MPI_COMM)
            continue

        print(
            f"[{i}/{len(datasets)}] {name}  type={dtype}  files={n_files}  nproc={MPI_SIZE if USE_MPI else nproc}",
            flush=True,
        )
        if dtype == "stream":
            print(f"  reader: rs.read_crystfel  backend: joblib  num_cpus={nproc}", flush=True)
        elif dtype == "dials":
            backend = "mpi" if USE_MPI else ("joblib" if nproc > 1 else "serial")
            nworkers = MPI_SIZE if USE_MPI else nproc
            print(f"  reader: read_dials_stills  backend: {backend}  numjobs={nworkers}  refl_files={n_files}", flush=True)
        elif dtype == "mtz":
            print(f"  reader: rs.read_mtz  backend: serial", flush=True)
        print("  loading...", flush=True)

        peak_ref = [psutil.Process().memory_info().rss / 1024**2]
        stop_event = threading.Event()
        tracemalloc.start()
        t0 = time.perf_counter()
        monitor = threading.Thread(target=_rss_monitor, args=(stop_event, peak_ref, t0), daemon=True)
        monitor.start()
        ds, n_refl = load_dataset(name, dataset, nproc)
        elapsed = time.perf_counter() - t0
        _, peak_python_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        stop_event.set()
        monitor.join()

        peak_rss_mb = peak_ref[0]
        peak_python_mb = peak_python_bytes / 1024**2

        row = {
            "dataset": name,
            "type": dtype,
            "num_cpus": MPI_SIZE if USE_MPI else nproc,
            "time_s": round(elapsed, 3),
            "peak_rss_mb": round(peak_rss_mb, 1),
            "peak_python_mb": round(peak_python_mb, 1),
            "num_reflections": n_refl,
        }
        results.append(row)

        print(f"  done in {elapsed:.1f}s", flush=True)
        print(f"  reflections:      {n_refl:,}", flush=True)
        print(f"  RSS peak:         {peak_rss_mb:.0f} MB", flush=True)
        print(f"  Python heap peak: {peak_python_mb:.0f} MB", flush=True)
        print(flush=True)
        del ds

    if results:
        fieldnames = list(results[0].keys())
        mode = "a" if append and os.path.exists(output_csv) else "w"
        with open(output_csv, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == "w":
                writer.writeheader()
            writer.writerows(results)
        print(f"Results {'appended to' if mode == 'a' else 'saved to'} {output_csv}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark rs data loading")
    parser.add_argument(
        "--nproc",
        type=int,
        default=1,
        help="Number of parallel workers (default: 1)",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=list(DATASETS.keys()),
        default=list(DATASETS.keys()),
        help="Datasets to benchmark (default: all)",
    )
    parser.add_argument(
        "--output",
        default="load_benchmark.csv",
        help="Output CSV file (default: load_benchmark.csv)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing CSV instead of overwriting",
    )
    args = parser.parse_args()

    selected = {k: DATASETS[k] for k in args.datasets}
    run_benchmark(selected, args.nproc, args.output, args.append)


if __name__ == "__main__":
    main()

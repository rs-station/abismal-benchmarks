# abismal-benchmarks
Scripts for abismal benchmarking and development of ABISMAL. 

# Setup
 1) install the dependencies, `abismal`, `phenix`, and `careless`. For data localization you will need the standard command line programs `wget`, `bunzip2`, and `tar`
 1b) per-epoch refinement runs through `torchref` in its own environment, pointed at by `ABISMAL_TORCHREF_PYTHON` in `setup.sh`. That environment also needs `scikit-image`, which the torchref worker uses for anomalous peak finding. Install it with numpy pinned -- a bare `pip install scikit-image` pulls numpy 2.5 and breaks both tensorflow (<2.1.0) and torchref (<2.4.0):
    ```
    pip install "numpy==2.0.2" "scikit-image==0.24.0"
    ```
    Sourcing `setup.sh` verifies both and warns if they are wrong.
 2) clone the benchmarks repo onto your cluster filesystem. `git clone https://github.com/rs-station/abismal-benchmarks`
 3) Enter the benchmarks directory `cd abismal-benchmarks`
 4) Modify the `setup.sh` script to source the right files to get the dependencies into your path. 
 5) Download the source dataset. First `source setup.sh` then run `download_examples`.
 6) Modify the SLURM preamble at the top of `benchmarks/job.sh`
 7) Run the benchmarks by executing `./submit_jobs.sh` from the `benchmarks` directory

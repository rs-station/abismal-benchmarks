# abismal-benchmarks
Scripts for abismal benchmarking and development of ABISMAL. 

# Setup
 1) install the dependencies, `abismal`, `phenix`, and `careless`. For data localization you will need the standard command line programs `wget`, `bunzip2`, and `tar`
 1b) per-epoch refinement runs through `torchref` in the same environment as abismal -- there is no second environment and no `ABISMAL_TORCHREF_PYTHON`. Install it with the `torchref` extra, which also brings the `scikit-image` the worker uses for anomalous peak finding:
    ```
    micromamba create -yn abismal -c conda-forge python=3.12 dials "pandas<2.4" "scipy<1.18"
    micromamba activate abismal
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install -e "/path/to/abismal[dev,cuda,torchref]"
    ```
    Refinement runs on CPU, so install the CPU build of PyTorch first -- the CUDA build is several unused gigabytes, and it cannot be safely uninstalled later. Extras compose, so ask for all of them in one command.
    The pins keep numpy inside the one window tensorflow, torchref and dxtbx all accept; see "About the version pins" in the abismal README. Sourcing `setup.sh` checks the active environment and warns if anything is missing.
 2) clone the benchmarks repo onto your cluster filesystem. `git clone https://github.com/rs-station/abismal-benchmarks`
 3) Enter the benchmarks directory `cd abismal-benchmarks`
 4) Modify the `setup.sh` script to source the right files to get the dependencies into your path. 
 5) Download the source dataset. First `source setup.sh` then run `download_examples`.
 6) Modify the SLURM preamble at the top of `benchmarks/job.sh`
 7) Run the benchmarks by executing `./submit_jobs.sh` from the `benchmarks` directory

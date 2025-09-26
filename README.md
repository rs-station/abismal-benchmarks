# abismal-benchmarks
Scripts for abismal benchmarking and development of ABISMAL. 

# Setup
 1) install the dependencies, `abismal`, `phenix`, and `careless`. For data localization you will need the standard command line programs `wget`, `bunzip2`, and `tar`
 2) clone the benchmarks repo onto your cluster filesystem. `git clone https://github.com/rs-station/abismal-benchmarks`
 3) Enter the benchmarks directory `cd abismal-benchmarks`
 4) Modify the `setup.sh` script to source the right files to get the dependencies into your path. 
 5) Download the source dataset. First `source setup.sh` then run `download_examples`.

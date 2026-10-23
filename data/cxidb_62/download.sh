mkdir -p $ABISMAL_BENCHMARKS/data/cxidb_62/reflection_data
cd $ABISMAL_BENCHMARKS/data/cxidb_62/reflection_data
wget https://www.cxidb.org/data/62/all-amb.stream.bz2
bunzip2 all-amb.stream.bz2

# The deposited stream has nearly every crystal in one indexing setting already. For testing indexing-ambiguity
# resolution, also write a copy with each crystal reindexed by the twin operator (h, k, l) -> (k, h, -l) with
# probability 1/2 (fixed seed), and which ones were flipped (all-amb-scrambled.labels.csv).
python $ABISMAL_BENCHMARKS/data/cxidb_62/scramble_stream.py all-amb.stream all-amb-scrambled.stream --seed 2026

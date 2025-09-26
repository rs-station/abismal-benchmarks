mkdir -p $ABISMALDIR/data/cxidb_61/reflection_data
cd $ABISMALDIR/data/cxidb_61/reflection_data
wget https://www.cxidb.org/data/61/all.stream.bz2
tar xvf all.stream.bz2
rm all.stream.bz2

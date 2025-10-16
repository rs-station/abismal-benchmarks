set_anom_sigma 5.0, 2.0
load_pdb refine_001.pdb

load_phenix_mtz refine_001.mtz, selection=refine_001, carve=2.0
show spheres
hide volume, fofc_p
hide volume, fofc_m

set_view (\
    -0.445643276,    0.892736971,    0.066482835,\
    -0.874519885,   -0.418276191,   -0.245444894,\
    -0.191312164,   -0.167521343,    0.967125893,\
     1.322641850,   -1.602244377,  -28.811153412,\
     8.746000290,    4.153999805,   10.748000145,\
    26.006135941,   35.416069031,  -20.000000000 )

draw 4000, 3000, antialias=2
save mse_144.png

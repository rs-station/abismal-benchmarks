set_anom_sigma 5.0, 2.0
load_pdb refine_001.pdb

load_phenix_mtz refine_001.mtz, selection=refine_001, carve=2.0
show spheres
hide volume, fofc_p
hide volume, fofc_m

set_view (\
     0.834934473,    0.336691290,   -0.435342550,\
     0.021605963,    0.770360827,    0.637233734,\
     0.549925923,   -0.541457832,    0.635928452,\
     0.752164960,   -1.878951788,  -39.482131958,\
    13.265250206,    9.105250359,    2.613499880,\
    35.427181244,   44.637104034,  -20.000000000 )

draw 4000, 3000, antialias=2
save mse_144.png

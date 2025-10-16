set_anom_sigma 5.0, 2.0
load_pdb refine_001.pdb

load_phenix_mtz refine_001.mtz, selection=refine_001, carve=2.0
show spheres
hide volume, fofc_p
hide volume, fofc_m

set_view (\
     0.860513926,   -0.501015782,   -0.092199318,\
     0.142660618,    0.410745353,   -0.900514662,\
     0.489046186,    0.761755705,    0.424929649,\
     5.017398834,   -2.631676197,  -40.799591064,\
    15.411874771,   10.612125397,   18.692501068,\
    35.500091553,   46.099090576,  -20.000000000 )

draw 4000, 3000, antialias=2
save mse_144.png

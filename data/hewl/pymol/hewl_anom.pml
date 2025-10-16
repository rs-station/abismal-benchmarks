set_anom_sigma 5.0, 2.0
load_pdb refine_001.pdb

load_phenix_mtz refine_001.mtz, selection=refine_001, carve=2.0
disable 2fofc

show cartoon
hide sticks
hide spheres
show sticks, (resn cys or resn met) and (sidechain or name ca)
show spheres, (resn cys or resn met) and (sidechain or name ca)
hide everything, hydro

set_view (\
     0.705993533,    0.326296359,   -0.628571510,\
     0.149204165,   -0.936147034,   -0.318379849,\
    -0.692322075,    0.130988404,   -0.709597826,\
    -3.028208017,   -1.169481993,  -93.746337891,\
    35.358253479,   17.617406845,   10.723238945,\
    60.734214783,  127.851821899,  -20.000000000 )

draw 4000, 3000, antialias=2
save hewl_anom.png

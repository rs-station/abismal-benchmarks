load_phenix refine_001.mtz, refine_001.pdb, carve=2.0
show spheres
hide volume, fofc_p
hide volume, fofc_m

set_view (\
     0.436641395,    0.276933819,   -0.855940580,\
    -0.576923907,   -0.643836439,   -0.502617896,\
    -0.690281987,    0.713284671,   -0.121355355,\
    -2.127886772,    0.749814987,  -40.065052032,\
    35.888141632,   46.590656281,   -7.084664345,\
    36.365051270,   43.730648041,  -20.000000000 )

hide volume, fofc_p
hide volume, fofc_m

draw 4000, 3000, antialias=2
save thermolysin.png

load_phenix refine_001.mtz, refine_001.pdb, carve=2.0
hide sticks, resi 157 #remove disordered active site tyrosine

set_view (\
     0.622224331,    0.206181481,   -0.755186617,\
    -0.434614331,   -0.711371660,   -0.552314997,\
    -0.651100576,    0.671887696,   -0.353025347,\
    -0.000122017,    0.000038601,  -42.053745270,\
    35.888141632,   46.590656281,   -7.084664345,\
    38.353744507,   45.719341278,  -20.000000000 )

hide volume, fofc_p
hide volume, fofc_m

draw 4000, 3000, antialias=2
save thermolysin.png

"""Write phase1.tsv: one line per run (name, seed, flags), every arm x dataset x seed. Each arm changes one thing from
the base configuration in run_one.sh. Ev11 a, b are abismal.ml's fitted values per dataset."""
EV11 = {'hewl': (0.994, 0.047), 'cx81s': (20.72, 0.1969), 'cx61': (1.812, 0.3045), 'cx62': (2.821, 0.7809), 'cx81': (11.51, 0.3252)}
RELU = '--pre-activation relu --activation relu --no-gated --hidden-multiplier 2'
ARMS = {
    'base': '',
    # likelihood tails
    'nu4': '--studentt-dof 4', 'nu8': '--studentt-dof 8', 'nu16': '--studentt-dof 16', 'nu64': '--studentt-dof 64',
    'normal': '--studentt-dof none',
    # error model held at abismal.ml's values
    'ev11t': '--error-model ev11 --error-model-a {a} --error-model-b {b} --fix-error-model',
    'ev11n': '--error-model ev11 --error-model-a {a} --error-model-b {b} --fix-error-model --studentt-dof none',
    # scale network
    'relu128': f'--d-model 128 {RELU}', 'relu256': f'--d-model 256 {RELU}',
    'swiglu64': '--d-model 64', 'swiglu256': '--d-model 256', 'depth3': '--layers 3', 'depth10': '--layers 10',
    # regularization of the scale network
    'noise0': '--metadata-noise-factor 0', 'noise0.3': '--metadata-noise-factor 0.3', 'nopostfeat': '--no-posterior-features',
}
with open('phase1.tsv', 'w') as f:
    f.write('name\tseed\tflags\n')
    for ds in ('cx81s', 'cx61', 'cx62', 'hewl'):
        a, b = EV11[ds]
        for arm, flags in ARMS.items():
            for seed in (1, 2, 3):
                f.write(f'{ds}_{arm}\t{seed}\t{flags.format(a=a, b=b)}\n')
print(sum(1 for _ in open('phase1.tsv')) - 1, 'runs')

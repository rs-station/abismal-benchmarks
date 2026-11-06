"""Freeze the resolution shells the measures use (written once on the workstation; edges.json ships with the plan).
ccanom: 10 shells equal in count of 1/d^2 over the model's anomalous reflections; rfree_shells: 10 over the free set.
Both from bench_obsnll/<ds>_s1 at epoch 10, the same base the workstation tables used."""
import sys, json, numpy as np, reciprocalspaceship as rs
sys.path.insert(0, sys.argv[2]); import measures as M
R = sys.argv[1] + '/'
KEY = {'hewl': 'hewl', 'cx81s': 'cxidb', 'cx81': 'cxidb', 'cx61': 'cx61', 'cx62': 'cx62'}
out = {}
for ds, key in KEY.items():
    base = R + f'bench_obsnll/{ds}_s1/torchref_0_asu_0_epoch_10'
    _, _, q = M.model_delta_f(base, key)
    m = rs.read_mtz(base + '/refined.mtz').compute_dHKL().dropna(subset=['F-obs', 'F-model'])
    qf = m[m['R-free-flags'].to_numpy() == 0].dHKL.to_numpy(float) ** -2
    out[ds] = dict(key=key, ccanom=np.quantile(q, np.linspace(0, 1, 11)).tolist(), rfree=np.quantile(qf, np.linspace(0, 1, 11)).tolist())
    print(ds, len(q), len(qf))
json.dump(out, open(sys.argv[2] + '/edges.json', 'w'), indent=1)

"""Measure merged + refined runs and append one row per (run, epoch) to a CSV.

usage: ABISMAL=<checkout> python measure_runs.py out.csv <run_dir> [<run_dir> ...]
A run dir is <results>/<name> holding asu_0_epoch_N.mtz, history.csv and torchref_0_asu_0_epoch_N/refined.mtz; the
dataset is the name's first '_' field (hewl, cx81s, cx81, cx61, cx62). abismal.ml references (cycle_N) work too.
Columns: run, ds, epoch, rfree, rfree_shell (mean over 10 free-set shells), peaks as-is and flat (dataset-specific),
ccanom (model anomalous CC, unweighted mean over 10 shells), wilson_b (merged I, d < 4.5 A), outer_cc and outer_fofc
(free set, top 10% of 1/d^2), plus val_nll, val_ccpred, kl_scale and trend_range from history.csv at that epoch."""
import os, re, sys, json, numpy as np, pandas as pd, reciprocalspaceship as rs
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import measures as M
EDGES = json.load(open(os.path.join(HERE, 'edges.json')))

def wilson(p):
    s = rs.read_mtz(p)[['I(+)', 'I(-)']].stack_anomalous().dropna(subset=['I']).compute_dHKL().compute_multiplicity()
    q, v = s.dHKL.to_numpy() ** -2, s.I.to_numpy(float) / s.EPSILON.to_numpy(float)
    k = q >= 4.5 ** -2; q, v = q[k], v[k]
    e = np.quantile(q, np.linspace(0, 1, 16)); lab = np.clip(np.searchsorted(e, q, side='right') - 1, 0, 14)
    x = np.array([q[lab == i].mean() for i in range(15)]); y = np.array([v[lab == i].mean() for i in range(15)]); ok = y > 0
    return -2 * np.polyfit(x[ok], np.log(y[ok]), 1)[0]

def outer(rd):
    m = rs.read_mtz(rd + '/refined.mtz').compute_dHKL().dropna(subset=['F-obs', 'F-model'])
    m = m[m['R-free-flags'].to_numpy() == 0]; q = m.dHKL.to_numpy() ** -2; s = q >= np.quantile(q, .9)
    fo, fm = m['F-obs'].to_numpy(float)[s], m['F-model'].to_numpy(float)[s]
    return np.corrcoef(fo, fm)[0, 1], np.median(fo / fm)

rows = []
for run in sys.argv[2:]:
    run = run.rstrip('/'); name = os.path.basename(run); ds = name.split('_')[0]
    if ds not in EDGES:
        print('skip (unknown dataset)', run); continue
    key, e = EDGES[ds]['key'], EDGES[ds]
    h = pd.read_csv(run + '/history.csv') if os.path.exists(run + '/history.csv') else None
    for rd in sorted(d for d in os.listdir(run) if d.startswith('torchref_0_asu_0_')):
        tag = rd[len('torchref_0_asu_0_'):]; rd = f'{run}/{rd}'
        if not os.path.exists(rd + '/refined.mtz'):
            continue
        epoch = int(re.sub(r'\D', '', tag))
        row = dict(run=name, ds=ds, epoch=epoch, rfree=M.rfree(rd), rfree_shell=M.rfree_shells(rd, np.array(e['rfree']))['mean'],
                   ccanom=M.ccanom(rd, key, np.array(e['ccanom']))['mean'], wilson_b=wilson(f'{run}/asu_0_{tag}.mtz'))
        for w in ('asis', 'flat'):
            for k, v in M.heights(rd, key, w).items():
                row[f'{k}_{w}'] = v
        row['outer_cc'], row['outer_fofc'] = outer(rd)
        if h is not None and 'val_NLL' in h and tag.startswith('epoch'):
            i = min(epoch, len(h) - 1)
            for col, k in (('val_NLL', 'val_nll'), ('val_CCpred', 'val_ccpred'), ('KL_Σ', 'kl_scale'), ('TrendRange', 'trend_range'), ('NLL', 'train_nll')):
                if col in h:
                    row[k] = h[col].iloc[i]
        rows.append(row); print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)
out = pd.DataFrame(rows)
out.to_csv(sys.argv[1], mode='a', header=not os.path.exists(sys.argv[1]), index=False)

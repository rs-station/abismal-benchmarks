"""Phase-1 analysis (PLAN.md sections 9 and 12): tables, drift, decisions and per-epoch plots.

    python analyze_phase1.py phase1.csv workstation_reference.csv OUTDIR

Writes OUTDIR/tables.md (arm x dataset at epoch 10 as mean +- sd over seeds, with ml; the epoch 5->10 drift; the
section-9 decision for every arm and measure) and OUTDIR/plots/*.png (each measure by epoch, mean and seed range,
with base and ml as references). Epoch 10 and epoch 5 decisions are both reported.
"""
import sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

csv, ref, out = sys.argv[1:4]
os.makedirs(f'{out}/plots', exist_ok=True)

DS = ['cx81s', 'cx61', 'cx62', 'hewl']
SITES = {'cx81s': ['Zn', 'Zn2'], 'cx61': ['Se', 'Se166'], 'cx62': ['Se'], 'hewl': ['S']}
GROUPS = {'tails': ['nu4', 'nu8', 'nu16', 'nu64', 'normal'],
          'error model': ['ev11t', 'ev11n'],
          'unit / width': ['relu128', 'relu256', 'swiglu64', 'swiglu256'],
          'depth': ['depth3', 'depth10'],
          'regularization': ['noise0', 'noise0.3', 'nopostfeat']}
ARMS = ['base'] + [a for g in GROUPS.values() for a in g]
# (column, label, +1 if higher is better); peak1/peak2 are each dataset's first/second anomalous site.
MEASURES = [('rfree_shell', 'shell Rfree', -1), ('outer_cc', 'outer CC', +1),
            ('peak1_flat', 'peak, flat (σ)', +1), ('peak1_asis', 'peak, as-is (σ)', +1),
            ('ccanom', 'CCanom', +1), ('rfree', 'Rfree', -1)]
EXTRA = [('peak2_flat', '2nd peak, flat (σ)', +1), ('peak2_asis', '2nd peak, as-is (σ)', +1),
         ('wilson_b', 'Wilson B', 0), ('outer_fofc', 'outer Fo/Fc', 0)]

def tidy(df):
    df = df.copy()
    for ds, sites in SITES.items():
        m = df.ds == ds
        for i, s in enumerate(sites, 1):
            for w in ('asis', 'flat'):
                if f'{s}_{w}' in df:
                    df.loc[m, f'peak{i}_{w}'] = df.loc[m, f'{s}_{w}']
    return df

d = tidy(pd.read_csv(csv))
d['arm'] = d.run.str.replace(r'^[a-z0-9]+_', '', regex=True).str.replace(r'_s\d+$', '', regex=True)
d['seed'] = d.run.str.extract(r'_s(\d+)$')[0].astype(int)
r = tidy(pd.read_csv(ref))
ml = r[r.run.isin(['hewl_l2_0', 'cx81s_l2_0', 'cx61_l2_0', 'cx62']) & (r.epoch == 20)].set_index('ds')

cols = [m[0] for m in MEASURES + EXTRA]
g = d.groupby(['ds', 'arm', 'epoch'])[cols]
mean, sd, n = g.mean(), g.std(), g.count()
lo, hi = g.min(), g.max()

def fmt(v, c):
    if pd.isna(v): return '–'
    return f'{v:.4f}' if c in ('rfree', 'rfree_shell', 'outer_cc', 'ccanom', 'outer_fofc') else f'{v:.2f}'

L = ['# Phase 1 tables', '', f'Source: `{os.path.basename(csv)}`. Mean ± sd over seeds (n in the coverage table). '
     'ml is abismal.ml at cycle 20 on the workstation (`workstation_reference.csv`).', '']
# coverage
cov = d[d.epoch == 10].groupby(['arm', 'ds']).seed.nunique().unstack().reindex(index=ARMS, columns=DS)
L += ['## Seeds with an epoch-10 refinement', '', '| arm | ' + ' | '.join(DS) + ' |', '|---' * (len(DS) + 1) + '|']
L += [f'| {a} | ' + ' | '.join('–' if pd.isna(v) else str(int(v)) for v in cov.loc[a]) + ' |' for a in ARMS] + ['']

for c, lab, _ in MEASURES + EXTRA:
    L += [f'## {lab} (`{c}`), epoch 10', '', '| arm | ' + ' | '.join(DS) + ' |', '|---' * (len(DS) + 1) + '|']
    for a in ARMS:
        cells = []
        for ds in DS:
            k = (ds, a, 10)
            cells.append(f'{fmt(mean[c].get(k), c)} ± {fmt(sd[c].get(k), c)}' if k in mean.index and not pd.isna(mean[c].get(k)) else '–')
        L.append(f'| {a} | ' + ' | '.join(cells) + ' |')
    L.append('| **ml** | ' + ' | '.join(fmt(ml[c].get(ds) if c in ml else np.nan, c) for ds in DS) + ' |')
    L.append('')

# drift: epoch 10 minus epoch 5, mean over seeds of the per-seed difference
L += ['## Drift, epoch 10 − epoch 5 (mean over seeds)', '']
for c, lab in (('rfree_shell', 'shell Rfree'), ('peak1_flat', 'peak flat'), ('peak1_asis', 'peak as-is'),
               ('peak2_flat', '2nd peak flat'), ('peak2_asis', '2nd peak as-is')):
    p = d.pivot_table(index=['ds', 'arm', 'seed'], columns='epoch', values=c)
    if 10 not in p or 5 not in p: continue
    dr = (p[10] - p[5]).groupby(['ds', 'arm']).mean()
    L += [f'**{lab}**', '', '| arm | ' + ' | '.join(DS) + ' |', '|---' * (len(DS) + 1) + '|']
    for a in ARMS:
        L.append(f'| {a} | ' + ' | '.join(('–' if (ds, a) not in dr.index or pd.isna(dr[(ds, a)]) else
                                           (f'{dr[(ds, a)]:+.4f}' if c == 'rfree_shell' else f'{dr[(ds, a)]:+.2f}')) for ds in DS) + ' |')
    L.append('')

# decisions (section 9)
def decide(epoch):
    rows = []
    for a in ARMS[1:]:
        for c, lab, better in MEASURES:
            sig, diff, cost = {}, {}, []
            for ds in DS:
                kb, ka = (ds, 'base', epoch), (ds, a, epoch)
                if ka not in mean.index or kb not in mean.index or pd.isna(mean[c].get(ka)) or pd.isna(mean[c].get(kb)):
                    continue
                dv, s = mean[c][ka] - mean[c][kb], sd[c][kb]
                diff[ds] = dv
                sig[ds] = int(np.sign(dv)) if abs(dv) > 2 * s else 0
                if better * dv < -s:
                    cost.append(ds)
            ups = [ds for ds in sig if sig[ds] * better > 0]
            downs = [ds for ds in sig if sig[ds] * better < 0]
            verdict = ''
            if len(ups) >= 3 or ('cx81s' in ups and 'cx61' in ups):
                verdict = 'better' if not cost else 'dataset-specific (costs >1 sd on ' + ', '.join(cost) + ')'
            elif len(downs) >= 3 or ('cx81s' in downs and 'cx61' in downs):
                verdict = 'worse'
            elif ups and not cost:
                verdict = 'better on ' + ', '.join(ups) + ' only'
            elif ups:
                verdict = 'mixed: better on ' + ', '.join(ups) + ', costs on ' + ', '.join(cost)
            elif downs:
                verdict = 'worse on ' + ', '.join(downs) + ' only'
            rows.append((a, lab, diff, sig, verdict))
    return rows

for epoch in (10, 5):
    L += [f'## Section-9 decisions at epoch {epoch}', '',
          'Difference from base (arm − base, mean over seeds); `*` marks |diff| > 2 × base seed sd. "better"/"worse" '
          'follow the rule in PLAN.md §9 (same sign on ≥3 of 4 datasets, or on both cx81s and cx61); a change that '
          'helps but costs more than one base sd on any dataset is dataset-specific.', '',
          '| arm | measure | ' + ' | '.join(DS) + ' | verdict |', '|---' * (len(DS) + 3) + '|']
    for a, lab, diff, sig, verdict in decide(epoch):
        cells = []
        for ds in DS:
            if ds not in diff: cells.append('–'); continue
            f = f'{diff[ds]:+.4f}' if 'Rfree' in lab or lab in ('outer CC', 'CCanom') else f'{diff[ds]:+.2f}'
            cells.append(f + ('*' if sig[ds] else ''))
        L.append(f'| {a} | {lab} | ' + ' | '.join(cells) + f' | {verdict} |')
    L.append('')
open(f'{out}/tables.md', 'w').write('\n'.join(L))

# plots: one figure per measure, rows = datasets, columns = arm groups
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4']   # reference categorical slots 1-5, fixed order
MK = ['o', 's', '^', 'D', 'v']
INK, MUTED, SURF = '#0b0b0b', '#52514e', '#fcfcfb'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'xtick.color': MUTED,
                     'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#e4e3df', 'grid.linewidth': 0.6, 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'savefig.facecolor': SURF})

def series(ds, a, c):
    idx = [(ds, a, e) for e in sorted(d[(d.ds == ds) & (d.arm == a)].epoch.unique())]
    idx = [k for k in idx if k in mean.index and not pd.isna(mean[c].get(k))]
    e = np.array([k[2] for k in idx])
    return e, np.array([mean[c][k] for k in idx]), np.array([lo[c][k] for k in idx]), np.array([hi[c][k] for k in idx])

for c, lab, better in MEASURES + EXTRA[:2]:
    rows = [ds for ds in DS if ((d.ds == ds) & d[c].notna()).any()] if c in d else []
    if not rows: continue
    fig, axs = plt.subplots(len(rows), len(GROUPS), figsize=(3.1 * len(GROUPS), 2.3 * len(rows) + 0.6),
                            sharex=True, squeeze=False)
    for i, ds in enumerate(rows):
        # Zoom each row to epochs >= 2 of every arm but `normal` (and ml), so one off-scale arm or the epoch-1 merge
        # doesn't flatten the rest; anything outside is labelled off scale.
        vals = []
        for a in ARMS:
            if a == 'normal': continue
            e, m, l, h = series(ds, a, c)
            vals += list(l[e >= 2]) + list(h[e >= 2])
        if c in ml and ds in ml.index and not pd.isna(ml.loc[ds, c]): vals.append(ml.loc[ds, c])
        ymin, ymax = np.nanmin(vals), np.nanmax(vals); pad = 0.08 * (ymax - ymin or 1)
        ylim = (ymin - pad, ymax + pad)
        for j, (gname, arms) in enumerate(GROUPS.items()):
            ax = axs[i, j]
            ax.set_ylim(*ylim); ax.set_xlim(0.7, 10.3)
            off = [a for a in arms if len(series(ds, a, c)[0]) and
                   not (ylim[0] <= series(ds, a, c)[1][-1] <= ylim[1])]
            if off:
                ax.text(0.98, 0.02, 'off scale at e10: ' + ', '.join(
                    f'{a} {fmt(series(ds, a, c)[1][-1], c)}' for a in off), transform=ax.transAxes,
                    ha='right', va='bottom', fontsize=7, color=MUTED)
            e, m, l, h = series(ds, 'base', c)
            ax.fill_between(e, l, h, color=MUTED, alpha=0.15, lw=0)
            ax.plot(e, m, color=INK, lw=2, label='base')
            for k, a in enumerate(arms):
                e, m, l, h = series(ds, a, c)
                if not len(e): continue
                ax.fill_between(e, l, h, color=PAL[k], alpha=0.15, lw=0)
                ax.plot(e, m, color=PAL[k], lw=2, marker=MK[k], ms=4, label=a)
            if c in ml and ds in ml.index and not pd.isna(ml.loc[ds, c]):
                ax.axhline(ml.loc[ds, c], color=MUTED, ls='--', lw=1.2, label='ml (cycle 20)')
            if i == 0: ax.set_title(gname, fontsize=10, color=INK)
            if j == 0: ax.set_ylabel(f'{ds}\n{lab}')
            if i == len(rows) - 1: ax.set_xlabel('epoch')
            if i == len(rows) - 1:
                ax.legend(fontsize=7, frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.32), ncol=2)
    arrow = {-1: 'lower is better', 1: 'higher is better', 0: ''}[better]
    fig.suptitle(f'{lab} by epoch: mean over seeds, band = seed range ({arrow})', color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(f'{out}/plots/phase1_{c}.png', dpi=130)
    plt.close(fig)
print('wrote', f'{out}/tables.md', 'and', f'{out}/plots/')

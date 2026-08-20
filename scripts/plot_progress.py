import pandas as pd
from pylab import *
import seaborn as sns
import reciprocalspaceship as rs
import re
from os.path import dirname,abspath


csv_file = "history.csv"
title = dirname(abspath(csv_file))
print(title)

csv = pd.read_csv(csv_file)
palette_name='Dark2'

#A list of anything that has ever been a key in history.csv
keys = [
#    "Epoch",
#    "Time (s)",
#    "FB Total (MiB)",
#    "FB Reserved (MiB)",
#    "FB Used (MiB)",
#    "FB Free (MiB)",
#    "BAR1 Total (MiB)",
#    "BAR1 Used (MiB)",
#    "BAR1 Free (MiB)",
#    "Conf Compute Protected Total (MiB)",
#    "Conf Compute Protected Used (MiB)",
#    "Conf Compute Protected Free (MiB)",
    "loss",
    "Istd",
    "Icount",
    "NLL",
    "wCCpred",
    "CCpred",
    #"Σ_loc",
    #"Σ_scale",
    #"Σ_mean",
    #"Σ_std",
    "|∇s|",
    "|∇q|",
    "WilsonB",
    "WilsonK",
]

for k in csv:
    if 'KL' in k:
        keys.append(k)


if keys is not None:
    active_keys = ['Epoch']
    for k in keys:
        if k in csv:
            active_keys.append(k)
            vk = 'val_' + k
            if vk in csv:
                active_keys.append(vk)
    csv = csv[active_keys]

plt.figure()
df = csv.melt("Epoch")
df['Test'] = df.variable.str.startswith("val_")
df['variable'] = df.variable.str.removeprefix("val_")
sns.lineplot(df, x='Epoch', y='value', hue='variable', style='Test', palette=palette_name)
plt.semilogy()
plt.grid(which='both', linestyle='-.')
ax = plt.gca()
sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.title(title)
plt.savefig("history.png", dpi=300)
plt.savefig("history.svg")


from glob import glob
from os.path import exists

folders = sorted(glob("*_asu_0_epoch_*"), key = lambda x: int(x.split('_')[-1]))

#Markers written by abismal's _torchref_worker.print_summary
SUMMARY_BEGIN = "=== torchref summary ==="
SUMMARY_END = "=== end torchref summary ==="
PEAKS_BEGIN = "--- peaks.csv ---"
PEAKS_END = "--- end peaks.csv ---"


def _summary_block(stdout_file):
    """Return the torchref summary block from a stdout.txt, or None."""
    if not exists(stdout_file):
        return None
    text = open(stdout_file).read()
    if SUMMARY_BEGIN not in text or SUMMARY_END not in text:
        #Run died before the summary, or is still going
        return None
    return text.split(SUMMARY_BEGIN)[-1].split(SUMMARY_END)[0]


def rvals_from_stdout(stdout_file):
    """Rwork/Rfree as torchref reported them at the end of its run."""
    block = _summary_block(stdout_file)
    if block is None:
        return {}
    out = {}
    for key in ('Rwork', 'Rfree'):
        m = re.search(rf'^{key}=([0-9.]+)$', block, re.M)
        if m:
            out[key] = float(m.group(1))
    return out


def peaks_from_stdout(stdout_file):
    """The peak table embedded in the summary block, for runs whose peaks.csv
    is missing (the worker writes the file first, so this is a fallback)."""
    block = _summary_block(stdout_file)
    if block is None or PEAKS_BEGIN not in block:
        return None
    body = block.split(PEAKS_BEGIN)[-1].split(PEAKS_END)[0].strip()
    if not body:
        return None
    from io import StringIO
    return pd.read_csv(StringIO(body))


def rvals_from_mtz(mtz_file, torchref):
    """R/CC for work and free from a refined mtz.

    phenix and torchref disagree on both the amplitude column names and the
    R-free convention, so the caller says which produced the file:

      phenix   : F-obs-filtered / F-model, R-free-flags == 1 marks free
      torchref : F-obs          / F-model, R-free-flags == 0 marks free
    """
    ds = rs.read_mtz(mtz_file)
    #Only phenix output needs stacking. On anomalous data torchref writes ANOM
    #alongside merged F-obs/F-model *and* the F-obs(+/-) pairs, so stacking it
    #would collide with the columns that are already there.
    if 'ANOM' in ds and not torchref:
        ds = ds.stack_anomalous()

    fo = 'F-obs' if torchref else 'F-obs-filtered'
    fc = 'F-model'
    if fo not in ds or fc not in ds:
        return {}

    free = ds['R-free-flags'] == (0 if torchref else 1)
    work = ~free
    if free.sum() == 0 or work.sum() == 0:
        return {}

    #On anomalous data torchref refined against BOTH Friedel mates, so scoring
    #the merged F-obs/F-model here would not reproduce the R it reports. Use the
    #(+)/(-) pairs when they are present, with each mate carrying its own row's
    #free flag.
    #On anomalous data torchref refined against BOTH Friedel mates, so scoring
    #the merged F-obs/F-model would not reproduce the R it reports. Score the
    #(+)/(-) pairs when they are present, each mate carrying its own row's flag.
    #NB: `from pylab import *` shadows the builtin all() with numpy.all(), which
    #does NOT consume a generator -- np.all(<genexpr>) is always True. Hence the
    #set comparison rather than all(... for ...).
    cols = set(ds.columns)
    pairs = [(f'{fo}({s})', f'{fc}({s})') for s in ('+', '-')]
    needed = {c for pair in pairs for c in pair}
    use_pairs = bool(torchref) and needed.issubset(cols)
    if use_pairs:
        obs = pd.concat([ds[a] for a, _ in pairs], ignore_index=True)
        calc = pd.concat([ds[b] for _, b in pairs], ignore_index=True)
        is_free = pd.concat([free] * len(pairs), ignore_index=True)
    else:
        obs, calc, is_free = ds[fo], ds[fc], free

    obs = pd.Series(np.asarray(obs, dtype='float64'))
    calc = pd.Series(np.asarray(calc, dtype='float64'))
    is_free = pd.Series(np.asarray(is_free, dtype=bool))
    ok = obs.notna() & calc.notna()

    out = {}
    for label, sel in (('free', ok & is_free), ('work', ok & ~is_free)):
        if sel.sum() == 0:
            return {}
        o, c = obs[sel], calc[sel]
        out['R' + label] = float((o - c).abs().sum() / o.abs().sum())
        out['CC' + label] = float(o.corr(c))
    return out



df = []
for folder in folders:
    epoch = int(folder.split('_')[-1])
    csv_file = folder + '/peaks.csv'
    #phenix writes peaks.csv via rs.find_peaks; the torchref worker writes the
    #same table itself and also echoes it into stdout.txt, which is the fallback.
    #The worker's switch from gemmi flood fill to skimage peak_local_max kept the
    #column schema (chain, seqid, residue, name, dist, peak, peakz, score,
    #scorez, cen[xyz], coord[xyz]), so both producers still parse identically.
    if exists(csv_file):
        _df = pd.read_csv(csv_file)
    else:
        _df = peaks_from_stdout(folder + '/stdout.txt')
    if _df is not None and len(_df) > 0:
        _df['Epoch'] = epoch
        df.append(_df)
df = pd.concat(df) if len(df) > 0 else pd.DataFrame()

if 'peakz' in df:
    #Nothing here fixes the number of peaks. The worker's peak_local_max search
    #returns however many sites clear the z-score cutoff, and that count moves
    #between epochs and between abismal versions -- hewl went from 6 sites to 10
    #when the map grid changed to a 0.3 A voxel, and every peakz shifted by ~0.1
    #with it. So the hue/style levels below are whatever the data contains, and
    #z-scores are only comparable within a run, never against a banked one.
    plt.figure()
    df['seqid'] = df.apply(lambda x: f'{x.chain}-{x.seqid}', axis=1)

    sns.lineplot(df, x='Epoch', y='peakz', hue='residue', style='seqid', palette=palette_name)
    plt.grid(which='both', linestyle='-.')
    ax = plt.gca()
    sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
    plt.title(title)
    plt.tight_layout()
    plt.savefig("peaks.png", dpi=300)
    plt.savefig("peaks.svg")

df = []
for folder in folders:
    epoch = int(folder.split('_')[-1])
    _df = pd.DataFrame({'Epoch': [epoch]})

    # torchref writes a known filename; phenix's is whatever refinement emitted,
    # so it is globbed. Exclude the worker's own inputs and its anomalous
    # difference map, neither of which carries F-obs/F-model.
    refined_mtz = folder + '/refined.mtz'
    torchref = exists(refined_mtz)
    if torchref:
        candidates = [refined_mtz]
    else:
        candidates = [
            i for i in glob(folder + '/*.mtz')
            if not i.endswith("_data.mtz") and not i.endswith("anomalous.mtz")
        ]

    vals = {}
    if len(candidates) > 0:
        try:
            #Sometimes a partially written mtz will cause an error here
            vals = rvals_from_mtz(candidates[0], torchref)
        except RuntimeError:
            continue

    if torchref:
        # Prefer the R-factors torchref itself reports. They apply its outlier
        # mask and scaled Fcalc, so they differ slightly from a recomputation
        # off the mtz and they are what the run's logs show. CC still comes
        # from the mtz -- torchref does not report it.
        vals.update(rvals_from_stdout(folder + '/stdout.txt'))

    _df = _df.assign(**vals)

    
#    log_files = glob(folder + "/*.log")
#    if len(log_files) > 0:
#        log_file = log_files[0]
#        lines = re.findall("Final R-work =.+\n", open(log_file).read())
#        if len(lines) > 0:
#            line = lines[0]
#            Rwork,Rfree = line.split(',')
#            Rwork = float(Rwork.split()[-1])
#            Rfree = float(Rfree.split()[-1])
#            _df['Rwork'] = Rwork
#            _df['Rfree'] = Rfree

    df.append(_df)

df = pd.concat(df)
if 'Rfree' in df:
    plt.figure()
    r = df[['Epoch', 'Rfree', 'Rwork', 'CCwork', 'CCfree']].melt('Epoch')
    r['Set'] = r['variable'].str.slice(-4).str.capitalize()
    r['Measure'] = r['variable'].str.slice(0, -4).str.capitalize()
    sns.lineplot(r, x='Epoch', y='value', style='Set', hue='Measure', palette=palette_name)

    plt.grid(which='both', linestyle='-.')
    ax = plt.gca()
    plt.title(title)
    plt.tight_layout()
    plt.savefig("rvals.png", dpi=300)
    plt.savefig("rvals.svg")
plt.show()


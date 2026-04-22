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
    "KL",
    "wCCpred",
    "CCpred",
    #"Σ_loc",
    #"Σ_scale",
    #"Σ_mean",
    #"Σ_std",
    "KL_Σ",
    "|∇s|",
    "|∇q|",
    "WilsonB",
    "Wilsonk",
]



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

df = []
for folder in folders:
    epoch = int(folder.split('_')[-1])
    csv_file = folder + '/peaks.csv'
    if exists(csv_file):
        _df = pd.read_csv(folder + '/peaks.csv')
        _df['Epoch'] = epoch
        df.append(_df)
if len(df) > 0:
    df = pd.concat(df)

if 'peakz' in df:
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

    phenix_mtz = glob(folder + '/*.mtz')
    phenix_mtz = [i for i in phenix_mtz if not i.endswith("_data.mtz")]
    if len(phenix_mtz) > 0:
        try:
            #Sometimes a partially written mtz will cause an error here
            ds = rs.read_mtz(phenix_mtz[0])
        except RuntimeError:
            continue
        if 'ANOM' in ds:
            ds = ds.stack_anomalous()
        free = ds['R-free-flags'] == 1
        work = ~free
        fo = 'F-obs-filtered'
        fc = 'F-model'
        _df['Rfree'] = (ds[free][fo] - ds[free][fc]).abs().sum() / ds[free][fo].abs().sum()
        _df['Rwork'] = (ds[work][fo] - ds[work][fc]).abs().sum() / ds[work][fo].abs().sum()
        _df['CCfree'] = ds[free][[fo, fc]].corr()[fo][fc]
        _df['CCwork'] = ds[work][[fo, fc]].corr()[fo][fc]

    
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


import reciprocalspaceship as rs
import gemmi
from pylab import *
import seaborn as sns
import pandas as pd
from os.path import exists
from glob import glob
from os import listdir
from inspect import signature
from functools import wraps


def with_axis(func=None, *ax_args):
    if not callable(func) and func is not None:
        ax_args = (func, *ax_args)

    if len(ax_args) == 0:
        ax_args = ("ax", "axis")

    def _decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            old_ax = plt.gca()
            sig = signature(f)
            bargs = sig.bind(*args, **kwargs)
            bargs.apply_defaults()
            for arg in ax_args:
                if arg in bargs.arguments:
                    ax = bargs.arguments[arg]
                    if ax is not None:
                        plt.sca(ax)
            result = f(*bargs.args, **bargs.kwargs)
            plt.sca(old_ax)
            return result

        return wrapped

    return _decorator(func) if callable(func) else _decorator

def plot_history(csv_file, keys=None): 
    df = pd.read_csv(csv_file) 
    if keys is None: 
        keys = [k for k in default_keys if k in df] 
    for k in keys: 
        val_keys = [] 
        if f'val_{k}' in df: 
            val_keys.append(f'val_{k}') 
        keys = keys + val_keys 
    if 'Epoch' not in keys: 
        keys.append('Epoch') 

    #Filter by keys 
    df = df[keys]  

    #Make data 'tidy' for seaborn 
    data = df.melt("Epoch") 
    data['Set'] = np.array(['Train', 'Test'])[data['variable'].str.startswith('val_').to_numpy('int')] 
    data['variable'] = data['variable'].str.removeprefix('val_') 

    sns.lineplot( 
        data, 
        x='Epoch', 
        y='value', 
        hue='variable', 
        style='Set', 
        palette='Dark2', 
    ) 
    plt.semilogy() 
    plt.grid(which='both', axis='both', ls='-.') 


# Markers written by the torchref worker's print_summary. Keep in sync with
# abismal/callbacks/_torchref_worker.py and scripts/plot_progress.py.
TORCHREF_SUMMARY_BEGIN = "=== torchref summary ==="
TORCHREF_SUMMARY_END = "=== end torchref summary ==="


class BenchmarkReport():
    def __init__(self, results_dir, steps_per_epoch=1_000, cchalf_bins=12):
        self.cchalf_bins = cchalf_bins
        self.cchalf_data = None
        self.results_dir = results_dir
        self.steps_per_epoch = steps_per_epoch
        # Runs used to land in results/job_<N>/<benchmark>/, so the job number
        # was parsed out of the path. job.sh now writes results/torchref/
        # <benchmark>/, where there is no number to find -- keep the label as a
        # string rather than crashing on int('torchref').
        parent = results_dir.rstrip('/').split('/')[-2]
        stripped = parent.removeprefix('job_')
        self.job_number = int(stripped) if stripped.isdigit() else parent
        self.benchmark_name = results_dir.split('/')[-1]
        self._populate_data()
        #self._do_plots()

    def _populate_data(self):
        summary = {
            'Job' : self.job_number,
            'Benchmark' : self.benchmark_name,
        }
        self.summary = {}
        self.history = pd.read_csv(f"{self.results_dir}/history.csv")
        
        # Refinement used to be phenix.refine driven by EFFS, writing to
        # eff_<i>_asu_<j>_epoch_<n>/. It is now torchref, writing to
        # torchref_<i>_asu_<j>_epoch_<n>/. Both are globbed so banked results
        # stay readable; the underscore positions are identical, so the parsing
        # below is unchanged.
        peaks_files = (glob(f"{self.results_dir}/torchref*/peaks.csv")
                       + glob(f"{self.results_dir}/eff*/peaks.csv"))
        data = []
        for peaks_file in peaks_files:
            df = pd.read_csv(peaks_file)
            if df.empty:
                # An epoch can legitimately find no peaks above the cutoff.
                continue
            runstring = peaks_file.split('/')[-2]
            df['Eff'] = int(runstring.split('_')[1])
            df['Asu'] = int(runstring.split('_')[3])
            df['Epoch'] = int(runstring.split('_')[-1])
            data.append(df)

        if not data:
            raise FileNotFoundError(
                f"no peaks.csv under {self.results_dir}/torchref*/ or eff*/. "
                "A non-anomalous run writes none; an anomalous one should."
            )
        data = pd.concat(data)
        self.peak_data = data.melt(['Epoch', 'chain', 'residue', 'seqid'], 'peakz')
        self.peak_data['Residue'] = self.peak_data['residue'] + '-' + self.peak_data['seqid'].astype('str') + ':' + self.peak_data['chain']

        # R-values come from two formats. phenix.refine wrote a log ending in
        # "Final R-work = 0.1973, R-free = 0.2053"; the torchref worker writes a
        # delimited summary block to stdout.txt, the same one
        # scripts/plot_progress.py parses. Read whichever is present so banked
        # phenix-era results and current torchref results both work.
        records = []
        for filename in glob(f"{self.results_dir}/torchref*/stdout.txt"):
            epoch = int(filename.split('/')[-2].split('_')[-1])
            rwork = rfree = None
            text = open(filename).read()
            if TORCHREF_SUMMARY_BEGIN in text and TORCHREF_SUMMARY_END in text:
                block = text.split(TORCHREF_SUMMARY_BEGIN)[-1].split(TORCHREF_SUMMARY_END)[0]
                for line in block.splitlines():
                    if line.startswith('Rwork='):
                        rwork = float(line.split('=')[1])
                    elif line.startswith('Rfree='):
                        rfree = float(line.split('=')[1])
            if rwork is not None and rfree is not None:
                records.append({'Epoch': epoch, 'R': rwork, 'Set': 'Work'})
                records.append({'Epoch': epoch, 'R': rfree, 'Set': 'Free'})

        log_files = glob(f"{self.results_dir}/eff*/*.log")
        for filename in log_files:
            effstring = filename.split('/')[-2]
            epoch = int(effstring.split('_')[-1])
            rwork = None
            for line in open(filename).readlines()[-25:]:
                if line.startswith("Final"):
                    rwork = float(line.split()[3].removesuffix(','))
                    rfree = float(line.split()[-1])
            if rwork is not None:
                records.append({
                    'Epoch' : epoch,
                    'R' : rwork,
                    'Set' : 'Work',
                })
                records.append({
                    'Epoch' : epoch,
                    'R' : rfree,
                    'Set' : 'Free',
                })
        
        rvals = pd.DataFrame.from_records(records)
        self.rvals = rvals.groupby(['Epoch', 'Set']).min().reset_index()
        
        def pearson_ccfunc(df):
            return df[['F1', 'F2']].corr(method='pearson')['F1']['F2']

        def weighted_pearson_ccfunc(df):
            x = df['F1'].to_numpy('float32')
            y = df['F2'].to_numpy('float32')
            w = np.reciprocal(
                np.square(df['SigF1']) + np.square(df['SigF2'])
            ).to_numpy('float32')
            return rs.utils.weighted_pearsonr(x, y, w)


        def make_halves_cchalf(mtz, op='x,y,z', bins=10):
            """Construct half-datasets for computing CChalf"""
        
            half1 = mtz.loc[mtz.half == 0].copy()
            half2 = mtz.loc[mtz.half == 1].copy()
            half2 = half2.apply_symop(op).hkl_to_asu(anomalous=True)
        
            out = half1[["F", "SigF", "repeat"]].merge(
                half2[["F", "SigF", "repeat"]], on=["H", "K", "L", "repeat"], suffixes=("1", "2")
            ).dropna()
            return out

        xval_file = f"{self.results_dir}/abismal_xval.mtz"
        self.cchalf_data = None
        if exists(xval_file):
            ds = rs.read_mtz(f"{self.results_dir}/abismal_xval.mtz")
            ops = [gemmi.Op('x,y,z')]
            ops.extend(gemmi.find_twin_laws(ds.cell, ds.spacegroup, 1e-3, False))
            for op in ops:
                hds = make_halves_cchalf(ds, op=op, bins=self.cchalf_bins).compute_dHKL()
                hds['bin'],edges = rs.utils.bin_by_percentile(hds.dHKL, ascending=False)
                labels = [f"{e1:0.2f} - {e2:0.2f}" for e1,e2 in zip(edges[:-1], edges[1:])]
        
                cchalf_data = pd.DataFrame({
                    'Labels' : ['Overall'] + labels,
                    'CChalf' : [pearson_ccfunc(hds)] + hds.groupby('bin').apply(pearson_ccfunc, include_groups=False).to_list(),
                    'wCChalf' : [weighted_pearson_ccfunc(hds)] + hds.groupby('bin').apply(weighted_pearson_ccfunc, include_groups=False).to_list(),
                })
                if self.cchalf_data is None:
                    self.cchalf_data = cchalf_data
                else:
                    self.cchalf_data = np.maximum(cchalf_data, self.cchalf_data)

            summary['CChalf'] = self.cchalf_data.iloc[0]['CChalf']
            summary['wCChalf'] = self.cchalf_data.iloc[0]['wCChalf']
    
        summary['Peak Final'] = self.peak_data.groupby("Epoch").max().iloc[-1].value
        summary['Peak Max'] = self.peak_data.max().value

        #R-factors
        rvals = self.rvals
        summary['Rfree Min'] = rvals[rvals.Set == 'Free'].min().R
        summary['Rfree Final'] = rvals[rvals.Set == 'Free'].iloc[-1].R
        summary['Rwork Min'] = rvals[rvals.Set == 'Work'].min().R
        summary['Rwork Final'] = rvals[rvals.Set == 'Work'].iloc[-1].R

        #Likelihood
        summary['NLL Min'] = self.history['NLL'].min()
        summary['NLL Final'] = self.history['NLL'].iloc[-1]
        summary['NLL (Test) Min'] = self.history['val_NLL'].min()
        summary['NLL (Test) Final'] = self.history['val_NLL'].iloc[-1]

        #CCpred
        summary['CCpred Max'] = self.history['CCpred'].max()
        summary['wCCpred Max'] = self.history['wCCpred'].max()
        summary['CCpred Final'] = self.history['CCpred'].iloc[-1]
        summary['wCCpred Final'] = self.history['wCCpred'].iloc[-1]
        summary['CCpred (Test) Max'] = self.history['val_CCpred'].max()
        summary['wCCpred (Test) Max'] = self.history['val_wCCpred'].max()
        summary['CCpred (Test) Final'] = self.history['val_CCpred'].iloc[-1]
        summary['wCCpred (Test) Final'] = self.history['val_wCCpred'].iloc[-1]

        #Performance
        summary['Runtime (s)'] = self.history['Time (s)'].max()
        summary['Runtime (HH:MM:SS)'] = pd.to_datetime(summary['Runtime (s)'], unit='s').strftime('%H:%M:%S')
        summary['Memory Usage (MB)'] = self.history['FB Used (MiB)'].max()
        self.summary = summary

    @property
    def plot_title(self):
        return ' - '.join([self.summary['Job Name'], self.summary['Benchmark']])

    @with_axis
    def plot_peaks(self, min_points=10, ax=None):
        """
        min_points filters peaks which appear in fewer epochs than min_points
        """
        idx = self.peak_data.groupby("Residue").transform('size') >= min_points
        peak_data = self.peak_data[idx]
        sns.lineplot(
            peak_data,
            x='Epoch',
            y='value',
            hue='Residue',
            palette='Dark2',
        )
        ax = plt.gca()
        sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
        plt.semilogy()
        plt.grid(which='both', axis='both', ls='-.')
        plt.ylabel(r"Anomalous Peak Height ($\sigma$)")
        #plt.title(self.plot_title)

    @with_axis
    def plot_history(self, keys, ax=None):
        title = ' - '.join([self.summary['Job Name'], self.summary['Benchmark']])
        plot_history(f"{self.results_dir}/history.csv", keys)
        sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
        #plt.ylabel("Objective")
        #plt.title(self.plot_title)

    @with_axis
    def plot_r_values(self, ax=None):
        sns.lineplot(
            self.rvals,
            x="Epoch",
            y='R',
            style='Set',
            color='k',
        )
        sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
        plt.grid(which='both', axis='both', ls='-.')
        #plt.title(self.plot_title)

    @with_axis
    def plot_cchalf(self, ax=None):
        sns.lineplot(
            self.cchalf_data.melt("Labels"), x='Labels', y='value', style='variable', color='k', ax=ax
        )
        sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))
        plt.xticks(rotation=45, rotation_mode='anchor', ha='right')
        plt.grid(which='both', axis='both', ls='-.')
        plt.xlabel("Resolution (Å)")
        #plt.title(self.plot_title)

    def _do_plots(self, figsize=(15,10)):
        f = plt.figure(figsize=figsize, constrained_layout=True)
        if self.cchalf_data is not None:
            gs = f.add_gridspec(3, 2)
        else:
            gs = f.add_gridspec(2, 2)

        ax = f.add_subplot(gs[0, 0])
        self.plot_history(['CCpred', 'wCCpred'], ax=ax)

        ax = f.add_subplot(gs[0, 1])
        self.plot_history(['loss', 'NLL', 'KL', 'KL_Σ'], ax=ax)

        ax = f.add_subplot(gs[1, 0])
        self.plot_peaks(ax=ax)

        ax = f.add_subplot(gs[1, 1])
        self.plot_r_values(ax=ax)

        if self.cchalf_data is not None:
            ax = f.add_subplot(gs[2, :])
            self.plot_cchalf(ax=ax)

        plt.suptitle(self.plot_title)

class JobReport():
    def __init__(self, *job_dirs, names=None):
        self.job_dirs = job_dirs
        self.reports = []
        if names is None:
            names = job_dirs

        records = []
        for name,job_dir in zip(names, self.job_dirs):
            for benchmark in listdir(job_dir):
                #print(f"Processing {job_dir}/{benchmark} ...")
                try:
                    report = BenchmarkReport(f'{job_dir}/{benchmark}')
                    report.summary['name'] = name
                    report.summary['Job Name'] = name
                    self.reports.append(report)
                    records.append(report.summary)
                except Exception as e:
                    print(f"Warning: could not construct report for {benchmark} due to Error: {e}")
        self.results = pd.DataFrame.from_records(records)

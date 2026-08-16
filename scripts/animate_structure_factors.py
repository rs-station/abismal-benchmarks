from pylab import *
from sys import argv
import reciprocalspaceship as rs
from matplotlib.animation import FuncAnimation, FFMpegWriter
from tqdm import tqdm

epoch_from_file = lambda x: int(x.split('_')[-1][:-4])
mtz_files = sorted(argv[1:], key=epoch_from_file)
ds = rs.read_mtz(mtz_files[0]).stack_anomalous().dropna()
has_structure_factors = "F" in ds

# ── Scatter plot animation ────────────────────────────────────────────────────

fig, ax = plt.subplots()

if has_structure_factors:
    ax.set_xlabel("Structure Factor Amplitude (|F|)")
    ax.set_ylabel(r"Uncertainty ($\sigma_F$)")
else:
    ax.set_xlabel("Intensity (I)")
    ax.set_ylabel(r"Uncertainty ($\sigma_I$)")

ax.set_xscale("log")
ax.set_yscale("log")
ax.grid(which="major", linestyle="-.")

# Pre-load all data so we don't re-read inside the draw call
scatter_data = []
for mtz_file in tqdm(mtz_files, desc="Loading scatter data"):
    d = rs.read_mtz(mtz_file).stack_anomalous().dropna()
    if has_structure_factors:
        scatter_data.append((d.F, d.SIGF, epoch_from_file(mtz_file)))
    else:
        scatter_data.append((d.I, d.SIGI, epoch_from_file(mtz_file)))

# Compute global axis limits so they stay fixed across frames
all_x = np.concatenate([s[0].values for s in scatter_data])
all_y = np.concatenate([s[1].values for s in scatter_data])
ax.set_xlim(all_x[all_x > 0].min(), all_x.max())
ax.set_ylim(all_y[all_y > 0].min(), all_y.max())

(line,) = ax.plot([], [], "k.", alpha=0.01)
title_text = ax.text(0.5, 1.01, "", transform=ax.transAxes, ha="center")


def init_scatter():
    line.set_data([], [])
    title_text.set_text("")
    return line, title_text


def update_scatter(frame):
    x, y, epoch = scatter_data[frame]
    line.set_data(x, y)
    title_text.set_text(f"Epoch {epoch}")
    return line, title_text


anim = FuncAnimation(
    fig,
    update_scatter,
    frames=len(scatter_data),
    init_func=init_scatter,
    blit=True,
)

if has_structure_factors:
    anim.save("scatter_fsigf.mp4", writer=FFMpegWriter())
    anim.save("scatter_fsigf.gif")
else:
    anim.save("scatter_isigi.mp4", writer=FFMpegWriter())
    anim.save("scatter_isigi.gif")

plt.close(fig)

# ── Histogram animation ───────────────────────────────────────────────────────

fig, ax = plt.subplots()

if has_structure_factors:
    ax.set_xlabel(r"Signal to Noise (F/$\sigma_F$)")
else:
    ax.set_xlabel(r"Signal to Noise (I/$\sigma_I$)")

ax.set_yscale("log")
ax.grid(which="major", linestyle="-.")

# Pre-load SNR data
hist_data = []
eps = 1e-6
for mtz_file in tqdm(mtz_files, desc="Loading histogram data"):
    d = rs.read_mtz(mtz_file).stack_anomalous().dropna()
    snr = (d.F / (d.SIGF + eps) if has_structure_factors else d.I / (d.SIGI + eps)).values
    hist_data.append((snr, epoch_from_file(mtz_file)))

# Fixed x-limits across all frames
all_snr = np.concatenate([h[0] for h in hist_data])
x_min, x_max = all_snr.min(), all_snr.max()
bin_edges = np.linspace(x_min, x_max, 101)  # 100 bins → 101 edges
ax.set_xlim(x_min, x_max)

title_text = ax.text(0.5, 1.01, "", transform=ax.transAxes, ha="center")

# We'll redraw the bars each frame by storing a reference
bar_container = [None]  # mutable container so the closure can update it


def init_hist():
    title_text.set_text("")
    return (title_text,)


def update_hist(frame):
    # Remove previous bars
    if bar_container[0] is not None:
        for patch in bar_container[0]:
            patch.remove()

    snr, epoch = hist_data[frame]
    _, _, patches = ax.hist(snr, bins=bin_edges, color="k", log=True)
    bar_container[0] = patches
    title_text.set_text(f"Epoch {epoch}")

    # Adjust y-limits to the current frame's data
    ax.relim()
    ax.autoscale_view(scalex=False, scaley=True)

    return tuple(patches) + (title_text,)


anim = FuncAnimation(
    fig,
    update_hist,
    frames=len(hist_data),
    init_func=init_hist,
    blit=False,  # blit=False because we're adding/removing artists
)

if has_structure_factors:
    anim.save("hist_fsigf.mp4", writer=FFMpegWriter())
    anim.save("hist_fsigf.gif")
else:
    anim.save("hist_isigi.mp4", writer=FFMpegWriter())
    anim.save("hist_isigi.gif")

plt.close(fig)

# ── Resolution scatterplot animation ─────────────────────────────────────────

fig, ax = plt.subplots()

if has_structure_factors:
    ax.set_ylabel("Structure Factor Amplitude (|F|)")
else:
    ax.set_ylabel("Intensity (I)")

ax.set_xlabel(r"Resolution ($\AA$)")
ax.set_yscale("log")
ax.grid(which="major", linestyle="-.")

# Pre-load resolution data
res_scatter_data = []
for mtz_file in tqdm(mtz_files, desc="Loading resolution scatter data"):
    d = rs.read_mtz(mtz_file).stack_anomalous().dropna()
    d = d.compute_dHKL()
    dHKL = d["dHKL"].values.astype(float)
    inv_d2 = 1.0 / dHKL**2
    vals = (d.F if has_structure_factors else d.I).values.astype(float)
    res_scatter_data.append((inv_d2, vals, epoch_from_file(mtz_file)))

all_inv_d2 = np.concatenate([r[0] for r in res_scatter_data])
all_vals   = np.concatenate([r[1] for r in res_scatter_data])
x_min, x_max = all_inv_d2.min(), all_inv_d2.max()
y_min = all_vals[all_vals > 0].min()
y_max = all_vals.max()
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# Choose tick positions in 1/d² space, label them in Å
d_tick_values = np.array([10.0, 5.0, 3.0, 2.0, 1.5, 1.2, 1.0, 0.9, 0.8])
d_tick_values = d_tick_values[(1.0 / d_tick_values**2 >= x_min) & (1.0 / d_tick_values**2 <= x_max)]
ax.set_xticks(1.0 / d_tick_values**2)
ax.set_xticklabels([f"{d:g}" for d in d_tick_values])

(res_line,) = ax.plot([], [], "k.", alpha=0.05, markersize=2)
res_title = ax.text(0.5, 1.01, "", transform=ax.transAxes, ha="center")


def init_res():
    res_line.set_data([], [])
    res_title.set_text("")
    return res_line, res_title


def update_res(frame):
    inv_d2, vals, epoch = res_scatter_data[frame]
    res_line.set_data(inv_d2, vals)
    res_title.set_text(f"Epoch {epoch}")
    return res_line, res_title


anim = FuncAnimation(
    fig,
    update_res,
    frames=len(res_scatter_data),
    init_func=init_res,
    blit=True,
)

if has_structure_factors:
    anim.save("scatter_f_vs_resolution.mp4", writer=FFMpegWriter())
    anim.save("scatter_f_vs_resolution.gif")
else:
    anim.save("scatter_i_vs_resolution.mp4", writer=FFMpegWriter())
    anim.save("scatter_i_vs_resolution.gif")

plt.close(fig)

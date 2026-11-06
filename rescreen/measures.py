"""Anomalous measures of one refinement (refined.mtz + refined.pdb), two of them independent of how the
anomalous differences are weighted by resolution.

heights(rundir, ds, weighting)  peak heights (sigma) in the ANOM/PANOM map, as the torchref worker computes it
                                ('asis'), or with ANOM rescaled to unit RMS in each resolution shell ('flat').
                                cxidb: Zn (largest ZN site) and Zn2 (HOH A1002); hewl: S (mean over Cys SG, Met SD);
                                cx61 (cxidb_61, SeMet, chains A and B): Se (mean over all six MSE SE) and Se166 (mean
                                over the weak, high-B MSE 166 SE of both chains);
                                cx62 (cxidb_62, SeMet, P 65 with an indexing ambiguity): Se (mean over the MSE 104 SE
                                of both chains, both alternate conformations).
ccanom(rundir, ds, edges)       per-shell Pearson CC between observed DeltaF = F-obs(+) - F-obs(-) and DeltaF
                                calculated from the refined model with f'' for the anomalous scatterers, in shells
                                given by `edges` (1/d^2). A CC is unchanged by rescaling a shell.

Model DeltaF: with F_N = F-model exp(i PH-model) from refined.mtz and A(h) = i sum_j sum_ops f''_j occ_j
exp(-B_j/(4 d^2)) exp(2 pi i h.(R x_j + t)) over the anomalous scatterers, F(+) = F_N + A and F(-)* = F_N - A,
so DeltaF = |F_N + A| - |F_N - A|. f'' from Cromer-Liberman at each dataset's wavelength.
"""
import os, sys, numpy as np, gemmi, reciprocalspaceship as rs, warnings
sys.path.insert(0, os.path.join(os.environ["ABISMAL"], "abismal", "callbacks"))  # the checkout the runs used
from _torchref_worker import map_grid_size
warnings.filterwarnings("ignore")
# Beam wavelengths of the data (not the reference models' REMARK 200): cxidb_81 is 9.75 keV at LCLS (median of the
# DIALS experiments, 1.254-1.276 A), just above the Zn K edge; until 2026-10-25 this was 1.5418 (2tli.pdb's rotating
# anode), which put Zn's f'' at ~0.7 e instead of several.
WAVELENGTH = {"cxidb": 1.2717, "hewl": 1.892, "cx61": 0.9539, "cx62": 0.9571}
ANOMALOUS = {"ZN", "CA", "S", "SE", "CL", "FE", "CU", "MN", "NI", "CO"}

def _chains(st, ds):
    # cxidb_81 and HEWL were measured on chain A alone; cxidb_61 has two copies.
    return list(st[0]) if ds in ("cx61", "cx62") else [st[0]["A"]]

def _sites(st, ds):
    out = []
    for r in (r for ch in _chains(st, ds) for r in ch):
        for a in r:
            if ds == "cxidb" and ((r.name == "ZN") or (r.name == "HOH" and r.seqid.num == 1002)):
                out.append(("Zn" if r.name == "ZN" else "Zn2", a.pos))
            if ds == "hewl" and ((r.name == "CYS" and a.name == "SG") or (r.name == "MET" and a.name == "SD")):
                out.append(("S", a.pos))
            if ds == "cx62" and r.name == "MSE" and a.name == "SE":
                out.append(("Se", a.pos))
            if ds == "cx61" and r.name == "MSE" and a.name == "SE":
                out.append(("Se", a.pos))
                if r.seqid.num == 166:
                    out.append(("Se166", a.pos))
    return out

def _peak(arr, st, pos, radius=1.2):
    n = np.array(arr.shape)
    r = int(np.ceil(radius / min(st.cell.a / n[0], st.cell.b / n[1], st.cell.c / n[2])))
    f = st.cell.fractionalize(pos); c = np.round(np.array([f.x, f.y, f.z]) * n).astype(int)
    best = -np.inf
    for d in np.stack(np.meshgrid(*[np.arange(-r, r + 1)] * 3, indexing="ij"), -1).reshape(-1, 3):
        if st.cell.orthogonalize(gemmi.Fractional(*((c + d) / n))).dist(pos) <= radius:
            best = max(best, arr[tuple((c + d) % n)])
    return best

def shells(q, edges):
    return np.clip(np.searchsorted(edges, q, side="right") - 1, 0, len(edges) - 2)

def heights(rundir, ds, weighting="asis", nshell=20):
    st = gemmi.read_pdb(f"{rundir}/refined.pdb")
    m = rs.read_mtz(f"{rundir}/refined.mtz").compute_dHKL()[["ANOM", "PANOM", "dHKL"]].dropna()
    if weighting == "flat":
        q = m.dHKL.to_numpy() ** -2
        lab = shells(q, np.quantile(q, np.linspace(0, 1, nshell + 1)))
        a = m.ANOM.to_numpy(float)
        rms = np.sqrt(np.bincount(lab, a * a) / np.bincount(lab))
        m["ANOM"] = rs.DataSeries(a / rms[lab], index=m.index, dtype="SFAmplitude")
    grid = m[["ANOM", "PANOM"]].to_gemmi().transform_f_phi_to_map("ANOM", "PANOM", min_size=map_grid_size(st.cell))
    arr = np.array(grid, copy=False); mu, sd = float(arr.mean()), float(arr.std())
    res = {}
    for name, pos in _sites(st, ds):
        res.setdefault(name, []).append((_peak(arr, st, pos) - mu) / sd)
    return {k: float(np.max(v) if k == "Zn" else np.mean(v)) for k, v in res.items()}

def model_delta_f(rundir, ds):
    st = gemmi.read_pdb(f"{rundir}/refined.pdb"); st.setup_entities()
    m = rs.read_mtz(f"{rundir}/refined.mtz").compute_dHKL()
    m = m[["F-obs(+)", "F-obs(-)", "F-model", "PH-model", "dHKL"]].dropna()
    H = m.get_hkls().astype(float)
    energy = gemmi.hc / WAVELENGTH[ds]
    ops = gemmi.SpaceGroup(st.spacegroup_hm).operations()
    A = np.zeros(len(m), complex)
    s2 = m.dHKL.to_numpy() ** -2
    for r in (r for ch in _chains(st, ds) for r in ch):
        for a in r:
            el = a.element.name.upper()
            if el not in ANOMALOUS:
                continue
            fpp = gemmi.cromer_liberman(z=a.element.atomic_number, energy=energy)[1]
            f = st.cell.fractionalize(a.pos)
            w = fpp * a.occ * np.exp(-a.b_iso * s2 / 4.)
            for op in ops:
                x = np.array(op.apply_to_xyz([f.x, f.y, f.z]))
                A += 1j * w * np.exp(2j * np.pi * (H @ x))
    FN = m["F-model"].to_numpy(float) * np.exp(1j * np.deg2rad(m["PH-model"].to_numpy(float)))
    dm = np.abs(FN + A) - np.abs(FN - A)
    do = (m["F-obs(+)"] - m["F-obs(-)"]).to_numpy(float)
    return do, dm, s2

def ccanom(rundir, ds, edges):
    do, dm, q = model_delta_f(rundir, ds)
    lab = shells(q, edges)
    cc = np.array([np.corrcoef(do[lab == k], dm[lab == k])[0, 1] if (lab == k).sum() > 20 else np.nan for k in range(len(edges) - 1)])
    n = np.bincount(lab, minlength=len(edges) - 1)
    return {"by_shell": cc.tolist(), "n": n.tolist(), "mean": float(np.nansum(cc * n) / n[~np.isnan(cc)].sum())}

def ccanom_weighted(rundir, ds, edges=None):
    """
    Inverse-variance weighted anomalous CC: weighted Pearson correlation between observed and model DeltaF (as ccanom)
    with weights 1/(SIGF-obs(+)^2 + SIGF-obs(-)^2), overall and per shell (if `edges`), so precise differences count
    more than noisy ones. Returns {"overall", "by_shell"}.
    """
    st = gemmi.read_pdb(f"{rundir}/refined.pdb")
    m = rs.read_mtz(f"{rundir}/refined.mtz")
    need = ["F-obs(+)", "F-obs(-)", "F-model", "PH-model", "SIGF-obs(+)", "SIGF-obs(-)"]
    sig = m[need].dropna()
    do, dm, q = model_delta_f(rundir, ds)
    full = m.compute_dHKL()[["F-obs(+)", "F-obs(-)", "F-model", "PH-model", "dHKL"]].dropna()
    s2 = sig.reindex(full.index)
    w = (1. / (s2["SIGF-obs(+)"].to_numpy(float) ** 2 + s2["SIGF-obs(-)"].to_numpy(float) ** 2))
    ok = np.isfinite(w) & (w > 0)
    def wcc(a, b, w):
        w = w / w.sum(); ma, mb = (w * a).sum(), (w * b).sum()
        return float((w * (a - ma) * (b - mb)).sum() / np.sqrt((w * (a - ma) ** 2).sum() * (w * (b - mb) ** 2).sum()))
    out = {"overall": wcc(do[ok], dm[ok], w[ok])}
    if edges is not None:
        lab = shells(q, edges)
        out["by_shell"] = [wcc(do[ok & (lab == k)], dm[ok & (lab == k)], w[ok & (lab == k)]) if (ok & (lab == k)).sum() > 20 else float("nan")
                           for k in range(len(edges) - 1)]
    return out

def rfree_shells(rundir, edges=None, nshell=10):
    """
    Rfree (flag 0) per resolution shell from refined.mtz, R = sum|Fo - Fmodel| / sum Fo within each shell, and its
    falloff-neutral summary: the unweighted mean over shells. The overall Rfree weights each shell by its sum of Fo, so
    a merge with a steeper falloff (smaller high-resolution Fo, where R is highest) gets a lower overall Rfree without
    being better; the per-shell values and their mean do not have that bias. `edges` in 1/d^2 (default: `nshell`
    shells of equal reflection count over this run's free set). Returns {"by_shell", "d", "mean", "n"}.
    """
    m = rs.read_mtz(f"{rundir}/refined.mtz").compute_dHKL().dropna(subset=["F-obs", "F-model"])
    m = m[m["R-free-flags"].to_numpy() == 0]
    fo, fm = m["F-obs"].to_numpy(float), m["F-model"].to_numpy(float)
    q = m.dHKL.to_numpy(float) ** -2
    if edges is None:
        edges = np.quantile(q, np.linspace(0, 1, nshell + 1))
    lab = shells(q, edges)
    k = len(edges) - 1
    num = np.bincount(lab, np.abs(fo - fm), minlength=k); den = np.bincount(lab, fo, minlength=k)
    n = np.bincount(lab, minlength=k)
    r = np.where(n > 20, num / np.maximum(den, 1e-30), np.nan)
    return {"by_shell": r.tolist(), "d": (np.asarray(edges[1:]) ** -0.5).tolist(), "mean": float(np.nanmean(r)), "n": n.tolist()}

def rfree(rundir):
    import re
    t = open(f"{rundir}/stdout.txt").read()
    v = re.findall(r"^Rfree=([0-9.]+)", t, re.M)
    return float(v[-1]) if v else None

#!/usr/bin/env python
"""Parameterised re-implementations of the current T2 board picks (box-local, released stages only).

interp  ~ v0014 (embryo, e_o1_shrinkmerge) / v0019+v0023 (heart interp, h_o1_shrinkmerge + h_aniso50)
    carrier rows   : cells of the LEFT released stage, per-state counts by the mass bridge
                     share_s = (1-lam)*p_left(s) + lam*p_right(s) for shared states, p_left(s) otherwise
                     (largest-remainder counts; per-state draws without replacement where possible)
    expression     : x + w * (mu_T(s) - mu_carrier(s)),  mu_T = (1-lam)*mu_L + lam*mu_R,
                     w = |t|/(|t|+C) gene-wise, t = (mu_R-mu_L)/se (se from left/right state variances),
                     shared states only; clip at 0
    geometry       : 'logrms'  -> uniform scale so RMS radius = exp(lerp(log RMS_L, log RMS_R))   (v0002 G1 L1 rule)
                     'aniso'   -> warp carrier PCA spectrum to lerp(spectrum_L, spectrum_R) + same RMS (v0023 rule, t=lam)
extrap  ~ v0030 (heart extrap, x_r3_medlib09)
    carrier rows   : stratified uniform draw of n cells from the LAST released stage
    expression     : shared states (present in prev and last): x + damp * timescale * (median_last(s) - median_prev(s));
                     then per-cell library preserve (sum expm1 restored to the cell's original value); orphans unchanged
    geometry       : carrier coordinates unchanged
Differences vs the repo artifacts: the repo picks were built on non-git parent h5ads (v0002 / v0009 FGW / baseline-001
row selection), so these are faithful re-implementations of the recipe, not byte replays.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
from vecommon import load_stage, panel, make_submission, format_check, INDEX


def parse_stage(s):
    name, t = s.rsplit(":", 1)
    return name, float(t)


def state_stats(X, labels):
    out = {}
    for s in np.unique(labels):
        m = X[labels == s]
        out[str(s)] = (m.mean(0).astype(np.float64), m.var(0).astype(np.float64), len(m))
    return out


def counts_from_raw(raw, n):
    states = sorted(raw)
    tot = sum(raw.values()); raw = {s: raw[s] / tot for s in states}
    counts = {s: int(raw[s] * n) for s in states}
    deficit = n - sum(counts.values())
    rema = sorted(states, key=lambda s: (raw[s] * n - counts[s], s), reverse=True)
    for i in range(deficit):
        counts[rema[i % len(rema)]] += 1
    return counts


def select_rows(labels, counts, seed):
    rng = np.random.default_rng(seed); chosen = []
    for s in sorted(counts):
        pool = np.flatnonzero(labels == s); k = counts[s]
        if k == 0: continue
        if k < len(pool): sel = pool[rng.choice(len(pool), k, replace=False)]
        elif k == len(pool): sel = pool
        else: sel = pool[rng.choice(len(pool), k, replace=True)]
        chosen.extend(np.sort(sel).tolist())
    return np.asarray(chosen, dtype=np.int64)


def stratified_indices(labels, n, seed):
    """Repo scripts/t2_pseudo_holdout.py::select_indices (proportional, lexical tie-break)."""
    values = np.asarray(labels).astype(str); groups = sorted(np.unique(values).tolist())
    gi = {g_: np.flatnonzero(values == g_) for g_ in groups}
    cnt = np.asarray([len(gi[g_]) for g_ in groups], float); exact = cnt * n / len(values)
    take = np.floor(exact).astype(int); rem = int(n - take.sum()); fr = exact - take
    for i in sorted(range(len(groups)), key=lambda i: (-fr[i], groups[i]))[:rem]: take[i] += 1
    rng = np.random.default_rng(int(seed))
    return np.sort(np.concatenate([rng.choice(gi[g_], size=int(take[i]), replace=False) for i, g_ in enumerate(groups)]))


def center_rms(c):
    c = np.asarray(c, np.float64)[:, :3]; mu = c.mean(0, keepdims=True); x = c - mu
    return x, mu, float(np.sqrt((x ** 2).sum(1).mean()))


def spectrum(c):
    x, _, r = center_rms(c); _, s, _ = np.linalg.svd(x, full_matrices=False)
    return np.sqrt(s ** 2 / x.shape[0]) / r


def warp_to(c, aspects_t, rms_t):
    x, mu, _ = center_rms(c); _, _, vt = np.linalg.svd(x, full_matrices=False)
    y = ((x @ vt.T) * (aspects_t / spectrum(c))) @ vt
    y *= rms_t / float(np.sqrt((y ** 2).sum(1).mean()))
    return y + mu


def scale_to_rms(c, rms_t):
    x, mu, r = center_rms(c)
    return mu + x * (rms_t / r)


def run_interp(a):
    board = a.board; g = panel(board)
    (nl, tl), (nr, tr) = parse_stage(a.left), parse_stage(a.right)
    lam = (a.target - tl) / (tr - tl)
    L = load_stage(nl, g); R = load_stage(nr, g)
    labL = np.asarray(L.obs[a.label].astype(str)); labR = np.asarray(R.obs[a.label].astype(str))
    sL, sR = state_stats(L.X, labL), state_stats(R.X, labR)
    shared = sorted(set(sL) & set(sR))
    pL = {s: sL[s][2] / L.n_obs for s in sL}; pR = {s: sR[s][2] / R.n_obs for s in sR}
    rL, rR = center_rms(L.obsm["spatial_3D"])[2], center_rms(R.obsm["spatial_3D"])[2]
    rms_t = float(np.exp((1 - lam) * np.log(rL) + lam * np.log(rR)))
    carrier = getattr(a, "carrier", "left")
    if carrier == "baseline":
        # v0014-faithful chain: official pseudobulk_shift on the full left stage (delta = mu_left(c) - mu_prev(c)),
        # stratified base_n subsample (repo select_indices, seed base_seed), log-RMS rescale of that base (v0002),
        # then mass-bridge counts drawn INSIDE the base pool (seed bridge_seed), shift toward mu_T relative to the
        # base's own per-state mean (v0014 / e_o1_shrinkmerge).
        npv, tpv = parse_stage(a.prev)
        Pv = load_stage(npv, g); labP = np.asarray(Pv.obs[a.label].astype(str))
        XB = L.X.astype(np.float64).copy()
        for c in np.unique(labL):
            mp = labP == c
            if mp.any():
                XB[labL == c] += XB[labL == c].mean(0) - Pv.X[mp].mean(0)
        np.clip(XB, 0, None, out=XB); del Pv
        base_idx = stratified_indices(labL, a.base_n, a.base_seed)
        XB = XB[base_idx]; labB = labL[base_idx]
        CB = scale_to_rms(np.asarray(L.obsm["spatial_3D"])[base_idx, :3], rms_t)
        namesB = np.asarray(L.obs_names)[base_idx]
        pB = {s: float((labB == s).mean()) for s in np.unique(labB)}
        raw = {s: ((1 - lam) * pL.get(s, 0) + lam * pR[s]) if s in shared else 0.5 * pB[s] + 0.5 * pL.get(s, 0) for s in pB}
        counts = counts_from_raw(raw, a.n)
        rows = select_rows(labB, counts, a.bridge_seed)
        X = XB[rows].copy(); lab = labB[rows]
        muB = {s: XB[labB == s].mean(0) for s in pB}
        C_fixed = CB[rows]; names_src = namesB[rows]
        shared = [s for s in shared if s in pB]
    else:
        raw = {s: ((1 - lam) * pL[s] + lam * pR[s]) if s in shared else pL[s] for s in sL}
        counts = counts_from_raw(raw, a.n)
        rows = select_rows(labL, counts, a.seed)
        X = L.X[rows].astype(np.float64); lab = labL[rows]
        muB = {s: sL[s][0] for s in sL}; C_fixed = None; names_src = np.asarray(L.obs_names)[rows]
    wmean = []
    for s in shared:
        muL, vL, nL = sL[s]; muR, vR, nR = sR[s]
        muT = (1 - lam) * muL + lam * muR
        shift = muT - muB[s]
        if a.C > 0:
            se = np.sqrt(vL / nL + vR / nR)
            with np.errstate(divide="ignore", invalid="ignore"):
                t = np.where(se > 0, np.abs((muR - muL) / se), 0.0)
            w = t / (t + a.C); shift = shift * w; wmean.append(float(w.mean()))
        m = lab == s
        if getattr(a, "zero_preserve", False):
            # apply the state mean shift to detected (non-zero) entries only, rescaled by the detected fraction,
            # so zeros stay zeros (keeps the pairwise |x_i - x_j|^0.5 structure the variogram scores)
            Xs = X[m]; nz = Xs > 0
            frac = np.maximum(nz.mean(0), 0.05)
            Xs = np.where(nz, Xs + shift / frac, 0.0)
            X[m] = Xs
        else:
            X[m] += shift
    clip = float((X < 0).mean()); np.clip(X, 0, None, out=X)
    C = np.asarray(L.obsm["spatial_3D"])[rows, :3] if C_fixed is None else C_fixed
    if C_fixed is not None and a.geometry == "logrms":
        C2 = C                                  # already log-RMS scaled at the base level (v0002 rule)
    elif a.geometry == "logrms":
        C2 = scale_to_rms(C, rms_t)
    elif a.geometry == "aniso":
        asp = (1 - lam) * spectrum(L.obsm["spatial_3D"]) + lam * spectrum(R.obsm["spatial_3D"])
        C2 = warp_to(C, asp, rms_t)
    else:
        C2 = C
    names = [f"{n}__r{i}" for i, n in enumerate(names_src)]
    prov = dict(recipe="interp_bridge_shrink", carrier=carrier, board=board, left=a.left, right=a.right, target=a.target, lam=lam,
                n=a.n, C=a.C, geometry=a.geometry, zero_preserve=bool(getattr(a, "zero_preserve", False)), seed=a.seed, shared_states=len(shared), clip_frac=clip,
                mean_w=float(np.mean(wmean)) if wmean else None, rms_target=rms_t, external_sources="none")
    out = make_submission(X, g, C2, names, prov)
    out.obs["celltype"] = lab
    return out, prov


def run_extrap(a):
    board = a.board; g = panel(board)
    (np_, tp), (nl, tl) = parse_stage(a.prev), parse_stage(a.last)
    P = load_stage(np_, g); L = load_stage(nl, g)
    labP = np.asarray(P.obs[a.label].astype(str)); labL = np.asarray(L.obs[a.label].astype(str))
    n = min(a.n, L.n_obs)
    # stratified uniform draw (keeps last-stage composition)
    if getattr(a, "rows", "draw") == "repo":
        rows = stratified_indices(labL, n, a.row_seed)    # baseline-001 row rule (select_indices, seed 20260821)
    else:
        shares = {s: float((labL == s).mean()) for s in np.unique(labL)}
        rows = select_rows(labL, counts_from_raw(shares, n), a.seed)
    X = L.X[rows].astype(np.float64); lab = labL[rows]
    lib0 = np.expm1(X).sum(1)
    ts = (a.target - tl) / (tl - tp) if a.timescale == "linear" else 1.0
    shared = sorted(set(np.unique(labP)) & set(np.unique(labL)))
    shared = [s for s in shared if (labP == s).sum() >= a.min_cells and (labL == s).sum() >= a.min_cells]
    touched = np.zeros(n, bool)
    for s in shared:
        stat = np.median if a.stat == "median" else np.mean
        d = stat(L.X[labL == s], axis=0) - stat(P.X[labP == s], axis=0)
        m = lab == s; X[m] += a.damp * ts * d; touched |= m
    np.clip(X, 0, None, out=X)
    if a.lib_preserve:
        E = np.expm1(X[touched]); lib1 = E.sum(1)
        E *= (lib0[touched] / np.maximum(lib1, 1e-12))[:, None]
        X[touched] = np.log1p(E)
    C = np.asarray(L.obsm["spatial_3D"])[rows, :3]
    names = [f"{n_}__r{i}" for i, n_ in enumerate(np.asarray(L.obs_names)[rows])]
    prov = dict(recipe="extrap_median_delta_libpreserve", board=board, prev=a.prev, last=a.last, target=a.target,
                n=n, damp=a.damp, timescale=a.timescale, time_factor=ts, stat=a.stat, lib_preserve=a.lib_preserve,
                shared_states=shared, touched_rows=int(touched.sum()), seed=a.seed, rows=getattr(a, "rows", "draw"), external_sources="none")
    out = make_submission(X, g, C, names, prov)
    out.obs["celltype"] = lab
    return out, prov


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("interp", "extrap"):
        p = sub.add_parser(name)
        p.add_argument("--board", required=True); p.add_argument("--target", type=float, required=True)
        p.add_argument("--n", type=int, required=True); p.add_argument("--seed", type=int, default=20261008)
        p.add_argument("--label", default="celltype"); p.add_argument("--out", required=True)
    pi = sub.choices["interp"]
    pi.add_argument("--left", required=True, help="stage_name:time"); pi.add_argument("--right", required=True)
    pi.add_argument("--carrier", choices=["left", "baseline"], default="left"); pi.add_argument("--prev", default=None)
    pi.add_argument("--base-n", type=int, default=5000); pi.add_argument("--base-seed", type=int, default=20260821); pi.add_argument("--bridge-seed", type=int, default=20260904)
    pi.add_argument("--C", type=float, default=2.0); pi.add_argument("--zero-preserve", action="store_true"); pi.add_argument("--geometry", choices=["logrms", "aniso", "none"], default="logrms")
    px = sub.choices["extrap"]
    px.add_argument("--prev", required=True); px.add_argument("--last", required=True)
    px.add_argument("--damp", type=float, default=0.9); px.add_argument("--timescale", choices=["none", "linear"], default="none")
    px.add_argument("--stat", choices=["median", "mean"], default="median"); px.add_argument("--min-cells", type=int, default=30)
    px.add_argument("--no-lib-preserve", dest="lib_preserve", action="store_false")
    px.add_argument("--rows", choices=["draw", "repo"], default="draw"); px.add_argument("--row-seed", type=int, default=20260821)
    a = ap.parse_args(argv)
    out, prov = (run_interp if a.cmd == "interp" else run_extrap)(a)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.write_h5ad(a.out)
    fc = format_check(Path(a.out), a.board)
    print(json.dumps({"provenance": prov, "format_check": fc}, default=str, indent=1))
    return 0 if fc["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Pure operators for T2 round2 lanes. Every function is deterministic and
individually unit-tested in tests/t2_round2/test_ops.py. No IO here."""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------- quantile bridge

def rank_normalized(values: np.ndarray) -> np.ndarray:
    """Average-tie ranks normalized to (0,1) via (rank-0.5)/n."""
    v = np.asarray(values, dtype=np.float64)
    n = v.shape[0]
    if n == 0:
        raise ValueError("rank_normalized: empty input")
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(n, dtype=np.float64)
    sorted_v = v[order]
    i = 0
    while i < n:
        j = i
        while j + 1 < n and sorted_v[j + 1] == sorted_v[i]:
            j += 1
        avg = 0.5 * (i + j) + 1.0  # 1-based average rank
        ranks[order[i:j + 1]] = avg
        i = j + 1
    return (ranks - 0.5) / n


def empirical_quantile(values: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Empirical quantile function of `values` evaluated at u in (0,1)."""
    v = np.sort(np.asarray(values, dtype=np.float64))
    n = v.shape[0]
    if n == 0:
        raise ValueError("empirical_quantile: empty reference")
    grid = (np.arange(n) + 0.5) / n
    return np.interp(u, grid, v, left=v[0], right=v[-1])


def quantile_bridge_map(parent_vals: np.ndarray, left_vals: np.ndarray,
                        right_vals: np.ndarray, lam: float) -> np.ndarray:
    """Map parent rows onto the (1-lam,lam)-interpolated bracket distribution,
    preserving each row's within-group rank. Output is non-negative."""
    if not (0.0 <= lam <= 1.0):
        raise ValueError("lam outside [0,1]")
    p = np.asarray(parent_vals, dtype=np.float64)
    if p.shape[0] == 0:
        return p.copy()
    r = rank_normalized(p)
    out = (1.0 - lam) * empirical_quantile(left_vals, r) + lam * empirical_quantile(right_vals, r)
    out = np.clip(out, 0.0, None)
    return out


# ---------------------------------------------------------------- time trends

def linfit_eval(times: np.ndarray, values: np.ndarray, t_eval: float) -> float:
    """Least-squares linear fit of values vs times, evaluated at t_eval."""
    t = np.asarray(times, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if t.ndim != 1 or y.shape != t.shape or t.size < 2:
        raise ValueError("linfit_eval: need >=2 paired points")
    A = np.column_stack([np.ones_like(t), t])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return float(coef[0] + coef[1] * t_eval)


def lagrange3_weights(times: np.ndarray, t_eval: float) -> np.ndarray:
    t = np.asarray(times, dtype=np.float64)
    if t.shape != (3,):
        raise ValueError("lagrange3_weights: need exactly 3 times")
    w = np.ones(3, dtype=np.float64)
    for i in range(3):
        for j in range(3):
            if i != j:
                w[i] *= (t_eval - t[j]) / (t[i] - t[j])
    return w


def lagrange3_eval(times: np.ndarray, values: np.ndarray, t_eval: float) -> float:
    w = lagrange3_weights(times, t_eval)
    return float(np.dot(w, np.asarray(values, dtype=np.float64)))


def share_series_predict(times: np.ndarray, share_series: np.ndarray, t_eval: float,
                         *, log_eps: float = 1e-6, quadratic: bool = False) -> float:
    """Predict a share at t_eval from a (>=2)-point series in log space."""
    t = np.asarray(times, dtype=np.float64)
    s = np.asarray(share_series, dtype=np.float64)
    if s.shape != t.shape or t.size < 2:
        raise ValueError("share_series_predict: bad shapes")
    if (s < 0).any():
        raise ValueError("share_series_predict: negative share")
    log_s = np.log(s + log_eps)
    if quadratic and t.size >= 3:
        pred = lagrange3_eval(t, log_s, t_eval)
    else:
        pred = linfit_eval(t, log_s, t_eval)
    out = float(np.exp(pred) - log_eps)
    return max(out, 0.0)


# ---------------------------------------------------------------- shrinkage

def shrink_weights(shift: np.ndarray, se: np.ndarray, C: float = 2.0) -> np.ndarray:
    """w = |t|/(|t|+C) with t = shift/se. se<=0 (or non-finite) -> w = 0."""
    if C < 0:
        raise ValueError("C must be non-negative")
    d = np.asarray(shift, dtype=np.float64)
    s = np.asarray(se, dtype=np.float64)
    if d.shape != s.shape:
        raise ValueError("shrink_weights: shape mismatch")
    with np.errstate(divide="ignore", invalid="ignore"):
        tstat = np.abs(d / s)
    tstat = np.where(np.isfinite(tstat), tstat, 0.0)
    tstat = np.where(s > 0, tstat, 0.0)
    if C == 0.0:
        return np.where(tstat > 0, 1.0, 0.0)
    return tstat / (tstat + C)


def se_two_means(var_a: np.ndarray, n_a: int, var_b: np.ndarray, n_b: int) -> np.ndarray:
    if n_a <= 0 or n_b <= 0:
        raise ValueError("se_two_means: non-positive n")
    return np.sqrt(np.asarray(var_a, dtype=np.float64) / n_a + np.asarray(var_b, dtype=np.float64) / n_b)


# ---------------------------------------------------------------- geometry (G1 convention, mirrors scripts/t2_g1_scale.py)

def rms_radius(coords: np.ndarray) -> float:
    v = np.asarray(coords, dtype=np.float64)[:, :3]
    if v.shape[0] == 0:
        raise ValueError("rms_radius: empty coords")
    centered = v - v.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("rms_radius: non-positive RMS")
    return rms


def l1_target_log_rms(times: np.ndarray, rms_values: np.ndarray, target_stage: float) -> float:
    """Strict linear interpolation of log-RMS (B1-A1 L1 rule, interp branch only)."""
    t = np.asarray(times, dtype=np.float64)
    r = np.asarray(rms_values, dtype=np.float64)
    if t.size != r.size or t.size < 2:
        raise ValueError("l1_target_log_rms: need >=2 stages")
    if np.any(np.diff(t) <= 0) or (r <= 0).any():
        raise ValueError("l1_target_log_rms: bad stages/rms")
    log_r = np.log(r)
    exact = np.flatnonzero(np.isclose(t, target_stage, rtol=0.0, atol=1e-12))
    if len(exact):
        return float(log_r[int(exact[0])])
    right = int(np.searchsorted(t, target_stage, side="right"))
    left = right - 1
    if left < 0 or right >= len(t):
        raise ValueError("l1_target_log_rms: target outside stage range (interp lane)")
    frac = (target_stage - t[left]) / (t[right] - t[left])
    return float(log_r[left] + frac * (log_r[right] - log_r[left]))


def scale_to_rms(coords: np.ndarray, target_rms: float) -> tuple[np.ndarray, float]:
    """centroid + factor*(coords-centroid) so that cloud RMS equals target_rms."""
    v = np.asarray(coords, dtype=np.float64)[:, :3]
    cur = rms_radius(v)
    if target_rms <= 0 or not np.isfinite(target_rms):
        raise ValueError("scale_to_rms: bad target")
    factor = float(target_rms / cur)
    c = v.mean(axis=0, keepdims=True)
    return c + factor * (v - c), factor


# ---------------------------------------------------------------- lineage map

def cosine_lineage_map(orphan_types: list[str], cand_means: dict[str, np.ndarray],
                       orphan_means: dict[str, np.ndarray]) -> dict[str, str]:
    """Each orphan type -> argmax-cosine candidate type. Deterministic
    (ties broken by candidate name)."""
    out: dict[str, str] = {}
    cands = sorted(cand_means.keys())
    for t in sorted(orphan_types):
        v = np.asarray(orphan_means[t], dtype=np.float64)
        nv = float(np.linalg.norm(v))
        best_s, best_c = None, -np.inf
        for c in cands:
            u = np.asarray(cand_means[c], dtype=np.float64)
            nu = float(np.linalg.norm(u))
            if nv == 0.0 or nu == 0.0:
                sim = 0.0
            else:
                sim = float(np.dot(v, u) / (nv * nu))
            if sim > best_c:
                best_s, best_c = c, sim
        if best_s is None:
            raise ValueError("cosine_lineage_map: no candidates")
        out[t] = best_s
    return out


# ---------------------------------------------------------------- library renormalization

def library_remap_targets(row_libs: np.ndarray, left_libs: np.ndarray,
                          right_libs: np.ndarray, lam: float) -> np.ndarray:
    """Rank-preserving library targets from the interpolated bracket library
    distribution. Same quantile machinery as the quantile bridge."""
    return quantile_bridge_map(row_libs, left_libs, right_libs, lam)


def apply_library_scale(X: np.ndarray, row_libs: np.ndarray, target_libs: np.ndarray) -> np.ndarray:
    """Scale each row to its target library. Rows with lib==0 are unchanged."""
    X = np.asarray(X, dtype=np.float64)
    lib = np.asarray(row_libs, dtype=np.float64)
    tgt = np.asarray(target_libs, dtype=np.float64)
    if X.shape[0] != lib.shape[0] or lib.shape != tgt.shape:
        raise ValueError("apply_library_scale: shape mismatch")
    if (tgt < 0).any() or (lib < 0).any():
        raise ValueError("apply_library_scale: negative library")
    factor = np.ones_like(lib)
    nz = lib > 0
    factor[nz] = tgt[nz] / lib[nz]
    out = X * factor[:, None]
    return np.clip(out, 0.0, None)


# ---------------------------------------------------------------- compmix shares

def compmix_predict_shares(times: np.ndarray, share_matrix: np.ndarray, t_eval: float,
                           ref_shares: np.ndarray, *, log_eps: float = 1e-6,
                           max_fold: float = 2.0) -> np.ndarray:
    """Per-type log-share linear trend -> t_eval, fold-capped vs ref, renormalized.

    share_matrix: (n_types, n_times) shares (0 allowed). ref_shares: (n_types,)
    shares at the last observed stage used for the fold cap."""
    S = np.asarray(share_matrix, dtype=np.float64)
    ref = np.asarray(ref_shares, dtype=np.float64)
    if S.ndim != 2 or S.shape[0] != ref.shape[0]:
        raise ValueError("compmix_predict_shares: shape mismatch")
    if (S < 0).any() or (ref < 0).any() or max_fold < 1.0:
        raise ValueError("compmix_predict_shares: bad inputs")
    t = np.asarray(times, dtype=np.float64)
    pred = np.array([share_series_predict(t, S[i], t_eval, log_eps=log_eps)
                     for i in range(S.shape[0])])
    lo = ref / max_fold
    hi = ref * max_fold
    pred = np.minimum(np.maximum(pred, lo), hi)
    tot = pred.sum()
    if tot <= 0:
        raise ValueError("compmix_predict_shares: all-zero prediction")
    return pred / tot

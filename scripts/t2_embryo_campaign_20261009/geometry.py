"""Source-only conditional Gaussian displacement interpolation, preserving row pairing.

No target measurements or scorer feedback are inputs. The model interpolates
conditional means/covariances, not arbitrary non-Gaussian endpoint distributions.
The final RMS constraint intentionally changes the interpolated absolute moments.
"""
from __future__ import annotations
import numpy as np


def _cloud(x, labels):
    x = np.asarray(x, dtype=np.float64)
    labels = np.asarray(labels).astype(str)
    if x.ndim != 2 or x.shape[1] != 3 or labels.shape != (len(x),):
        raise ValueError('Expected (n,3) coordinates and n labels')
    if len(x) < 2 or not np.isfinite(x).all():
        raise ValueError('Cloud must contain >=2 finite points')
    return x, labels


def rms_radius(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt(np.mean(np.sum((x-x.mean(0))**2, axis=1))))


def proper_alignment(left, left_labels, right, right_labels):
    """Return right aligned into left frame, using harmonic-count-weighted anchors.

    Reflection is prohibited. Three non-collinear shared centroids are necessary;
    a rank-deficient anchor configuration raises rather than inventing a frame.
    """
    left, ll = _cloud(left, left_labels)
    right, rl = _cloud(right, right_labels)
    shared = sorted(set(ll) & set(rl))
    if len(shared) < 3:
        raise ValueError('Need >=3 shared type centroids for rigid registration')
    a = np.array([left[ll == s].mean(0) for s in shared])
    b = np.array([right[rl == s].mean(0) for s in shared])
    nl = np.array([(ll == s).sum() for s in shared], dtype=float)
    nr = np.array([(rl == s).sum() for s in shared], dtype=float)
    w = 2*nl*nr/(nl+nr); w /= w.sum()
    ma, mb = w @ a, w @ b
    ac, bc = a-ma, b-mb
    sa = np.linalg.svd(ac*np.sqrt(w[:, None]), compute_uv=False)
    sb = np.linalg.svd(bc*np.sqrt(w[:, None]), compute_uv=False)
    if min(sa[1]/max(sa[0], 1e-300), sb[1]/max(sb[0], 1e-300)) < 1e-8:
        raise ValueError('Shared type centroids are collinear or numerically degenerate')
    u, singular, vt = np.linalg.svd((bc*w[:, None]).T @ ac)
    correction = np.eye(3); correction[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    aligned = (right-mb) @ rotation + ma
    residual = (b-mb) @ rotation + ma-a
    return aligned, {
        'shared_anchor_types': shared, 'anchor_weights': w.tolist(),
        'rotation': rotation.tolist(), 'determinant': float(np.linalg.det(rotation)),
        'right_anchor_center': mb.tolist(), 'left_anchor_center': ma.tolist(),
        'anchor_singular_values': singular.tolist(),
        'anchor_weighted_residual_rms': float(np.sqrt(np.sum(w*np.sum(residual**2, axis=1)))),
        'left_anchor_rank_ratio': float(sa[1]/sa[0]),
        'right_anchor_rank_ratio': float(sb[1]/sb[0]),
    }


def _sym(a):
    return (a+a.T)*0.5


def _power(a, p):
    val, vec = np.linalg.eigh(_sym(a))
    if val.min() <= 0:
        raise ValueError('Matrix power requires positive definite covariance')
    return _sym((vec * val**p) @ vec.T)


def _cov(x, floor):
    centered = x-x.mean(0)
    cov = centered.T @ centered/len(x)
    val, vec = np.linalg.eigh(_sym(cov))
    clipped = np.maximum(val, floor)
    return _sym((vec*clipped) @ vec.T), {'n': len(x), 'raw_eigenvalues': val.tolist(),
          'eigenvalue_floor': float(floor), 'regularized_axes': int((val < floor).sum())}


def gaussian_transport(source_cov, target_cov):
    """Symmetric Gaussian W2 optimal linear map, column-vector convention."""
    root = _power(source_cov, 0.5)
    invroot = _power(source_cov, -0.5)
    return _sym(invroot @ _power(root @ target_cov @ root, 0.5) @ invroot)


def interpolate_geometry(base_coords, base_labels, left_coords, left_labels,
                         right_coords, right_labels, t, target_rms=None):
    """Push base rows to Bures-interpolated state geometry in left's frame.

    Base must already be in the left endpoint's coordinate frame (up to global
    translation/isotropic scale). It is not independently registered. Absent
    endpoint states retain their base geometry; this is disclosed, never hidden.
    At endpoints exact covariance recovery requires full-rank empirical clouds;
    ridge-regularized singular supports cannot create missing intrinsic dimensions.
    """
    if not np.isfinite(t) or not 0 <= t <= 1:
        raise ValueError('t must be finite in [0,1]')
    base, bl = _cloud(base_coords, base_labels)
    left, ll = _cloud(left_coords, left_labels)
    right, rl = _cloud(right_coords, right_labels)
    current_rms = rms_radius(base)
    target_rms = current_rms if target_rms is None else float(target_rms)
    if current_rms <= 0 or not np.isfinite(target_rms) or target_rms <= 0:
        raise ValueError('RMS must be positive and finite')
    aligned, registration = proper_alignment(left, ll, right, rl)
    # Coordinate-unit covariant numerical floor, fixed before any experiment.
    floor = 1e-6 * max(rms_radius(left)**2, rms_radius(aligned)**2, current_rms**2)/3
    out = base.copy(); state_audit = {}; fallback = []
    eye = np.eye(3)
    for s in sorted(set(bl)):
        mask = bl == s
        if s not in set(ll) or s not in set(rl):
            fallback.append(s)
            continue
        a, b, v = left[ll == s], aligned[rl == s], base[mask]
        ca, da = _cov(a, floor); cb, db = _cov(b, floor); cv, dv = _cov(v, floor)
        step = (1-t)*eye + t*gaussian_transport(ca, cb)
        ct = _sym(step @ ca @ step.T)
        mt = (1-t)*a.mean(0) + t*b.mean(0)
        move = gaussian_transport(cv, ct)
        out[mask] = (v-v.mean(0)) @ move.T + mt
        state_audit[s] = {'left': da, 'right': db, 'base': dv,
            'target_mean_before_rms': mt.tolist(), 'target_cov_before_rms': ct.tolist(),
            'transport_eigenvalues': np.linalg.eigvalsh(move).tolist()}
    before = rms_radius(out)
    if not np.isfinite(out).all() or before <= 0:
        raise ValueError('Nonfinite or collapsed interpolated geometry')
    center = out.mean(0)
    out = center + (out-center)*(target_rms/before)
    return out, {'method': 'proper_procrustes_conditional_bures_pushforward',
        't': float(t), 'registration': registration, 'states': state_audit,
        'fallback_absent_endpoint_types': fallback,
        'rms_before_lock': before, 'rms_target': target_rms,
        'rms_after_lock': rms_radius(out), 'rms_factor': target_rms/before,
        'row_order_preserved': True, 'target_measurements_used': False,
        'limitation': 'Moment interpolation, not exact non-Gaussian endpoint recovery; singular supports stay singular'}

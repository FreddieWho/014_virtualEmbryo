"""Chunked full-gene random-pair diagnostics, without hidden target data.

The variogram is not a pure covariance statistic: changing per-gene marginals
changes it too. This module separates its marginal and co-detection terms.
Bounds are deliberately labelled loose; they are not feasible joint couplings
across all genes at once and not a forecast of score improvement.
"""
from __future__ import annotations

import numpy as np


def uniform_pairs(n_genes, n_pairs=20000, seed=20261009):
    rng = np.random.default_rng(seed)
    i = rng.integers(0, n_genes, n_pairs)
    j = rng.integers(0, n_genes, n_pairs)
    keep = i != j
    return np.column_stack([i[keep], j[keep]])


def pair_moments(X, pairs, chunk_size=128):
    """Use every supplied row; buffers are rows x chunk_size, not genes^2."""
    if len(X.shape) != 2 or X.shape[0] == 0:
        raise ValueError("X must contain cells and genes")
    n = len(pairs)
    out = {k: np.zeros(n, dtype=np.float64) for k in
           ("moment", "marginal_term", "joint_term", "codetection",
            "loose_joint_upper_bound")}
    for start in range(0, n, chunk_size):
        stop = min(n, start+chunk_size)
        ids = pairs[start:stop]
        a = np.asarray(X[:, ids[:, 0]], dtype=np.float64)
        b = np.asarray(X[:, ids[:, 1]], dtype=np.float64)
        ma = np.sqrt(a).mean(axis=0)
        mb = np.sqrt(b).mean(axis=0)
        moment = np.sqrt(np.abs(a-b)).mean(axis=0)
        marginal = ma+mb
        joint = marginal-moment
        if joint.min() < -1e-10:
            raise AssertionError("co-detection term must be nonnegative")
        out["moment"][start:stop] = moment
        out["marginal_term"][start:stop] = marginal
        out["joint_term"][start:stop] = joint
        out["codetection"][start:stop] = ((a > 0) & (b > 0)).mean(axis=0)
        out["loose_joint_upper_bound"][start:stop] = 2*np.minimum(ma, mb)
    return out


def compare_pair_moments(parent, alternative, reference=None):
    """Arguments are pair_moments results for identical pairs.

    An optional reference must be a genuinely allowed observed source,
    labelled by the caller. Never call a released-stage reference future truth.
    """
    dm = alternative["marginal_term"]-parent["marginal_term"]
    dj = alternative["joint_term"]-parent["joint_term"]
    dv = alternative["moment"]-parent["moment"]
    result = {
        "n_pairs": int(len(dm)),
        "marginal_term_max_abs_change": float(np.max(np.abs(dm))),
        "joint_term_mean_abs_change": float(np.mean(np.abs(dj))),
        "pair_moment_mean_abs_change": float(np.mean(np.abs(dv))),
        "pair_moment_rms_change": float(np.sqrt(np.mean(dv*dv))),
        "decomposition_max_abs_error": float(np.max(np.abs(dv-(dm-dj)))),
        "parent_joint_term_mean": float(np.mean(parent["joint_term"])),
        "alternative_joint_term_mean": float(np.mean(alternative["joint_term"])),
        "parent_codetection_mean": float(np.mean(parent["codetection"])),
        "alternative_codetection_mean": float(np.mean(alternative["codetection"])),
        "loose_bound_is_not_jointly_attainable_claim": True,
    }
    if reference is not None:
        ep = parent["moment"]-reference["moment"]
        ea = alternative["moment"]-reference["moment"]
        delta_a = parent["marginal_term"]-reference["marginal_term"]
        delta_j = parent["joint_term"]-reference["joint_term"]
        result["released_reference_raw_variogram_parent"] = float(np.mean(ep*ep))
        result["released_reference_raw_variogram_alternative"] = float(np.mean(ea*ea))
        result["reference_error_decomposition"] = {
            "marginal_square": float(np.mean(delta_a*delta_a)),
            "joint_square": float(np.mean(delta_j*delta_j)),
            "cross_term": float(-2*np.mean(delta_a*delta_j)),
        }
        result["actual_variogram_change"] = float(np.mean(ea*ea)-np.mean(ep*ep))
        result["fixed_marginal_predicted_variogram_change"] = float(
            -2*np.mean(ep*dj)+np.mean(dj*dj))
    return result


def changed_pair_support(parent, alternative, pairs, block_size=256):
    """Actual sampled-pair coverage and zero-gene limitations, not a forecast."""
    if parent.shape != alternative.shape:
        raise ValueError("shape mismatch")
    G = parent.shape[1]
    changed = np.zeros(G, dtype=bool)
    active = np.zeros(G, dtype=bool)
    for start in range(0, G, block_size):
        stop = min(start+block_size, G)
        a = np.asarray(parent[:,start:stop])
        b = np.asarray(alternative[:,start:stop])
        changed[start:stop] = (a != b).any(axis=0)
        active[start:stop] = (a > 0).any(axis=0)
    i,j = pairs[:,0],pairs[:,1]
    pm = pair_moments(parent,pairs)
    am = pair_moments(alternative,pairs)
    moment_change = np.abs(am["moment"]-pm["moment"])
    zero_gene_pair = ~active[i] | ~active[j]
    return {
        "sampled_pairs":int(len(pairs)),
        "both_changed_columns":int((changed[i]&changed[j]).sum()),
        "at_least_one_changed_column":int((changed[i]|changed[j]).sum()),
        "both_globally_nonzero_genes":int((active[i]&active[j]).sum()),
        "parent_pairs_with_actual_codetection":int((pm["codetection"]>0).sum()),
        "alternative_pairs_with_actual_codetection":int((am["codetection"]>0).sum()),
        "pairs_with_a_globally_zero_gene":int(zero_gene_pair.sum()),
        "zero_gene_pair_max_moment_change":float(moment_change[zero_gene_pair].max())
            if zero_gene_pair.any() else 0.,
        "all_pair_abs_moment_change_quantiles":np.quantile(
            moment_change,[0,.5,.9,.99,1]).tolist(),
        "unchanged_marginals_required_for_zero_gene_invariance":True,
    }

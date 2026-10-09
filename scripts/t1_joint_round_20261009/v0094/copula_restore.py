"""Paired empirical-copula restoration with exact state/gene marginals.

No model fitting, dense gene covariance, normalization or artifact writes here.
Full input matrices can be memory maps; work buffers are state-by-gene-block.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import rankdata


def restore(parent, template, states, *, blend=0.5, block_size=256,
            shuffle_template=False, seed=20261009):
    """Return a dense copy of parent and auditable diagnostics.

    Parent/template must already have exact paired rows and identical columns.
    Caller owns row identity and input-hash validation. states cannot be inferred
    from a held-out stage. Template shuffle retains each gene's template values
    but destroys its joint cell identity, using one fixed RNG per column/state.
    """
    P, T = np.asarray(parent), np.asarray(template)
    states = np.asarray(states).astype(str)
    if P.ndim != 2 or T.shape != P.shape or len(states) != P.shape[0]:
        raise ValueError("Parent, template and states must have paired shapes")
    if not np.isfinite(blend) or not 0 <= blend <= 1:
        raise ValueError("blend must be finite and in [0, 1]")
    if block_size < 1:
        raise ValueError("block_size must be positive")
    for name, A in (("parent", P), ("template", T)):
        if not np.isfinite(A).all() or (A < 0).any():
            raise ValueError(f"{name} must be finite and nonnegative")
    out = P.copy()
    changed_genes = np.zeros(P.shape[1], dtype=bool)
    changed_entries = 0
    transitions_on = transitions_off = 0
    rank_abs_sum = 0.0
    total_rank_values = 0
    state_diag = {}
    if blend == 0:
        return out, {"operator_off_exact": True, "changed_entries": 0,
                     "changed_genes": 0, "state_gene_multisets_exact": True}

    # A per-state/per-gene generator makes results independent of block_size.
    for state_i, state in enumerate(sorted(set(states))):
        rows = np.flatnonzero(states == state)
        n = len(rows)
        if n < 2:
            state_diag[state] = {"rows": n, "changed_entries": 0}
            continue
        row_ids = np.arange(n)
        state_changes = 0
        for start in range(0, P.shape[1], block_size):
            stop = min(start + block_size, P.shape[1])
            B = np.asarray(P[np.ix_(rows, np.arange(start, stop))])
            C = np.asarray(T[np.ix_(rows, np.arange(start, stop))])
            for j in range(stop - start):
                x, t = B[:, j], C[:, j]
                # Preserve unsupported/constant parent and template genes.
                if np.ptp(x) == 0 or np.ptp(t) == 0:
                    continue
                if shuffle_template:
                    rng = np.random.default_rng(np.random.SeedSequence(
                        [int(seed), int(state_i), int(start + j)]))
                    t = t[rng.permutation(n)]
                # Average ranks are integer or half-integer. Integer doubled
                # ranks avoid dtype/version-dependent roundoff splitting ties.
                rxi = np.rint(2*np.asarray(rankdata(x, method="average"),
                                          dtype=np.float64)).astype(np.int64)
                rti = np.rint(2*np.asarray(rankdata(t, method="average"),
                                          dtype=np.float64)).astype(np.int64)
                rx = (rxi.astype(np.float64)-1)/(2*n)
                score = rxi+rti if blend == .5 else (1-blend)*rxi+blend*rti
                order = np.lexsort((row_ids, x, score))
                vals = np.sort(x, kind="stable")
                result = np.empty_like(x)
                result[order] = vals
                if not np.array_equal(np.sort(result), vals):
                    raise AssertionError("state/gene marginal changed")
                changed = result != x
                k = int(changed.sum())
                state_changes += k
                changed_entries += k
                changed_genes[start + j] |= bool(k)
                transitions_on += int(((x == 0) & (result > 0)).sum())
                transitions_off += int(((x > 0) & (result == 0)).sum())
                new_rank = (np.asarray(rankdata(result, method="average"),
                                       dtype=np.float64)-.5)/n
                rank_abs_sum += float(np.abs(new_rank - rx).sum())
                total_rank_values += n
                out[rows, start + j] = result
        state_diag[state] = {"rows": n, "changed_entries": state_changes}
    G = P.shape[1]
    k = int(changed_genes.sum())
    den = G * (G - 1)
    diag = {
        "blend": float(blend), "shuffle_template": bool(shuffle_template),
        "seed": int(seed), "shape": list(P.shape),
        "changed_entries": changed_entries,
        "changed_fraction": changed_entries / P.size,
        "changed_genes": k,
        "uniform_gene_pair_at_least_one_changed_fraction":
            1 - (G-k) * (G-k-1) / den if den else 0.0,
        "uniform_gene_pair_both_changed_fraction":
            k * (k-1) / den if den else 0.0,
        "on_transitions": transitions_on, "off_transitions": transitions_off,
        "mean_absolute_rank_change": rank_abs_sum / max(total_rank_values, 1),
        "state_gene_multisets_exact": True,
        "state_diagnostics": state_diag,
        "row_libraries_are_not_invariant": True,
        "server_de_scores_are_not_guaranteed_invariant": True,
    }
    return out, diag

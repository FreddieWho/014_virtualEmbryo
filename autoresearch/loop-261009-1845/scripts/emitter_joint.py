"""New T3 route: empirical joint donor transport (different architecture).

Assumption under test
---------------------
The incumbent v0088 emitter transports the response gene-by-gene: within a
state it picks n rows per gene, then fills each gene independently from that
gene's quantile-shift curve. That construction cannot change WHICH genes are
detected together, which is why de_skill was immovable across every emitter
parameter variant measured on 2026-10-09.

This route replaces the marginal quantile interpolation with a JOINT operator:
cells are transported as whole profiles by rank matching on a state-level
joint score, so gene co-detection moves with the transported cell.

The score is a per-cell aggregate over the response-weighted gene set, so it
is exactly the quantity the marginal construction discards. No target outcome
is read; the score uses only the WT carrier and the source response.
"""
import numpy as np
from scipy.special import logsumexp

from crossko import closed


def joint_score(model, cells, response, state, genes):
    """Rank score from the response-weighted aggregate over selected genes."""
    sub = cells[:, genes]
    w = np.abs(response["delta"][state][:, genes]).mean(0)
    w = w / max(w.sum(), 1e-8)
    return sub.astype(float) @ w


def emit_joint(
    model,
    carrier,
    response,
    mode="combined",
    frac_scale=1.0,
    conditional=True,
    residual=False,
    genes=None,
):
    """Joint donor transport. Same outer contract as emit(): closed panel units,
    7449x500 shape, same composition resampling and same final renormalization.
    """
    closed(carrier)
    if not residual and not conditional:
        # Controlled comparison: the control arm stays on the frozen marginal path.
        return model.emit(carrier, response, mode=mode)
    if genes is None:
        # Genes the frozen response actually moves in this run; others keep the
        # carrier profile so the joint operator acts only where there is signal.
        moved = np.abs(response["delta"]).max(0).max(0) > 0
        genes = np.flatnonzero(moved)
    if len(genes) == 0:
        return carrier.copy(), np.arange(len(carrier))

    rng = np.random.default_rng(model.seed)
    lab = model.assign(carrier)
    ix = np.arange(len(carrier))
    prop = None
    if conditional:
        from emitter_v88 import detection_propensity

        prop = detection_propensity(model, carrier, lab)

    if mode in ("composition", "combined"):
        mass = np.bincount(lab, minlength=model.S).astype(float)
        mass *= np.exp(np.clip(response["composition"], -2, 2))
        mass /= mass.sum()
        cnt = np.bincount(lab, minlength=model.S)
        p = mass[lab] / np.maximum(cnt[lab], 1)
        p /= p.sum()
        ix = rng.choice(ix, len(ix), replace=True, p=p)

    out = carrier[ix].copy().astype(float)
    labels = lab[ix]
    global_q, _ = model.positive_quantiles(carrier, np.zeros((model.G, len(model.positive_q))))

    if mode in ("within", "combined") and np.any(response["delta"]):
        for s in range(model.S):
            rows = np.flatnonzero(labels == s)
            if not len(rows) or not response["support"][s]:
                continue
            local = out[rows].copy()
            baseq, _ = model.positive_quantiles(local, global_q)

            # Number of cells to transport this state, from the frozen detection rule.
            dmax = np.abs(response["delta"][s]).max(0)
            active = np.flatnonzero(dmax > 0)
            if not len(active):
                continue
            dfrac = float(np.clip(response["delta"][s][active, -1].mean(), 0, 1))
            base_det = float((local[:, active] > 0).mean())
            frac = float(np.clip(base_det + dfrac, 0, 1))
            n = int(np.floor(len(rows) * frac * frac_scale + rng.random()))
            if n <= 0:
                continue

            # Joint rank transport over the response-active gene block.
            score = joint_score(model, local, response, s, active)
            if conditional and prop is not None:
                # State-conditioned tie-breaking, same prior as the incumbent.
                score = score + 1e-6 * prop[ix[rows][:, None], active[None, :]].mean(1)
            order = np.argsort(score, kind="stable")[-n:]

            moved = out[rows[order]].copy()
            npos = []
            for j in active:
                col = local[:, j]
                pos = np.flatnonzero(col > 0)
                if len(pos) < 2:
                    npos.append(0)
                    continue
                npos.append(len(pos))
                src = pos[np.argsort(col[pos], kind="stable")]
                # Marginal quantile shift applied to the transported profile.
                rr = col[src] - np.interp(
                    (np.arange(len(src)) + 0.5) / len(src), model.positive_q, baseq[j]
                )
                tgt = moved[:, j] - np.interp(
                    (np.arange(n) + 0.5) / n, model.positive_q, baseq[j]
                )
                # Resample the donor residual distribution onto the n transported
                # cells; the joint operator moves whole profiles, so the residual
                # must follow the same rank count as the transported block.
                rr_n = np.interp(
                    (np.arange(n) + 0.5) / n,
                    (np.arange(len(src)) + 0.5) / len(src),
                    rr,
                )
                vals = np.maximum.accumulate(np.maximum(tgt + rr_n, 0))
                if residual:
                    vals = np.maximum.accumulate(vals)
                moved[:, j] = vals
            out[rows[order]] = moved

    with np.errstate(divide="ignore", invalid="ignore"):
        lc = out + np.log(-np.expm1(-out))
    den = logsumexp(lc, axis=1)
    if not np.isfinite(den).all():
        raise ValueError("Empty output cell")
    out = np.log1p(10000 * np.exp(lc - den[:, None])).astype("float32")
    closed(out)
    return out, ix
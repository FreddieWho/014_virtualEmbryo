"""Late-anchor machinery for T1: per-coarse-group within-batch external trajectory (GSE230531 E8.5 -> E14.5),
time-warped to the target day pair, applied to real competition carrier cells as a zero-preserving shift."""
import numpy as np, scipy.sparse as sp
from pathlib import Path
VE = Path("/workspace/ve")
from label_means_const import COARSE  # noqa
G = np.load(VE / "ext/proc/groups.npz", allow_pickle=True)
GENES = list(G["genes"]); GROUPS = list(G["groups"])
def get(prefix, g, what):
    k = f"{prefix}|{g}|{what}"; return G[k] if k in G.files else None
def n(prefix, g): return int(G[f"{prefix}|{g}|n"]) if f"{prefix}|{g}|n" in G.files else 0
INEXT = None
def ext_delta(g, t_late=14.5, min_n=30, min_expr=0.02, shrink_k=50):
    """e_late - e8.5 for group g (within external batch), shrunk by cell count, masked for genes absent
    from the external features or not expressed in either external stage."""
    a, b = f"ext8.5", f"ext{t_late}"
    if n(a, g) < min_n or n(b, g) < min_n: return None
    ma, mb = get(a, g, "mean"), get(b, g, "mean")
    d = (mb - ma).astype(np.float64)
    nn = min(n(a, g), n(b, g)); d *= nn / (nn + shrink_k)
    d[(ma < min_expr) & (mb < min_expr)] = 0.0
    d[~INEXT_MASK] = 0.0
    return d
# Genes never trusted from the external anchor in ANY group: haemoglobins (blood ambient RNA), dissociation
# immediate-early/stress genes (enzymatic whole-heart digestion; van den Brink et al. 2017 list core), and
# platform-sensitive transcripts (competition data are multiome nuclei, external are whole cells): Malat1,
# mt- genes.
IEG = {"Fos", "Fosb", "Jun", "Junb", "Jund", "Egr1", "Egr2", "Egr3", "Atf3", "Ier2", "Ier3", "Ier5", "Dusp1",
       "Zfp36", "Klf2", "Klf4", "Klf6", "Nr4a1", "Hspa1a", "Hspa1b", "Hspa8", "Hsph1", "Btg2", "Cyr61", "Ccn1",
       "Socs3", "Gadd45b", "Ppp1r15a", "Mt1", "Mt2"}
GLOBAL_MASK = np.array([x.startswith(("Hba", "Hbb", "mt-")) or x in IEG or x == "Malat1" for x in GENES])
def ambient_mask(g, t_late=14.5, ratio=4.0):
    """For non-CM groups: genes whose external late-stage level in g is mostly CM ambient RNA
    (CM_V or CM_A mean > ratio x group mean) are not trusted; also haemoglobin genes (blood ambient)."""
    if g.startswith("CM"): return GLOBAL_MASK.copy()
    cm = np.maximum(get(f"ext{t_late}", "CM_V", "mean"), get(f"ext{t_late}", "CM_A", "mean"))
    m = cm > ratio * np.maximum(get(f"ext{t_late}", g, "mean"), 1e-3)
    m &= cm > 0.3
    hb = np.array([x.startswith(("Hba", "Hbb")) for x in GENES])
    return m | hb | GLOBAL_MASK
INEXT_MASK = np.array([True] * len(GENES))
def set_inext(mask):
    global INEXT_MASK; INEXT_MASK = mask
def warp_fraction(t0, t1, kind="log", t_a=8.5, t_b=14.5):
    phi = {"log": np.log, "lin": lambda t: t}[kind]
    return float((phi(t1) - phi(t0)) / (phi(t_b) - phi(t_a)))
def zp_shift(X, groups_of_rows, deltas, floor=0.05, det=None):
    """Zero-preserving per-group shift: detected entries move by delta/detfrac (detfrac from the carrier
    group itself), so the group mean moves by ~delta; result clipped at 0. X: CSR, returns new CSR."""
    X = X.tocsr(copy=True).astype(np.float32)
    for g, d in deltas.items():
        rows = np.where(groups_of_rows == g)[0]
        if len(rows) == 0 or d is None: continue
        sub = X[rows]; detf = np.asarray((sub > 0).mean(0)).ravel()
        step = (d / np.maximum(detf, floor)).astype(np.float32)
        for r in rows:
            s, e = X.indptr[r], X.indptr[r + 1]
            X.data[s:e] = np.maximum(X.data[s:e] + step[X.indices[s:e]], 0)
    X.eliminate_zeros(); return X

COMP_SUBSET = ("CM_V", "CM_A", "ENDO", "SHF")
def comp_weights(carrier_groups, frac, subset=COMP_SUBSET, t_late=14.5, strength=1.0):
    """Per-cell sampling weights moving the carrier's group proportions, within `subset` only (the subset's
    total share is preserved), a log-time fraction toward the external late-stage proportions."""
    lab = np.load(VE / f"ext/proc/ext{t_late}_labels.npy", allow_pickle=True)
    q = np.array([(lab == g).sum() for g in subset], float); q /= q.sum()
    p = np.array([(carrier_groups == g).sum() for g in subset], float); p /= p.sum()
    pn = p * np.exp(strength * frac * np.log(np.maximum(q, 1e-3) / p)); pn /= pn.sum()
    w = np.ones(len(carrier_groups))
    for k, g in enumerate(subset): w[carrier_groups == g] = pn[k] / p[k]
    return w, dict(zip(subset, np.round(pn / p, 3)))

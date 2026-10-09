"""(A) OT-coupled two-part generative displacement for T1.
Within each coarse group, entropic OT couples external E8.5 cells to external E14.5 cells (same batch,
GSE230531). Each external E8.5 cell gets a cell-specific displacement in full gene space, split in two parts:
  dlogit = logit(det of barycentric E14.5 partners) - logit(det of kNN-smoothed self)   (gene on/off)
  dlev   = level-given-detected of partners - level-given-detected of self               (expression level)
Carrier (competition) cells inherit the field from their k nearest external E8.5 analogues (group-wise
z-scored PCA latent, so batch/platform offsets cancel), and are then *generated*: zero entries switch on
with prob (p_new-d)/(1-d) using a value drawn from the carrier group's real detected values of that gene,
detected entries switch off with prob (d-p_new)/d, and surviving detected values move by tau*dlev
(floored at the gene's smallest detected level). tau = log-time warp fraction x amplitude.
No group-mean zero-preserving shift (the LA mechanism) is used."""
import numpy as np, scipy.sparse as sp, anndata as ad
from pathlib import Path
from scipy.special import logsumexp, expit, logit
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
import anchor as A
VE = Path("/workspace/ve"); P = VE / "ext/proc"
OT_GROUPS = ("CM_V", "CM_A", "ENDO", "EPI", "MESO", "NCC", "SHF")

def load_ext(t):
    tag = {8.5: "E8_5", 14.5: "E14_5"}[t]
    X = sp.vstack([ad.read_h5ad(f).X for f in sorted(P.glob(f"GSM*_{tag}_*.h5ad"))]).tocsr().astype(np.float32)
    lab = np.load(P / f"ext{t}_labels.npy", allow_pickle=True).astype(str); assert len(lab) == X.shape[0]
    return X, lab

def sinkhorn(C, eps, iters=1000, tol=1e-6):
    n, m = C.shape; la, lb = -np.log(n), -np.log(m); f = np.zeros(n); g = np.zeros(m); K = -C / eps
    for it in range(iters):
        f_old = f
        f = eps * (la - logsumexp(K + g[None, :] / eps, axis=1))
        g = eps * (lb - logsumexp(K + f[:, None] / eps, axis=0))
        if it % 20 == 0 and np.max(np.abs(f - f_old)) < tol * eps: break
    return np.exp(K + f[:, None] / eps + g[None, :] / eps)

def hvg(X, ok, n):
    mu = np.asarray(X.mean(0)).ravel(); var = np.asarray(X.multiply(X).mean(0)).ravel() - mu ** 2
    disp = np.where(ok & (mu > 0.02), var / np.maximum(mu, 1e-6), -np.inf)
    return np.sort(np.argsort(-disp)[:n])

def zscore(Xd):
    mu = Xd.mean(0); sd = Xd.std(0) + 1e-2; return (Xd - mu) / sd

def group_field(g, X8, X14, trust, n_hvg=2000, n_pc=30, k_self=15, eps=0.05, shrink_k=50, seed=0):
    """Field on external E8.5 cells of group g. trust: bool gene mask (in_external & not masked)."""
    n8, n14 = X8.shape[0], X14.shape[0]
    h = hvg(sp.vstack([X8, X14]).tocsr(), trust, n_hvg)
    Zp = PCA(n_pc, random_state=seed).fit_transform(np.vstack([X8[:, h].toarray(), X14[:, h].toarray()]))
    z8, z14 = Zp[:n8], Zp[n8:]
    C = ((z8[:, None, :] - z14[None, :, :]) ** 2).sum(-1); C /= np.median(C)
    pi = sinkhorn(C, eps); W = pi / pi.sum(1, keepdims=True)
    B14 = (X14 > 0).astype(np.float32)
    yhat = (sp.csr_matrix(W.astype(np.float32)) @ X14).toarray()
    qhat = (sp.csr_matrix(W.astype(np.float32)) @ B14).toarray()
    nn = NearestNeighbors(n_neighbors=min(k_self, n8)).fit(z8); _, ix = nn.kneighbors(z8)
    S = sp.csr_matrix((np.full(ix.size, 1.0 / ix.shape[1], np.float32), (np.repeat(np.arange(n8), ix.shape[1]), ix.ravel())), shape=(n8, n8))
    xhat = (S @ X8).toarray(); phat = (S @ (X8 > 0).astype(np.float32)).toarray()
    lo, hi = 1e-3, 1 - 1e-3
    dlogit = logit(np.clip(qhat, lo, hi)) - logit(np.clip(phat, lo, hi))
    both = (qhat >= 0.02) & (phat >= 0.02)
    dlev = np.where(both, yhat / np.maximum(qhat, 1e-6) - xhat / np.maximum(phat, 1e-6), 0.0)
    f = min(n8, n14) / (min(n8, n14) + shrink_k)                      # same n-shrinkage as the LA anchor
    m8 = np.asarray(X8.mean(0)).ravel(); m14 = np.asarray(X14.mean(0)).ravel()
    dead = (~trust) | ((m8 < 0.02) & (m14 < 0.02))
    dlogit[:, dead] = 0; dlev[:, dead] = 0
    # transfer latent: PCA on z-scored external E8.5 cells (HVGs of E8.5 within group)
    h8 = hvg(X8, trust, n_hvg); X8h = X8[:, h8].toarray()
    mu8 = X8h.mean(0); sd8 = X8h.std(0) + 1e-2
    pca8 = PCA(n_pc, random_state=seed).fit((X8h - mu8) / sd8)
    diag = {"n8": n8, "n14": n14, "shrink": f, "ot_entropy_rowmax_mean": float((W.max(1)).mean()),
            "mean_dlogit_abs": float(np.abs(dlogit).mean()), "mean_dlev_abs": float(np.abs(dlev).mean())}
    return {"dlogit": (f * dlogit).astype(np.float32), "dlev": (f * dlev).astype(np.float32), "h8": h8,
            "pca8": pca8, "z8t": pca8.transform((X8h - mu8) / sd8), "diag": diag}

def build_fields(groups=OT_GROUPS, t_late=14.5, log=print):
    X8, l8 = load_ext(8.5); X14, l14 = load_ext(t_late); fields = {}
    for g in groups:
        a, b = l8 == g, l14 == g
        if a.sum() < 30 or b.sum() < 30: log(f"skip {g} n8={a.sum()} n14={b.sum()}"); continue
        trust = A.INEXT_MASK & ~A.ambient_mask(g, t_late)
        fields[g] = group_field(g, X8[a], X14[b], trust); log(f"field {g} {fields[g]['diag']}")
    return fields

def generate(Xc, groups_c, fields, tau, seed, k_transfer=10, level=True, onoff=True, smooth=False, k_smooth=15, neutral=False):
    """Xc: CSR carrier (log1p CP10k, panel genes); returns new CSR + per-group diagnostics."""
    rng = np.random.default_rng(seed); Xc = Xc.tocsr().astype(np.float32)
    blocks = {}; diag = {}
    for g, F in fields.items():
        rows = np.flatnonzero(groups_c == g)
        if not len(rows): continue
        B = Xc[rows].toarray()
        Zc = B[:, F["h8"]]; Zc = (Zc - Zc.mean(0)) / (Zc.std(0) + 1e-2)
        zc = F["pca8"].transform(Zc)
        _, nb = NearestNeighbors(n_neighbors=k_transfer).fit(F["z8t"]).kneighbors(zc)
        M = sp.csr_matrix((np.full(nb.size, 1.0 / nb.shape[1], np.float32), (np.repeat(np.arange(len(rows)), nb.shape[1]), nb.ravel())), shape=(len(rows), F["dlogit"].shape[0]))
        dl = np.asarray(M @ F["dlogit"]); dv = np.asarray(M @ F["dlev"])          # (n_c, G) kNN-averaged field
        det = B > 0; d = det.mean(0)                                     # carrier group detection per gene
        minpos = np.where(det.any(0), np.where(det, B, np.inf).min(0), 0.0)
        lo, hi = 1e-3, 1 - 1e-3
        L0 = logit(np.clip(d, lo, hi))[None, :]; act = (d > 0)[None, :] & (dl != 0)
        if neutral:   # complexity-neutral: per-cell logit offset c with sum_j (pnew - d) = 0 over active genes
            # (external E8.5->E14.5 loses 20-30% genes/cell from protocol/tissue; competition E8.5->E9.5 is flat)
            lo_c = np.full((len(rows), 1), -6.0, np.float32); hi_c = np.full((len(rows), 1), 6.0, np.float32)
            for _ in range(30):
                mid = (lo_c + hi_c) / 2
                bal = np.where(act, expit(L0 + tau * dl + mid) - d[None, :], 0).sum(1, keepdims=True)
                lo_c = np.where(bal < 0, mid, lo_c); hi_c = np.where(bal >= 0, mid, hi_c)
            coff = (lo_c + hi_c) / 2
        else: coff = 0.0
        pnew = np.where(act, expit(L0 + tau * dl + coff), d[None, :])
        u = rng.random(B.shape, dtype=np.float32)
        p_on = np.where(d[None, :] > 0, np.clip((pnew - d[None, :]) / np.maximum(1 - d[None, :], 1e-6), 0, 1), 0)
        p_off = np.clip((d[None, :] - pnew) / np.maximum(d[None, :], 1e-6), 0, 1)
        if smooth:   # neighbour-aware switching: genes turn on where the cell's carrier neighbours express them
            _, nbc = NearestNeighbors(n_neighbors=min(k_smooth, len(rows))).fit(zc).kneighbors(zc)
            Mc = sp.csr_matrix((np.full(nbc.size, 1.0 / nbc.shape[1], np.float32), (np.repeat(np.arange(len(rows)), nbc.shape[1]), nbc.ravel())), shape=(len(rows), len(rows)))
            sd = np.asarray(Mc @ det.astype(np.float32))
            w_on = np.where(~det, sd, 0); w_on = w_on / np.maximum(w_on.sum(0) / np.maximum((~det).sum(0), 1), 1e-6)
            w_off = np.where(det, 1 - sd, 0); w_off = w_off / np.maximum(w_off.sum(0) / np.maximum(det.sum(0), 1), 1e-6)
            p_on = np.clip(p_on * w_on, 0, 1); p_off = np.clip(p_off * w_off, 0, 1)
        if not onoff: p_on = np.zeros_like(p_on); p_off = np.zeros_like(p_off)
        on = (~det) & (u < p_on); off = det & (u < p_off)
        newB = B.copy()
        keep = det & ~off
        if level: newB[keep] = np.maximum(B[keep] + tau * dv[keep], np.broadcast_to(minpos, B.shape)[keep])
        newB[off] = 0
        if on.any():   # draw onset values from the carrier group's real detected values of the gene (+ level shift)
            Csc = sp.csc_matrix(B); ci, cj = np.nonzero(on)
            nnz = np.diff(Csc.indptr)[cj]; pick = Csc.indptr[cj] + (rng.random(len(cj)) * nnz).astype(np.int64)
            vals = Csc.data[pick] + (tau * dv[ci, cj] if level else 0)
            newB[ci, cj] = np.maximum(vals, minpos[cj])
        blocks[g] = (rows, newB)
        diag[g] = {"rows": int(len(rows)), "complexity_offset_mean": float(np.mean(coff)), "on": int(on.sum()), "off": int(off.sum()), "nnz_before": int(det.sum()),
                   "pb_shift_l2": float(np.linalg.norm(newB.mean(0) - B.mean(0)))}
        del B, dl, dv, u, p_on, p_off
    changed = np.concatenate([r for r, _ in blocks.values()]) if blocks else np.array([], int)
    rest = np.setdiff1d(np.arange(Xc.shape[0]), changed)
    full = sp.vstack([sp.csr_matrix(b) for _, b in blocks.values()] + [Xc[rest]]).tocsr()
    order = np.concatenate([changed, rest]); Xn = full[np.argsort(order)]
    return Xn.tocsr().astype(np.float32), diag

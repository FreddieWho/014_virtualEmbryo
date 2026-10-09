"""Prepare GSE230531 allowed samples (E8.5, E14.5, E16.5 only) for T1 late-anchor work.
Raw unfiltered 10x matrices -> cell calling (UMI/genes/mito thresholds) -> log1p(CP10k on ALL features,
same scheme as released T1 h5ad) -> subset to T1 panel genes by symbol (missing genes = 0, flagged in var).
"""
import gzip, sys, json
from pathlib import Path
import numpy as np, scipy.io, scipy.sparse as sp, anndata as ad, pandas as pd
VE = Path("/workspace/ve"); D = VE / "ext/GSE230531"; OUT = VE / "ext/proc"; OUT.mkdir(exist_ok=True)
PANEL = [l.strip() for l in open(VE / "data/T1__val.genes.txt")]
SAMPLES = {"GSM7226268_E8_5_1": 8.5, "GSM7226269_E8_5_2": 8.5, "GSM7226272_E14_5_1": 14.5,
           "GSM7226273_E14_5_2": 14.5, "GSM7226274_E16_5_1": 16.5, "GSM7226276_E16_5_2": 16.5}
BANNED = lambda t: 9.5 < t <= 13.5
MIN_UMI, MIN_GENES, MAX_MT = 1500, 700, 0.25
def read_mtx(path):
    """Tolerant MatrixMarket reader: GSM7226268's GEO file is a truncated gzip (size matches GEO listing);
    entries are column(barcode)-sorted, so a truncated read = complete cells for a barcode prefix + one
    partial last barcode, which is dropped."""
    import subprocess
    proc = subprocess.Popen(["bash", "-c", f"zcat {path} 2>/dev/null"], stdout=subprocess.PIPE)
    df = pd.read_csv(proc.stdout, sep=" ", comment="%", header=None, dtype=np.float64, on_bad_lines="skip")
    proc.wait()
    ng_, nb_, nnz = df.iloc[0].astype(int).tolist(); df = df.iloc[1:].dropna()
    truncated = len(df) < nnz
    i = df[0].values.astype(np.int64) - 1; j = df[1].values.astype(np.int64) - 1; v = df[2].values.astype(np.float32)
    if truncated:
        last = j.max(); k = j < last; i, j, v = i[k], j[k], v[k]
    return sp.csc_matrix((v, (i, j)), shape=(ng_, nb_)), (truncated, int(len(v)), int(nnz))
qc = {}
for s, t in SAMPLES.items():
    assert not BANNED(t), s
    feats = pd.read_csv(D / f"{s}_features.tsv.gz", sep="\t", header=None)
    M, truncated = read_mtx(D / f"{s}_matrix.mtx.gz")
    umi = np.asarray(M.sum(0)).ravel(); ng = np.asarray((M > 0).sum(0)).ravel()
    mt = feats[1].str.startswith("mt-").values
    mtf = np.asarray(M[mt].sum(0)).ravel() / np.maximum(umi, 1)
    keep = (umi >= MIN_UMI) & (ng >= MIN_GENES) & (mtf <= MAX_MT)
    M = M[:, keep].T.tocsr().astype(np.float32)                           # cells x genes
    lib = np.asarray(M.sum(1)).ravel()
    M = sp.diags(1e4 / lib) @ M; M.data = np.log1p(M.data)
    sym = feats[1].values; first = ~pd.Series(sym).duplicated().values
    idx = {g: i for i, g in enumerate(sym) if first[i]}
    cols = np.array([idx.get(g, -1) for g in PANEL]); have = cols >= 0
    P = sp.lil_matrix((M.shape[0], len(PANEL)), dtype=np.float32).tocsc()
    Msub = M.tocsc()[:, cols[have]]
    P = sp.csc_matrix((M.shape[0], len(PANEL)), dtype=np.float32)
    P = sp.hstack([Msub, sp.csc_matrix((M.shape[0], (~have).sum()), dtype=np.float32)]).tocsc()
    order = np.concatenate([np.where(have)[0], np.where(~have)[0]]); inv = np.argsort(order)
    P = P[:, inv].tocsr()
    a = ad.AnnData(P, obs=pd.DataFrame({"sample": s, "stage": t, "umi": umi[keep], "n_genes": ng[keep],
                                        "mt_frac": mtf[keep]}, index=[f"{s}:{i}" for i in range(P.shape[0])]),
                   var=pd.DataFrame({"in_external": have}, index=PANEL))
    a.write_h5ad(OUT / f"{s}.h5ad", compression="gzip")
    qc[s] = {"stage": t, "barcodes_raw": int(len(umi)), "cells_kept": int(keep.sum()), "median_umi": float(np.median(umi[keep])),
             "median_genes": float(np.median(ng[keep])), "panel_genes_present": int(have.sum()),
             "mtx_truncated_at_source": truncated[0], "entries_read": truncated[1], "entries_declared": truncated[2]}
    print(s, qc[s], flush=True); del M, P, Msub
json.dump({"thresholds": {"min_umi": MIN_UMI, "min_genes": MIN_GENES, "max_mt": MAX_MT}, "samples": qc},
          open(OUT / "QC.json", "w"), indent=1)

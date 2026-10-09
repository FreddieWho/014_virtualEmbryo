"""Small full-panel engineering smoke, never a future-stage validation.

Uses 256+256 disjoint E9.5 cells and no fitted candidate or submission.
One PCA fit for the allowed reference is reused across all raw MMD metrics.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import json, sys, time, hashlib, resource
from pathlib import Path
import numpy as np
import anndata as ad
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import rbf_kernel
from copula_restore import restore
from pair_diagnostics import uniform_pairs, pair_moments, compare_pair_moments

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("T1_RECOVERY_ROOT", "t1_recovery_run"))/"data/E9.5_RNA.h5ad"
N, SEED = 256, 20261009


def library_summary(X):
    lib = np.empty(X.shape[0],dtype=np.float64)
    det = np.empty(X.shape[0],dtype=np.int64)
    for start in range(0,X.shape[0],128):
        stop=min(start+128,X.shape[0])
        block=np.asarray(X[start:stop],dtype=np.float64)
        lib[start:stop]=np.expm1(block).sum(axis=1)
        det[start:stop]=(block>0).sum(axis=1)
    return {"library_quantiles": np.quantile(lib, [.01, .5, .99]).tolist(),
            "zero_library_rows": int((lib == 0).sum()),
            "median_detected_genes": float(np.median(det))}


def health(parent, candidate):
    p, c = library_summary(parent), library_summary(candidate)
    ratios = np.asarray(c["library_quantiles"])/np.maximum(p["library_quantiles"], 1e-12)
    det = c["median_detected_genes"]/max(p["median_detected_genes"], 1e-12)
    ok = (c["zero_library_rows"] <= p["zero_library_rows"] and
          .8 <= ratios[1] <= 1.25 and .5 <= ratios[0] <= 2 and
          .5 <= ratios[2] <= 2 and .8 <= det <= 1.25)
    return {"pass": bool(ok), "parent": p, "candidate": c,
            "library_quantile_ratios": ratios.tolist(),
            "median_detected_ratio": float(det)}


def main():
    t0 = time.time()
    a = ad.read_h5ad(DATA, backed="r")
    rng = np.random.default_rng(SEED)
    ix = rng.choice(a.n_obs, 2*N, replace=False)
    src_ix, ref_ix = np.sort(ix[:N]), np.sort(ix[N:])
    X = a[src_ix].X.toarray().astype(np.float32)
    Y = a[ref_ix].X.toarray().astype(np.float32)
    states = a.obs.iloc[src_ix]["celltype"].astype(str).to_numpy()
    panel = a.var_names.astype(str).tolist()
    a.file.close()
    if X.shape[1] != 32285:
        raise AssertionError("T1 full-panel check failed")
    C = X.copy()
    # Marginal-preserving, deliberately synthetic gene-wise emitter corruption.
    for state_i, state in enumerate(sorted(set(states))):
        rows = np.flatnonzero(states == state)
        k = int(.1*len(rows))
        if k < 2:
            continue
        for g in range(X.shape[1]):
            rr = np.random.default_rng(np.random.SeedSequence([SEED,state_i,g]))
            ids = rr.choice(rows, k, replace=False)
            C[ids,g] = X[rr.permutation(ids),g]
    np.savez_compressed(ROOT/"SOURCE_SPLIT.npz", source_rows=src_ix,
                        reference_rows=ref_ix, states=states.astype("U"))
    O, od = restore(C, X, states)
    S, sd = restore(C, X, states, shuffle_template=True)
    arms = {"clean_source_template": X, "synthetic_corruption": C,
            "coherent_restore": O, "shuffled_template_control": S}
    # Truth-fitted PCA matches core_metrics.mmd_unbiased's feature-space policy.
    pca = PCA(n_components=30, random_state=0).fit(Y)
    ZY = pca.transform(Y)
    d2 = ((ZY[:,None,:]-ZY[None,:,:])**2).sum(-1)
    gamma = 1/(np.median(d2[d2 > 0])+1e-9)
    Dyy = cdist(Y, Y)
    metrics = {}
    for name, A in arms.items():
        ZA = pca.transform(A)
        da = cdist(A,A)
        energy = 2*cdist(A,Y).mean()-da.sum()/(N*(N-1))-Dyy.sum()/(N*(N-1))
        mmd = 0
        for scale in (.25,.5,1.,2.,4.):
            aa, bb, ab = (rbf_kernel(ZA,ZA,gamma=gamma*scale),
                          rbf_kernel(ZY,ZY,gamma=gamma*scale),
                          rbf_kernel(ZA,ZY,gamma=gamma*scale))
            np.fill_diagonal(aa,0); np.fill_diagonal(bb,0)
            mmd += aa.sum()/(N*(N-1))+bb.sum()/(N*(N-1))-2*ab.mean()
        metrics[name] = {"energy_distance":float(energy),"mmd_u":float(mmd/5),
                         "library":library_summary(A)}
    pair_results = []
    for seed in (20261009,20261010,20261011):
        pairs = uniform_pairs(X.shape[1], seed=seed)
        yy = pair_moments(Y,pairs)
        pp = {name:pair_moments(A,pairs) for name,A in arms.items()}
        row = {"seed":seed, "pairs":int(len(pairs)), "comparisons":{}}
        for name in ("clean_source_template","coherent_restore","shuffled_template_control"):
            row["comparisons"][name] = compare_pair_moments(pp["synthetic_corruption"],pp[name],yy)
        for name in arms:
            metrics[name].setdefault("variogram_by_seed",[]).append(
                float(np.mean((pp[name]["moment"]-yy["moment"])**2)))
        pair_results.append(row)
    result = {
        "status":"ENGINEERING_SMOKE_ONLY", "future_truth_used":False,
        "limitation":"Paired clean template gives structural recovery advantage. No biological or temporal-validation claim, no setting selection.",
        "n_source":N,"n_disjoint_reference":N,"n_genes":X.shape[1],
        "input_file":str(DATA),"input_sha256_expected":"0296e0043842f944a663f3c11ac1542d1bbee733c1cd657bd56f75af65958361",
        "input_hash_verified_by":"baseline recovery worker; source file read-only",
        "seed":SEED,"corruption_fraction":.1,"blend":.5,
        "health_coherent":health(C,O),"health_shuffled":health(C,S),
        "operator_coherent":od,"operator_shuffled":sd,
        "metrics":metrics,"pair_decomposition":pair_results,
        "wall_seconds":time.time()-t0,
        "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    (ROOT/"SOURCE_SANITY.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k in
          ("status","n_source","n_genes","wall_seconds","metrics")},indent=2))


if __name__ == "__main__":
    main()

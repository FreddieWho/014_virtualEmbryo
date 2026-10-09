"""Source-reference full-panel diagnostics for fixed final arms.

E9.5 is a released source, not E10.5 truth. These numbers cannot rank future
predictions or attach an official score to the reconstructed baseline.
"""
import os
for k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[k]="1"
import argparse,json,sys,time,resource
from pathlib import Path
import numpy as np
import anndata as ad
from scipy import sparse
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import rbf_kernel
from pair_diagnostics import uniform_pairs,pair_moments,compare_pair_moments,changed_pair_support


def distances(A,B):
    # Same Euclidean metric, BLAS-based chunks rather than slow scalar cdist.
    A=np.asarray(A,dtype=np.float64);B=np.asarray(B,dtype=np.float64)
    sq=(A*A).sum(1)[:,None]+(B*B).sum(1)[None,:]-2*(A@B.T)
    return np.sqrt(np.maximum(sq,0))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",required=True)
    p.add_argument("--candidate",required=True)
    p.add_argument("--control",required=True)
    p.add_argument("--reference",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args();t0=time.time()
    out=Path(a.out)
    if out.exists():raise FileExistsError(out)
    pa=ad.read_h5ad(a.parent)
    P=pa.X.toarray() if sparse.issparse(pa.X) else np.asarray(pa.X)
    C=np.load(a.candidate,mmap_mode="r");S=np.load(a.control,mmap_mode="r")
    arms={"reconstructed_parent":P,"coherent_carrier":C,"shuffled_carrier_control":S}
    src=ad.read_h5ad(a.reference,backed="r")
    if list(src.var_names)!=list(pa.var_names):raise AssertionError("reference panel")
    reference_indices=np.sort(np.random.default_rng(20261009).choice(src.n_obs,2000,replace=False))
    R=src[reference_indices].X.toarray().astype(np.float32)
    src.file.close()
    pca=PCA(n_components=30,random_state=0).fit(R)
    ZR=pca.transform(R)
    seeds=(20261009,20261010,20261011)
    metrics={name:[] for name in arms}
    for seed in seeds:
        rng=np.random.default_rng(seed)
        # Match pair counts across arms and keep independent source references.
        pred_idx=rng.choice(P.shape[0],2000,replace=False)
        ref_idx=rng.choice(len(R),2000,replace=False)
        Eidx=pred_idx[:1500];Tidx=ref_idx[:1500]
        B=ZR[ref_idx]
        d2=((B[:,None,:]-B[None,:,:])**2).sum(-1)
        gamma=1/(np.median(d2[d2>0])+1e-9)
        ref_energy=distances(R[Tidx],R[Tidx])
        n=len(Eidx);m=len(Tidx)
        for name,A in arms.items():
            az=pca.transform(np.asarray(A[pred_idx]))
            mmd=0.
            for scale in (.25,.5,1.,2.,4.):
                aa,bb,ab=rbf_kernel(az,az,gamma=gamma*scale),rbf_kernel(B,B,gamma=gamma*scale),rbf_kernel(az,B,gamma=gamma*scale)
                np.fill_diagonal(aa,0);np.fill_diagonal(bb,0)
                mmd+=aa.sum()/(len(az)*(len(az)-1))+bb.sum()/(len(B)*(len(B)-1))-2*ab.mean()
            aa=distances(A[Eidx],A[Eidx]);ab=distances(A[Eidx],R[Tidx])
            energy=2*ab.mean()-aa.sum()/(n*(n-1))-ref_energy.sum()/(m*(m-1))
            pairs=uniform_pairs(P.shape[1],seed=seed)
            ap=pair_moments(A[Eidx],pairs)
            rp=pair_moments(R[Tidx],pairs)
            vario=float(np.mean((ap["moment"]-rp["moment"])**2))
            metrics[name].append({"seed":seed,"mmd_u":float(mmd/5),"energy_distance":float(energy),"variogram":vario})
            print(name,metrics[name][-1],flush=True)
    # Full-row decomposition is necessary for exact fixed-marginal algebra.
    pairs=uniform_pairs(P.shape[1],seed=20261009)
    pm=pair_moments(P,pairs);cm=pair_moments(C,pairs);sm=pair_moments(S,pairs)
    rr=pair_moments(R,pairs)
    result={
        "status":"SOURCE_REFERENCE_DIAGNOSTIC_ONLY",
        "reference_stage":"released official E9.5, not hidden E10.5",
        "baseline_server_score":None,"historical_comparison_replay_confounded":True,
        "full_gene_panel":P.shape[1],"n_parent_cells":P.shape[0],
        "reference_rows":reference_indices.tolist(),"metrics":metrics,
        "full_row_pair_moments":{
            "coherent":compare_pair_moments(pm,cm,rr),
            "shuffled":compare_pair_moments(pm,sm,rr)},
        "actual_sampled_pair_support":{
            "coherent":changed_pair_support(P,C,pairs),
            "shuffled":changed_pair_support(P,S,pairs)},
        "wall_seconds":time.time()-t0,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    out.write_text(json.dumps(result,indent=2))
    print(json.dumps({"status":result["status"],"wall_seconds":result["wall_seconds"],"out":str(out)},indent=2))


if __name__=="__main__":main()

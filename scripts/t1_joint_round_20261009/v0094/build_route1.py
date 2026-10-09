"""Build the one frozen route-1 intervention after baseline recovery.

Requires explicit baseline and template hashes. Never uploads or edits a
previous artifact. The common reconstructed parent has no inherited score.
"""
import os
for k in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS"):
    os.environ[k] = "1"
import argparse, hashlib, json, platform, resource, time
from pathlib import Path
import numpy as np
import scipy
from scipy import sparse
import anndata as ad
from copula_restore import restore
from source_sanity import health


def sha(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def expression_sha(X):
    h=hashlib.sha256()
    for start in range(0,X.shape[0],128):
        h.update(np.ascontiguousarray(X[start:start+128],dtype=np.float32).tobytes())
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",required=True)
    p.add_argument("--parent-sha256",required=True)
    p.add_argument("--template",required=True)
    p.add_argument("--template-expression-sha256",required=True)
    p.add_argument("--states",required=True)
    p.add_argument("--states-sha256",required=True)
    p.add_argument("--recovery-receipt",required=True)
    p.add_argument("--recovery-receipt-sha256",required=True)
    p.add_argument("--panel",required=True)
    p.add_argument("--panel-sha256",required=True)
    p.add_argument("--outdir",required=True)
    p.add_argument("--name",required=True)
    p.add_argument("--shuffle-control",action="store_true")
    a=p.parse_args()
    t0=time.time()
    outdir=Path(a.outdir)
    output=outdir/(a.name+".h5ad")
    npy_output=outdir/(a.name+".npy")
    result_path=outdir/(a.name+".json")
    if output.exists() or result_path.exists() or npy_output.exists():
        raise FileExistsError("Never overwrite a prior candidate or receipt")
    if sha(a.parent)!=a.parent_sha256 or sha(a.states)!=a.states_sha256:
        raise AssertionError("baseline/state identity drift")
    if sha(a.recovery_receipt)!=a.recovery_receipt_sha256:
        raise AssertionError("baseline recovery receipt drift")
    if sha(a.panel)!=a.panel_sha256:
        raise AssertionError("official panel identity drift")
    official_panel=Path(a.panel).read_text().splitlines()
    pa=ad.read_h5ad(a.parent)
    if list(pa.var_names)!=official_panel:
        raise AssertionError("parent panel differs from official T1 panel order")
    X=pa.X.toarray() if sparse.issparse(pa.X) else np.asarray(pa.X)
    X=np.asarray(X,dtype=np.float32)
    T=np.load(a.template,mmap_mode="r")
    states=np.load(a.states).astype(str)
    if expression_sha(T)!=a.template_expression_sha256:
        raise AssertionError("paired template expression drift")
    if X.shape!=(5118,32285) or T.shape!=X.shape or len(states)!=len(X):
        raise AssertionError("full T1 panel/paired-row shape contract")
    O,d=restore(X,T,states,blend=.5,block_size=256,
                shuffle_template=a.shuffle_control,seed=20261009)
    h=health(X,O)
    # Independent multiset check, without relying on restore's internal assertion.
    for c in sorted(set(states)):
        rows=np.flatnonzero(states==c)
        for start in range(0,X.shape[1],256):
            ix=np.ix_(rows,np.arange(start,min(start+256,X.shape[1])))
            if not np.array_equal(np.sort(X[ix],axis=0),np.sort(O[ix],axis=0)):
                raise AssertionError("independent state/gene multiset check failed")
    source_files=[Path(__file__),Path(__file__).with_name("copula_restore.py"),
                  Path(__file__).with_name("source_sanity.py")]
    prov={
        "method":"paired_empirical_copula_restoration",
        "baseline_identity":"RECONSTRUCTED_v0092_NOT_EXACT_HISTORICAL_SCORED_FILE",
        "baseline_server_score":None,
        "historical_v0092_comparison_replay_confounded":True,
        "parent_path":a.parent,"parent_sha256":a.parent_sha256,
        "parent_expression_sha256":expression_sha(X),
        "paired_template_path":a.template,
        "paired_template_expression_sha256":a.template_expression_sha256,
        "state_path":a.states,"state_sha256":a.states_sha256,
        "recovery_receipt_sha256":sha(a.recovery_receipt),
        "official_panel_path":a.panel,"official_panel_sha256":a.panel_sha256,
        "operator":d,"health":h,
        "exact_state_gene_marginals":True,
        "row_libraries_not_invariant":True,
        "hidden_target_used":False,"new_external_source":False,
        "runtime":{"python":platform.python_version(),"numpy":np.__version__,
                   "scipy":scipy.__version__,"anndata":ad.__version__,"threads":1},
        "code_sha256":{x.name:sha(x) for x in source_files},
    }
    if not h["pass"]:
        outdir.mkdir(parents=True,exist_ok=True)
        result_path.write_text(json.dumps({"status":"FAILED_FROZEN_HEALTH_GATE",
            "provenance":prov},indent=2))
        raise RuntimeError("Frozen health gate failed; no candidate emitted")
    out=pa.copy()
    out.X=sparse.csr_matrix(O.astype(np.float32))
    out.uns["t1_joint_restore_provenance"]=json.dumps(prov,sort_keys=True)
    if list(out.var_names)!=list(pa.var_names) or not out.obs_names.equals(pa.obs_names):
        raise AssertionError("protected rows/columns changed")
    outdir.mkdir(parents=True,exist_ok=True)
    out.write_h5ad(output,compression="gzip")
    # Save portable expression plus hashes; full H5AD is retained for Library.
    np.save(npy_output,O)
    result={"status":"LOCAL_CONTROL_NOT_FOR_SUBMISSION" if a.shuffle_control else
                      "CANDIDATE_BUILT_NOT_SUBMITTED",
            "file":str(output),"file_sha256":sha(output),
            "expression_sha256":expression_sha(O),"bytes":output.stat().st_size,
            "provenance":prov,"wall_seconds":time.time()-t0,
            "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    result_path.write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="provenance"},indent=2))


if __name__=="__main__":
    main()

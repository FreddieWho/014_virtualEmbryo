"""Independent scalar-loop replay; does not import the candidate operator."""
import runtime
import argparse,json
from pathlib import Path
import numpy as np,anndata as ad

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--artifacts',required=True);a=ap.parse_args()
    v=runtime.initialize(a.data);out=Path(a.artifacts);b=json.loads((out/'BUILD.json').read_text());m=np.load(out/'frozen_model.npz')
    genes=m['genes'].tolist();early_name=b['args']['prev'].split(':')[0];late_name=b['args']['last'].split(':')[0]
    assert set([early_name,late_name])<=set(['E8.25_late','E8.75','E9.5'])
    E=v.load_stage(early_name,genes);L=v.load_stage(late_name,genes)
    for stage in [early_name,late_name]:assert v.sha256(Path(a.data)/(stage+'.h5ad'))==b['source_hashes'][stage]
    et=np.asarray(E.obs.celltype.astype(str));lt=np.asarray(L.obs.celltype.astype(str));rows=m['source_rows'];x=np.asarray(L.X[rows],np.float64);labels=lt[rows]
    states=m['states'].tolist();d=m['delta']
    for j,s in enumerate(states):assert np.array_equal(d[j],np.median(L.X[lt==s],axis=0)-np.median(E.X[et==s],axis=0))
    parent=ad.read_h5ad(b['artifacts']['parent']['path']);candidate=ad.read_h5ad(b['artifacts']['zp']['path'])
    y=x.copy();touched=np.zeros(len(x),bool)
    for j,s in enumerate(states):
        ix=np.flatnonzero(labels==s);touched[ix]=True;block=x[ix].copy();positive=block>0
        frequency=np.maximum(np.count_nonzero(positive,axis=0)/len(ix),.05)
        drift=.9*d[j]
        for g in range(len(genes)):
            block[positive[:,g],g]+=drift[g]/frequency[g]
        block=np.maximum(block,0.)
        count=np.expm1(block);count*=np.expm1(x[ix]).sum(1)[:,None]/np.maximum(count.sum(1),1e-12)[:,None]
        y[ix]=np.log1p(count)
    y=y.astype(np.float32)
    checks={'independent_X_exact':bool(np.array_equal(y,candidate.X)),'max_abs_X_error':float(np.max(np.abs(y-candidate.X))),
            'median_deltas_source_exact':True,'source_hashes_exact':True,'same_obs':candidate.obs.equals(parent.obs),'same_var':candidate.var.equals(parent.var),
            'same_coordinates':bool(np.array_equal(candidate.obsm['spatial_3D'],parent.obsm['spatial_3D'])),
            'coordinates_source_exact':bool(np.array_equal(candidate.obsm['spatial_3D'],np.asarray(L.obsm['spatial_3D'])[rows,:3].astype(np.float32))),
            'orphan_source_exact':bool(np.array_equal(candidate.X[~touched],x[~touched].astype(np.float32))),
            'zero_to_positive':int(((x==0)&(candidate.X>0)).sum()),'source_row_count':len(rows),'source_rows_unique':len(np.unique(rows))==len(rows),
            'historical_X2_byte_parity':b['historical_x2_byte_parity'],'historical_v30_byte_parity':False}
    lib0=np.expm1(x).sum(1);lib1=np.expm1(np.asarray(candidate.X,np.float64)).sum(1);checks['max_library_ratio_error']=float(np.max(np.abs(lib1/lib0-1)))
    checks['library_preservation_pass']=checks['max_library_ratio_error']<1e-6
    bad=np.flatnonzero(np.abs(lib1/lib0-1)>=1e-6)
    checks['library_failure_rows']=[{'output_row':int(i),'source_row':int(rows[i]),'state':str(labels[i]),'source_library':float(lib0[i]),'output_library':float(lib1[i])} for i in bad]
    checks['status']='PASS' if checks['library_preservation_pass'] else 'EXACT_REPLAY_LIBRARY_INVARIANT_FAIL'
    (out/'INDEPENDENT_CHECK.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
    assert checks['independent_X_exact'] and checks['same_obs'] and checks['same_var'] and checks['same_coordinates'] and checks['coordinates_source_exact'] and checks['orphan_source_exact'] and checks['zero_to_positive']==0 and checks['source_rows_unique']
    if b['split']=='final':assert checks['library_preservation_pass']

if __name__=='__main__':main()

"""Replicate-level coverage/onset audit, without candidate construction or tuning."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[k]='1'
import sys,argparse,json,gc
from pathlib import Path
import numpy as np,anndata as ad
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vework/t1ext'))
from label_means_const import COARSE

def stats(x):
 n=x.shape[0];nnz=np.asarray((x>0).sum(0)).ravel().astype(np.int32);sm=np.asarray(x.astype(np.float64).sum(0)).ravel();ss=np.asarray(x.astype(np.float64).power(2).sum(0)).ravel()
 return {'n':np.array(n),'positive_count':nnz,'det':nnz/max(n,1),'mean':sm/max(n,1),'positive_mean':sm/np.maximum(nnz,1),'positive_var':np.maximum((ss-sm*sm/np.maximum(nnz,1))/np.maximum(nnz-1,1),0)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--parent',required=True);p.add_argument('--states',required=True);p.add_argument('--official95',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 root=Path(a.inputs);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 par=ad.read_h5ad(a.parent);genes=np.array(par.var_names,dtype=str);states=np.load(a.states).astype(str);groups=np.array([COARSE[x] for x in states]);statsout={'genes':genes};allsamples=[];haveall=np.ones(len(genes),bool);cellcounts={}
 for f in sorted((root/'external_processed').glob('GSM*.h5ad')):
  obj=ad.read_h5ad(f);assert np.array_equal(obj.var_names,genes);name=f.stem;allsamples.append(name);haveall&=obj.var['in_external'].values;cellcounts[name]={}
  for g in sorted(set(COARSE.values())):
   m=obj.obs.coarse.to_numpy()==g;x=obj.X[m];st=stats(x);cellcounts[name][g]=int(m.sum())
   for k,v in st.items():statsout[f'{name}|{g}|{k}']=v
  del obj;gc.collect()
 official=ad.read_h5ad(a.official95,backed='r');have95=np.zeros(len(genes),int)
 for lo in range(0,official.n_obs,256):have95+=np.asarray((official.X[lo:lo+256]>0).sum(0)).ravel().astype(int)
 official.file.close();statsout['official95_positive_count']=have95;statsout['in_all_external']=haveall
 early=[x for x in allsamples if 'E8_5' in x];late=[x for x in allsamples if 'E14_5' in x];assert len(early)==len(late)==2
 globallyzero=np.asarray((par.X>0).sum(0)).ravel()==0
 rows=[];anyeligible=np.zeros(len(genes),bool);early_n={}
 for g in ['CM_V','CM_A','ENDO','EPI','MESO','NCC','SHF']:
  carrierzero=np.asarray((par.X[groups==g]>0).sum(0)).ravel()==0
  measured=haveall & carrierzero
  min_n=min(int(statsout[f'{s}|{g}|n']) for s in allsamples)
  latecnt=np.minimum(*[statsout[f'{s}|{g}|positive_count'] for s in late]);latedet=np.minimum(*[statsout[f'{s}|{g}|det'] for s in late]);earlydet=np.maximum(*[statsout[f'{s}|{g}|det'] for s in early])
  support=haveall&(latecnt>=8)&(latedet>=.1)&(earlydet<=.01)&(have95>=20)&(min_n>=20)
  eligible=carrierzero&support;anyeligible|=eligible
  statsout[f'onset|{g}|eligible']=eligible
  rows.append({'group':g,'recipient_rows':int((groups==g).sum()),'min_cells_per_external_library':min_n,'carrier_zero_genes':int(carrierzero.sum()),'carrier_zero_and_external_measured':int(measured.sum()),'replicate_supported_onset_gene_count':int(eligible.sum()),'globally_zero_onsets':int((eligible&globallyzero).sum()),'genes':genes[eligible].tolist(),'reason_if_empty':'frozen eligibility: >=20 group cells in each library, >=8 late detections in each library, late detection>=0.10, early detection<=0.01, observed official E9.5 in >=20 cells; all four external panels measured'})
 np.savez_compressed(out/'REPLICATE_STATS.npz',**statsout)
 result={'status':'SOURCE_ELIGIBILITY_ONLY_NO_CANDIDATE','global_parent_zero_genes':int(globallyzero.sum()),'external_measured_all_libraries':int(haveall.sum()),'external_missing':int((~haveall).sum()),'parent_zero_external_missing_overlap':int((globallyzero&~haveall).sum()),'parent_zero_external_measured':int((globallyzero&haveall).sum()),'unique_eligible_onset_genes':int(anyeligible.sum()),'replicate_group_cell_counts':cellcounts,'eligibility':rows,'frozen_criteria_not_retuned':True,'important_limitation':'Only two libraries per stage, source E8.5_1 truncated at public source, coarse labels inherited from official-source trained mapping; no genuine future-stage validation'}
 (out/'ONSET_ELIGIBILITY.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()

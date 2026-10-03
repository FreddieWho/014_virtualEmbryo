"""Fixed server-informed half step; diagnostic results never choose its strength."""
import csv
import json
from pathlib import Path
import shutil
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from t3_sparse_response.evaluate import load, fit_log_multiplier, emit, measure, dump, sha, KEYS

OUT=ROOT/'reports/t3_halfstep_20261003'
RUN=ROOT/'artifacts/t3_halfstep_20261003'

def main():
    assert not (OUT/'SELECTION.json').exists()
    selection={'method':'s050','strength':0.5,'basis':'one predeclared half step after v0071 server return; not local winner',
               'selected_before_test':True,'target_truth_used':False,'design_sha256':sha(OUT/'DESIGN.md')}
    dump(OUT/'SELECTION.json',selection)
    x,labels,ctrl,cfg,predict=load()
    rows=[]
    for g in cfg['split']['test']:
        beta=fit_log_multiplier(ctrl,predict(cfg['split']['train'],g))
        pred=emit(ctrl,beta,.5)
        assert np.array_equal(pred>0,ctrl>0)
        rows.append({'split':'historical_test','gene':g,'method':'s050',**measure(pred,x[labels==g],ctrl)})
        print('historical_test',g,flush=True)
    with (OUT/'FULL_MATRIX_METRICS.tsv').open('w') as f:
        w=csv.DictWriter(f,list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
    summary={}
    for k in KEYS+['mean_response_mse','density']:
        vals=[r[k] for r in rows if r[k] is not None]
        summary[k]={'mean':float(np.mean(vals)) if vals else None,'n':len(vals)}
    dump(OUT/'SUMMARY.json',summary)
    old=ROOT/'artifacts/t3_sparse_response_20261003/LOG_MULTIPLIER.npy'
    old_result=json.loads((ROOT/'reports/t3_sparse_response_20261003/EVALUATION_COMPLETE.json').read_text())
    assert sha(old)==old_result['multiplier_sha256']
    shutil.copyfile(old,RUN/'LOG_MULTIPLIER.npy')
    dump(OUT/'EVALUATION_COMPLETE.json',{'selection':selection,'multiplier_sha256':sha(RUN/'LOG_MULTIPLIER.npy'),
        'metrics_sha256':sha(OUT/'FULL_MATRIX_METRICS.tsv'),'status':'COMPLETE'})
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()

"""Collect completed full-run metrics and model diagnostics without refitting."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
import argparse,json,pickle
from pathlib import Path
import numpy as np
from .common import dump


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    result={}
    for lane in ['n1stack','n2composition','n3states','o1caldensity','o2shrinkmass']:
        r=args.root/lane;x=json.loads((r/'RESULT.json').read_text());assert x['report_scorer']=='EXECUTED'
        row={'result':x,'engineering':json.loads((r/'CHECKS.json').read_text()),'models':{}}
        for scope in ['report','final']:
            with (r/f'{scope}_model.pkl').open('rb') as f:m=pickle.load(f)
            op=json.loads((r/('REPORT_OPERATOR.json' if scope=='report' else 'FINAL_OPERATOR.json')).read_text())
            d={'rows':len(op['donor_indices']),'unique_row_indices':len(set(op['donor_indices']))}
            if lane=='n2composition':
                d.update(steps=m['steps'],training_labels=m['labels'],counts_early=m['counts_early'],counts_late=m['counts_late'],predicted_counts=op['predicted_counts'],recipient_counts=op['recipient_counts'])
                d['unique_effective_source_rows']=len(set(np.asarray(op['density_donors'])[op['donor_indices']].tolist()))
            elif lane=='n3states':
                d['groups']={t:{'states':len(g['step']),'early_counts':g['early_counts'],'late_counts':g['late_counts'],'log_weights':g['step']} for t,g in m['groups'].items()}
            elif lane=='o1caldensity':
                d['groups']={t:{**g['internal_diagnostic'],'final_slope':float(g['calibrator'].coef_[0,0])} for t,g in m['groups'].items()}
            elif lane=='o2shrinkmass':
                d['type_gene_models']=sum(len(g) for g in m['mass']['groups'].values())
                d['identity_models']=sum(int(g.get('identity',False)) for group in m['mass']['groups'].values() for g in group.values())
            row['models'][scope]=d
        result[lane]=row
    dump(args.out,{'routes':result,'scope':'read-only frozen fit diagnostics; no candidate changes or parameter selection','future_validation':'NOT_RUN_NO_E105_TRUTH'})


if __name__=='__main__':main()

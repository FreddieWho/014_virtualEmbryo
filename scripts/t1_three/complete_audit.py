"""Verify all three implemented routes and the actual upload package."""
import json,csv,zipfile,hashlib
from pathlib import Path
from .common import sha,dump


def main():
    root=Path('artifacts/t1_three/T1-THREE-20260929-v1');report=Path('reports/t1_three_20260929');checks={}
    def read(p):return json.loads(Path(p).read_text())
    def check(k,v):
        assert v,k
        checks[k]='PASS'
    v=read(report/'VALIDATION.json');lanes=['r1compose','r2joint','r3mix']
    check('three_designed_and_executed_routes',v['routes_executed']==3 and [r['lane'] for r in v['routes']]==lanes and read(root/'COMPLETE.json')['status']=='ALL_THREE_EXECUTED')
    ready=read(root/'shared/READY.json');check('two_scored_components_both_scenarios',len(ready['components_exact'])==4 and all(x['exact'] for x in ready['components_exact']))
    index=list(csv.DictReader(open('submissions/INDEX.tsv'),delimiter='\t'))
    candidates=[]
    for r in v['routes']:
        run=root/r['lane'];result=read(run/'RESULT.json');c=result['candidates'][0];candidates.append(c)
        check(r['lane']+'_full_model_operator_contract',r['full_model_replay']==r['whole_row_operator_identity']==r['contract']=='PASS' and r['shape']==[5118,32285])
        check(r['lane']+'_full_panel_official_scorer',result['report_scorer']=='EXECUTED' and read(run/'SCORER.json')['meta']['genes']==32285 and read(run/'SCORER_PROCESS.json')['exit_code']==0)
        check(r['lane']+'_one_ready_candidate',result['status']=='CANDIDATES_READY' and len(result['candidates'])==1 and result['wall_s']<6*3600)
        rows=[row for row in index if row['board']=='T1:val' and row['version']==c['version']]
        check(r['lane']+'_authority',len(rows)==1 and rows[0]['sha256']==c['sha256'] and rows[0]['score_status']=='score_pending')
        check(r['lane']+'_audit_tracking',f"{c['version']}/three_{r['lane']}" in Path('AUDIT.md').read_text() and 'T1-THREE-'+r['lane'] in Path('reports/LANE_VERDICTS.tsv').read_text())
    a=read(root/'r1compose/FINAL_OPERATOR.json');b=read(root/'r2joint/FINAL_OPERATOR.json');mix=read(root/'r3mix/FINAL_OPERATOR.json')
    check('joint_equal_type_allocation',a['predicted_types']==b['predicted_types'] and a['predicted_counts']==b['predicted_counts'])
    check('mixture_exact_equal_parent_quota',mix['parent_A_count']==mix['parent_B_count']==2559)
    receipt=read('deliveries/t1three__t1__upload__20260929.receipt.json')
    check('package_three_h5ad_current_hash',receipt['members']==3 and sha(receipt['path'])==receipt['sha256'])
    with zipfile.ZipFile(receipt['path']) as z:
        check('four_manifests',set(['MANIFEST.tsv','UPLOAD_MANIFEST.tsv','RUN_ID_MAP.tsv','EVIDENCE_MANIFEST_POINTERS.tsv'])<=set(z.namelist()))
        for c in candidates:
            name=c['portal_file'];check(name+'_actual_bytes',len(name)<=50 and name==name.lower() and hashlib.sha256(z.read(name)).hexdigest()==c['sha256'])
    check('targeted_tests',read(report/'TESTS.json')['status']=='PASS')
    D='D-20260929-T1THREE-001';check('paired_decisions',all(D in Path(p).read_text() for p in ['DECISIONS.md','docs/coordination/DECISIONS.md']))
    check('report_delivered',(report/'REPORT.md').exists())
    dump(report/'COMPLETION_AUDIT.json',{'status':'PASS','checks':checks,'unrun':{'future_truth':'NOT_RUN_NO_E105_E125_TRUTH','portal_upload_and_new_server_scores':'NOT_RUN','new_base_model_training':'NOT_RUN_FROZEN_SCORED_COMPONENTS_REUSED_BY_DESIGN'},'scientific_status':'EXPLORATORY_LOCAL','blocks_submission':False,'external_data_added':False})
    print('COMPLETION AUDIT PASS',len(checks))


if __name__=='__main__':main()

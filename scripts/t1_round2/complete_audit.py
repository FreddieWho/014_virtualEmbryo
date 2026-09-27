"""Itemized user-objective completion audit against actual delivery receipts."""
import json,zipfile
from pathlib import Path
from .common import sha,dump


def main():
    root=Path('artifacts/t1_round2/T1-ROUND2-20260928-v1');report=Path('reports/t1_round2_20260928');checks={}
    def read(p):return json.loads(p.read_text())
    def check(name,condition):
        assert condition,name
        checks[name]='PASS'
    v=read(report/'VALIDATION.json');lanes=['n1stack','n2composition','n3states','o1caldensity','o2shrinkmass']
    check('three_new_two_existing_optimizations',v['new_routes']==3 and v['existing_optimizations']==2 and [r['lane'] for r in v['routes']]==lanes)
    check('five_complete_actual_executions',read(root/'COMPLETE.json')['status']=='ALL_FIVE_EXECUTED')
    check('high_scoring_components_exact_in_both_scenarios',len(read(root/'shared/READY.json')['components_exact'])==4 and all(x['exact'] for x in read(root/'shared/READY.json')['components_exact']))
    for r in v['routes']:
        run=root/r['lane'];x=read(run/'RESULT.json');scorer=read(run/'SCORER.json')
        check(r['lane']+'_full_fit_replay_contract',r['full_model_replay']==r['contract']=='PASS' and r['shape']==[5118,32285] and bool(r['fitted_parameter_audit']))
        check(r['lane']+'_real_full_panel_scorer',x['report_scorer']=='EXECUTED' and scorer['meta']['genes']==32285 and read(run/'SCORER_PROCESS.json')['exit_code']==0)
        check(r['lane']+'_bounded_run',x['wall_s']<6*3600 and len(x['candidates'])==1)
        check(r['lane']+'_registered_in_audit',f"{r['version']}/round2_{r['lane']}" in Path('AUDIT.md').read_text())
    p=read(Path('deliveries/t1r2__t1__upload__20260928.receipt.json'))
    check('five_candidate_package_current_hash',p['members']==5 and p['sha256']==sha(p['path']))
    with zipfile.ZipFile(p['path']) as z:
        names=z.namelist();check('package_naming_and_manifests',len([n for n in names if n.endswith('.h5ad')])==5 and all(n==n.lower() and len(n)<=50 for n in names if n.endswith('.h5ad')) and set(['MANIFEST.tsv','UPLOAD_MANIFEST.tsv','RUN_ID_MAP.tsv','EVIDENCE_MANIFEST_POINTERS.tsv'])<=set(names))
    check('targeted_tests',read(report/'TESTS.json')['status']=='PASS')
    decision='D-20260928-T1R2-001'
    check('paired_decision_indices',all(decision in Path(p).read_text() for p in ['DECISIONS.md','docs/coordination/DECISIONS.md']))
    check('five_lane_verdicts',all('T1-ROUND2-'+l in Path('reports/LANE_VERDICTS.tsv').read_text() for l in lanes))
    check('final_report_and_model_diagnostics',(report/'REPORT.md').exists() and len(read(report/'MODEL_DIAGNOSTICS.json')['routes'])==5)
    check('current_best_not_promoted','current_best_score: 51.92' in Path('docs/coordination/STATUS.md').read_text())
    dump(report/'COMPLETION_AUDIT.json',{'status':'PASS','checks':checks,'scope':'full objective completed: 3 new routes, 2 optimizations, actual high-score composition, full runs, validated delivery','unrun':{'future_E105_E125_truth':'NOT_RUN_NO_TRUTH','server_upload_and_scores':'NOT_RUN','independent_embryo_validation':'NOT_AVAILABLE_NO_EMBRYO_IDS','causal_validation':'NOT_RUN'},'blocks_submission':False,'external_data_added':False})
    print('COMPLETION AUDIT PASS',len(checks))


if __name__=='__main__':main()

"""Invoke the repository's real parent-bound validator against restored board bytes."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'docs/batch3/interfaces'))
from virtual_embryo_tools.contract_io import validate_h5ad_contract
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--parent',required=True);p.add_argument('--parent-sha256',required=True);p.add_argument('--scorer-lock',required=True);p.add_argument('--report',required=True);a=p.parse_args()
r=validate_h5ad_contract(Path(a.candidate),task='T1',board='val',scorer_lock=Path(a.scorer_lock),parent_path=Path(a.parent),parent_sha256=a.parent_sha256)
Path(a.report).write_text(json.dumps(r,indent=2));print(json.dumps({'status':r['status'],'valid':r['valid'],'errors':r['errors']},indent=2));assert r['valid']

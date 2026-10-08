"""Run the frozen source evaluator with only two local path substitutions.
Use an extracted copy: this reruns source_evaluation outputs in that copy.
"""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent
manifest=json.loads((P/'PACK_FILE_HASHES.json').read_text())
required=['evaluate_source.py','crossko.py','crossko_hurdle_v2.py','emitter_v88.py','public_core/common/core_metrics.py','inference/state_emitter.joblib']+[str(p.relative_to(P)) for p in (P/'source_panel/normalized').glob('*.h5ad')]
for name in required:assert hashlib.sha256((P/name).read_bytes()).hexdigest()==manifest[name],('Pack input hash mismatch',name)
path=P/'evaluate_source.py';code=path.read_text();old1="R=Path('/workspace/shared/t3_v87_restored')";old2="'/workspace/shared/t3repo/third_party/veckit'"
assert code.count(old1)==1 and code.count(old2)==1
code=code.replace(old1,'R=P').replace(old2,repr(str(P/'public_core')))
(P/'LOCAL_PATH_REBINDING.json').write_text(json.dumps({'scope':'Only source-root/model and scorer import paths rebound to extracted pack; model parameters and frozen evaluator file unchanged','original_code_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'executed_code_sha256':hashlib.sha256(code.encode()).hexdigest()},indent=2))
sys.path.insert(0,str(P));exec(compile(code,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})

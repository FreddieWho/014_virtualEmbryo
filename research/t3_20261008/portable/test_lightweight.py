"""Run archived synthetic tests in disposable copies; never modify scored/source trees."""
import tempfile,shutil,subprocess,sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for row in json.loads((R/'SNAPSHOT_INVENTORY.json').read_text()):
 assert hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
with tempfile.TemporaryDirectory(prefix='t3-public-test-') as tmp:
 d=Path(tmp);v=d/'v87';w=d/'v88';audit=d/'audit'
 shutil.copytree(R/'snapshots/v0087',v);shutil.copytree(R/'snapshots/v0088',w);audit.mkdir()
 for script in ['test_crossko.py','test_crossko_hurdle.py','test_crossko_hurdle_v2.py']:
  subprocess.run([sys.executable,str(v/script)],check=True,cwd=d)
 # Explicit path-only adaptation in temporary working file; original remains immutable.
 source=(R/'snapshots/v0088_audit/check_emitter.py').read_text()
 source=source.replace('/workspace/shared/t3_v87_restored',str(v)).replace('/workspace/shared/t3_v88_optimization_20261008',str(w)).replace('/workspace/shared/t3_v88_independent_audit',str(audit))
 script=d/'check_emitter_portable.py';script.write_text(source)
 subprocess.run([sys.executable,str(script)],check=True,cwd=d)
print('PASS: snapshot integrity, three historical synthetic suites, four-arm emitter controls; no source or scored artifact mutation')

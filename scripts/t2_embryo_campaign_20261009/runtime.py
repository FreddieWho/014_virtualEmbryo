"""Load unchanged recipe helpers in a consumer-local data workspace.
Only the VE constant is rebound; original source hash and override are reported.
"""
from pathlib import Path
import hashlib, sys, types
REPO=Path(__file__).resolve().parents[2]

def initialize(data):
    data=Path(data).resolve()
    source=REPO/'scripts/vework/vecommon.py'
    code=source.read_text()
    needle='VE = Path("/workspace/ve")\nDATA = VE / "data"'
    assert code.count(needle)==1
    code=code.replace(needle, f'VE = Path({str(data.parent)!r})\nDATA = Path({str(data)!r})')
    module=types.ModuleType('vecommon');module.__file__=str(source)
    sys.modules['vecommon']=module
    exec(compile(code,str(source),'exec'),module.__dict__)
    sys.path.insert(0,str(REPO/'scripts/vework'))
    sys.path.insert(0,str(REPO/'third_party/veckit'))
    return module, {'source':str(source.relative_to(REPO)), 'sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'override':{'DATA':str(data)}}

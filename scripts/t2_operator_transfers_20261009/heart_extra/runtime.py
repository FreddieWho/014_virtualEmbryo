"""Consumer-local binding for the unchanged historical recipe; thread budget one."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS','LOKY_MAX_CPU_COUNT'):
    os.environ[key]='1'
from pathlib import Path
import hashlib,sys,types
ROOT=Path(__file__).resolve().parent

def initialize(data):
    data=Path(data).resolve()
    source=ROOT/'vecommon.py';code=source.read_text()
    needle='VE = Path("/workspace/ve")\nDATA = VE / "data"'
    assert code.count(needle)==1
    code=code.replace(needle,f'VE = Path({str(data.parent)!r})\nDATA = Path({str(data)!r})')
    module=types.ModuleType('vecommon');module.__file__=str(source)
    sys.modules['vecommon']=module
    exec(compile(code,str(source),'exec'),module.__dict__)
    sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'veckit'))
    return module

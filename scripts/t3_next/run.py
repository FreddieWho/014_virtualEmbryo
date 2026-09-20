"""Run one locked route. Example: python -m scripts.t3_next.run r1 --run-dir ..."""
from __future__ import annotations
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import argparse,json,signal,sys,time,traceback
from pathlib import Path
from .common import Context,dump,ROOT
from . import routes_local,routes_extended


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('route',choices=['r1','r2','r3','r4','r5','r6']);ap.add_argument('--run-dir',type=Path,required=True);ap.add_argument('--source-manifest',type=Path)
    args=ap.parse_args();ctx=None
    if args.run_dir.exists():raise FileExistsError('immutable run directory already exists; use a new run id')
    cfg=json.loads((ROOT/'configs/t3_next/design.json').read_text())
    def timeout(*_):raise TimeoutError('predeclared route wall limit reached')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(int(cfg['wall_hours'][args.route]*3600))
    try:
        ctx=Context(args.run_dir)
        if args.route in ['r1','r2','r3']:getattr(routes_local,args.route)(ctx)
        else:getattr(routes_extended,args.route)(ctx,**({'manifest':args.source_manifest} if args.route in ['r5','r6'] else {}))
    except Exception as exc:
        args.run_dir.mkdir(parents=True,exist_ok=True)
        dump(args.run_dir/'FAILURE.json',{'status':'BLOCKED_WALLTIME' if isinstance(exc,TimeoutError) else 'FAILED_EXECUTION','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'partial_candidates':ctx.candidates if ctx else [],'no_full_success_claim':True})
        traceback.print_exc();return 1
    finally:signal.alarm(0)
    return 0

if __name__=='__main__':raise SystemExit(main())

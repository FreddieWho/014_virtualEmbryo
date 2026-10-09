#!/usr/bin/env python3
"""Relocate the unchanged frozen runner without editing scientific source files."""
from pathlib import Path
import argparse, sys, types

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous-root',type=Path,required=True,help='Prior campaign directory containing heart_interp/')
    p.add_argument('--data-root',type=Path,help='Released .h5ad, index.json and panel directory; defaults to previous-root/data/official')
    p.add_argument('--mode',choices=['dev','final','replay'],required=True)
    p.add_argument('--out',type=Path,required=True,help='New output directory; must not exist')
    p.add_argument('--choice',choices=['global_b075','global_b100','within_state_b050'])
    a=p.parse_args()
    if a.mode!='dev' and not a.choice: p.error('--choice is required for final/replay')
    root=Path(__file__).resolve().parent
    previous=a.previous_root.resolve();data=(a.data_root or previous/'data/official').resolve()
    source=root/'run.py';code=source.read_text()
    old="OLD=Path('/workspace/shared/t2_operator_transfers_20261009');DATA=OLD/'data/official'"
    assert code.count(old)==1, 'Frozen source differs from expected relocation anchor'
    code=code.replace(old,f'OLD=Path({str(previous)!r});DATA=Path({str(data)!r})')
    sys.argv=[str(source),'--mode',a.mode,'--out',str(a.out.resolve())]
    if a.choice:sys.argv += ['--choice',a.choice]
    module=types.ModuleType('__main__');module.__file__=str(source)
    exec(compile(code,str(source),'exec'),module.__dict__)

if __name__=='__main__': main()

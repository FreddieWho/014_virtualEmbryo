"""Portable launcher for historical experiments, not an automatic new experiment.
Path substitutions happen only in memory. Original frozen files stay unchanged.
"""
import argparse,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name,inputs,work,repo):
 path=HERE/'frozen'/f'{name}.py';source=path.read_text()
 source=source.replace('/workspace/shared/t3repo',str(repo))
 if name=='evaluate':source=source.replace("(ROOT/'flow.py').read_bytes()",f"Path({str(HERE/'frozen/flow.py')!r}).read_bytes()")
 source=source.replace('/workspace/shared/virtual_embryo_data',str(inputs))
 source=source.replace('/workspace/shared/t2_external_sources_20261008/go_topology/panel_gene_go_interpro.json',str(repo/'infra/bioinf-data-index/t2_heart_extra_20261008/go_topology/panel_gene_go_interpro.json'))
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(source,str(path),'exec'),m.__dict__)
 if name=='flow':m.ROOT=work;m.PANEL=HERE/'T2__heart__val_extrap.genes.txt'
 if hasattr(m,'R'):m.R=work
 if name=='evaluate':m.ROOT=work
 return m

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True,type=Path);p.add_argument('--work',required=True,type=Path);p.add_argument('--module',required=True,choices=['flow','graph_velocity','endpoint_flow','endpoint_residual','evaluate']);p.add_argument('--action',required=True,help='dev/final for builders; split or lane for evaluator');p.add_argument('--endpoint',type=Path);p.add_argument('--partition',choices=['dev','reserve'],default='dev');p.add_argument('--repo',type=Path,default=HERE.parents[1]);a=p.parse_args()
 a.inputs=a.inputs.resolve();a.work=a.work.resolve();a.repo=a.repo.resolve();a.work.mkdir(parents=True,exist_ok=True)
 load('flow',a.inputs,a.work,a.repo)
 if a.module in ['endpoint_flow','endpoint_residual']:load('endpoint_flow',a.inputs,a.work,a.repo)
 m=sys.modules.get(a.module) or load(a.module,a.inputs,a.work,a.repo)
 if a.module=='evaluate':m.split() if a.action=='split' else m.score(a.action,a.partition)
 elif a.module=='endpoint_flow':
  assert a.endpoint is not None,'--endpoint required';m.build(a.action,a.endpoint)
 else:m.build(a.action)
if __name__=='__main__':main()

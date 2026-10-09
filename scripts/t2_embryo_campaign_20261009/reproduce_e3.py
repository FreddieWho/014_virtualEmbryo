"""Byte-exact reproduction of scored E3, NOT the original v0014.
Expected digest comes from reports/t1_late_anchor_20261008/MANIFEST.tsv.
"""
import argparse
from pathlib import Path
from types import SimpleNamespace as NS
from runtime import initialize

def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 v,_=initialize(a.data);import t2_recipes as r
 dest=Path(a.out)
 if dest.exists():raise FileExistsError(dest)
 args=NS(board='T2:embryo:val_interp',left='E7.25:7.25',right='E8.0:8.0',prev='E6.75:6.75',target=7.5,n=5000,seed=20261008,label='celltype',carrier='baseline',base_n=5000,base_seed=20260821,bridge_seed=20260904,C=2.,geometry='logrms',zero_preserve=False)
 out,_=r.run_interp(args);dest.parent.mkdir(parents=True,exist_ok=True);out.write_h5ad(dest)
 got=v.sha256(dest);assert got=='e93d56f2130297f7c5b256e3e26fc072b8913766772b3ffcb2634f7a3fdbfdae',got
 print('BYTE_EXACT_E3_PASS',got)
if __name__=='__main__':main()

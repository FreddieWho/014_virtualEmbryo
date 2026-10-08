"""Portable extraction adapter: replace only original path literals in memory.
The frozen source bytes and extraction rules remain independently inspectable.
"""
import argparse,json,sys
from pathlib import Path
from portable import sha,HERE

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
 index=HERE.parents[1]/'infra/bioinf-data-index/t2_heart_extra_20261008'
 receipt=json.loads((index/'E145_FETCH_RECEIPT.json').read_text())
 assert a.source.stat().st_size==receipt['bytes'] and sha(a.source)==receipt['sha256'],'Original E14.5 identity mismatch'
 a.out.mkdir(parents=True,exist_ok=True)
 # The extraction reads its receipt and creates endpoint files under r/e145_endpoint.
 (a.out/'E145_FETCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2))
 source=(HERE/'frozen/source_extraction/extract_e145.py').read_text()
 source=source.replace("r=Path('/workspace/shared/t2_external_sources_20261008')",f'r=Path({str(a.out.resolve())!r})')
 source=source.replace("p=r/'quarantine/E14.5_E1S3.MOSTA.h5ad'",f'p=Path({str(a.source.resolve())!r})')
 source=source.replace("Path('/workspace/shared/virtual_embryo_data/T2__heart__val_extrap.genes.txt')",f'Path({str(HERE/"T2__heart__val_extrap.genes.txt")!r})')
 exec(compile(source,str(HERE/'frozen/source_extraction/extract_e145.py'),'exec'),{'__name__':'__main__'})
 permit=json.loads((index/'endpoint/T2_DATA_PERMIT.json').read_text())
 permit['publication_rebuild_note']='Portable rebuild; original artifact hashes remain in repository permit. This permit binds freshly emitted files; H5AD bytes may differ by library version.'
 for item in permit['model_artifacts']:
  path=a.out/'e145_endpoint'/Path(item['path']).name;item['path']=path.name;item['sha256']=sha(path);item['bytes']=path.stat().st_size
 (a.out/'e145_endpoint/T2_DATA_PERMIT.json').write_text(json.dumps(permit,indent=2)+'\n')
if __name__=='__main__':main()

from pathlib import Path
import json,hashlib
root=Path('/workspace/shared/t3_developmental_sources');m=json.loads((root/'RESTORE_MANIFEST_1141.json').read_text());out=[]
for r in m['records']:
 p=Path(r['file']);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 assert h.hexdigest()==r['sha256'] and p.stat().st_size==r['bytes'],p
 out.append({'file':str(p),'sha256':h.hexdigest(),'bytes':p.stat().st_size})
 print('verified',p.name,flush=True)
# Original archived manifests, rather than restoration's own claims, bind actual source hashes.
old=Path('/workspace/shared/t3_v87_restored/external_sources')
texts='\n'.join(p.read_text() for p in old.glob('*.json'))
for r in out: assert r['sha256'] in texts,r['file']
result={'status':'PASS','source_files':len(out),'total_bytes':sum(r['bytes'] for r in out),'all_hashes_bound_in_immutable_original_manifests':True,'records':out}
Path('/workspace/shared/t3_v88_independent_audit/RESTORED_SOURCE_HASH_AUDIT.json').write_text(json.dumps(result,indent=2))
print('PASS',len(out),flush=True)

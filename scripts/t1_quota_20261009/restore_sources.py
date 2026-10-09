"""Restore only previously admitted E8.5/E14.5 samples, with frozen hashes."""
import argparse,concurrent.futures,hashlib,json,urllib.request,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--out',required=True);a=p.parse_args()
root=Path(a.out);root.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.archive) as z: manifest=json.loads(z.read('code/SOURCE_RECOVERY.json'))
records=[s for s in manifest['sources'] if any(x in s['name'] for x in ('E8_5','E14_5'))]
assert len(records)==8

def run(s):
 out=root/s['name']
 if not out.exists():
  req=urllib.request.Request(s['url'],headers={'User-Agent':'VirtualEmbryo-reproducibility/1.0'})
  with urllib.request.urlopen(req,timeout=120) as r,out.open('wb') as f:
   while b:=r.read(1<<20): f.write(b)
 h=hashlib.sha256(out.read_bytes()).hexdigest()
 assert h==s['sha256'],(out,h)
 result={**s,'verified_sha256':h,'path':str(out)}
 print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(run,records))
(root/'RESTORED.json').write_text(json.dumps(results,indent=2))

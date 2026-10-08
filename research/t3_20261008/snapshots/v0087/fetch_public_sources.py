"""Fetch only hash-bound public GEO inputs. Does not obtain challenge-heldout data.
python fetch_public_sources.py --destination /workspace/shared
Default dry-run; add --download for authorized acquisition. Existing matches are reused.
"""
import argparse,json,hashlib,urllib.request
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--destination',type=Path,required=True);ap.add_argument('--download',action='store_true');args=ap.parse_args();root=Path(__file__).parent;records={}
for name in ['TASK_DATA_PERMIT.json','TASK_DATA_PERMIT_v2.json']:
 permit=json.loads((root/'external_sources'/name).read_text())
 for r in permit['files']:
  if r.get('source_url') and r.get('sha256'):records[r['file']]=r
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
for original,r in records.items():
 url=r['source_url']
 if not url.startswith('https://ftp.ncbi.nlm.nih.gov/geo/'):
  print('METADATA_SEPARATE',url);continue
 rel=Path(original).relative_to('/workspace/shared');out=args.destination/rel
 if out.exists():assert digest(out)==r['sha256'],('Existing hash mismatch',out);print('VERIFIED',out);continue
 print('DOWNLOAD' if args.download else 'PLAN',url,'->',out)
 if not args.download:continue
 out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_name(out.name+'.part')
 with urllib.request.urlopen(url) as response,tmp.open('wb') as f:
  while True:
   b=response.read(1024*1024)
   if not b:break
   f.write(b)
 assert digest(tmp)==r['sha256'],('Downloaded hash mismatch',tmp);tmp.replace(out)
print('Public-source plan complete. Official released WT/Mab inputs require the challenge Download controls; see README_REPRODUCTION.md.')

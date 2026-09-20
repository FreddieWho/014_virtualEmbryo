"""Hash-bound metadata/resource acquisition only; never grants a model permit."""
import argparse, concurrent.futures, hashlib, json
from pathlib import Path
import requests

def fetch(item, root):
    dest = root / item['name']
    if dest.exists():
        data = dest.read_bytes()
        return dict(item, path=str(dest), status='CACHED', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), model_input=False)
    try:
        with requests.get(item['url'], timeout=(15, 90), stream=True) as r:
            r.raise_for_status()
            data = bytearray()
            for chunk in r.iter_content(1024*1024):
                data.extend(chunk)
                if len(data) > item.get('max_bytes', 20_000_000):
                    raise ValueError('metadata-first size cap exceeded')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dict(item, path=str(dest), status='DOWNLOADED_QUARANTINE', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), model_input=False)
    except Exception as e:
        return dict(item, status='FETCH_FAILED', error=type(e).__name__+': '+str(e), model_input=False)

if __name__ == '__main__':
    a=argparse.ArgumentParser();a.add_argument('plan');a.add_argument('--root', required=True);a.add_argument('--receipt',required=True);args=a.parse_args()
    root=Path(args.root);root.mkdir(parents=True,exist_ok=True)
    items=json.loads(Path(args.plan).read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda item:fetch(item,root),items))
    Path(args.receipt).write_text(json.dumps({'date':'2026-09-20','purpose':'quarantine metadata and input audit only','model_input':False,'files':results},indent=2)+'\n')
    for r in results:print(r['name'],r['status'],r.get('bytes',0))

"""Package only current registered, contract-valid unsubmitted candidates."""
from __future__ import annotations
import argparse,csv,io,json,zipfile
from pathlib import Path
from .common import ROOT,sha,dump


def tsv(rows,fields):
    out=io.StringIO();w=csv.DictWriter(out,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows);return out.getvalue()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run-dirs',nargs='+',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise FileExistsError('immutable delivery already exists')
    with (ROOT/'submissions/INDEX.tsv').open() as f:idx={r['path']:r for r in csv.DictReader(f,delimiter='\t')}
    members=[];mapping=[];runs=[];evidence=[]
    for run in a.run_dirs:
        result=json.loads((run/'RESULT.json').read_text())
        for c in result.get('candidates',[]):
            row=idx[c['path']]
            if row['score_status']!='score_pending' or row['local_contract']!='pass':raise ValueError('ineligible/withdrawn candidate '+c['path'])
            path=ROOT/c['path'];name=c['portal_file']
            if len(name)>50 or name!=name.lower():raise ValueError('portal name contract')
            if sha(path)!=row['sha256']:raise ValueError('candidate drift')
            members.append({'filename':name,'bytes':path.stat().st_size,'sha256':row['sha256']})
            mapping.append({'filename':name,'board':row['board'],'version':row['version'],'canonical_path':row['path']})
            runs.append({'filename':name,'run_id':str(run),'parent_version':c['parent'],'candidate_version':c['version']})
            evidence.append({'filename':name,'input_lock':str(run/'INPUT_LOCK.json'),'contract':str(run/f"{c['lane']}_CONTRACT.json"),'result':str(run/'RESULT.json')})
    if not members:raise ValueError('no candidates')
    if len({m['filename'] for m in members})!=len(members):raise ValueError('duplicate member')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for m in mapping:z.write(ROOT/m['canonical_path'],m['filename'])
        for name,rows in [('MANIFEST.tsv',members),('UPLOAD_MANIFEST.tsv',mapping),('RUN_ID_MAP.tsv',runs),('EVIDENCE_MANIFEST_POINTERS.tsv',evidence)]:z.writestr(name,tsv(rows,list(rows[0])))
    with zipfile.ZipFile(a.output) as z:
        for m in members:
            import hashlib
            if hashlib.sha256(z.read(m['filename'])).hexdigest()!=m['sha256']:raise ValueError('package hash mismatch')
        if z.testzip() is not None:raise ValueError('zip CRC failure')
    dump(a.output.with_suffix('.receipt.json'),{'status':'READY_NOT_SUBMITTED','zip_path':str(a.output),'zip_sha256':sha(a.output),'members':len(members),'portal_upload':'NOT_RUN','server_scores':'NOT_RUN','run_dirs':[str(p) for p in a.run_dirs]})
    print(json.dumps({'package':str(a.output),'candidates':len(members),'status':'READY_NOT_SUBMITTED'}))

if __name__=='__main__':main()

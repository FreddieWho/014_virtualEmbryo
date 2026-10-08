"""Two bounded subprocess workers; durable completion/failure receipts per route."""
import os,json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'artifacts/t1_six/T1-SIX-20261007-v1'

def worker(lane):
    command=[sys.executable,'-m','scripts.t1_six.run',lane,'--run-dir',str(RUN/lane)]
    with (RUN/(lane+'.log')).open('x') as f:
        p=subprocess.Popen(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'LD_LIBRARY_PATH':'/opt/anaconda3/lib'})
        (RUN/(lane+'.process.json')).write_text(json.dumps({'pid':p.pid,'command':command,'status':'RUNNING'})+'\n')
        code=p.wait()
    receipt={'lane':lane,'pid':p.pid,'exit_code':code,'status':'COMPLETED' if code==0 else 'FAILED'}
    (RUN/(lane+'.process.json')).write_text(json.dumps(receipt)+'\n');print(json.dumps(receipt),flush=True);return receipt

def main():
    cfg=json.loads((ROOT/'configs/t1_six/design_20261007.json').read_text());assert (RUN/'shared/CACHE_LOCK.json').is_file()
    started=time.time();results=[]
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs=[executor.submit(worker,lane) for lane in cfg['six']['lanes']]
        for job in as_completed(jobs):
            results.append(job.result());(RUN/'BATCH_PROGRESS.json').write_text(json.dumps(results,indent=2)+'\n')
    result={'status':'COMPLETED' if all(r['exit_code']==0 for r in results) else 'FAILED','routes':results,'wall_s':time.time()-started}
    (RUN/'BATCH_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    if result['status']!='COMPLETED':sys.exit(1)
if __name__=='__main__':main()

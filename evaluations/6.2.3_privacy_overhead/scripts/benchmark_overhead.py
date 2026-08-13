#!/usr/bin/env python3
import argparse,csv,json,platform,statistics,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

def plaintext_once():
    # Same k=10 workload as the depth-2 zk input: two active, one expired, seven empty.
    q,t=[20,15,5]+[0]*7,[90,80,60]+[0]*7
    now,window,limit,current=100,30,60,10
    active=sum(x for x,y in zip(q,t) if y and 0 <= now-y < window)
    if active+current>limit:return False
    for i,y in enumerate(t):
        if y==0 or now-y>=window:q[i],t[i]=current,now;return True
    return False
def timed(cmd,cwd):
    t=time.perf_counter();p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True);dt=time.perf_counter()-t
    if p.returncode:raise RuntimeError(' '.join(cmd)+'\n'+p.stderr)
    return dt
def summary(rows,metric):
    v=[r[metric] for r in rows];return statistics.mean(v),statistics.stdev(v),statistics.median(v),min(v),max(v)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runs',type=int,default=30);ap.add_argument('--warmups',type=int,default=5);ap.add_argument('--baseline-iterations',type=int,default=100000);a=ap.parse_args()
    here=Path(__file__).resolve().parent.parent;root=here.parent.parent;zk=root/'evaluations'/'6.2.2_merkle_depth';b=zk/'build'/'d2';name='merkle_depth_d2';js=b/f'{name}_js';inp=zk/'inputs'/'d2_valid.json';wasm=js/f'{name}.wasm';gen=js/'generate_witness.js';zkey=b/f'{name}_final.zkey';vk=b/f'{name}_vk.json'
    missing=[str(x) for x in (inp,wasm,gen,zkey,vk) if not x.exists()]
    if missing:raise FileNotFoundError('Section 6.2.2 depth-2 build is required:\n'+'\n'.join(missing))
    res=here/'results';res.mkdir(exist_ok=True);(res/'environment.json').write_text(json.dumps({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'runs':a.runs,'warmups':a.warmups,'baseline_iterations':a.baseline_iterations,'zk_configuration':{'k':10,'depth':2}},indent=2)+'\n')
    rows=[]
    for i in range(1,a.warmups+a.runs+1):
        t=time.perf_counter()
        for _ in range(a.baseline_iterations):plaintext_once()
        base=(time.perf_counter()-t)/a.baseline_iterations
        out=res/'artifacts'/f'run_{i:02d}';out.mkdir(parents=True,exist_ok=True);w=out/'witness.wtns';proof=out/'proof.json';pub=out/'public.json'
        wit=timed(['node',str(gen),str(wasm),str(inp),str(w)],root);prove=timed(['snarkjs','groth16','prove',str(zkey),str(w),str(proof),str(pub)],root);verify=timed(['snarkjs','groth16','verify',str(vk),str(pub),str(proof)],root)
        if i>a.warmups:rows.append({'run':i-a.warmups,'plaintext_s':base,'witness_s':wit,'prove_s':prove,'verify_s':verify,'zk_prover_s':wit+prove,'zk_end_to_end_s':wit+prove+verify,'prover_overhead_factor':(wit+prove)/base,'end_to_end_overhead_factor':(wit+prove+verify)/base})
    with (res/'raw_measurements.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    metrics=('plaintext_s','witness_s','prove_s','verify_s','zk_prover_s','zk_end_to_end_s','prover_overhead_factor','end_to_end_overhead_factor');out=[]
    for m in metrics:mean,sd,median,lo,hi=summary(rows,m);out.append({'metric':m,'mean':mean,'stdev':sd,'median':median,'min':lo,'max':hi})
    with (res/'summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print('Wrote',res/'raw_measurements.csv');print('Wrote',res/'summary.csv')
if __name__=='__main__':main()

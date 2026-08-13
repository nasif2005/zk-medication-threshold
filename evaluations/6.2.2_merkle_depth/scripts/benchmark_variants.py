#!/usr/bin/env python3
import argparse,csv,json,platform,statistics,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
def timed(cmd,cwd):
 t=time.perf_counter();p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True);dt=time.perf_counter()-t
 if p.returncode: raise RuntimeError(' '.join(cmd)+'\n'+p.stdout+'\n'+p.stderr)
 return dt
def stat(v): return statistics.mean(v),statistics.stdev(v) if len(v)>1 else 0,statistics.median(v),min(v),max(v)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--runs',type=int,default=30);ap.add_argument('--warmups',type=int,default=5);a=ap.parse_args()
 here=Path(__file__).resolve().parent.parent;root=here.parent.parent;res=here/'results';res.mkdir(exist_ok=True)
 (res/'environment.json').write_text(json.dumps({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'runs':a.runs,'warmups':a.warmups},indent=2)+'\n')
 cfg=[]
 for d in (2,4,8,16):
  n=f'merkle_depth_d{d}';b=here/'build'/f'd{d}';js=b/f'{n}_js';items=(here/'inputs'/f'd{d}_valid.json',js/f'{n}.wasm',js/'generate_witness.js',b/f'{n}_final.zkey',b/f'{n}_vk.json')
  miss=[str(x) for x in items if not x.exists()]
  if miss: raise FileNotFoundError('Run build_variants.sh first. Missing:\n'+'\n'.join(miss))
  cfg.append((d,*items))
 rows=[]
 for d,inp,wasm,gen,zkey,vk in cfg:
  for i in range(1,a.warmups+a.runs+1):
   out=res/'artifacts'/f'd{d}'/f'run_{i:02d}';out.mkdir(parents=True,exist_ok=True);w=out/'witness.wtns';proof=out/'proof.json';pub=out/'public.json'
   wt=timed(['node',str(gen),str(wasm),str(inp),str(w)],root);pt=timed(['snarkjs','groth16','prove',str(zkey),str(w),str(proof),str(pub)],root);vt=timed(['snarkjs','groth16','verify',str(vk),str(pub),str(proof)],root)
   if i>a.warmups: rows.append({'experiment':'merkle_depth','k':10,'depth':d,'run':i-a.warmups,'witness_s':wt,'prove_s':pt,'verify_s':vt,'total_prover_s':wt+pt,'status':'success'})
 fields=list(rows[0]);
 with (res/'raw_measurements.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 summary=[]
 for d in (2,4,8,16):
  for m in ('witness_s','prove_s','verify_s','total_prover_s'):
   vals=[r[m] for r in rows if r['depth']==d];mean,sd,median,lo,hi=stat(vals);summary.append({'experiment':'merkle_depth','k':10,'depth':d,'metric':m,'mean_s':mean,'stdev_s':sd,'median_s':median,'min_s':lo,'max_s':hi})
 with (res/'summary.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 print('Wrote',res/'raw_measurements.csv');print('Wrote',res/'summary.csv')
if __name__=='__main__': main()

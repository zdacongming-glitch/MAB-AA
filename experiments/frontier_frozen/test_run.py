from pathlib import Path
import argparse,time,json
import numpy as np,pandas as pd
from engine_new import simulate
from test_protocol import ROOT,TEST,POLICIES,streams

def run(si):
 sc=TEST[si];mu=np.array(sc['means']);tau=np.array(sc['arrivals'],np.int64);rows=[];paths={};start=time.time()
 for rep in range(48):
  data=streams(sc,6210000+1000*si+rep)
  for p in POLICIES:
   st=time.time()
   out,snap,cnt=simulate(data,mu,tau,sc['epsilon'],sc['eta'],sc['delta'],sc['T'],p['reward'],p['scheduler'],p['period'],p['price'],.5,1,True,True,True,sc['eta']/4,7310000+1000*si+rep,200,p['beta'],1)
   rows.append(dict(scenario=sc['name'],rep=rep,method=p['name'],regret=out[0],area=out[1],final_unresolved=out[2],service_pulls=out[3],service_regret=out[4],label_error=out[5],coverage_error=out[6],empty_intersection=out[7],tax=out[8],denials=out[9],runtime=time.time()-st,total_pulls=int(sum(cnt))))
   if p['name'] in ['Shared-b1.0','CCP-b1.0','ALLplus-b1.0','MC-MOSS','KL-UCB'] and rep<8:paths[p['name']+'-'+str(rep)]=snap
  if rep%8==7:
   pd.DataFrame(rows).to_csv(ROOT/f'holdout-{si}.csv',index=False);print(si,rep+1,round(time.time()-start,1),flush=True)
 pd.DataFrame(rows).to_csv(ROOT/f'holdout-{si}.csv',index=False);np.savez_compressed(ROOT/f'holdout-{si}-paths.npz',**paths)
 return len(rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--worker',type=int,default=0);args=ap.parse_args()
 # Four workers, disjoint output files. No parameter changes between workers.
 for si in range(args.worker,len(TEST),4):run(si)

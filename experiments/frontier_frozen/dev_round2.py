import json,time,sys
from pathlib import Path
import numpy as np,pandas as pd
from engine_new import simulate
P=Path(__file__).parent
sys.path.insert(0,str(P/'prior'/'CCP_research_2026-10-16'))
from protocol import DEV, streams, policy
ps=[policy('CCP',reward=7,scheduler=13),policy('ALLplus',reward=7,scheduler=1)]
for sh in [21,24,26,28,30,31,32,33,34,35]:ps.append(policy('new'+str(sh),reward=7,scheduler=sh))
(P/'development-policies.json').write_text(json.dumps(ps,indent=2))
rows=[];start=time.time()
for si,sc in enumerate(DEV):
 mu=np.array(sc['means']);tau=np.array(sc['arrivals'],np.int64)
 for r in range(4):
  obs=streams(sc,350000+si*1000+r)
  for p in ps:
   out,_,cnt=simulate(obs,mu,tau,sc['epsilon'],sc['eta'],sc['delta'],sc['T'],p['reward'],p['scheduler'],2,p['price'],.5,1,True,True,True,sc['eta']/4,450000+si*1000+r,200,1.,1)
   rows.append(dict(scenario=sc['name'],rep=r,method=p['name'],regret=out[0],area=out[1],fail=out[5],n=int(sum(cnt))))
 print(si,round(time.time()-start,2),flush=True)
 pd.DataFrame(rows).to_csv(P/'development-round2.csv',index=False)
df=pd.DataFrame(rows)
s=df.groupby(['scenario','method'])[['regret','area']].mean().reset_index();s.to_csv(P/'development-round2-summary.csv',index=False)
print(s.to_string(index=False),flush=True)

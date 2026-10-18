from pathlib import Path
import sys,json,time,numpy as np,pandas as pd
P=Path(__file__).parent
sys.path.insert(0,str(P/'prior/CCP_research_2026-10-16'))
from protocol import DEV,streams
from engine_v2 import simulate
pol=[]
for r in [7,3,4]:
 for sh in [13,1,36,37,38,39,40]:
  pol.append(dict(name=f'dev3-r{r}-s{sh}',reward=r,scheduler=sh))
(P/'development-round3-protocol.json').write_text(json.dumps(dict(seed=8440000,reps=8,policies=pol),indent=2))
rows=[];st=time.time()
for si,sc in enumerate(DEV):
 for rep in range(8):
  rw=streams(sc,8440000+1000*si+rep)
  for po in pol:
   z,_,_=simulate(rw,np.array(sc['means']),np.array(sc['arrivals']),sc['epsilon'],sc['eta'],sc['delta'],sc['T'],po['reward'],po['scheduler'],2,.1,.5,1,True,True,True,sc['eta']/4,8450000+1000*si+rep,200,1.,1)
   rows.append(dict(scenario=sc['name'],rep=rep,method=po['name'],regret=z[0],area=z[1]))
 pd.DataFrame(rows).to_csv(P/'development-round3.csv',index=False)
 print(si,round(time.time()-st,1),flush=True)
pd.DataFrame(rows).groupby('method')[['regret','area']].mean().to_csv(P/'development-round3-summary.csv')

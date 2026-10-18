from pathlib import Path
import json, numpy as np
from practical import MaintenancePlanner
from verify_engine import simulate_trace
from test_protocol import TEST,streams
P=Path(__file__).parent;checks=[]
for si in [0,2]:
 sc=TEST[si];mu=np.array(sc['means']);tau=np.array(sc['arrivals']);rw=streams(sc,9981000+si)
 for name,sh in [('ccp',13),('shared',28),('allplus',1),('bundle',24)]:
  out,snap,counts,trace=simulate_trace(rw,mu,tau,sc['epsilon'],sc['eta'],sc['delta'],sc['T'],7,sh,2,.1,.5,1,True,True,True,sc['eta']/4,9983000+si,200,1.,1)
  alg=MaintenancePlanner(sc['epsilon'],sc['eta'],sc['delta'],scheduler=name)
  k=0;reg=0.;area=0
  for t in range(1,sc['T']+1):
   start=k
   while k<len(mu) and tau[k]<=t:k+=1
   i,service=alg.choose(list(range(start,k)))
   assert i==trace[t-1,0] and service==bool(trace[t-1,1]),(si,name,t,i,trace[t-1].tolist())
   x=rw[i,alg.n[i]];alg.observe(float(x));C,D,V=alg.report();B=mu[:k].max()
   reg+=B-mu[i];area+=sum(abs(B-mu[j]-sc['epsilon'])>sc['eta']+1e-12 for j in V)
  assert np.array_equal(alg.n[:k],counts)
  assert abs(reg-out[0])<1e-7 and abs(area-out[1])<1e-7
  checks.append(dict(scenario=sc['name'],scheduler=name,rounds=sc['T'],identical_actions=True,identical_service=True,identical_counts=True,regret=float(reg),area=int(area)))
(P/'api-verification.json').write_text(json.dumps(checks,indent=2));print('verified rounds',sum(x['rounds'] for x in checks))

from pathlib import Path
import json,time,argparse,datetime,hashlib
import numpy as np,pandas as pd
from flexible_v2 import simulate_dual
from study import ROOT,sc,streams,DEV,COLS
COLS2=COLS+['reward_tax','service_tax','spectrum_max']
def p(name,core=3,priority=0.,adaptive=False,br=None,bs=None,temperature=1.,scheduler=50,prior=1.,pfloor=.02,k0=4.):
 return dict(name=name,core=core,priority=priority,adaptive=adaptive,beta_r=br,beta_s=bs,temperature=temperature,scheduler=scheduler,prior=prior,pfloor=pfloor,k0=k0,price=.1)
D2=DEV+[sc('dev2_rare',[(1,[.045,.035,.02,.015]),(5001,[.06,.04,.025])],eps=.025,eta=.0075),sc('dev2_ceiling',[(1,[.99,.98,.95,.81]),(4901,[.995,.96,.91])],eps=.04,eta=.01),sc('dev2_close_two',[(1,[.48,.52])],eps=.03,eta=.01),sc('dev2_reverse_two',[(1,[.52,.48])],eps=.03,eta=.01)]
P2=[p('TS'),p('MC-MOSS',core=2),p('Growing-MOSS',core=1),p('KL-UCB',core=4),p('TS-temp0.5',temperature=.5),p('TS-temp0.75',temperature=.75)]
for temp in [.5,.75]:
 for br in [2.,4.,8.,16.]:P2.append(p(f'TS-temp{temp}-guard{br}',temperature=temp,br=br))
for pr in [.1,.3,.6,.9,1.]:
 P2.append(p('F-auto'+str(pr),priority=pr,adaptive=True,br=8.,bs=1.))
 if pr in [.3,.6,1.]:P2.append(p('F-open'+str(pr),priority=pr,adaptive=True))
P2.extend([p('F-bothcold',priority=.6,adaptive=True,br=8.,bs=1.,temperature=.5),p('F-area',priority=1.,br=8.),p('ALL-area',priority=1.,br=8.,scheduler=1),p('ALL-auto',priority=.6,adaptive=True,br=8.,bs=1.,scheduler=1)])

def freeze(stage,scenarios,policies,reps,rs,ps):
 obj=dict(stage=stage,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenarios=scenarios,policies=policies,reps=reps,reward_seed=rs,policy_seed=ps,
 hashes={f:hashlib.sha256((ROOT/'src'/f).read_bytes()).hexdigest() for f in ['ccp_primitives.py','flexible_engine.py','flexible_v2.py','study.py','study_v2.py']},notes='Two disjoint optimism-gap ledgers; pure reference samplers unchanged. Frozen before all runs in this stage. Boundary truth tolerances only in evaluation.')
 path=ROOT/'protocols'/f'{stage}-freeze.json'
 if path.exists():raise RuntimeError('Already frozen')
 path.write_text(json.dumps(obj,indent=2));print(len(scenarios)*len(policies)*reps)

def run(stage,worker,workers):
 cfg=json.loads((ROOT/'protocols'/f'{stage}-freeze.json').read_text())
 for si,s in enumerate(cfg['scenarios']):
  if si%workers!=worker:continue
  rows=[];paths={};st=time.time();mu=np.array(s['means']);arr=np.array(s['arrivals'],np.int64)
  for r in range(cfg['reps']):
   case=s
   if cfg.get('shuffle_within_batch',False):
    mu=np.array(s['means']);rng=np.random.default_rng(cfg['reward_seed']+50000000+si*10000+r)
    for at in np.unique(arr):
     ids=np.flatnonzero(arr==at);mu[ids]=mu[ids][rng.permutation(len(ids))]
    case=dict(s,means=mu.tolist())
   rew=streams(case,cfg['reward_seed']+si*10000+r)
   for pol in cfg['policies']:
    start=time.time();out,path,cnt=simulate_dual(rew,mu,arr,s['epsilon'],s['eta'],s['delta'],s['T'],pol['core'],pol['priority'],pol['adaptive'],1e100 if pol['beta_r'] is None else pol['beta_r'],1e100 if pol['beta_s'] is None else pol['beta_s'],pol['price'],pol['pfloor'],pol['k0'],pol['scheduler'],pol['temperature'],pol['prior'],cfg['policy_seed']+si*10000+r,200)
    row=dict(stage=stage,scenario=s['name'],rep=r,method=pol['name'],T=s['T'],K=len(mu),runtime=time.time()-start,total_pulls=int(sum(cnt)))
    row.update(dict(zip(COLS2,out)));rows.append(row)
    if r<4:paths[pol['name']+'-'+str(r)]=path
   if r%8==7:
    pd.DataFrame(rows).to_csv(ROOT/'results'/f'{stage}-{si}.csv',index=False);print(stage,si,r+1,round(time.time()-st,1),flush=True)
  pd.DataFrame(rows).to_csv(ROOT/'results'/f'{stage}-{si}.csv',index=False);np.savez_compressed(ROOT/'results'/f'{stage}-{si}-paths.npz',**paths)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--freeze-dev2',action='store_true');ap.add_argument('--stage',default='development2');ap.add_argument('--worker',type=int,default=0);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 if args.freeze_dev2:freeze('development2',D2,P2,24,94110100,94120100)
 else:run(args.stage,args.worker,args.workers)

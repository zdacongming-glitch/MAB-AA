"""Prespecified environments, development and locked-test runner."""
from __future__ import annotations
from pathlib import Path
import math,json,hashlib,time,datetime,argparse
import numpy as np,pandas as pd
from flexible_engine import simulate_flexible
ROOT=Path(__file__).resolve().parents[1]

def sc(name,batches,eps=.2,eta=.05,T=10000,kind='bernoulli'):
    a=[];m=[]
    for t,v in batches:a.extend([t]*len(v));m.extend(v)
    return dict(name=name,arrivals=a,means=m,epsilon=eps,eta=eta,delta=.05,T=T,kind=kind)
DEV=[
 sc('dev_sparse',[(1,[.72,.43]),(2701,[.17]),(6401,[.59])]),
 sc('dev_records',[(1,[.39,.13]),(2801,[.66,.41,.49]),(6701,[.92,.69,.81])]),
 sc('dev_boundary',[(1,[.76,.53,.58,.68,.17]),(4701,[.55,.62,.33])],eta=.035),
 sc('dev_ties',[(1,[.58,.575,.55,.525,.49]),(5101,[.595,.54,.52,.43])],eps=.1,eta=.025),
 sc('dev_lowvar',[(1,[.69,.63,.53,.38]),(3401,[.78,.68,.57]),(7801,[.82,.76,.66])],kind='two_point'),
]

def policy(name,core=3,priority=0.,adaptive=False,beta=None,price=.1,pfloor=.02,k0=4.,scheduler=50,temperature=1.,prior=1.,cap=2):
    return dict(name=name,core=core,priority=priority,adaptive=adaptive,beta=beta,price=price,pfloor=pfloor,k0=k0,scheduler=scheduler,temperature=temperature,prior=prior,cap_mode=(0 if beta is None else cap))
DEV_POLICIES=[policy('UCB',0),policy('Growing-MOSS',1),policy('MC-MOSS',2),policy('MC-MOSS-clipped',7),policy('TS',3),policy('KL-UCB',4)]
for prior in [.5,2.]:DEV_POLICIES.append(policy('TS-prior'+str(prior),prior=prior))
for temp in [.5,.75,1.5]:DEV_POLICIES.append(policy('TS-temperature'+str(temp),temperature=temp))
DEV_POLICIES.append(policy('Optimistic-TS',8))
for beta in [.05,.1,.25,.5,1.,2.]:DEV_POLICIES.append(policy('TS-projected'+str(beta),beta=beta))
for priority in [.1,.3,.6,.9,1.]:
    DEV_POLICIES.append(policy('F-TS-fixed'+str(priority),priority=priority))
    if priority<1.:DEV_POLICIES.append(policy('F-TS-auto'+str(priority),priority=priority,adaptive=True))
for beta in [.25,1.,4.]:
    DEV_POLICIES.append(policy('F-TS-auto0.6-safe'+str(beta),priority=.6,adaptive=True,beta=beta))
DEV_POLICIES.extend([policy('Old-CCP',7,priority=.5,beta=1.,scheduler=13,cap=1),policy('ALLplus',7,priority=.5,beta=1.,scheduler=1,cap=1),policy('ALL-TS-fast',3,priority=1.,scheduler=1)])

def streams(s,seed):
    rng=np.random.default_rng(seed);mu=np.array(s['means']);u=rng.random((len(mu),s['T']))
    if s['kind']=='bernoulli':return np.asarray(u<mu[:,None],dtype=np.float64)
    spread=np.minimum(.045,np.minimum(mu,1.-mu))
    return mu[:,None]+np.where(u<.5,-spread[:,None],spread[:,None])
COLS=['regret','area','final_unresolved','service_pulls','service_regret','label_error','coverage_error','empty_intersection','tax','service_denials','reward_projections','service_mass','service_attempts','active_service_rounds','final_all_unresolved']

def freeze(stage,scenarios,policies,reps,reward_seed,policy_seed):
    obj=dict(stage=stage,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenarios=scenarios,policies=policies,reps=reps,reward_seed=reward_seed,policy_seed=policy_seed,
        hashes={f:hashlib.sha256((ROOT/'src'/f).read_bytes()).hexdigest() for f in ['ccp_primitives.py','flexible_engine.py','study.py']},
        notes='All methods share potential reward streams, no future inputs to action functions. Pure reward modes have no service or projection unless explicit. Fractional-beta TS for non-Bernoulli rewards is a heuristic; exact Bernoulli posteriors only on Bernoulli trials.')
    path=ROOT/'protocols'/f'{stage}-freeze.json'
    if path.exists():raise RuntimeError('Freeze already exists; do not overwrite')
    path.write_text(json.dumps(obj,indent=2));return path

def run(stage,worker,workers):
    p=json.loads((ROOT/'protocols'/f'{stage}-freeze.json').read_text())
    for si,s in enumerate(p['scenarios']):
        if si%workers!=worker:continue
        rows=[];paths={};start=time.time()
        mu=np.array(s['means']);arr=np.array(s['arrivals'],np.int64)
        for r in range(p['reps']):
            rew=streams(s,p['reward_seed']+si*10000+r)
            for pol in p['policies']:
                tm=time.time()
                out,path,cnt=simulate_flexible(rew,mu,arr,s['epsilon'],s['eta'],s['delta'],s['T'],pol['core'],pol['priority'],pol['adaptive'],1e100 if pol['beta'] is None else pol['beta'],pol['price'],pol['pfloor'],pol['k0'],pol['scheduler'],pol['temperature'],pol['prior'],pol['cap_mode'],p['policy_seed']+si*10000+r,200)
                row=dict(stage=stage,scenario=s['name'],rep=r,method=pol['name'],T=s['T'],K=len(mu),runtime=time.time()-tm,total_pulls=int(sum(cnt)))
                row.update(dict(zip(COLS,out)));rows.append(row)
                if r<4:paths[pol['name']+'-'+str(r)]=path
            if r%8==7:
                pd.DataFrame(rows).to_csv(ROOT/'results'/f'{stage}-{si}.csv',index=False)
                print(stage,si,r+1,round(time.time()-start,1),flush=True)
        pd.DataFrame(rows).to_csv(ROOT/'results'/f'{stage}-{si}.csv',index=False)
        np.savez_compressed(ROOT/'results'/f'{stage}-{si}-paths.npz',**paths)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--freeze-dev',action='store_true');ap.add_argument('--stage',default='development');ap.add_argument('--worker',type=int,default=0);ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    if a.freeze_dev:print(freeze('development',DEV,DEV_POLICIES,16,83110100,83120100))
    else:run(a.stage,a.worker,a.workers)

from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def scenario(name,batches,eps=.2,eta=.05,T=16000,kind='bernoulli'):
    tau=[];means=[]
    for t,ms in batches:
        tau.extend([t]*len(ms)); means.extend(ms)
    return dict(name=name,arrivals=tau,means=means,epsilon=eps,eta=eta,delta=.05,T=T,kind=kind)

DEV=[
 scenario('dev_stable',[(1,[.72,.56]),(2501,[.18,.43]),(6001,[.65,.3]),(9001,[.55,.1])],T=12000),
 scenario('dev_updates',[(1,[.4,.17]),(3001,[.64,.39,.43]),(6001,[.82,.55,.63]),(9001,[.95,.7,.76])],T=12000),
 scenario('dev_burst',[(1,[.65,.42]),(4001,[.9,.72,.58,.12,.3,.7,.8,.51,.6,.68,.48,.88])],T=12000),
 scenario('dev_heterogeneous',[(1,[.85,.8,.68,.64,.62,.4,.25,.15]),(4001,[.82,.66])],T=12000),
]
TEST=[
 scenario('stable',[(1,[.70,.53]),(3501,[.10,.26]),(7501,[.46,.63]),(11001,[.20,.55])]),
 scenario('improvements',[(1,[.45,.18]),(4001,[.68,.46]),(8001,[.86,.59]),(12001,[.98,.76])]),
 scenario('burst',[(1,[.66,.50]),(5501,[.91,.89,.72,.68,.60,.40,.30,.10,.78,.82])]),
 scenario('arrivals_stop',[(1,[.62,.30]),(2037,[.85,.61,.43]),(4037,[.76,.56,.16])]),
 scenario('near_boundary',[(1,[.80,.595,.605,.53,.67,.10]),(6001,[.62,.58])],eta=.04),
 scenario('near_tied_top',[(1,[.65,.64,.63,.50]),(5001,[.66,.60,.49,.20]),(10001,[.67,.61,.55,.40])],eps=.12,eta=.03),
 scenario('late_best',[(1,[.50,.39,.27,.20]),(4001,[.10,.42]),(12001,[.88,.65])]),
 scenario('low_variance',[(1,[.70,.55,.35,.20]),(5001,[.85,.65]),(10001,[.78,.45])],kind='two_point_low_variance'),
 scenario('many_heterogeneous',[(1,[.80,.70,.65,.45]),(5001,[.10,.16,.22,.28,.34,.40,.46,.52,.58,.64,.70,.76,.82,.86,.89,.90]),(14001,[.94,.92,.73,.67])],T=20000),
 scenario('near_upper_boundary',[(1,[.96,.85,.75,.20]),(5001,[.98,.77]),(10001,[.60,.10])],eps=.15,eta=.04)
]

def streams(sc,seed):
    rng=np.random.default_rng(seed)
    mu=np.asarray(sc['means'],float)
    u=rng.random((len(mu),sc['T']))
    if sc['kind']=='bernoulli': return (u<mu[:,None]).astype(np.float64)
    if sc['kind']=='two_point_low_variance':
        a=np.minimum(.05,np.minimum(mu,1-mu))
        return mu[:,None]+np.where(u<.5,-a[:,None],a[:,None])
    raise ValueError(sc['kind'])

def policy(name,reward=2,scheduler=1,period=2,price=.1,xi=.5,conf=1,exact=True,band=True,cap=True,rho=None):
    return dict(name=name,reward=reward,scheduler=scheduler,period=period,price=price,xi=xi,conf=conf,exact=exact,band=band,cap=cap,rho=rho)

PROTOCOL=dict(date='2026-10-16',development=DEV,test=TEST,
 development_reward_seed_base=110000,test_reward_seed_base=910000,
 development_policy_seed_base=210000,test_policy_seed_base=1010000,
 metrics=['pseudo_regret','charged_unresolved_area','final_charged_unresolved','designated_service_pulls','service_regret','any_label_error','any_interval_miss','empty_intersection'],
 selection_note='All algorithm and parameter development uses DEV only. TEST executed only after candidate configurations frozen. Test suite is new, not a reproduction of manuscript Table 2; original complete simulation code/config is not mounted.',
 scalar_diagnostics=[.01,.03,.1,.3],
 reporting='Exact relative labels. Boundary-band certification suspends service but does not assign a determinate label. Same robust report and confidence objects for fair upgraded baselines.',
 no_future_information=True)
if __name__=='__main__':
    path=ROOT/'protocol.json'
    data=json.dumps(PROTOCOL,ensure_ascii=False,indent=2).encode()
    if path.exists() and path.read_bytes()!=data: raise RuntimeError('Refusing to change frozen protocol')
    path.write_bytes(data)
    print('Protocol SHA256',hashlib.sha256(data).hexdigest())

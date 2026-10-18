"""Fresh holdout scenarios and pre-frozen candidate families."""
from pathlib import Path
import hashlib,json,datetime
import numpy as np
ROOT=Path(__file__).parent

def scenario(name,batches,epsilon=.2,eta=.05,T=14000,kind='bernoulli'):
    tau=[];mus=[]
    for t,ms in batches:tau.extend([t]*len(ms));mus.extend(ms)
    return dict(name=name,arrivals=tau,means=mus,epsilon=epsilon,eta=eta,delta=.05,T=T,kind=kind)

TEST=[
 scenario('stable_new',[(1,[.74,.65]),(2777,[.12,.26]),(6129,[.46,.69]),(9779,[.31,.57])]),
 scenario('updates_new',[(1,[.38,.14]),(3113,[.62,.36,.49]),(6779,[.81,.59,.53]),(10331,[.965,.735,.84])]),
 scenario('burst_new',[(1,[.64,.47]),(4337,[.905,.865,.755,.70,.62,.55,.41,.31,.13,.79,.81,.67])]),
 scenario('stopped_new',[(1,[.66,.29]),(1777,[.86,.59,.44]),(3337,[.77,.52,.18,.69])]),
 scenario('boundary_new',[(1,[.78,.568,.592,.49,.665,.15]),(5777,[.61,.55,.72])],eta=.04),
 scenario('near_ties_new',[(1,[.625,.61,.60,.465]),(4337,[.64,.58,.515,.25]),(8779,[.65,.595,.53,.36,.48])],epsilon=.13,eta=.035),
 scenario('late_record_new',[(1,[.515,.415,.27,.19]),(4337,[.15,.46]),(11311,[.895,.67,.84])]),
 scenario('low_means',[(1,[.245,.19,.14,.06]),(3779,[.215,.07]),(8111,[.27,.17,.105])],epsilon=.08,eta=.025),
 scenario('ceiling_new',[(1,[.965,.855,.755,.24]),(3779,[.985,.805,.70]),(9113,[.615,.13])],epsilon=.15,eta=.04),
 scenario('many_new',[(1,[.805,.735,.62,.45]),(4337,[.12,.175,.23,.285,.34,.395,.45,.505,.56,.615,.67,.725,.78,.835,.865,.895]),(11213,[.945,.915,.755,.675,.51])],T=18000),
 scenario('serial_arrivals',[(1,[.655,.44])]+[(601+613*j,[float(x)]) for j,x in enumerate([.12,.38,.68,.49,.56,.2,.72,.6,.41,.77,.52,.25,.73,.81,.61,.45,.86,.68,.57,.32])],T=15000),
 scenario('bounded_low_variance_new',[(1,[.69,.52,.33,.17]),(4777,[.84,.62,.73]),(9449,[.79,.46,.26])],kind='two_point'),
]

def p(name,reward=7,scheduler=-1,beta=1e100,period=2):
 return dict(name=name,reward=reward,scheduler=scheduler,beta=beta,period=period,price=.1)
POLICIES=[p('UCB',0),p('Growing-MOSS',1),p('MC-MOSS',2),p('MC-MOSS-clipped',7),p('Thompson',3),p('KL-UCB',4)]
for fam,sh in [('CCP',13),('ALLplus',1),('Shared',28)]:
 for b in [.25,1.,4.,1e100]:POLICIES.append(p(fam+('-free' if b>1e90 else '-b'+str(b)),scheduler=sh,beta=b))
POLICIES.append(p('Bundle-b1',scheduler=24,beta=1.))
for fam,sh in [('CCP',13),('ALLplus',1),('Shared',28)]:POLICIES.append(p(fam+'-fast',scheduler=sh,period=1))


def streams(sc,seed):
 rng=np.random.default_rng(seed);mu=np.array(sc['means']);u=rng.random((len(mu),sc['T']))
 if sc['kind']=='bernoulli':return (u<mu[:,None]).astype(float)
 spread=np.minimum(.065,np.minimum(mu,1-mu))
 return mu[:,None]+np.where(u<.5,-spread[:,None],spread[:,None])

if __name__=='__main__':
 obj=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reps=48,scenarios=TEST,policies=POLICIES,primary='Shared-b1.0',primary_comparators=['CCP-b1.0','ALLplus-b1.0'],reward_seed=6210000,policy_seed=7310000,
 note='New predefined environments, independent seeds. Prior scenarios used for development only. Primary chosen on development average relative area subject to modest regret change; no superiority assumed. Pure reward policies share the report layer only, with no service or budget restrictions. Fractional Beta-TS on non-Bernoulli observations is a heuristic, not a correct Bayesian posterior.',
 hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['engine_base.py','engine_new.py','new_schedulers.py']})
 file=ROOT/'holdout-freeze.json'
 if file.exists():raise RuntimeError('Frozen file already exists')
 file.write_text(json.dumps(obj,indent=2));print(len(TEST),len(POLICIES),len(TEST)*len(POLICIES)*48)

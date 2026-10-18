import hashlib,json
from protocol import ROOT,policy
ps=[policy('CP-original-004',reward=0,scheduler=0,conf=2,exact=False,band=False,cap=True,rho=.04),
    policy('CP-original-012',reward=0,scheduler=0,conf=2,exact=False,band=False,cap=True,rho=.12),
    policy('ALL-prefix-UCB',reward=0,scheduler=1,conf=0,exact=False,band=False,cap=False),
    policy('MC-report',reward=7,scheduler=-1),
    policy('TS-report',reward=3,scheduler=-1),
    policy('KLUCB-report',reward=4,scheduler=-1)]
for sch,nm in [(1,'ALLplus'),(13,'CCP')]:
    for beta in [.25,.5,1.,2.]:
        p=policy(f'{nm}-beta{beta:g}',reward=7,scheduler=sch,period=2,price=.1)
        p.update(budget_scale=beta,budget_mode=1);ps.append(p)
p=policy('ST2plus-beta1',reward=7,scheduler=3);p.update(budget_scale=1.,budget_mode=1);ps.append(p)
ps += [policy('ALLplus-unlimited',reward=7,scheduler=1),policy('CCP-unlimited',reward=7,scheduler=13),
       policy('ALLplus-KLUCB-unlimited',reward=4,scheduler=1)]
for nm,kw in [('CCP-no-band',{'band':False}),('CCP-prefix',{'conf':0}),('CCP-empirical-cost',{'scheduler':9})]:
    p=policy(nm,reward=7,scheduler=13);p.update(budget_scale=1.,budget_mode=1);p.update(kw);ps.append(p)
f=ROOT/'test-policies-frozen.json'
if f.exists(): raise RuntimeError('Test policies already frozen')
f.write_text(json.dumps(ps,indent=2))
record={'frozen_before_test':True,'date':'2026-10-16','primary_candidate':'CCP-beta1',
 'family':['CCP-beta0.25','CCP-beta0.5','CCP-beta1','CCP-beta2'],
 'primary_fair_comparator':'ALLplus-beta1',
 'n_test_scenarios':10,'replications_per_scenario':64,'n_policy_configurations':len(ps),
 'default_lambda_time_price':.1,'maximum_designated_service_fraction':.5,
 'secondary_scores_weights':[.01,.03,.1,.3],
 'note':'Weights are diagnostic scalarizations of mean outcomes, not replacements for the high-probability area criterion. Development performed on four distinct environments; no TEST outcomes consulted before freezing.',
 'hashes':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['engine.py','protocol.json','test-policies-frozen.json']}}
(ROOT/'test-freeze-record.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))

from pathlib import Path
import json,math,random
import numpy as np
import sympy as sp
from abm import ActivationBudgetedMaintenance
P=Path(__file__).parent
x=sp.symbols('x',positive=True);f=(1-2*x)*sp.log((1-x)/x)
assert sp.simplify(sp.diff(f,x,2)-1/(x*x*(1-x)**2))==0
rng=np.random.default_rng(161026)
for _ in range(20000):
    delta=float(np.exp(rng.uniform(-25,math.log(1/16))))
    s=int(rng.integers(1,10000));v=-math.log1p(-4*delta)
    ff=(1-2*v/s)*math.log((1-v/s)/(v/s))
    assert ff+1e-10>=math.log(s/delta)/12
    m=int(rng.integers(2,1000));L=int(rng.integers(1,100000));B=int(rng.integers(1,100000))
    H=16*(L+B);V=m*H;amin=m*L+B
    a=float(rng.uniform(amin,V-1e-5))
    k=math.ceil((V-a)/H);n=math.ceil((V+B-a)/(H-L))
    assert 1<=n<=m and n<=2*k and (m-n)*H+n*L+B<=a+1e-6
    d=float(np.exp(rng.uniform(-15,math.log(1/1024))))
    q=math.ceil(32/d**2*math.log(4*(2*s)*(2*s+1)/delta))
    assert q<=97/d**2*math.log(s/delta)
# Fresh-block / no-future interface diagnostics; not the separated asymptotic family.
r=random.Random(66761);alg=ActivationBudgetedMaintenance(.3,.05,.2,.1,2)
means={};reg=0.;area=0;errors=0
arr={1:[.70,.30,.45],5000:[.90,.55]}
for t in range(1,10001):
    new=[]
    for mu in arr.get(t,[]):
        i=len(means)+1;means[i]=mu;new.append(i)
    i=alg.choose(new);alg.observe(float(r.random()<means[i]))
    PP,NN,VV=alg.report();B=max(means.values());reg+=B-means[i]
    G={j for j,mu in means.items() if B-mu<=.3+1e-12}
    errors+=int(not PP<=G or bool(NN&G))
    area+=sum(abs(B-means[j]-.3)>.1+1e-12 for j in VV)
    assert len(PP|NN|VV)==len(means) and not PP&NN and not PP&VV and not NN&VV
    assert sum(a.n for a in alg.arms.values())==t
    for a in alg.arms.values():
        if a.fine_rank:assert a.fine_n==min(a.n-a.fine_start_n,a.fine_quota)
result=dict(symbolic_f_second_derivative=True,scalar_and_budget_checks=20000,
 ABM_sanity=dict(rounds=10000,regret=reg,area=area,label_error_rounds=errors,
 fine_activations=alg.rank,remaining_candidates=alg.remaining,service_pulls=alg.designated_pulls,
 final_counts={str(i):a.n for i,a in alg.arms.items()},
 note='A single implementation test, not asymptotic theorem-family verification or a performance comparison'))
(P/'audit-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

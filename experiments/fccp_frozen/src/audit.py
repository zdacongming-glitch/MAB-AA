"""Implementation diagnostics (not a formal proof certificate)."""
from pathlib import Path
import sys,json,math,hashlib,platform,datetime
import numpy as np
import numba
from scipy.special import betaln
from flexible_ccp import FlexibleCCP,CORES
from flexible_engine import seed_policy,control_rate
from flexible_v2 import choose_dual
from ccp_primitives import beta_mix_interval,kl_ucb_index
ROOT=Path(__file__).resolve().parents[1]
checks={};counts={}
# Frozen test engine was not altered by the later comparator correction.
fr=json.loads((ROOT/'protocols/holdout-freeze.json').read_text())
for fn,h in fr['hashes'].items():assert hashlib.sha256((ROOT/'src'/fn).read_bytes()).hexdigest()==h
checks['frozen_main_engine_hashes']=True

# Exact pure-mode compatibility: independently maintained baseline state and RNG.
cores=['ucb1','growing_moss','mc_moss','thompson','kl_ucb'];T=2500;rounds=0
for core in cores:
 for seed in range(4):
  rng=np.random.default_rng(70400+seed);mu=np.array([.58,.44,.78,.36,.68]);rw=rng.binomial(1,mu[:,None],size=(5,T)).astype(float)
  births={1:['a','b'],701:['c'],1601:['d','e']};n=np.zeros(5,dtype=np.int64);S=np.zeros(5);k=0;base=0;start=1;brng=np.random.default_rng(seed)
  alg=FlexibleCCP.preset('compatibility',.2,.05,base=core,seed=seed)
  for t in range(1,T+1):
   new=births.get(t,[]);k+=len(new)
   if k>1 and (base==0 or k-1>=2*base):base=k-1;start=t
   sc=np.zeros(k)
   for i in range(k):
    if core=='thompson':sc[i]=brng.beta(1+S[i],1+n[i]-S[i])
    elif n[i]==0:sc[i]=math.inf
    elif core=='ucb1':sc[i]=S[i]/n[i]+math.sqrt(2*math.log(max(2,t))/n[i])
    elif core=='kl_ucb':sc[i]=kl_ucb_index(n[i],S[i],t)
    else:
     clock=t if core=='growing_moss' else t-start+1;cap=k if core=='growing_moss' else max(2,2*base)
     sc[i]=S[i]/n[i]+math.sqrt(max(0.,math.log(clock/(cap*n[i])))/n[i])
   a=int(np.argmax(sc));label,service=alg.choose(new)
   assert label=='abcde'[a] and not service
   x=rw[a,n[a]];n[a]+=1;S[a]+=x;alg.observe(x)
   assert np.array_equal(alg.n,n[:k]) and np.array_equal(alg.S,S[:k])
   C,D,V=alg.report();assert not C&D and not C&V and not D&V and C|D|V==set('abcde'[:k])
   rounds+=1
checks['independent_baseline_pure_compatibility']=True;counts['compatibility_rounds']=rounds

# Prefix padding cannot affect a selected action or its bookkeeping, even when
# future storage is filled with invalid sentinel values. Observed prefixes stay legal.
rng=np.random.default_rng(80331);padding_checks=0
for trial in range(100):
 k=int(rng.integers(2,10));n=rng.integers(0,500,k,dtype=np.int64);S=np.array([rng.binomial(nn,.6) for nn in n],float)
 lo=np.maximum(0.,np.divide(S,np.maximum(1,n))-.15);up=np.minimum(1.,np.divide(S,np.maximum(1,n))+.15)
 lo[n==0]=0;up[n==0]=1;q=np.full(k,1000,np.int64);birth=np.ones(k,np.int64)
 args=[n,S,lo,up,q,birth,k,501,k-1,1,0,.4,0.,0.,0.,False,.2,.05]
 for core in [0,1,2,3,4,7,10,11]:
  tail=[core,.6,True,16.,1.,.1,.02,4.,50,.5,1.]
  seed_policy(947+trial);a=choose_dual(*(args+tail))
  padded=[]
  for j,x in enumerate(args[:6]):
   sent=987654321 if x.dtype.kind in 'iu' else 99999.9
   padded.append(np.concatenate([x,np.full(17,sent,dtype=x.dtype)]))
  seed_policy(947+trial);b=choose_dual(*(padded+args[6:]+tail))
  assert a==b;padding_checks+=1
checks['future_padding_invariance']=True;counts['padding_cases']=padding_checks

# Distribution-free confidence set root diagnostics, including exact endpoints.
ci_cases=0
for n in [0,1,2,10,100,1000,100000]:
 for frac in [0.,1e-4,.1,.5,.9999,1.]:
  for alpha in [.001,.01,.1]:
   S=n*frac;l,u=beta_mix_interval(n,S,alpha)
   assert 0<=l<=u<=1
   if n:
    x=S/n
    assert l<=x+1e-12 and u>=x-1e-12
    c=betaln(S+.5,n-S+.5)-betaln(.5,.5)
    def lm(p):
     if p<=0:return c if S==0 else math.inf
     if p>=1:return c if S==n else math.inf
     return c-S*math.log(p)-(n-S)*math.log1p(-p)
    # Returned finite endpoints are exterior (up to lgamma floating error).
    assert lm(l)>=math.log(1/alpha)-2e-7 or l==0
    assert lm(u)>=math.log(1/alpha)-2e-7 or u==1
   ci_cases+=1
checks['confidence_interval_root_diagnostics']=True;counts['interval_cases']=ci_cases

# Adaptive rate lower bound and endpoint behavior: formula, not optimality.
for _ in range(10000):
 lam=rng.uniform(0,1);b=int(rng.integers(1,100));eps=rng.uniform(.001,.9);gap=rng.uniform(0,1)
 p=control_rate(lam,True,b,gap,eps,.02,4.)
 pmin=lam*.02/(1-lam+lam*.02)
 assert pmin-1e-14<=p<=lam+1e-14
 assert control_rate(0,True,b,gap,eps,.02,4.)==0
 assert control_rate(1,True,b,gap,eps,.02,4.)==1
 assert control_rate(lam,True,0,gap,eps,.02,4.)==0
checks['adaptive_rate_bounds']=True;counts['rate_cases']=10000

# Legal midstream preference changes never erase samples, confidence or budgets.
alg=FlexibleCCP.preset('balanced',.15,.04,seed=916);g=np.random.default_rng(1983);m=[.70,.53,.35];reward=g.binomial(1,np.array(m)[:,None],(3,4000)).astype(float)
for t in range(1,4001):
 if t in [701,1801,2701]:
  before=(alg.n.copy(),alg.S.copy(),alg.reward_tax,alg.service_tax,alg.phase,alg.l.copy(),alg.u.copy())
  alg.set_priority({701:0.,1801:1.,2701:.4}[t])
  assert np.array_equal(alg.n,before[0]) and np.array_equal(alg.S,before[1]) and alg.reward_tax==before[2] and alg.service_tax==before[3] and alg.phase==before[4] and np.array_equal(alg.l,before[5]) and np.array_equal(alg.u,before[6])
 new=[0,1,2] if t==1 else[];a,serv=alg.choose(new);count=alg.n[a];alg.observe(reward[a,count]);diag=alg.diagnostics()
 assert diag['total_actual_pulls']==t
 assert alg.reward_tax<=16*alg.spectrum_max+1e-8 and alg.service_tax<=alg.spectrum_max+1e-8
 if 701<=t<1801:assert not serv
checks['preference_switch_retains_state']=True;counts['switch_rounds']=4000

# Non-dominance minimax excess calculation.
p=np.linspace(0,1,10001);v=np.maximum(.5*(1-p),.5*p-.25)
assert abs(v.min()-.125)<1e-12
checks['two_baseline_counterexample']=True

# Standard API errors do not fake observations.
a=FlexibleCCP.preset('reward',.2,.05)
for op in [lambda:a.choose(),lambda:a.observe(.5),lambda:a.set_priority(1.1)]:
 try:op();raise AssertionError('expected rejection')
 except (ValueError,RuntimeError):pass
a.choose(['x'])
try:a.choose();raise AssertionError('expected pending error')
except RuntimeError:pass
try:a.set_priority(.5);raise AssertionError('expected pending error')
except RuntimeError:pass
a.observe(1.);assert a.report()==({'x'},set(),set())
checks['api_error_contracts']=True
out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='passed',checks=checks,counts=counts,environment=dict(python=sys.version,numpy=np.__version__,numba=numba.__version__,platform=platform.platform()),scope='Internal diagnostics, not independent external review or formal verification. API Generator and batch Numba use different RNG streams; pure equality is tested within the API backend and separately within frozen batch results.')
(ROOT/'results/implementation-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

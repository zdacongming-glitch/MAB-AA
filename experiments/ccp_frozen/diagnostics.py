from pathlib import Path
from itertools import product
import inspect,json,math,time,hashlib
import numpy as np
from scipy.optimize import brentq
from scipy.special import betaln
import engine
from engine import beta_mix_interval,gap_bounds,labels_work,pair_plan,current_spectrum,simulate
from ccp import CertificateCostPlanner
from protocol import ROOT,TEST,streams
rng=np.random.default_rng(730161)
results={};start=time.time()
# 1. Convex single-factor bound underpinning distribution-free mean validity.
for _ in range(5000):
 m,theta,x=rng.uniform(.001,.999,3)
 actual=(theta/m)**x*((1-theta)/(1-m))**(1-x)
 endpoint=(1-x)*(1-theta)/(1-m)+x*theta/m
 assert actual<=endpoint+1e-10
results['bounded_factor_convexity']=5000
# 2. Interval endpoints against independent scipy log-beta + root evaluator.
max_error=0.
for _ in range(1000):
 n=int(rng.integers(1,20001));S=float(rng.choice([0.,float(n),rng.uniform(0,n)]));alpha=float(10**rng.uniform(-7,-1))
 lo,up=beta_mix_interval(n,S,alpha);x=S/n
 const=betaln(S+.5,n-S+.5)-betaln(.5,.5)-math.log(1/alpha)
 def ff(m):
  v=const
  if S>0:v-=S*math.log(m)
  if n-S>0:v-=(n-S)*math.log1p(-m)
  return v
 lower=0. if S==0 else brentq(ff,1e-16,x,xtol=5e-15)
 upper=1. if S==n else brentq(ff,x,1-1e-16,xtol=5e-15)
 max_error=max(max_error,abs(lo-lower),abs(up-upper))
 assert lo<=lower+2e-10 and up>=upper-2e-10
 assert abs(lo-lower)<1e-8 and abs(up-upper)<1e-8
results['mixture_interval_roots']={'cases':1000,'max_absolute_error':max_error}
# 3. Exact rectangle gap range: exhaust vertices, not only sampled means.
for _ in range(1000):
 k=int(rng.integers(1,7));a=rng.random(k);b=rng.random(k);lo=np.minimum(a,b);up=np.maximum(a,b)
 gl,gu=gap_bounds(lo,up,k)
 points=np.array([np.where(np.array(bits),up,lo) for bits in product([0,1],repeat=k)])
 gaps=points.max(axis=1)[:,None]-points
 assert np.allclose(gl,gaps.min(axis=0),atol=1e-12)
 assert np.allclose(gu,gaps.max(axis=0),atol=1e-12)
results['rectangle_vertex_checks']=1000
# 4. Band suspension does not declare a determinate label, and reactivates on arrival.
l=np.array([.79,.595]);u=np.array([.81,.605]);lab,w,_,_=labels_work(l,u,2,.2,.03,True,True)
assert lab[1]==0 and not w[1]
l2=np.r_[l,0.];u2=np.r_[u,1.];lab2,w2,_,_=labels_work(l2,u2,3,.2,.03,True,True)
assert w2[1] and lab2[1]==0
# Cap-completion implication: every unresolved arm is in certified band.
for _ in range(1000):
 k=int(rng.integers(1,20));mu=rng.random(k);eta=float(rng.uniform(.005,.15));rho=eta/4
 lo=np.maximum(0.,mu-rng.uniform(0,rho/2,k));up=np.minimum(1.,lo+rho)
 # Guarantee coverage even close to support boundary.
 up=np.maximum(up,mu)
 lab,w,gl,gu=labels_work(lo,up,k,.2,eta,True,True)
 assert not w.any()
results['band_and_completion']=1001
# 5. Convex planner against independent multiplier root with box constraints.
maxrel=0.
for _ in range(2000):
 ni,nj=rng.integers(1,1001,2).astype(float);ri,rj=10**rng.uniform(-3,0,2);ci,cj=10**rng.uniform(-2,1,2)
 h=float((ri+rj)*rng.uniform(.08,1.15))
 mi,mj,cost=pair_plan(ni,nj,ri,rj,ci,cj,h)
 ai=ri*math.sqrt(ni);aj=rj*math.sqrt(nj)
 assert mi>=ni-1e-8 and mj>=nj-1e-8
 assert ai/math.sqrt(mi)+aj/math.sqrt(mj)<=h+1e-9 or ri+rj<=h
 if ri+rj<=h:
  assert cost==0;continue
 def f(lam):
  xi=max(ni,(lam*ai/(2*ci))**(2/3));xj=max(nj,(lam*aj/(2*cj))**(2/3))
  return ai/math.sqrt(xi)+aj/math.sqrt(xj)-h
 hi=1.
 while f(hi)>0:hi*=2
 lm=brentq(f,0.,hi,xtol=1e-12)
 xi=max(ni,(lm*ai/(2*ci))**(2/3));xj=max(nj,(lm*aj/(2*cj))**(2/3))
 value=ci*(xi-ni)+cj*(xj-nj)
 rel=abs(cost-value)/max(1.,value);maxrel=max(maxrel,rel)
 assert rel<1e-7
results['pair_planner_dual_checks']={'cases':2000,'max_relative_objective_error':maxrel}
# 6. Every-prefix spectrum monotonic envelope <= 2 endpoint spectrum.
for _ in range(1000):
 T=int(rng.integers(2,500));K=int(rng.integers(2,70));tau=np.sort(rng.integers(1,T+1,K));tau[0]=1
 full=current_spectrum(tau,K,T);run=0.
 for t in range(1,T+1):
  k=int(np.searchsorted(tau,t,side='right'));run=max(run,current_spectrum(tau,k,t))
 assert run<=2*full+1e-10
results['prefix_spectrum_checks']=1000
# 7. Reference class compared to a transparent traced version of frozen simulator.
source=inspect.getsource(simulate.py_func).split('\n',1)[1]
source=source.replace('def simulate(','def traced_simulate(',1)
source=source.replace('snapshots=np.zeros','actions=np.zeros(T,np.int64)\n    snapshots=np.zeros',1)
source=source.replace('x=rewards[a,n[a]]','actions[t-1]=a\n        x=rewards[a,n[a]]',1)
source=source.replace(',snapshots,n\n',',snapshots,n,actions\n')
ns=dict(engine.__dict__);exec(source,ns);trace=ns['traced_simulate']
matched=0
for scenario_no in [0,2,5,7]:
 sc=TEST[scenario_no];T=sc['T']
 data=streams(sc,930000+scenario_no);means=np.array(sc['means']);tau=np.array(sc['arrivals'],np.int64)
 out,snap,counts,actions=trace(data,means,tau,sc['epsilon'],sc['eta'],sc['delta'],T,7,13,2,.1,.5,1,True,True,True,sc['eta']/4,1030000+scenario_no,200,1.,1)
 alg=CertificateCostPlanner(sc['epsilon'],sc['eta'],sc['delta'],capacity=2)
 k=0
 for t in range(1,T+1):
  new=[]
  while k<len(means) and tau[k]==t:new.append(k);k+=1
  a,svc=alg.choose(new);assert a==actions[t-1],(scenario_no,t,a,actions[t-1])
  x=data[a,alg.n[a]];alg.observe(float(x));alg.report()
  assert alg.tax<=alg.spectrum_max+1e-9
  assert alg.n.sum()==t
  matched+=1
 assert np.array_equal(counts[:alg.k],alg.n[:alg.k])
 assert abs(out[8]-alg.tax)<1e-9 and out[3]==alg.services and out[9]==alg.denials
results['reference_class_matched_actions']=matched
# 8. Support boundary/singleton edge cases, unlimited service guarantee run.
for means,tau in [(np.array([1.,0.,.4]),np.array([1,2,3])),(np.array([0.]),np.array([1]))]:
 alg=CertificateCostPlanner(.2,.05,beta=None)
 k=0
 for t in range(1,1001):
  new=[]
  while k<len(means) and tau[k]==t:new.append(k);k+=1
  a,_=alg.choose(new);alg.observe(float(means[a]));P,N,V=alg.report()
  G={i for i in range(k) if max(means[:k])-means[i]<=.2}
  assert P<=G and not (N&G)
results['boundary_singleton_steps']=2000
results['seconds']=time.time()-start
results['note']='Internal diagnostics only; not formal proof or independent peer review. Floating-point intervals are outward-bisected within the tested numerical precision.'
(ROOT/'diagnostics-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))

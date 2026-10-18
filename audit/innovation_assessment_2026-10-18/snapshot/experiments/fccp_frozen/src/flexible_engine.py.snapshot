"""F-CCP research engine. Observations and control never receive evaluator truth.
All caches disabled: avoid stale cross-module Numba cache reuse.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit
from ccp_primitives import (kl, beta_mix_interval, labels_work, gap_bounds, pair_plan,
                           clipped_moss_indices, current_spectrum, kl_ucb_index, service_choice)

@njit(cache=False)
def seed_policy(seed):
    np.random.seed(seed)

@njit(cache=False)
def core_scores(n,S,k,t,base,segstart,core,temperature,prior):
    out=np.empty(k)
    if core==7:
        return clipped_moss_indices(n,S,k,t,base,segstart)
    for i in range(k):
        if core==3 or core==11 or core==12:
            local_temp=temperature
            if core==11 or core==12:
                warm=8. if core==11 else 32.
                local_temp=temperature+(1.-temperature)*min(1.,warm/max(1.,n[i]))
            # Exact fractional-count Beta TS when temperature=1 and prior=1.
            out[i]=np.random.beta(prior+S[i]/local_temp,
                                  prior+(n[i]-S[i])/local_temp)
        elif core==8:
            # Optimistic posterior sampling; development candidate, not standard TS.
            draw=np.random.beta(prior+S[i],prior+n[i]-S[i])
            out[i]=max(draw,(S[i]+prior)/(n[i]+2*prior))
        elif core==9:
            # Posterior draw clipped at one-sided KL index; development only.
            draw=np.random.beta(prior+S[i],prior+n[i]-S[i])
            out[i]=min(draw,kl_ucb_index(n[i],S[i],t))
        elif n[i]==0:
            out[i]=1e100
        elif core==0:
            out[i]=S[i]/n[i]+math.sqrt(3*math.log(2*t)/n[i])
        elif core==10:
            out[i]=S[i]/n[i]+math.sqrt(2*math.log(max(2,t))/n[i])
        elif core==4:
            out[i]=kl_ucb_index(n[i],S[i],t)
        else:
            clock=t if core==1 else t-segstart+1
            capacity=k if core==1 else max(2,2*base)
            out[i]=S[i]/n[i]+math.sqrt(max(0.,math.log(clock/(capacity*n[i])))/n[i])
    return out

@njit(cache=False)
def service_plan(n,S,l,u,k,eps,eta,work,q,idx,priority,price,scheduler):
    # scheduler 1 = strengthened ALL-epsilon widest-interval adaptation;
    # scheduler 13 = original CCP cost, 50 = priority-adjusted CCP cost.
    eligible=n[:k]<q[:k]
    if not np.any(eligible):return -1,0.
    if scheduler==1:
        ub=np.argmax(u[:k]);a=-1;best=-1.
        for i in range(k):
            if eligible[i] and (work[i] or i==ub):
                w=u[i]-l[i]
                if w>best+1e-14 or (abs(w-best)<=1e-14 and (a<0 or n[i]<n[a])):
                    a=i;best=w
        if a<0:
            for i in range(k):
                if eligible[i]:a=i;break
        return a,0.
    mid=np.empty(k);r=np.empty(k)
    for i in range(k):
        mid[i]=min(u[i],max(l[i],(S[i]+.5)/(n[i]+1)))
        r[i]=max(mid[i]-l[i],u[i]-mid[i])
    b=np.argmax(mid);top=np.max(idx);best=1e300;a=-1
    factor=1. if scheduler==13 else 1.-priority
    for i in range(k):
        if not work[i]:continue
        j=-1;mx=-1.
        for z in range(k):
            if z!=i and u[z]>mx:j=z;mx=u[z]
        if mid[b]-mid[i]>eps:j=b
        if j<0 or j==i:continue
        dd=abs(mid[j]-mid[i]-eps);h=.95*max(dd,eta-dd)
        ci=price+factor*(top-idx[i]);cj=price+factor*(top-idx[j])
        mi,mj,cost=pair_plan(n[i],n[j],r[i],r[j],ci,cj,h)
        ei=eligible[i] and mi>n[i]+1e-8;ej=eligible[j] and mj>n[j]+1e-8
        if not ei and not ej:continue
        zi=r[i]/(max(1.,n[i])*ci) if ei else -1.
        zj=r[j]/(max(1.,n[j])*cj) if ej else -1.
        z=i if zi>=zj else j
        if cost<best:best=cost;a=z
    if a<0:
        best=-1.
        for i in range(k):
            if eligible[i] and u[i]-l[i]>best:best=u[i]-l[i];a=i
    gap=max(0.,mid[b]-mid[a]) if a>=0 else 0.
    return a,gap

@njit(cache=False)
def control_rate(priority,adaptive,b,proposed_gap,eps,pfloor,k0):
    if b==0 or priority<=0.:return 0.
    if priority>=1.:return 1.
    if not adaptive:return priority
    pressure=pfloor+(1.-pfloor)*(b/(b+k0))*(eps/(eps+proposed_gap))
    return priority*pressure/(1.-priority+priority*pressure)

@njit(cache=False)
def choose_flexible(n,S,l,u,q,births,k,t,base,segstart,busy,phase,tax,smax,
                    failed,eps,eta,core,priority,adaptive,beta,price,pfloor,k0,
                    scheduler,temperature,prior,cap_mode):
    """Only observed state enters. cap_mode=0:none, 1:max fallback, 2:score projection."""
    if k>1 and (base==0 or k-1>=2*base):base=k-1;segstart=t
    idx=clipped_moss_indices(n,S,k,t,base,segstart)
    b=0;sa=-1;pg=0.;rate=0.;attempt=False
    if not failed and priority>0.:
        lab,work,gl,gu=labels_work(l,u,k,eps,eta,True,True)
        b=np.sum(work)
        if b>0:
            busy+=1
            sa,pg=service_plan(n,S,l,u,k,eps,eta,work,q,idx,priority,price,scheduler)
            rate=control_rate(priority,adaptive,b,pg,eps,pfloor,k0)
            phase+=rate
            if phase>=1.:
                phase-=1.;attempt=True
    service=attempt and sa>=0
    scores=np.zeros(k)
    if service:a=sa
    else:
        scores=core_scores(n,S,k,t,base,segstart,core,temperature,prior)
        a=np.argmax(scores)
    top=np.max(idx);z=max(0.,top-idx[a])
    denial=False;coremod=False
    if cap_mode>0:
        smax=max(smax,current_spectrum(births,k,t))
        limit=beta*smax
        if tax+z>limit+1e-12:
            denial=service;coremod=not service
            if cap_mode==1:a=np.argmax(idx)
            else:
                if service:scores=core_scores(n,S,k,t,base,segstart,core,temperature,prior)
                best=-1e300;a=np.argmax(idx)
                for i in range(k):
                    if tax+max(0.,top-idx[i])<=limit+1e-12 and scores[i]>best:
                        best=scores[i];a=i
            service=False;z=max(0.,top-idx[a])
    tax+=z
    return a,service,attempt,denial,coremod,base,segstart,busy,phase,tax,smax,rate

@njit(cache=False)
def update_interval(n,S,l,u,q,a,eta,delta,failed):
    if failed:return failed
    lo,up=beta_mix_interval(n[a],S[a],delta/(2*(a+1)*(a+2)))
    l[a]=max(l[a],lo);u[a]=min(u[a],up)
    if n[a]==q[a]:
        rho=eta/4
        l[a]=max(l[a],S[a]/n[a]-rho/2,0.)
        u[a]=min(u[a],S[a]/n[a]+rho/2,1.)
    return l[a]>u[a]

@njit(cache=False)
def simulate_flexible(rewards,means,arrivals,eps,eta,delta,T,
                      core,priority,adaptive,beta,price,pfloor,k0,
                      scheduler,temperature,prior,cap_mode,seed,stride=200):
    # Evaluator reads truth only AFTER action selection. Never sends it to policy.
    np.random.seed(seed)
    K=len(means);n=np.zeros(K,np.int64);S=np.zeros(K)
    l=np.zeros(K);u=np.ones(K);q=np.empty(K,np.int64)
    rho=eta/4
    for i in range(K):q[i]=math.ceil(2/rho**2*math.log(4*(i+1)*(i+2)/delta))
    k=0;base=0;segstart=1;busy=0;phase=0.;tax=0.;smax=0.;failed=False
    reg=0.;area=0;services=0;attempts=0;denials=0;mods=0;sr=0.;lf=False;cf=False
    mass=0.;rr=0.;work_rounds=0
    paths=np.zeros((T//stride+1,8))
    for t in range(1,T+1):
        while k<K and arrivals[k]<=t:k+=1
        a,service,attempt,d,mod,base,segstart,busy,phase,tax,smax,rate=choose_flexible(
            n,S,l,u,q,arrivals,k,t,base,segstart,busy,phase,tax,smax,failed,eps,eta,
            core,priority,adaptive,beta,price,pfloor,k0,scheduler,temperature,prior,cap_mode)
        services+=service;attempts+=attempt;denials+=d;mods+=mod;mass+=rate
        if rate>0:work_rounds+=1
        x=rewards[a,n[a]];n[a]+=1;S[a]+=x
        failed=update_interval(n,S,l,u,q,a,eta,delta,failed)
        if failed:lab=np.zeros(k,np.int64)
        else:lab,_,_,_=labels_work(l,u,k,eps,eta,True,True)
        B=np.max(means[:k]);cost=B-means[a];reg+=cost
        if service:sr+=cost
        unresolved=0;unresolved_all=0
        for i in range(k):
            gap=B-means[i]
            if (lab[i]==1 and gap>eps+1e-12) or (lab[i]==-1 and gap<=eps+1e-12):lf=True
            if lab[i]==0:
                unresolved_all+=1
                if abs(gap-eps)>eta+1e-12:unresolved+=1
            if means[i]<l[i]-1e-10 or means[i]>u[i]+1e-10:cf=True
        area+=unresolved
        if t%stride==0:
            paths[t//stride]=np.array([float(t),reg,float(area),float(unresolved),float(services),tax,mass,float(unresolved_all)])
    out=np.array([reg,float(area),float(unresolved),float(services),sr,(1. if lf else 0.),(1. if cf else 0.),(1. if failed else 0.),tax,float(denials),float(mods),mass,float(attempts),float(work_rounds),float(unresolved_all)])
    return out,paths,n

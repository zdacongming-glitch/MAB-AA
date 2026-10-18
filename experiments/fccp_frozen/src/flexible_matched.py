"""F-CCP two-budget controller. Uses unchanged verified CCP primitives.
The service ledger cannot be consumed by reward-core exploration.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit
from ccp_primitives import beta_mix_interval,labels_work,clipped_moss_indices,current_spectrum
from flexible_engine import core_scores,control_rate,update_interval
from matched_all import service_plan_matched

@njit(cache=False)
def choose_dual(n,S,l,u,q,births,k,t,base,segstart,busy,phase,rtax,stax,smax,
                failed,eps,eta,core,priority,adaptive,beta_r,beta_s,price,pfloor,k0,
                scheduler,temperature,prior):
    if k>1 and (base==0 or k-1>=2*base):base=k-1;segstart=t
    idx=clipped_moss_indices(n,S,k,t,base,segstart)
    top=np.max(idx)
    smax=max(smax,current_spectrum(births,k,t))
    b=0;sa=-1;pg=0.;rate=0.;attempt=False;denial=False;mod=False
    if not failed and priority>0.:
        lab,work,gl,gu=labels_work(l,u,k,eps,eta,True,True)
        b=np.sum(work)
        if b>0:
            busy+=1
            sa,pg=service_plan_matched(n,S,l,u,k,eps,eta,work,q,idx,priority,price,scheduler)
            rate=control_rate(priority,adaptive,b,pg,eps,pfloor,k0)
            phase+=rate
            if phase>=1.:phase-=1.;attempt=True
    service=attempt and sa>=0
    if service:
        z=max(0.,top-idx[sa])
        if beta_s<1e90 and stax+z>beta_s*smax+1e-12:
            service=False;denial=True
    if service:
        a=sa;stax+=max(0.,top-idx[a])
    else:
        scores=core_scores(n,S,k,t,base,segstart,core,temperature,prior)
        a=np.argmax(scores)
        z=max(0.,top-idx[a])
        if beta_r<1e90 and rtax+z>beta_r*smax+1e-12:
            mod=True;best=-1e300;a=np.argmax(idx)
            for i in range(k):
                if rtax+max(0.,top-idx[i])<=beta_r*smax+1e-12 and scores[i]>best:
                    best=scores[i];a=i
        rtax+=max(0.,top-idx[a])
    return a,service,attempt,denial,mod,base,segstart,busy,phase,rtax,stax,smax,rate

@njit(cache=False)
def simulate_dual(rewards,means,arrivals,eps,eta,delta,T,
                  core,priority,adaptive,beta_r,beta_s,price,pfloor,k0,
                  scheduler,temperature,prior,seed,stride=200):
    np.random.seed(seed)
    K=len(means);n=np.zeros(K,np.int64);S=np.zeros(K);l=np.zeros(K);u=np.ones(K)
    q=np.empty(K,np.int64);rho=eta/4
    for i in range(K):q[i]=math.ceil(2/rho**2*math.log(4*(i+1)*(i+2)/delta))
    k=0;base=0;segstart=1;busy=0;phase=0.;rtax=0.;stax=0.;smax=0.;failed=False
    reg=0.;area=0;services=0;attempts=0;denials=0;mods=0;sr=0.;lf=False;cf=False;mass=0.;work_rounds=0
    paths=np.zeros((T//stride+1,10))
    for t in range(1,T+1):
        while k<K and arrivals[k]<=t:k+=1
        a,service,attempt,d,mod,base,segstart,busy,phase,rtax,stax,smax,rate=choose_dual(
            n,S,l,u,q,arrivals,k,t,base,segstart,busy,phase,rtax,stax,smax,failed,eps,eta,
            core,priority,adaptive,beta_r,beta_s,price,pfloor,k0,scheduler,temperature,prior)
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
            paths[t//stride]=np.array([float(t),reg,float(area),float(unresolved),float(services),rtax,stax,mass,rate,smax])
    out=np.array([reg,float(area),float(unresolved),float(services),sr,(1. if lf else 0.),(1. if cf else 0.),(1. if failed else 0.),rtax+stax,float(denials),float(mods),mass,float(attempts),float(work_rounds),float(unresolved_all),rtax,stax,smax])
    return out,paths,n

"""Certificate-Cost Planning (CCP): causal research reference implementation.

Requires numpy, numba and engine.py from this bundle. No future schedule, endpoint,
true mean or candidate-best identity is accepted by the policy API.

beta=1.0 is the tested regret-budgeted configuration; beta=None disables that budget
and has the finite-work maintenance guarantee. Those guarantees must not be conflated.
"""
from __future__ import annotations
import math
from typing import Iterable
import numpy as np
from engine import beta_mix_interval, labels_work, clipped_moss_indices, service_choice

class CertificateCostPlanner:
    def __init__(self, epsilon: float, eta: float, delta: float=.05,
                 beta: float | None=1., time_price: float=.1, period: int=2,
                 capacity: int=16):
        if not (0<epsilon<1 and 0<eta<1 and 0<delta<.5):
            raise ValueError('epsilon, eta in (0,1); delta in (0,.5)')
        if beta is not None and not (math.isfinite(beta) and beta>0):
            raise ValueError('beta must be positive finite, or None')
        if not (math.isfinite(time_price) and time_price>0):
            raise ValueError('time_price must be positive finite')
        if not isinstance(period,int) or period<1: raise ValueError('period must be a positive integer')
        self.epsilon=epsilon;self.eta=eta;self.delta=delta;self.beta=beta
        self.time_price=time_price;self.period=period;self.rho=eta/4
        self.k=0;self.time=0;self.base=0;self.segstart=1;self.busy=0
        self.services=0;self.denials=0;self.tax=0.;self.spectrum_max=0.
        self.report_failure=False;self._awaiting=None;self.labels=[];self._label_set=set()
        cap=max(1,int(capacity))
        self.n=np.zeros(cap,np.int64);self.S=np.zeros(cap);self.l=np.zeros(cap);self.u=np.ones(cap)
        self.q=np.zeros(cap,np.int64);self.births=np.zeros(cap,np.int64)

    def _extend(self, needed: int):
        if needed<=len(self.n): return
        new=max(needed,2*len(self.n))
        for name,fill in [('n',0),('S',0.),('l',0.),('u',1.),('q',0),('births',0)]:
            a=getattr(self,name);b=np.full(new,fill,dtype=a.dtype);b[:len(a)]=a;setattr(self,name,b)

    def _spectrum(self)->float:
        bins={}
        for i in range(1,self.k):
            age=self.time-int(self.births[i])+1
            level=(age-1).bit_length();bins[level]=bins.get(level,0)+1
        return sum(min(float(2**l),math.sqrt(m*float(2**l))) for l,m in sorted(bins.items()))

    def choose(self,new_arms: Iterable[str | int]=())->tuple[str | int,bool]:
        if self._awaiting is not None: raise RuntimeError('Call observe before choose again')
        new=list(new_arms)
        if len(set(new))!=len(new) or any(x in self._label_set for x in new):
            raise ValueError('Arriving labels must be new and unique')
        if self.k+len(new)==0: raise ValueError('At least one arm must be available')
        self.time+=1;self._extend(self.k+len(new))
        for label in new:
            i=self.k;self.k+=1;self.labels.append(label);self._label_set.add(label)
            self.births[i]=self.time
            q=math.ceil(2/self.rho**2*math.log(4*(i+1)*(i+2)/self.delta))
            if q>np.iinfo(np.int64).max: raise OverflowError('Checkpoint quota exceeds int64 implementation range')
            self.q[i]=q
        k=self.k;t=self.time
        if k>1 and (self.base==0 or k-1>=2*self.base): self.base=k-1;self.segstart=t
        lab,work,_,_=labels_work(self.l,self.u,k,self.epsilon,self.eta,True,True)
        a=-1;service=False
        if np.any(work) and not self.report_failure:
            self.busy+=1
            if self.busy%self.period==0:
                a=int(service_choice(self.n,self.S,self.l,self.u,k,self.epsilon,self.eta,work,self.q,
                                     13,self.time_price,self.services,True,t,self.base,self.segstart))
                service=a>=0
        idx=clipped_moss_indices(self.n,self.S,k,t,self.base,self.segstart)
        if not service: a=int(np.argmax(idx))
        self.spectrum_max=max(self.spectrum_max,self._spectrum())
        z=max(0.,float(np.max(idx)-idx[a]))
        if self.beta is not None and self.tax+z>self.beta*self.spectrum_max:
            if service: self.denials+=1
            service=False;a=int(np.argmax(idx));z=0.
        self.tax+=z
        if service:self.services+=1
        self._awaiting=a
        return self.labels[a],service

    def observe(self,reward: float)->None:
        if self._awaiting is None: raise RuntimeError('choose is required before observe')
        if not (math.isfinite(reward) and 0<=reward<=1):raise ValueError('Reward must be finite in [0,1]')
        i=self._awaiting;self._awaiting=None
        self.n[i]+=1;self.S[i]+=reward
        if self.report_failure:return
        lo,up=beta_mix_interval(self.n[i],self.S[i],self.delta/(2*(i+1)*(i+2)))
        self.l[i]=max(self.l[i],lo);self.u[i]=min(self.u[i],up)
        if self.n[i]==self.q[i]:
            self.l[i]=max(self.l[i],self.S[i]/self.n[i]-self.rho/2,0.)
            self.u[i]=min(self.u[i],self.S[i]/self.n[i]+self.rho/2,1.)
        if self.l[i]>self.u[i]:self.report_failure=True

    def report(self)->tuple[set,set,set]:
        if self._awaiting is not None:raise RuntimeError('Formal reports follow observation')
        if self.k==0:return set(),set(),set()
        if self.report_failure:return set(),set(),set(self.labels)
        lab,_,_,_=labels_work(self.l,self.u,self.k,self.epsilon,self.eta,True,True)
        return ({self.labels[i] for i in range(self.k) if lab[i]==1},
                {self.labels[i] for i in range(self.k) if lab[i]==-1},
                {self.labels[i] for i in range(self.k) if lab[i]==0})

    def state(self)->dict:
        return dict(time=self.time,arms=self.k,tax=self.tax,spectrum_max=self.spectrum_max,
                    services=self.services,denials=self.denials,report_failure=self.report_failure)

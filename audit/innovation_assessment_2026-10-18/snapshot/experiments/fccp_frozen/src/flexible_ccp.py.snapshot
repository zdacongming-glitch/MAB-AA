"""Interactive F-CCP: tunable reward/maintenance preferences and two budgets.

Requirements: numpy, numba; ccp_primitives.py and flexible_engine.py from this bundle.
The interactive class owns its numpy Generator. It is independent of other instances.
The batch experiments use Numba's RNG: identical distributions, not bit-identical
random streams across backends. Same-core compatibility is pathwise within a backend.
No future arrivals, horizon, true means, or hidden labels are accepted by this API.
"""
from __future__ import annotations
from typing import Iterable
import math
import numpy as np
from ccp_primitives import (beta_mix_interval, labels_work, clipped_moss_indices,
                            current_spectrum, kl_ucb_index)
from flexible_engine import control_rate
from matched_all import service_plan_matched

CORES={'ucb1':10,'ucb':0,'growing_moss':1,'mc_moss':2,'mc_moss_clipped':7,'thompson':3,'kl_ucb':4,'warm_thompson':11}

def reward_scores(n:np.ndarray,S:np.ndarray,k:int,t:int,base:int,segstart:int,
                  core:str,temperature:float,prior:float,rng:np.random.Generator)->np.ndarray:
    """Independent reference implementation, using only revealed sample statistics."""
    if core=='mc_moss_clipped':
        return clipped_moss_indices(n,S,k,t,base,segstart)
    out=np.empty(k)
    for i in range(k):
        if core in ('thompson','warm_thompson'):
            temp=temperature
            if core=='warm_thompson':temp=temperature+(1-temperature)*min(1.,8/max(1,int(n[i])))
            out[i]=rng.beta(prior+S[i]/temp,prior+(n[i]-S[i])/temp)
        elif n[i]==0:out[i]=math.inf
        elif core=='ucb1':out[i]=S[i]/n[i]+math.sqrt(2*math.log(max(2,t))/n[i])
        elif core=='ucb':out[i]=S[i]/n[i]+math.sqrt(3*math.log(2*t)/n[i])
        elif core=='kl_ucb':out[i]=kl_ucb_index(n[i],S[i],t)
        else:
            clock=t if core=='growing_moss' else t-segstart+1
            cap=k if core=='growing_moss' else max(2,2*base)
            out[i]=S[i]/n[i]+math.sqrt(max(0.,math.log(clock/(cap*n[i])))/n[i])
    return out

class FlexibleCCP:
    """One actual pull per choose/observe pair; reports use the resulting history.

    priority: 0 = reward only, 1 = service on every busy round.
    adaptive: backlog/cost-based reduction of interior priority values.
    reward_budget, service_budget: nonnegative coefficient of running spectrum;
        None disables the corresponding guard. These are optimism-gap budgets,
        NOT realized regret relative to an independently run baseline.
    temperature: affects Thompson action scores only; confidence evidence is never
        powered or duplicated. Set 1 for standard Beta(1,1) Thompson sampling.
    """
    def __init__(self,epsilon:float,eta:float,delta:float=.05,priority:float=.6,
                 adaptive:bool=True,base:str='thompson',temperature:float=.5,
                 reward_budget:float|None=16.,service_budget:float|None=1.,
                 price:float=.1,pressure_floor:float=.02,backlog_scale:float=4.,
                 seed:int=0,scheduler:str='ccp'):
        if not (0<epsilon<1 and 0<eta<1 and 0<delta<.5):raise ValueError('epsilon/eta in (0,1), delta in (0,.5)')
        if not (math.isfinite(priority) and 0<=priority<=1):raise ValueError('priority must be in [0,1]')
        if base not in CORES:raise ValueError(f'base must be one of {tuple(CORES)}')
        if not (math.isfinite(temperature) and temperature>0):raise ValueError('temperature must be positive')
        for v in [reward_budget,service_budget]:
            if v is not None and not (math.isfinite(v) and v>=0):raise ValueError('budgets must be nonnegative finite or None')
        if not (all(math.isfinite(v) for v in [pressure_floor,backlog_scale,price]) and 0<pressure_floor<=1 and backlog_scale>0 and price>0):raise ValueError('invalid service parameters')
        if scheduler not in ('ccp','all_epsilon'):raise ValueError('scheduler must be ccp or all_epsilon')
        self.epsilon=epsilon;self.eta=eta;self.delta=delta;self.priority=priority;self.adaptive=adaptive
        self.core=base;self.temperature=temperature;self.reward_budget=reward_budget;self.service_budget=service_budget
        self.price=price;self.pressure_floor=pressure_floor;self.backlog_scale=backlog_scale
        self.scheduler=50 if scheduler=='ccp' else 1;self.rng=np.random.default_rng(seed)
        self.labels=[];self.seen=set();self.n=np.zeros(0,np.int64);self.S=np.zeros(0)
        self.l=np.zeros(0);self.u=np.ones(0);self.q=np.zeros(0,np.int64);self.births=np.zeros(0,np.int64)
        self.time=0;self.basecount=0;self.segstart=1;self.phase=0.;self.busy=0
        self.reward_tax=0.;self.service_tax=0.;self.spectrum_max=0.;self.services=0;self.denials=0;self.projections=0
        self.last_rate=0.;self.last_service=False;self.last_proposal=None;self.failed=False;self._pending=None

    @classmethod
    def preset(cls,mode:str,epsilon:float,eta:float,**kwargs):
        modes={
          'reward':dict(priority=0.,adaptive=False,temperature=.5,reward_budget=16.,service_budget=0.),
          'balanced':dict(priority=.6,adaptive=True,temperature=.5,reward_budget=16.,service_budget=1.),
          'classification':dict(priority=1.,adaptive=False,temperature=.5,reward_budget=16.,service_budget=None),
          'compatibility':dict(priority=0.,adaptive=False,temperature=1.,reward_budget=None,service_budget=0.),
        }
        if mode not in modes:raise ValueError(f'unknown mode {mode}')
        settings=modes[mode]|kwargs
        return cls(epsilon,eta,**settings)

    def set_priority(self,value:float)->None:
        if self._pending is not None:raise RuntimeError('change preference between physical rounds, after observe')
        if not (math.isfinite(value) and 0<=value<=1):raise ValueError('priority must belong to [0,1]')
        self.priority=value
        # Deliberately do not reset phase, counters, report evidence or either ledger.

    def choose(self,new_arms:Iterable[str|int]=())->tuple[str|int,bool]:
        if self._pending is not None:raise RuntimeError('observe the pending action before choosing again')
        new=list(new_arms)
        if len(set(new))!=len(new) or any(i in self.seen for i in new):raise ValueError('new arm labels must be unique')
        if not self.labels and not new:raise ValueError('at least one arm must be present')
        t=self.time+1
        newq=[]
        for j in range(len(new)):
            rank=len(self.labels)+j+1
            qq=math.ceil(32/self.eta**2*math.log(4*rank*(rank+1)/self.delta))
            if qq>np.iinfo(np.int64).max:raise OverflowError('checkpoint quota exceeds int64 implementation')
            newq.append(qq)
        self.time=t
        for attr,vals in [('n',np.zeros(len(new),np.int64)),('S',np.zeros(len(new))),('l',np.zeros(len(new))),('u',np.ones(len(new))),('q',np.array(newq,np.int64)),('births',np.full(len(new),t,np.int64))]:
            setattr(self,attr,np.concatenate((getattr(self,attr),vals)))
        self.labels.extend(new);self.seen.update(new);k=len(self.labels)
        if k>1 and (self.basecount==0 or k-1>=2*self.basecount):self.basecount=k-1;self.segstart=t
        idx=clipped_moss_indices(self.n,self.S,k,t,self.basecount,self.segstart);top=float(max(idx))
        self.spectrum_max=max(self.spectrum_max,float(current_spectrum(self.births,k,t)))
        sa=-1;attempt=False;rate=0.
        if not self.failed and self.priority>0:
            _,work,_,_=labels_work(self.l,self.u,k,self.epsilon,self.eta,True,True)
            if np.any(work):
                self.busy+=1
                sa,gap=service_plan_matched(self.n,self.S,self.l,self.u,k,self.epsilon,self.eta,work,self.q,idx,self.priority,self.price,self.scheduler)
                rate=float(control_rate(self.priority,self.adaptive,int(sum(work)),gap,self.epsilon,self.pressure_floor,self.backlog_scale))
                self.phase+=rate
                if self.phase>=1.:self.phase-=1.;attempt=True
        service=bool(attempt and sa>=0)
        if service and self.service_budget is not None and self.service_tax+top-idx[sa]>self.service_budget*self.spectrum_max+1e-12:
            self.denials+=1;service=False
        if service:
            a=int(sa);self.service_tax+=max(0.,top-float(idx[a]));self.services+=1
        else:
            scores=reward_scores(self.n,self.S,k,t,self.basecount,self.segstart,self.core,self.temperature,1.,self.rng)
            a=int(np.argmax(scores))
            if self.reward_budget is not None:
                feasible=self.reward_tax+np.maximum(0.,top-idx)<=self.reward_budget*self.spectrum_max+1e-12
                if not feasible[a]:
                    self.projections+=1
                    a=int(np.argmax(np.where(feasible,scores,-np.inf)))
            self.reward_tax+=max(0.,top-float(idx[a]))
        self._pending=a;self.last_rate=rate;self.last_service=service;self.last_proposal=self.labels[sa] if sa>=0 else None
        return self.labels[a],service

    def observe(self,reward:float)->None:
        if self._pending is None:raise RuntimeError('choose an action before observe')
        if not (math.isfinite(reward) and 0<=reward<=1):raise ValueError('reward must be finite in [0,1]')
        i=self._pending;self._pending=None;self.n[i]+=1;self.S[i]+=reward
        if self.failed:return
        lo,up=beta_mix_interval(int(self.n[i]),self.S[i],self.delta/(2*(i+1)*(i+2)))
        self.l[i]=max(self.l[i],lo);self.u[i]=min(self.u[i],up)
        if self.n[i]==self.q[i]:
            self.l[i]=max(self.l[i],self.S[i]/self.n[i]-self.eta/8,0.)
            self.u[i]=min(self.u[i],self.S[i]/self.n[i]+self.eta/8,1.)
        if self.l[i]>self.u[i]:self.failed=True

    def report(self)->tuple[set,set,set]:
        if self._pending is not None:raise RuntimeError('formal reports follow the observation')
        if not self.labels:return set(),set(),set()
        if self.failed:return set(),set(),set(self.labels)
        lab,_,_,_=labels_work(self.l,self.u,len(self.labels),self.epsilon,self.eta,True,True)
        return ({x for i,x in enumerate(self.labels) if lab[i]==1},{x for i,x in enumerate(self.labels) if lab[i]==-1},{x for i,x in enumerate(self.labels) if lab[i]==0})

    def diagnostics(self)->dict:
        return dict(time=self.time,arms=len(self.labels),priority=self.priority,last_service_rate=self.last_rate,
          service_pulls=self.services,service_denials=self.denials,reward_projections=self.projections,
          reward_tax=self.reward_tax,service_tax=self.service_tax,spectrum_max=self.spectrum_max,
          phase=self.phase,report_failure=self.failed,total_actual_pulls=int(self.n.sum()))

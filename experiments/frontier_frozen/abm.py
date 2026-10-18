"""Activation-Budgeted Maintenance (ABM), reference implementation.

This is the theoretical two-resolution construction, NOT the empirically tested
CCP-shared scheduler. Inputs do not include means, horizon or future arrivals.
Coarse lifetime evidence is retained. Each activated fine task uses a predictable
fresh observation block, with confidence allocated by activation rank.
Python 3.10+, standard library only.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterable
import math

@dataclass
class Arm:
    label: int
    batch: int
    quota: int
    n: int = 0
    total: float = 0.0
    lo: float = 0.0
    hi: float = 1.0
    coarse_mean: float | None = None
    fine_rank: int = 0
    fine_quota: int = 0
    fine_start_n: int = 0
    fine_n: int = 0
    fine_sum: float = 0.0

class ActivationBudgetedMaintenance:
    def __init__(self, epsilon: float, delta: float, coarse_precision: float,
                 fine_precision: float, fine_candidates: int):
        for name,x in [('epsilon',epsilon),('delta',delta),
                       ('coarse_precision',coarse_precision),('fine_precision',fine_precision)]:
            if not isinstance(x,(int,float)) or not math.isfinite(x) or not 0<x<1:
                raise ValueError(f'{name} must belong to (0,1)')
        if not isinstance(fine_candidates,int) or isinstance(fine_candidates,bool) or fine_candidates<0:
            raise ValueError('fine_candidates must be a nonnegative integer')
        self.epsilon=epsilon;self.delta=delta
        self.coarse_precision=coarse_precision;self.fine_precision=fine_precision
        self.remaining=fine_candidates;self.initial_fine_budget=fine_candidates
        self.arms:dict[int,Arm]={};self.batches:list[list[int]]=[];self.activated:set[int]=set()
        self.coarse=deque();self.fine=deque();self.rank=0;self.time=0;self.awaiting=None
        self.report_failure=False;self.designated_pulls=0;self.last_service='reward'

    def _quota(self, rank:int, rho:float)->int:
        return math.ceil(2/rho**2*math.log(4*rank*(rank+1)/self.delta))

    def choose(self, new_labels:Iterable[int]=())->int:
        if self.awaiting is not None:raise RuntimeError('observe() required before choose()')
        ids=list(new_labels)
        if ids!=list(range(len(self.arms)+1,len(self.arms)+1+len(ids))):
            raise ValueError('Labels must be consecutive positive integers in arrival order')
        if not self.arms and not ids:raise ValueError('At least one arm must be available')
        self.time+=1
        if ids:
            b=len(self.batches);self.batches.append(ids)
            for i in ids:
                self.arms[i]=Arm(i,b,self._quota(i,self.coarse_precision));self.coarse.append(i)
        while self.coarse and self.arms[self.coarse[0]].n>=self.arms[self.coarse[0]].quota:
            self.coarse.popleft()
        while self.fine and self.arms[self.fine[0]].fine_n>=self.arms[self.fine[0]].fine_quota:
            self.fine.popleft()
        self.last_service='reward'
        if self.time%2==0 and self.coarse:
            i=self.coarse[0];self.last_service='coarse';self.designated_pulls+=1
        elif self.time%2==0 and self.fine:
            i=self.fine[0];self.last_service='fine';self.designated_pulls+=1
        else:
            def index(i:int)->float:
                a=self.arms[i]
                return math.inf if a.n==0 else a.total/a.n+math.sqrt(3*math.log(2*self.time)/a.n)
            i=max(self.arms,key=lambda i:(index(i),-i))
        self.awaiting=i
        return i

    def _activate_completed_batch(self,b:int)->None:
        if b in self.activated:return
        ids=self.batches[b]
        if not all(self.arms[i].coarse_mean is not None for i in ids):return
        self.activated.add(b)
        # The role is inferred from observed coarse data, never provided by the simulator.
        ref=max(ids,key=lambda i:(self.arms[i].coarse_mean,-i))
        selected=[i for i in ids if i!=ref][:self.remaining]
        self.remaining-=len(selected)
        if not selected:return
        for i in [ref]+selected:
            a=self.arms[i]
            if a.fine_rank:raise AssertionError('Each arm belongs to one birth batch')
            self.rank+=1;a.fine_rank=self.rank
            a.fine_quota=self._quota(self.rank,self.fine_precision)
            a.fine_start_n=a.n;a.fine_n=0;a.fine_sum=0.
            self.fine.append(i)
        if self.rank>2*self.initial_fine_budget:raise AssertionError('Activation budget exceeded')

    def observe(self,reward:float)->None:
        if self.awaiting is None:raise RuntimeError('choose() must precede observe()')
        if not math.isfinite(reward) or not 0<=reward<=1:raise ValueError('Reward must be in [0,1]')
        a=self.arms[self.awaiting];a.n+=1;a.total+=reward
        # Only tasks active BEFORE this observation receive this fresh-block sample.
        if a.fine_rank and a.fine_n<a.fine_quota:
            a.fine_n+=1;a.fine_sum+=reward
            if a.fine_n==a.fine_quota:
                mean=a.fine_sum/a.fine_n;r=self.fine_precision/2
                a.lo=max(a.lo,mean-r,0.);a.hi=min(a.hi,mean+r,1.)
        if a.n==a.quota:
            a.coarse_mean=a.total/a.n;r=self.coarse_precision/2
            a.lo=max(a.lo,a.coarse_mean-r,0.);a.hi=min(a.hi,a.coarse_mean+r,1.)
        if a.lo>a.hi:self.report_failure=True
        self._activate_completed_batch(a.batch)
        self.awaiting=None

    def report(self)->tuple[set[int],set[int],set[int]]:
        if self.awaiting is not None:raise RuntimeError('Reports follow observation')
        A=set(self.arms)
        if not A:return set(),set(),set()
        if self.report_failure:return set(),set(),A
        L=max(a.lo for a in self.arms.values());U=max(a.hi for a in self.arms.values())
        P={i for i,a in self.arms.items() if a.lo>=U-self.epsilon}
        N={i for i,a in self.arms.items() if a.hi<L-self.epsilon}
        if P&N:raise AssertionError('Nonempty intervals require disjoint reports')
        return P,N,A-P-N

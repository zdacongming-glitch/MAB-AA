#!/usr/bin/env python3
"""CP-UCB-AA: lifetime checkpoint certification + full-history UCB.

No horizon, future arrivals, true means, or best-arm labels enter the policy.
The optional command-line run is a single implementation sanity check, NOT
an empirical comparison or a validation of theorem-level probabilities.
Python >=3.10, standard library only.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Iterable
import argparse
import json
import math
from pathlib import Path
import random


@dataclass
class ArmState:
    label: int
    born: int
    precision: float
    quota: int
    count: int = 0
    reward_sum: float = 0.0
    lower: float = 0.0
    upper: float = 1.0


class CheckpointUCBAA:
    def __init__(self, epsilon: float, delta: float, precision: float):
        if not (0 < epsilon < 1 and 0 < delta < 1 and 0 < precision < 1):
            raise ValueError('epsilon, delta and precision must belong to (0,1)')
        self.epsilon=epsilon; self.delta=delta; self.precision=precision
        self.arms: dict[int,ArmState]={}
        self.pending: deque[int]=deque()
        self.time=0
        self._awaiting: int | None=None
        self.identification_pulls=0

    def choose(self, new_arm_labels: Iterable[int] = ()) -> tuple[int,bool]:
        """Start next physical round; accept arrivals, then choose one arm.

        New labels must be consecutive positive integers in arrival order.
        Calls must alternate choose()/observe(). Rewards are not available here.
        """
        if self._awaiting is not None:
            raise RuntimeError('observe() is required before the next choose()')
        labels=list(new_arm_labels)
        expected=list(range(len(self.arms)+1,len(self.arms)+1+len(labels)))
        if labels!=expected:
            raise ValueError('new labels must be consecutive, in arrival order')
        if not self.arms and not labels:
            raise ValueError('At least one arm must be available')
        self.time+=1
        for i in labels:
            q=math.ceil(2/self.precision**2*math.log(4*i*(i+1)/self.delta))
            self.arms[i]=ArmState(i,self.time,self.precision,q)
            self.pending.append(i)
        while self.pending and self.arms[self.pending[0]].count>=self.arms[self.pending[0]].quota:
            self.pending.popleft()
        service=(self.time%2==0 and bool(self.pending))
        if service:
            label=self.pending[0]; self.identification_pulls+=1
        else:
            def index(i: int) -> float:
                a=self.arms[i]
                if a.count==0: return math.inf
                return a.reward_sum/a.count+math.sqrt(3*math.log(2*self.time)/a.count)
            label=max(self.arms,key=lambda i:(index(i),-i))
        self._awaiting=label
        return label,service

    def observe(self, reward: float) -> None:
        if self._awaiting is None:
            raise RuntimeError('choose() must precede observe()')
        if not (math.isfinite(reward) and 0<=reward<=1):
            raise ValueError('reward must be a finite number in [0,1]')
        a=self.arms[self._awaiting]
        a.count+=1; a.reward_sum+=reward
        if a.count==a.quota:
            estimate=a.reward_sum/a.count
            a.lower=max(0.,estimate-a.precision/2)
            a.upper=min(1.,estimate+a.precision/2)
        self._awaiting=None

    def report(self) -> tuple[set[int],set[int],set[int]]:
        if self._awaiting is not None:
            raise RuntimeError('The formal report is after observation')
        if not self.arms: return set(),set(),set()
        L=max(a.lower for a in self.arms.values())
        U=max(a.upper for a in self.arms.values())
        C={i for i,a in self.arms.items() if a.lower>=U-self.epsilon}
        D={i for i,a in self.arms.items() if a.upper<L-self.epsilon}
        if C&D: raise AssertionError('Nonempty checkpoint intervals imply disjoint labels')
        return C,D,set(self.arms)-C-D


def sanity_run(seed: int=20261014, horizon: int=20000) -> dict:
    rng=random.Random(seed)
    arrivals={1:[.50,.22],6001:[.70,.40],12001:[.90,.60]}
    alg=CheckpointUCBAA(epsilon=.30,delta=.05,precision=.12)
    means: dict[int,float]={}; regret=0.; area=0; label_errors=0; snapshots=[]
    old_D=set(); eta=.10
    for t in range(1,horizon+1):
        new=[]
        for mu in arrivals.get(t,[]):
            i=len(means)+1; means[i]=mu; new.append(i)
        i,service=alg.choose(new)
        alg.observe(float(rng.random()<means[i]))
        C,D,V=alg.report(); B=max(means.values())
        # Tolerance is used only to evaluate simulation truth near decimal ties.
        G={j for j,mu in means.items() if B-mu<=alg.epsilon+1e-12}
        if not C<=G or D&G: label_errors+=1
        assert old_D<=D
        old_D=D.copy()
        regret+=B-means[i]
        area+=sum(abs(B-means[j]-alg.epsilon)>eta+1e-12 for j in V)
        if t in {1,6000,6001,12000,12001,horizon}:
            snapshots.append(dict(t=t,C=sorted(C),D=sorted(D),V=sorted(V)))
    assert sum(a.count for a in alg.arms.values())==horizon
    assert alg.identification_pulls<=sum(a.quota for a in alg.arms.values())
    return dict(kind='single-run implementation sanity check',seed=seed,T=horizon,
                epsilon=alg.epsilon,delta=alg.delta,precision=alg.precision,eta=eta,
                pseudo_regret=regret,unresolved_area=area,observed_label_error_rounds=label_errors,
                fixed_checkpoint_intervals_cover=[a.lower<=means[i]<=a.upper for i,a in alg.arms.items()],
                final_counts={i:a.count for i,a in alg.arms.items()},
                quotas={i:a.quota for i,a in alg.arms.items()},snapshots=snapshots,
                warning='This is not the separated theorem family, not a baseline comparison, and not an estimate of a 1-delta guarantee.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='implementation-sanity.json')
    args=parser.parse_args()
    result=sanity_run();Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

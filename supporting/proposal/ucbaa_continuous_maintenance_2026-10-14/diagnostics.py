#!/usr/bin/env python3
"""Deterministic diagnostics for the accompanying proofs, not a proof or bandit experiment.
Run: python diagnostics.py --out diagnostics-results.json
Only Python's standard library is required.
"""
from __future__ import annotations
import argparse, itertools, json, math, random
from pathlib import Path


def kl(p: float, q: float) -> float:
    if not (0 < p < 1 and 0 < q < 1):
        raise ValueError('Interior Bernoulli parameters required')
    return p*math.log(p/q)+(1-p)*math.log((1-p)/(1-q))


def queue_area(arrivals: list[int], q: int) -> tuple[int, int]:
    """Arrival before service; area is measured after service, through full drainage."""
    Q=M=B=0
    work=q*sum(arrivals)
    for a in arrivals + [0]*work:
        M += a
        Q=max(0,Q+q*a-1)
        B += max(M-1,0)*(Q>0)
    assert Q == 0
    return B, M


def interval_partition(means: list[float], intervals: list[tuple[float,float]], eps: float):
    lo=max(a for a,b in intervals); hi=max(b for a,b in intervals)
    C={i for i,(a,b) in enumerate(intervals) if a>=hi-eps}
    D={i for i,(a,b) in enumerate(intervals) if b<lo-eps}
    assert C.isdisjoint(D)
    G={i for i,x in enumerate(means) if max(means)-x<=eps}
    assert C<=G and D.isdisjoint(G)
    return C,D


def main() -> dict:
    r=random.Random(20261014)
    exhaustive=0; min_slack=None
    for length in range(1,7):
        for arrivals in itertools.product(range(3),repeat=length):
            for q in range(2,7):
                B,M=queue_area(list(arrivals),q)
                lower=(q-1)*M*(M-1)//2
                assert B>=lower,(arrivals,q,B,lower)
                slack=B-lower
                min_slack=slack if min_slack is None else min(min_slack,slack)
                exhaustive+=1
    random_queues=5000
    for _ in range(random_queues):
        length=r.randrange(1,35); q=r.randrange(2,30)
        ar=[r.randrange(5) if r.random()<.3 else 0 for _ in range(length)]
        B,M=queue_area(ar,q)
        assert B>=(q-1)*M*(M-1)/2
        Q=0
        for t,a in enumerate(ar,1):
            Q=max(0,Q+q*a-1)
            suffix=max([0]+[q*sum(ar[u:t])-(t-u) for u in range(t)])
            assert Q==suffix
    constants=0; min_kl_ratio=float('inf')
    for k in range(10001):
        delta=math.exp(math.log(1/16)-k/100)
        if delta==0: continue
        ratio=kl(.25-delta,delta)/math.log(1/delta)
        min_kl_ratio=min(min_kl_ratio,ratio)
        assert ratio>=1/256
        constants+=1
    for m in [1024,1025,2048,10_000,10**6,10**12]:
        assert (3/16)*math.log(m/(4*math.log(2)))-1>=math.log(m)/256
    for _ in range(10000):
        eps=10**r.uniform(-5,math.log10(1/16)); delta=10**r.uniform(-6,math.log10(1/16))
        qminus=math.floor(kl(.25,delta)/kl(.25,.25+2*eps))
        assert qminus>=2
        constants+=1
    geometry=0; largest_area_ratio=0.
    for M in range(2,251):
        for J in range(1,M+1):
            B=2*(M+1)*(J*(2*M+1)+J*(J-1)/2)+2*(M+J+1)
            ratio=B/(128*J*M*(M+J+1))
            largest_area_ratio=max(largest_area_ratio,ratio)
            assert B<=12*J*M*M
            assert ratio<=1/8
            assert (161*(J+1)*(M+J+1)/(J*M))<=805
            geometry+=1
    interval_checks=10000
    for _ in range(interval_checks):
        M=r.randrange(2,10); J=r.randrange(1,M+1); eps=r.uniform(.03,.125)
        v=r.uniform(.2,1)*eps/(4*J); d=v*r.uniform(.001,1/32)
        rhos=[(d/4 if r.random()<.5 else v/8) for _ in range(J+1)]
        means=[]; intervals=[]; roles=[]; Dprevious=set()
        for e in range(J+1):
            b=.5+e*v
            vals=[b]+([b-eps+r.choice([-1,1])*d for _ in range(M)] if e<J else [])
            newidx=[]
            for value in vals:
                index=len(means); newidx.append(index)
                means.append(value); roles.append(e)
                # On the coverage event a fixed radius rho/2 interval has each endpoint error <=rho.
                err=r.uniform(-rhos[e]/2,rhos[e]/2)
                intervals.append((max(0,value+err-rhos[e]/2),min(1,value+err+rhos[e]/2)))
            C,D=interval_partition(means,intervals,eps)
            assert Dprevious<=D
            for i in range(len(means)):
                # All previous candidate cohorts retire, and all reference arms are good.
                if i%(M+1)!=0 and roles[i]<e:
                    assert i in D
                if i%(M+1)==0:
                    assert i in C
            if e<J and 2*rhos[e]<d:
                assert all(i in C or i in D for i in newidx)
            Dprevious=D
    rows=[]
    eps=1/8; J=3; M=8; v=eps/(8*J); delta=.05
    K=J*(M+1)+1
    for scale in [32,128,512,2048]:
        d=v/scale
        L=math.log(4*K*(K+1)/delta)
        qf=math.ceil(32*L/d**2); qc=math.ceil(128*L/v**2)
        H=128*(M+J+1)*qf; T=(J+1)*H; V=J*M*H
        B=2*(M+1)*(J*(2*M+1)+J*(J-1)/2)+2*(M+J+1)
        lower=eps*J*M*math.log(M/delta)/(2**20*d*d)
        coarse=2*eps*J*M*qc+64*(J*M/eps+J*J/v)*math.log(2*T)+1
        rows.append(dict(d=d,v_over_d=scale,q_f=qf,q_c=qc,H=H,T=T,V=V,
                         fine_area_bound=B*qf,coarse_area_bound=V+B*qc,
                         certified_fast_regret_lower=lower,coarse_regret_upper=coarse,
                         warning='Analytic bounds only; huge constants and horizons are not simulated.'))
    return dict(seed=20261014,kind='diagnostic-only',
                exhaustive_integer_queue_cases=exhaustive,random_queue_cases=random_queues,
                minimum_queue_slack=min_slack,scalar_constant_checks=constants,
                minimum_kl_to_log_ratio=min_kl_ratio,geometry_checks=geometry,
                maximum_fine_area_to_V_ratio=largest_area_ratio,
                interval_update_trials=interval_checks,analytic_scale_examples=rows,
                conclusions='All assertions passed. These tests do not establish universal theorems or estimate policy performance.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--out',default='diagnostics-results.json')
    args=parser.parse_args(); result=main()
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='analytic_scale_examples'},ensure_ascii=False,indent=2))

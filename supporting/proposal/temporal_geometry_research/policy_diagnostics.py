"""Finite diagnostics for clock-only and cold-reset MOSS.

The policy uses only t, present arms and observed rewards, never the simulation
horizon or true means. Numba is only a speed aid; the formulas are in the report.
No comparison here estimates general superiority or proves a regret bound.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import numpy as np
from numba import njit
from geometry import spectrum

ROOT = Path(__file__).resolve().parent

@njit
def run_policy(arrivals, means, horizon, cold_reset, deterministic, seed):
    np.random.seed(seed)
    n = np.zeros(len(means), dtype=np.int64)
    sums = np.zeros(len(means), dtype=np.float64)
    lifetime_pulls = np.zeros(len(means), dtype=np.int64)
    actions = np.zeros(horizon, dtype=np.int64)
    k = base = start = 0
    denom = 1
    best = -1.0
    regret = 0.0
    restarts = 0
    for tt in range(horizon):
        t = tt+1
        while k < len(arrivals) and arrivals[k] <= t:
            if means[k] > best:
                best = means[k]
            k += 1
        if k < 1:
            raise ValueError('At least one arm must arrive at time 1')
        if k == 1:
            chosen = 0
        else:
            if base == 0 or k-1 >= 2*base:
                base = k-1
                denom = 2*base
                start = t
                restarts += 1
                if cold_reset:
                    for i in range(k):
                        n[i] = 0
                        sums[i] = 0.0
            s = t-start+1
            chosen = -1
            maximum = -1.0
            for i in range(k):
                if n[i] == 0:
                    chosen = i
                    break
                q = s/(denom*n[i])
                bonus = math.sqrt(math.log(q)/n[i]) if q > 1 else 0.0
                index = sums[i]/n[i]+bonus
                if index > maximum:
                    maximum = index
                    chosen = i
        reward = means[chosen] if deterministic else (1.0 if np.random.random() < means[chosen] else 0.0)
        n[chosen] += 1
        lifetime_pulls[chosen] += 1
        sums[chosen] += reward
        actions[tt] = chosen
        regret += best-means[chosen]
    return regret, lifetime_pulls, actions, restarts


def tied_arrivals(m, h):
    a = [1,1]
    mus = [0.5,0.25]
    for j in range(1,m):
        a += [j*h+1]*(2**(j-1))
        mus += [0.5]*(2**(j-1))
    return np.array(a,np.int64), np.array(mus,float)

def main():
    # Compilation warm-up, excluded from reported research run counts.
    run_policy(np.array([1,1],np.int64), np.array([.5,.25]), 2, False, True, 1)
    rows=[]
    total_steps=0
    for m in range(1,8):
        h=65536
        a,mus=tied_arrivals(m,h)
        for cold in [False,True]:
            r,n,actions,stages=run_policy(a,mus,m*h,cold,True,20261012)
            assert np.all(a[actions] <= np.arange(1,m*h+1))
            if cold:
                assert n[1] >= m*math.floor(math.log(h))
            else:
                assert n[1] <= 1+16*math.log(m*h)+1e-8
            rows.append({'family':'tied_deterministic','m':m,'h':h,'T':m*h,
                         'K':len(a),'policy':'cold-reset' if cold else 'clock-only',
                         'regret':r,'bad_pulls':int(n[1]),'stages':stages})
            total_steps += m*h
    
    rng=np.random.default_rng(20261012)
    for z in range(12):
        T=12000
        k=2+5*z
        a=np.sort(np.r_[np.ones(2,dtype=np.int64),rng.integers(1,T+1,size=k-2)])
        mus=rng.uniform(.05,.95,k)
        for cold in [False,True]:
            r,n,actions,stages=run_policy(a,mus,T,cold,False,100+z)
            # Horizon-free prefix consistency: compare a fresh run on a shorter endpoint.
            short=T//2+137
            rs,ns,ac,ss=run_policy(a,mus,short,cold,False,100+z)
            assert np.array_equal(ac,actions[:short])
            assert np.all(a[actions] <= np.arange(1,T+1))
            S=spectrum([int(T-x+1) for x in a[1:]],T)['S']
            rows.append({'family':'bernoulli_diagnostic','m':z,'h':0,'T':T,
                         'K':k,'policy':'cold-reset' if cold else 'clock-only',
                         'regret':r,'bad_pulls':-1,'stages':stages})
            total_steps += T+short
    
    with (ROOT/'policy_results.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)
    summary={'seed':20261012,'total_policy_steps_excluding_compilation':total_steps,
             'deterministic_trajectories':14,'bernoulli_full_trajectories':24,
             'prefix_consistency_reruns':24,
             'status':'all feasibility, deterministic-count and prefix-consistency checks passed',
             'limitations':'Diagnostics only; no estimated coverage, no claim of universal superiority.'}
    (ROOT/'policy_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print('\nDeterministic diagnostics:')
    for row in rows[:14]:
        print(row)


if __name__ == "__main__":
    main()

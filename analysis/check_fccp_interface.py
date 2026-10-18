"""Short checks of frozen copied interfaces; no comparative experiment is run."""
from __future__ import annotations
import hashlib, json, math, os, platform, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RELEASE=ROOT/'experiments/fccp_frozen'
OUT=ROOT/'analysis/interface-checks.json'
os.environ['NUMBA_CACHE_DIR']=str(ROOT/'analysis/numba-cache')
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.dont_write_bytecode=True
sys.path.insert(0,str(RELEASE/'src'))
import numpy as np
import numba
from flexible_ccp import FlexibleCCP
from ccp_primitives import kl_ucb_index
from flexible_v2 import choose_dual
from flexible_engine import core_scores,seed_policy

def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    start_clock=time.perf_counter()
    before={str(p.relative_to(RELEASE)):sh(p) for p in (RELEASE/'src').glob('*.py')}
    rounds=0
    for core in ['ucb1','growing_moss','mc_moss','thompson','kl_ucb']:
        n=np.zeros(4,dtype=np.int64);S=np.zeros(4);base=0;segstart=1;k=0
        alg=FlexibleCCP.preset('compatibility',epsilon=.2,eta=.05,base=core,seed=303)
        rng=np.random.default_rng(303)
        for t in range(1,121):
            new={1:['a','b'],41:['c'],81:['d']}.get(t,[]);k+=len(new)
            if k>1 and (base==0 or k-1>=2*base):base=k-1;segstart=t
            scores=[]
            for i in range(k):
                if core=='thompson':score=rng.beta(1+S[i],1+n[i]-S[i])
                elif n[i]==0:score=math.inf
                elif core=='ucb1':score=S[i]/n[i]+math.sqrt(2*math.log(max(2,t))/n[i])
                elif core=='kl_ucb':score=kl_ucb_index(n[i],S[i],t)
                else:
                    clock=t if core=='growing_moss' else t-segstart+1
                    cap=k if core=='growing_moss' else max(2,2*base)
                    score=S[i]/n[i]+math.sqrt(max(0.,math.log(clock/(cap*n[i])))/n[i])
                scores.append(score)
            a=int(np.argmax(scores));label,service=alg.choose(new)
            assert label=='abcd'[a] and not service
            # Prescribed API observations, not sampled rewards or a performance test.
            x=float((t+a)%7<4);n[a]+=1;S[a]+=x;alg.observe(x)
            assert np.array_equal(alg.n,n[:k]) and np.array_equal(alg.S,S[:k])
            p,m,v=alg.report();assert p|m|v==set('abcd'[:k]) and not (p&m or p&v or m&v)
            rounds+=1
    mode_rounds=0
    for mode in ['reward','balanced','classification','compatibility']:
        alg=FlexibleCCP.preset(mode,.2,.05,seed=403)
        for t in range(1,81):
            if t==31:
                old=(alg.n.copy(),alg.S.copy(),alg.l.copy(),alg.u.copy(),alg.phase,alg.reward_tax,alg.service_tax)
                alg.set_priority(.6 if mode!='classification' else 1.)
                assert all(np.array_equal(getattr(alg,a),b) for a,b in zip(['n','S','l','u'],old[:4]))
                assert (alg.phase,alg.reward_tax,alg.service_tax)==old[4:]
            a,s=alg.choose(['a','b'] if t==1 else [])
            alg.observe(float((t+(a=='b'))%5<3));alg.report()
            d=alg.diagnostics();assert d['total_actual_pulls']==t
            if alg.reward_budget is not None:assert alg.reward_tax<=alg.reward_budget*alg.spectrum_max+1e-8
            if alg.service_budget is not None:assert alg.service_tax<=alg.service_budget*alg.spectrum_max+1e-8
            mode_rounds+=1
    # One revealed state, independently seeded within the Numba backend. No simulator.
    n=np.array([3,4,2],np.int64);S=np.array([2.,1.,1.]);l=np.zeros(3);u=np.ones(3)
    q=np.full(3,1000,np.int64);births=np.ones(3,np.int64)
    cases=0
    for core in [10,1,2,3,4]:
        for seed in [501,502]:
            seed_policy(seed)
            expected=int(np.argmax(core_scores(n,S,3,10,2,1,core,1.,1.)))
            seed_policy(seed)
            actual=choose_dual(n,S,l,u,q,births,3,10,2,1,0,0.,0.,0.,0.,False,.2,.05,
                               core,0.,False,1e100,1e100,.1,.02,4.,50,1.,1.)
            assert actual[0]==expected and not actual[1]
            cases+=1
    errors=0
    alg=FlexibleCCP.preset('reward',.2,.05)
    for op in [lambda:alg.choose(),lambda:alg.observe(.5),lambda:alg.set_priority(1.1)]:
        try:op()
        except (ValueError,RuntimeError):errors+=1
        else:raise AssertionError('expected validation error')
    alg.choose(['only'])
    for op in [lambda:alg.choose(),lambda:alg.set_priority(.5),lambda:alg.report()]:
        try:op()
        except RuntimeError:errors+=1
        else:raise AssertionError('expected pending-observation error')
    alg.observe(.7);assert alg.report()==({'only'},set(),set())
    after={str(p.relative_to(RELEASE)):sh(p) for p in (RELEASE/'src').glob('*.py')}
    assert before==after
    report=dict(status='passed',scope='short interface and same-backend compatibility diagnostics; no new reward-performance experiment',
      compatibility_action_rounds=rounds,mode_api_rounds=mode_rounds,numba_same_state_same_seed_cases=cases,
      API_validation_rejections=errors,copied_frozen_python_unchanged=True,elapsed_seconds=time.perf_counter()-start_clock,
      environment=dict(python=sys.version,numpy=np.__version__,numba=numba.__version__,platform=platform.platform()),
      original_research_directories_not_imported=True,cross_backend_seed_equality_not_asserted=True)
    OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

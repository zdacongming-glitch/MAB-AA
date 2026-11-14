"""Independent formulas, policy visibility, and compiled/pruned equivalence."""
import math
from copy import deepcopy
import numpy as np
import pytest
from scipy.optimize import brentq

from srcbench.simplified import (FullPolicy, full_budget, full_index, full_scores,
                                support_summary, gt_log_wealth, gt_interval, task_bets, FULL_METHOD)
from srcbench.mathcore import NumericList, inverse_index
from srcbench.methods import get_method
from srcbench.policy import Policy


@pytest.mark.parametrize("eta,M", [(.03,8),(.015,9),(.003,11),(.001,12),(.0005,13),(1.,1)])
def test_public_M(eta, M):
    assert task_bets(eta) == M


def test_full_formula_closed_form_constant_and_non_bernoulli():
    for n in (1, 3, 20, 80):
        v = 40.
        budget = max(0, math.log(v/n)) + math.log1p(max(0, math.log(v/n))**2)
        assert full_budget(v,n) == pytest.approx(budget)
        x = np.array([.3]); c = np.array([n])
        got = full_index(x,c,.3,False,budget)
        expected = 1-.7*math.exp(-budget/n)
        assert got == pytest.approx(expected, abs=3e-15)
    a = full_index(np.array([.3]),np.array([10]),.3,False,1.)
    b = full_index(np.array([0.,1.]),np.array([7,3]),.3,False,1.)
    assert abs(a-b) > .05


def test_full_pruning_matches_every_arm_full_solver():
    rng = np.random.default_rng(1294)
    for _ in range(60):
        k = 5
        n = rng.integers(1, 150, k)
        values, counts = NumericList(), NumericList()
        means, perfect = np.zeros(k), np.zeros(k,dtype=bool)
        for i in range(k):
            x = rng.choice([0., .1, .48, .9, 1.], size=n[i]) if _ % 2 else rng.beta(.2,.3,n[i])
            xs, cs = np.unique(x, return_counts=True)
            values.append(xs); counts.append(cs.astype(np.int64))
            means[i],perfect[i] = support_summary(xs,cs)
        for v in (1.,20.,1000.):
            a, _, _ = full_scores(n,values,counts,means,perfect,v,True)
            b, _, _ = full_scores(n,values,counts,means,perfect,v,False)
            assert a == b


def test_full_single_arm_arrival_clock_reset_and_lifetime_counts():
    p = FullPolicy(track_reports=False)
    for _ in range(8):
        assert p.choose(["a"] if _ == 0 else []) == "a"
        p.observe(.6)
        assert p.base == 0
    assert p.choose(["b"]) == "b"
    assert (p.base,p.sigma,p.dclock) == (1,9,2)
    p.observe(.4)
    assert p.choose(["c"]) == "c"
    assert (p.base,p.sigma,p.dclock) == (2,10,4)
    assert p.n[0] == 8
    p.observe(.8)
    with pytest.raises(RuntimeError):
        p.report()


def test_perfect_support_and_arrival_ties():
    p = FullPolicy(track_reports=False)
    assert p.choose(["first","second"]) == "first"; p.observe(1.)
    assert p.choose() == "second"; p.observe(1.)
    assert p.choose() == "first"; p.observe(1.)
    mean,perfect = support_summary(np.array([1.,np.nextafter(1.,0.)]),np.array([1,1]))
    assert not perfect and mean < 1
    assert full_index(np.array([1.,np.nextafter(1.,0.)]),np.array([1,1]),mean,perfect,.1) < 1


def test_gt_normalized_wealth_and_independent_roots():
    x = np.array([.1,.5,.8]); c = np.array([20,30,10]); n=int(c.sum()); total=float(x@c)
    eta, M, alpha=.15,5,.01
    def direct(m,s):
        return .5*math.exp(1.5*s*eta*(total-n*m)-9*n*eta**2/32)+sum(
            math.prod((1+s*2**(-j)*(value-m))**count for value,count in zip(x,c))/(2*M) for j in range(M))
    for m in (.1,.3,.8):
        for s in (-1,1):
            assert math.exp(gt_log_wealth(x,c,total,n,m,s,eta,M)) == pytest.approx(direct(m,s),rel=2e-13)
    lo,hi = gt_interval(x,c,total,n,alpha,eta,M)
    assert lo == pytest.approx(brentq(lambda m: direct(m,1)-1/alpha,0,1),abs=2e-13)
    assert hi == pytest.approx(brentq(lambda m: direct(m,-1)-1/alpha,0,1),abs=2e-13)
    assert gt_log_wealth(np.array([0.]),np.array([0]),0.,0,.3,1,.015,12) == pytest.approx(0,abs=1e-15)
    assert math.isfinite(gt_log_wealth(np.array([0.]),np.array([1]),0.,1,1.,1,.015,12))


@pytest.mark.parametrize("method",["SRC-R","SRC-KL-R","IMED","Empirical-KL-UCB","FULL-R"])
def test_reward_only_reporting_elision_preserves_complete_actions(method):
    spec = FULL_METHOD if method == "FULL-R" else get_method(method)
    cls = FullPolicy if method == "FULL-R" else Policy
    a = cls(spec,epsilon=.2,eta=.03,delta=.05,track_reports=True)
    b = cls(spec,epsilon=.2,eta=.03,delta=.05,track_reports=False)
    rng = np.random.default_rng(94)
    stream = rng.beta(.3,.7,(5,400))
    for t in range(240):
        arrivals = [0,1] if t == 0 else ([2] if t == 70 else ([3,4] if t == 150 else []))
        ia,ib = a.choose(arrivals),b.choose(arrivals)
        assert ia == ib
        y = stream[ia,a.n[ia]]
        a.observe(y); b.observe(y)
        assert np.array_equal(a.n,b.n)


def test_service_min_lifetime_counts_price_and_persistent_failure():
    p=FullPolicy(mode="ON",price=0,eta=.03)
    for t in range(20):
        chosen=p.choose([0,1,2] if t==0 else [])
        assert p.last_decision["probability"] == 1
        assert p.n[chosen] == min(p.n)
        p.observe(.5)
    old=p.n.copy()
    p.failed=True
    p.choose([3]);p.observe(.5)
    assert p.failed and p.report() == ([],[],[0,1,2,3])
    assert p.last_decision["branch"] == "reward"
    assert np.array_equal(p.n[:3],old)


def test_no_reporting_on_requires_explicit_off():
    with pytest.raises(ValueError):
        FullPolicy(mode="ON",track_reports=False)


def test_positive_price_uses_full_gap_and_strict_reference_work_union():
    p = FullPolicy(mode="ON", price=10., eta=.015, seed=2)
    p.choose([0,1,2,3]); p.observe(.2)
    # A valid observable history fixture with different actual lifetime counts.
    values = [.2,.8,.5,.72]
    p.n[:] = [1,9,3,1]
    p.S[:] = np.array(values)*p.n
    p.t = int(sum(p.n))
    for i,y in enumerate(values):
        p._values[i][:] = 0; p._counts[i][:] = 0
        p._values[i][0] = y; p._counts[i][0] = p.n[i]
        p._sizes[i] = 1; p._maps[i] = {y:0}
        p.means[i],p.perfect[i] = support_summary(p._values[i],p._counts[i])
    p.lower[:] = [.2,.75,.55,.7]
    p.upper[:] = [.3,.85,.8,.74]
    # B={1,2}, W={2}; arms 0 and 3 have lower counts but no service role.
    p.choose()
    d=p.last_decision
    assert d["service_candidate"] == 2
    v=(p.t-p.sigma+1)/p.dclock
    indices=[1-(1-y)*math.exp(-full_budget(v,int(n))/n) for y,n in zip(values,p.n)]
    expected=max(indices)-indices[2]
    assert d["opportunity_gap"] == pytest.approx(expected,abs=3e-15)
    assert d["probability"] == pytest.approx(1/(1+10*expected),abs=3e-15)
    p.observe(.6)


def test_arrival_revokes_positive_without_erasing_evidence():
    p=FullPolicy(mode="OFF",eta=.03)
    p.choose([0]);p.observe(.5)
    assert p.report() == ([0],[],[])
    before=(p.lower[0],p.upper[0],int(p.n[0]))
    assert p.choose([1])==1
    assert (p.lower[0],p.upper[0],int(p.n[0]))==before
    p.observe(.8)
    assert p.report() == ([],[],[0,1])

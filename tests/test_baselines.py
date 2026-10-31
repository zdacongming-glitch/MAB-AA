import math
import numpy as np
import pytest

from srcbench.baselines import BaselineSelector, bernoulli_kl, bernoulli_upper
from srcbench.methods import BASELINE_IDS
from srcbench.mathcore import dinf, inverse_index


def state(n=(10, 10), S=(5., 4.), Q=None):
    n, S = np.asarray(n, dtype=np.int64), np.asarray(S, dtype=float)
    Q = S.copy() if Q is None else np.asarray(Q, dtype=float)
    supports = [(np.array([0., 1.]), np.array([ni-si, si])) for ni, si in zip(n, S)]
    return n, S, Q, np.ones(len(n), dtype=np.int64), supports


def choose(selector, st, t=100, base=1, sigma=1):
    n, S, Q, births, supports = st
    return selector.choose(n, S, Q, births, t, base, sigma, supports)


def test_ucb_formulas_preserve_distinct_f17_constant():
    st = state()
    for name, coefficient, log_argument in [("UCB1", 2., 100), ("AUER", 8., 100),
                                             ("UCB-conservative", 3., 200)]:
        selector = BaselineSelector(name, seed=3)
        assert choose(selector, st) == 0
        assert selector.last_scores[0] == pytest.approx(.5 + math.sqrt(coefficient * math.log(log_argument) / 10))


def test_clipped_aci_preserves_arrival_ties_instead_of_forcing_initialization():
    st = state(n=(1, 0), S=(1., 0.))
    clipped = BaselineSelector("Clipped-ACI")
    assert choose(clipped, st) == 0  # Both reference indices equal one.
    unclipped = BaselineSelector("ACI")
    assert choose(unclipped, st) == 1


def test_arrival_clock_uses_lifetime_counts_after_restart():
    selector = BaselineSelector("ACI")
    st = state(n=(100, 2), S=(70., 1.))
    assert choose(selector, st, t=1000, base=2, sigma=991) == 1
    assert selector.last_scores[0] == pytest.approx(.7)
    assert selector.last_scores[1] == pytest.approx(.5 + math.sqrt(math.log(10 / 8) / 2))


def test_known_horizon_is_declared_and_rank_cap_is_enforced():
    with pytest.raises(ValueError, match="horizon"):
        BaselineSelector("MOSS-T-currentK")
    selector = BaselineSelector("BL-MOSS-b1", horizon=8)
    st = state(n=(1, 1, 0), S=(0., 0., 0.))
    assert choose(selector, st) in (0, 1)  # ceil(8^(1/3))=2, third arm excluded.
    assert selector.last_scores[2] == -math.inf


def test_beta_uniform_prior_is_not_forced_initialization():
    selector = BaselineSelector("Bayes-UCB")
    st = state(n=(0, 0), S=(0., 0.))
    assert choose(selector, st, t=1) == 0
    assert np.array_equal(selector.last_scores, [0., 0.])
    selector.observe(0, .3)
    choose(selector, st, t=10)
    assert np.allclose(selector.last_scores, [.9, .9])


def test_bernoulli_upper_obeys_independent_kl_constraint():
    for mu in (0., .05, .4, .95):
        upper = bernoulli_upper(mu, .03)
        assert mu < upper <= 1.
        assert bernoulli_kl(mu, upper) == pytest.approx(.03, abs=2e-12)


def test_empirical_kl_accepts_arbitrary_observed_support():
    selector = BaselineSelector("Empirical-KL-UCB")
    st = list(state(n=(4, 4), S=(1.8, 2.)))
    st[-1] = [(np.array([.1, .3, .6, .8]), np.ones(4)),
              (np.array([0., 1.]), np.array([2., 2.]))]
    choose(selector, st, t=20)
    assert np.all(np.isfinite(selector.last_scores))
    assert np.all(selector.last_scores >= np.array([.45, .5]))


def test_smab_reduction_equals_ts_on_binary_rewards():
    selectors = [BaselineSelector("TS", seed=730), BaselineSelector("TS-SMAB-bounded", seed=730)]
    n = np.zeros(3, dtype=np.int64)
    S = np.zeros(3)
    Q = np.zeros(3)
    supports = [(np.zeros(0), np.zeros(0)) for _ in n]
    for t in range(1, 40):
        actions = [s.choose(n, S, Q, np.ones(3), t, 2, 1, supports) for s in selectors]
        assert actions[0] == actions[1]
        a = actions[0]
        reward = float(t % 3 == 0)
        for s in selectors:
            s.observe(a, reward)
        n[a] += 1
        S[a] += reward
        Q[a] += reward


def test_sleeping_regret_update_matches_published_loss_estimator():
    selector = BaselineSelector("SB-EXP3-ATGT", seed=4)
    a = choose(selector, state(n=(0, 0, 0), S=(0., 0., 0.)), t=1, base=2)
    assert np.allclose(selector._probabilities, np.full(3, 1/3))
    selector.observe(a, 0.)
    expected = np.ones(3)
    expected[a] -= 3.
    assert np.allclose(selector._L, expected)


@pytest.mark.parametrize("name", BASELINE_IDS)
def test_registered_baseline_is_available_and_does_not_modify_actual_statistics(name):
    selector = BaselineSelector(name, seed=11, horizon=1000)
    st = state()
    before = [x.copy() for x in st[:4]]
    a = choose(selector, st)
    assert a in (0, 1)
    selector.observe(a, .37)
    assert all(np.array_equal(x, y) for x, y in zip(st[:4], before))
    with pytest.raises(RuntimeError, match="match"):
        selector.observe(a, .37)


def _actual_history(k, seed, continuous=True, samples=12):
    rng = np.random.default_rng(seed)
    supports, n, S, Q = [], [], [], []
    for i in range(k):
        count = samples + i % 5
        mu = rng.uniform(.03, .97)
        data = rng.beta(4*mu, 4*(1-mu), count) if continuous else rng.binomial(1, mu, count).astype(float)
        values, counts = np.unique(data, return_counts=True)
        supports.append((values, counts))
        n.append(count)
        S.append(float(np.sum(data)))
        Q.append(float(np.sum(data*data)))
    return (np.array(n, dtype=np.int64), np.array(S), np.array(Q),
            np.ones(k, dtype=np.int64), supports)


def _scalar_empirical_scores(name, st, t):
    """Independent per-arm expansion of the original, unpruned definition."""
    n, S, Q, births, supports = st
    target = float(np.max(S/n))
    if name == "IMED":
        return np.array([-ni * dinf(v, c, target) - math.log(ni)
                         for ni, (v, c) in zip(n, supports)])
    return np.array([inverse_index(v, c, math.log(t)) for v, c in supports])


@pytest.mark.parametrize("name", ["IMED", "Empirical-KL-UCB"])
@pytest.mark.parametrize("continuous", [False, True])
def test_pruned_empirical_selector_matches_unpruned_scalar_at_k256(name, continuous):
    st = _actual_history(256, 7217, continuous)
    t = int(np.sum(st[0])) + 1
    expected = _scalar_empirical_scores(name, st, t)
    selector = BaselineSelector(name)
    assert choose(selector, st, t=t) == int(np.argmax(expected))
    exact = selector.last_score_exact
    assert np.allclose(selector.last_scores[exact], expected[exact], atol=1e-12, rtol=1e-12)
    assert np.all(selector.last_scores[~exact] >= expected[~exact] - 1e-8)
    assert selector.last_full_index_solves < len(st[0])


@pytest.mark.parametrize("name", ["IMED", "Empirical-KL-UCB"])
def test_large_continuous_fixture_and_exact_ties(name):
    st = _actual_history(4000, 18021, continuous=True, samples=2)
    t = int(np.sum(st[0])) + 1
    selector = BaselineSelector(name)
    assert choose(selector, st, t=t) == int(np.argmax(_scalar_empirical_scores(name, st, t)))
    selector.observe(selector._pending, .5)
    tied = state(n=(20, 20, 20), S=(20., 20., 20.))
    assert choose(BaselineSelector(name), tied, t=61) == 0


@pytest.mark.parametrize("name", ["IMED", "Empirical-KL-UCB"])
def test_support_cache_refreshes_after_actual_updates_and_growth(name):
    st = list(_actual_history(12, 1990, continuous=True, samples=3))
    selector = BaselineSelector(name)
    for step in range(8):
        t = int(np.sum(st[0])) + 1
        a = choose(selector, st, t=t)
        assert a == int(np.argmax(_scalar_empirical_scores(name, st, t)))
        reward = .127 + .073 * step
        selector.observe(a, reward)
        st[0][a] += 1
        st[1][a] += reward
        st[2][a] += reward * reward
        values, counts = st[4][a]
        st[4][a] = (np.append(values, reward), np.append(counts, 1))
    # A newly observed arm can arrive between calls, after an allocation
    # initialization fixture; cache growth must not retain an old root/budget.
    st[0] = np.append(st[0], 1)
    st[1] = np.append(st[1], .97)
    st[2] = np.append(st[2], .97*.97)
    st[3] = np.append(st[3], t)
    st[4].append((np.array([.97]), np.array([1])))
    t = int(np.sum(st[0])) + 30
    assert choose(selector, st, t=t) == int(np.argmax(_scalar_empirical_scores(name, st, t)))


def test_compiled_numeric_scores_match_independent_scalar_formulas():
    st = _actual_history(256, 6377, continuous=True)
    n, S, Q, _, _ = st
    t, base, sigma = 8192, 130, 7993
    for name in ["UCB1", "AUER", "UCB-log2t-c3", "UCB-V", "UCB1-Tuned",
                 "ACI", "Clipped-ACI", "Growing-MOSS", "MOSS-T-currentK"]:
        scores = []
        for ni, si, qi in zip(n, S, Q):
            mu, lt = si/ni, math.log(t)
            variance = max(0., qi/ni - mu*mu)
            if name == "UCB1":
                value = mu + math.sqrt(2*lt/ni)
            elif name == "AUER":
                value = mu + math.sqrt(8*lt/ni)
            elif name == "UCB-log2t-c3":
                value = mu + math.sqrt(3*math.log(2*t)/ni)
            elif name == "UCB-V":
                value = mu + math.sqrt(2*variance*lt/ni) + 3*lt/ni
            elif name == "UCB1-Tuned":
                value = mu + math.sqrt(lt/ni*min(.25,variance+math.sqrt(2*lt/ni)))
            elif name in {"ACI", "Clipped-ACI"}:
                value = mu + math.sqrt(max(0.,math.log((t-sigma+1)/(2*base*ni)))/ni)
                if name == "Clipped-ACI":
                    value = min(1.,value)
            else:
                clock = 20000 if name == "MOSS-T-currentK" else t
                value = mu + math.sqrt(max(0.,math.log(clock/(len(n)*ni)))/ni)
            scores.append(value)
        selector = BaselineSelector(name, horizon=20000)
        assert choose(selector, st, t=t, base=base, sigma=sigma) == int(np.argmax(scores))
        assert np.allclose(selector.last_scores, scores, atol=1e-13, rtol=1e-13)

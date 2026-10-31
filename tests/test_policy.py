"""Independent numerical fixtures and allocation-state contract checks."""
import itertools
import math

import numpy as np
import pytest
from scipy.optimize import brentq, minimize
from scipy.special import betaln

from srcbench.mathcore import (dinf, inverse_index, prefix_interval, pair_plan,
                               reporter, reference_indices, spectrum_scale)
from srcbench.policy import Policy


def candidate(family='src', **overrides):
    method = dict(id=family, family=family, preference=.6, beta_r=32., beta_c=1.,
                  planner='paired', kernel='IMED', params={})
    method.update(overrides)
    return method


def test_empirical_divergence_matches_bernoulli_and_degenerate_formulas():
    values, counts = np.array([0., 1.]), np.array([3, 2], dtype=np.int64)
    expected = .4*math.log(.4/.7)+.6*math.log(.6/.3)
    assert dinf(values, counts, .7) == pytest.approx(expected, abs=2e-13)
    assert dinf(np.array([.3]), np.array([5]), .7) == pytest.approx(math.log(.7/.3))
    assert math.isinf(dinf(values, counts, 1.))
    assert dinf(np.array([1.]), np.array([5]), 1.) == 0
    assert dinf(values, counts, .3) == 0
    assert math.isinf(dinf(np.array([1., np.nextafter(1., 0.)]), np.array([1, 1]), 1.))


def test_empirical_divergence_matches_independent_primal_optimization():
    values = np.array([.1, .35, .7])
    counts = np.array([2, 3, 1], dtype=np.int64)
    probabilities = counts/counts.sum()
    augmented = np.r_[values, 1.]
    target = .68

    def objective(weights):
        return np.sum(probabilities*np.log(probabilities/weights[:3]))

    result = minimize(objective, np.full(4, .25), method='SLSQP',
                      bounds=[(1e-12, 1.)]*4,
                      constraints=[{'type': 'eq', 'fun': lambda q: q.sum()-1},
                                   {'type': 'ineq', 'fun': lambda q: q@augmented-target}],
                      options={'ftol': 1e-13, 'maxiter': 500})
    assert result.success
    assert dinf(values, counts, target) == pytest.approx(result.fun, abs=2e-9)


def test_inverse_index_uses_total_information_budget_and_full_support():
    values, counts = np.array([.1, .35, .7]), np.array([2, 3, 1])
    budget = .8
    endpoint = inverse_index(values, counts, budget)
    assert counts.sum()*dinf(values, counts, endpoint) == pytest.approx(budget, abs=2e-10)
    assert inverse_index(values, counts, 0.) == pytest.approx(values@counts/counts.sum())
    assert inverse_index(np.array([1.]), np.array([2]), 1.) == 1.


def test_mixture_interval_matches_independent_beta_function_roots():
    n, total, alpha = 75, 28.35, .002
    constant = betaln(total+.5, n-total+.5)-betaln(.5, .5)

    def equation(mean):
        return constant-total*np.log(mean)-(n-total)*np.log1p(-mean)-np.log(1/alpha)

    expected_l = brentq(equation, 1e-12, total/n, xtol=1e-14)
    expected_u = brentq(equation, total/n, 1-1e-12, xtol=1e-14)
    lower, upper = prefix_interval(n, total, alpha)
    assert lower == pytest.approx(expected_l, abs=3e-13)
    assert upper == pytest.approx(expected_u, abs=3e-13)
    # Constant endpoints have elementary beta-mixture inversions.
    c = math.exp((betaln(.5, 10.5)-betaln(.5, .5)+math.log(alpha))/10)
    assert prefix_interval(10, 0., alpha)[1] == pytest.approx(1-c, abs=1e-13)
    assert prefix_interval(10, 10., alpha)[0] == pytest.approx(c, abs=1e-13)


@pytest.mark.parametrize('fixture', [(.2, .1, 5, 20, .1, .4, .15),
                                     (.02, .3, 100, 2, .1, 1., .2),
                                     (.01, .01, 0, 0, .1, .1, .1)])
def test_pair_proxy_matches_independent_constrained_minimizer(fixture):
    vi, vj, ni, nj, ci, cj, target = fixture
    xi, xj, cost = pair_plan(*fixture)
    bi, bj = max(1, ni), max(1, nj)
    ai, aj = vi*math.sqrt(bi), vj*math.sqrt(bj)
    assert xi >= bi-1e-10 and xj >= bj-1e-10
    assert ai/math.sqrt(xi)+aj/math.sqrt(xj) <= target+1e-12
    result = minimize(lambda x: ci*(x[0]-bi)+cj*(x[1]-bj),
                      np.array([xi, xj])*1.001, method='SLSQP',
                      bounds=[(bi, None), (bj, None)],
                      constraints={'type': 'ineq', 'fun': lambda x: target-ai/np.sqrt(x[0])-aj/np.sqrt(x[1])},
                      options={'ftol': 1e-10, 'maxiter': 500})
    assert result.success
    assert cost == pytest.approx(result.fun, abs=2e-7)


def test_self_excluding_reporter_agrees_with_confidence_rectangle_corners():
    lower = np.array([.65, .2, .49, .47])
    upper = np.array([.8, .3, .55, .53])
    epsilon, eta = .2, .03
    labels, work = reporter(lower, upper, epsilon, eta)
    corners = np.array(list(itertools.product(*zip(lower, upper))))
    for i in range(4):
        gaps = np.maximum(0, np.max(np.delete(corners, i, axis=1), axis=1)-corners[:, i])
        lo, hi = gaps.min(), gaps.max()
        expected = 1 if hi <= epsilon else (-1 if lo > epsilon else 0)
        assert labels[i] == expected
        assert work[i] == (expected == 0 and not (lo >= epsilon-eta and hi <= epsilon+eta))
    assert reporter(np.array([0.]), np.array([1.]), epsilon, eta)[0].tolist() == [1]


def test_arrival_spectrum_counts_each_age_bin_and_omits_first_initial_arm():
    # Ages 1,2,3,4,5 fall in bins 0,1,2,2,3 after omitting arm zero.
    births = np.array([1, 10, 9, 8, 7, 6], dtype=np.int64)
    expected = 1+math.sqrt(2)+math.sqrt(8)+math.sqrt(8)
    assert spectrum_scale(births, 10) == pytest.approx(expected)
    assert spectrum_scale(np.array([1]), 10) == 0


@pytest.mark.parametrize('family', ['src', 'src_kl'])
def test_shared_observation_counts_nested_intervals_and_budgets(family):
    policy = Policy(candidate(family, beta_r=.3, beta_c=.2), .2, .05, .05)
    rng = np.random.default_rng(8)
    previous_lower, previous_upper = np.empty(0), np.empty(0)
    charged_r = charged_c = 0.
    attempts = 0
    for t in range(1, 240):
        arrivals = ['a', 'b'] if t == 1 else (['c'] if t == 71 else [])
        chosen = policy.choose(arrivals)
        decision = policy.last_decision.copy()
        index = policy.ids.index(chosen)
        assert decision['index'] == index
        assert 0 <= decision['reference_deficit'] <= 1
        assert decision['attempt'] == (decision['denied'] or decision['branch'] == 'classification')
        attempts += int(decision['attempt'])
        if decision['branch'] == 'classification':
            assert policy.n[index] < policy.quota[index]
            charged_c += decision['reference_deficit']
        else:
            charged_r += decision['reference_deficit']
        policy.observe(float(rng.beta(2, 8) if chosen == 'b' else rng.beta(8, 2)))
        assert policy.n.sum() == t
        assert np.all(policy.lower[:len(previous_lower)] >= previous_lower)
        assert np.all(policy.upper[:len(previous_upper)] <= previous_upper)
        previous_lower, previous_upper = policy.lower.copy(), policy.upper.copy()
        assert policy.reward_tax == pytest.approx(charged_r)
        assert policy.service_tax == pytest.approx(charged_c)
        assert policy.reward_tax <= decision['budget_r']+2e-12
        assert policy.service_tax <= decision['budget_c']+2e-12
        assert sum(len(group) for group in policy.report()) == len(policy.n)
    assert attempts == math.floor(policy.service_mass+1e-12)
    assert policy.service_attempts == policy.service_pulls+policy.service_denials
    for i, (values, counts) in enumerate(policy.supports):
        assert counts.sum() == policy.n[i]
        assert values@counts == pytest.approx(policy.S[i])


def test_checkpoint_uses_fixed_prefix_and_retains_its_constraint():
    policy = Policy(candidate(preference=0.), .5, .4, .9)
    policy.choose([17])
    quota = int(policy.quota[0])
    policy.observe(.5)
    for _ in range(1, quota+5):
        assert policy.choose([]) == 17
        policy.observe(.5)
    assert policy.checkpoint_hits == 1
    assert policy.lower[0] >= .5-.4/8-1e-14
    assert policy.upper[0] <= .5+.4/8+1e-14
    assert policy.upper[0]-policy.lower[0] <= .4/4+1e-13


def test_arrivals_withdraw_single_arm_label_and_unobserved_arms_take_priority():
    policy = Policy(candidate(preference=0.), .2, .05, .05)
    assert policy.choose(['first']) == 'first'
    policy.observe(.8)
    assert policy.report() == (['first'], [], [])
    assert policy.choose(['second']) == 'second'
    assert policy.report() == ([], [], ['first', 'second'])
    policy.observe(.1)
    assert policy.choose(['third']) == 'third'
    policy.observe(.6)


def test_empty_intersection_is_persistent_and_stops_designated_service():
    policy = Policy(candidate(preference=1., beta_c=None), .2, .05, .05)
    policy.choose([0, 1])
    selected = policy.last_decision['index']
    policy.lower[selected], policy.upper[selected] = .9, .1
    policy.observe(.5)
    assert policy.failed and policy.report() == ([], [], [0, 1])
    attempts = policy.service_attempts
    for _ in range(5):
        policy.choose([])
        assert policy.last_decision['branch'] == 'reward'
        policy.observe(.5)
    assert policy.failed and policy.service_attempts == attempts
    assert policy.n.sum() == 6


def test_one_observation_contract_and_preference_updates_preserve_state():
    policy = Policy(candidate(), .2, .05, .05)
    with pytest.raises(RuntimeError):
        policy.observe(.5)
    policy.choose([0, 1])
    with pytest.raises(RuntimeError):
        policy.choose([])
    with pytest.raises(ValueError):
        policy.observe(float('nan'))
    policy.observe(.5)
    old = policy.state()
    policy.set_preference(0.)
    assert policy.state() == old
    with pytest.raises(ValueError):
        policy.choose([0])
    assert policy.t == 1


def test_explicit_delta_changes_evidence_and_checkpoint_calibration():
    loose = Policy(candidate(preference=0.), .2, .05, .2)
    tight = Policy(candidate(preference=0.), .2, .05, .001)
    for policy in (loose, tight):
        for i in range(12):
            policy.choose([0] if i == 0 else [])
            policy.observe(.35)
    assert tight.quota[0] > loose.quota[0]
    assert tight.lower[0] < loose.lower[0]
    assert tight.upper[0] > loose.upper[0]


def test_kl_reference_and_sublog_cap_are_distinct_from_original_reference():
    policy = Policy(candidate('src_kl', preference=0.), .2, .05, .05)
    for t in range(1, 121):
        policy.choose([0, 1] if t == 1 else [])
        index = policy.last_decision['index']
        policy.observe(.65 if index == 0 else .2)
    assert policy.reward_tax <= math.sqrt(math.log(math.e+policy.t))+2e-12
    # Inject a valid empirical prefix with one observation to exercise the KL branch.
    values = np.array([.3])
    counts = np.array([1])
    v = 32.
    exploration = math.log(v)+math.log1p(math.log(v)**2)
    kl = inverse_index(values, counts, exploration)
    moss = reference_indices(np.array([1, 1]), np.array([.3, .4]), 64, 1, 2)[0]
    assert kl != pytest.approx(moss)


@pytest.mark.parametrize('family', ['src', 'src_kl'])
def test_zero_budgets_allow_only_exact_zero_reference_deficits(family):
    policy = Policy(candidate(family, beta_r=0., beta_c=0., preference=1.), .2, .05, .05)
    rng = np.random.default_rng(2026)
    for t in range(90):
        policy.choose([0, 1, 2] if t == 0 else [])
        assert policy.last_decision['reference_deficit'] == 0.
        policy.observe(float(rng.random()))
    assert policy.reward_tax == 0. and policy.service_tax == 0.

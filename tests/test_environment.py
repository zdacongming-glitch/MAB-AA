import numpy as np
import pytest

from srcbench.environment import PotentialRewards, record_flags, sample_reward


LAYOUT = {"id": "fixture/paired", "T": 30, "arms": [
    {"arrival": 1, "mean": .2}, {"arrival": 1, "mean": .8},
    {"arrival": 10, "mean": .7}]}


def test_batch_records_and_label_shuffle():
    assert record_flags(LAYOUT["arms"]) == [False, True, False]
    e = PotentialRewards(LAYOUT, "hetero_best_quiet", 0, 25)
    assert sorted(a["original_id"] for a in e.layout["arms"][:2]) == [0, 1]
    assert [a["record"] for a in e.layout["arms"] if a["original_id"] == 1] == [True]


def test_random_access_and_method_order_preserve_pairing():
    a = PotentialRewards(LAYOUT, "beta02", 2, 25)
    b = PotentialRewards(LAYOUT, "beta02", 2, 25)
    x = a.draw(0, 13)
    b.draw(1, 25)
    assert b.draw(0, 13) == x
    assert a.draw(0, 3) == b.draw(0, 3)
    assert len(a.cache[2]) == 0


@pytest.mark.parametrize("law", ["bernoulli", "deterministic", "two_point", "uniform",
    "trunc_normal", "spike_mix", "endpoint_two", "rare_jackpot", "hetero_jackpot",
    "beta02", "beta2", "beta20", "binomial4", "binomial16",
    "hetero_best_noisy", "hetero_best_quiet"])
def test_laws_are_bounded_and_centered(law):
    rng = np.random.default_rng(20261031)
    ys = np.array([sample_reward(rng, .37, law, True) for _ in range(12000)])
    assert np.all((ys >= 0) & (ys <= 1))
    # A distribution-free seven-SE tolerance; this checks broken mean formulas,
    # not whether one finite simulation attains a theoretical performance rate.
    assert abs(ys.mean() - .37) < 7 * np.sqrt(.25 / len(ys))


def test_unknown_law_rejected_and_endpoints_exact():
    rng = np.random.default_rng(2)
    with pytest.raises(ValueError):
        sample_reward(rng, .4, "not-a-law", False)
    assert sample_reward(rng, 1., "beta02", True) == 1.

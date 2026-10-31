"""Pruned allocation must agree with exhaustive true-information costs.

These are history fixtures, not simulated bandit paths. The oracle evaluates
every feasible arm without a Bernoulli bound or an incumbent shortcut.
"""
import math

import numpy as np
import pytest

from srcbench.mathcore import NumericList, dinf, information_choice


def _history(observations):
    """Match observe(): sequential sums and first-seen, padded supports."""
    n = np.array([len(history) for history in observations], dtype=np.int64)
    sums = np.zeros(len(n), dtype=np.float64)
    values, counts = NumericList(), NumericList()
    for i, history in enumerate(observations):
        frequencies = {}
        for observation in history:
            observation = float(observation)
            sums[i] += observation
            frequencies[observation] = frequencies.get(observation, 0) + 1
        capacity = 4
        while capacity < len(frequencies):
            capacity *= 2
        atoms = np.zeros(capacity, dtype=np.float64)
        multiplicities = np.zeros(capacity, dtype=np.int64)
        for j, (atom, count) in enumerate(frequencies.items()):
            atoms[j], multiplicities[j] = atom, count
        values.append(atoms)
        counts.append(multiplicities)
    return n, sums, values, counts


def _exhaustive_costs(n, sums, values, counts, coefficient):
    target = max((float(total / size) for size, total in zip(n, sums)
                  if size > 0), default=0.)
    return [(-math.inf if size == 0 else
             int(size) * dinf(atoms, multiplicities, target)
             + coefficient * math.log(int(size)))
            for size, atoms, multiplicities in zip(n, values, counts)]


def _histories():
    rng = np.random.default_rng(2026110101)
    # A cheap witness and a long, poor arm exercise genuine pruning margins.
    yield [np.full(4, .95), np.full(200, .15), np.full(10, .7)]
    yield [[], [], []]
    yield [[.4, .4], [], [.8], []]
    yield [[.3, .7], [.3, .7], [.3, .7]]
    for case in range(24):
        histories = []
        for arm in range(2 + case % 6):
            size = int(rng.integers(1, 65))
            if case % 3 == 0:
                history = rng.choice([0., 1.], size=size,
                                     p=[.1 + .1 * arm, .9 - .1 * arm])
            elif case % 3 == 1:
                palette = rng.uniform(0., 1., size=3 + arm)
                history = rng.choice(palette, size=size)
            else:
                history = rng.uniform(0., 1., size=size)
            histories.append(history)
        yield histories
    # Differences of a few representable numbers below one can carry order-
    # one information. Sequential addition may also round a mixed mean to one.
    unit = 1. - np.nextafter(1., 0.)
    for case in range(18):
        histories = []
        for arm in range(2 + case % 5):
            size = int(rng.integers(1, 65))
            offsets = [0, 1, 2, 9, 31, 127] if case % 3 == 0 else [1, 2, 9, 31, 127]
            history = rng.choice(1. - unit * np.array(offsets), size=size)
            if case % 3 == 0 and arm == 0:
                history = np.ones(size)
            elif case % 3 == 2:
                history = np.full(size, 1. - unit * offsets[arm % len(offsets)])
            histories.append(history)
        yield histories


@pytest.mark.parametrize("coefficient", [0., .25, .5, 1., 1.5])
def test_pruning_matches_exhaustive_scores_on_padded_histories(coefficient):
    rng = np.random.default_rng(2026110102)
    for case, observations in enumerate(_histories()):
        n, sums, values, counts = _history(observations)
        # Compute the true cost of every arm once. Feasibility changes never
        # change the global information target, including when best is barred.
        costs = _exhaustive_costs(n, sums, values, counts, coefficient)
        k = len(n)
        full = np.ones(k, dtype=np.bool_)
        alternating = np.arange(k) % 2 == 0
        singleton = np.arange(k) == k - 1
        without_best = full.copy()
        empirical = np.divide(sums, n, out=np.zeros(k), where=n > 0)
        without_best[int(np.argmax(empirical))] = False
        random_allowed = rng.random(k) > .4
        random_allowed[int(rng.integers(k))] = True
        for allowed in (full, alternating, singleton, without_best, random_allowed):
            feasible = np.flatnonzero(allowed)
            # min preserves arrival order for exact ties, including +/-inf.
            expected = min(feasible, key=lambda arm: costs[arm])
            actual = information_choice(n, sums, allowed, values, counts, coefficient)
            assert actual == expected, (
                f"history={case}, coefficient={coefficient}, allowed={allowed}, "
                f"costs={costs}, selected={actual}, exhaustive={expected}")

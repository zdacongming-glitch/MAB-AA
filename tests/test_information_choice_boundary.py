"""At target one, actual support determines information and pruning bounds."""
import math

import numpy as np
import pytest

from srcbench.baselines import BaselineSelector
from srcbench.mathcore import NumericList, dinf, information_choice
from srcbench.methods import get_method


def _one_boundary_history(rounded_mean, capacity):
    below_one = np.nextafter(1., 0.) if rounded_mean else .999999999999999
    n = np.array([3, 2, 3], dtype=np.int64)
    # Both are actual sequential floating sums of the stated observations.
    sums = np.array([3., 1. + below_one, 3.])
    atoms = [np.array([1.]), np.array([1., below_one]), np.array([1.])]
    frequencies = [np.array([3]), np.array([1, 1]), np.array([3])]
    values, counts = NumericList(), NumericList()
    for support, frequency in zip(atoms, frequencies):
        length = capacity or len(support)
        padded_values = np.zeros(length, dtype=np.float64)
        padded_counts = np.zeros(length, dtype=np.int64)
        padded_values[:len(support)] = support
        padded_counts[:len(frequency)] = frequency
        values.append(padded_values)
        counts.append(padded_counts)
    return n, sums, values, counts


@pytest.mark.parametrize("coefficient", [.5, 1.])
@pytest.mark.parametrize("rounded_mean", [False, True], ids=["near-one", "rounded-one"])
@pytest.mark.parametrize("capacity", [0, 4, 8], ids=["trimmed", "capacity-four", "capacity-eight"])
def test_one_boundary_pruning_matches_true_scores_and_first_arrival(
        coefficient, rounded_mean, capacity):
    n, sums, values, counts = _one_boundary_history(rounded_mean, capacity)
    target = float(np.max(sums / n))
    assert target == 1.
    assert bool(sums[1] / n[1] == 1.) == rounded_mean

    # A non-one atom gives infinite information at the left limit of one,
    # even when its sequential empirical mean has rounded to exactly one.
    divergence = np.array([dinf(v, c, target) for v, c in zip(values, counts)])
    assert np.array_equal(divergence, [0., math.inf, 0.])
    scalar_costs = np.array([ni * d + coefficient * math.log(ni)
                             for ni, d in zip(n, divergence)])
    expected_cost = coefficient * math.log(3)
    assert scalar_costs[0] == scalar_costs[2] == expected_cost
    assert math.isinf(scalar_costs[1])

    # The unpruned true scores tie on arms zero and two. The earlier arm
    # must survive any initial pruning bound, including near-one witnesses.
    allowed = np.ones(3, dtype=np.bool_)
    assert int(np.argmin(scalar_costs)) == 0
    assert information_choice(n, sums, allowed, values, counts, coefficient) == 0

    # Feasibility can remove the first tied arm without making the mixed
    # support a valid witness or changing the global information target.
    allowed[0] = False
    feasible_costs = np.where(allowed, scalar_costs, math.inf)
    assert information_choice(n, sums, allowed, values, counts, coefficient) == int(np.argmin(feasible_costs)) == 2

    # IMED uses the same true score. Compare against its independent chooser,
    # with either fixed coefficient, rather than a copy of SRC pruning code.
    spec = get_method("IMED")
    spec["params"]["log_coefficient"] = coefficient
    selector = BaselineSelector(spec)
    supports = [(np.asarray(v), np.asarray(c)) for v, c in zip(values, counts)]
    squared_sums = np.array([3., 1. + values[1][1] ** 2, 3.])
    assert selector.choose(n, sums, squared_sums, np.ones(3, dtype=np.int64),
                           int(n.sum()) + 1, 2, 1, supports) == 0

"""Independent primal KL fixtures within a few floating steps of one."""
from decimal import Decimal, localcontext
import math

import numpy as np
import pytest

from srcbench.mathcore import dinf, inverse_index


ONE_ULP_BELOW_ONE = 1. - np.nextafter(1., 0.)


def _primal_information_at_one(low, low_count, high_count, target):
    """KL of the exact mean-constrained primal projection on {low, 1}.

    Decimal.from_float retains the actual binary observations. This computes
    the new distribution's masses directly from its mean constraint and does
    not use the production dual optimizer or its stationary-point formula.
    A zero high_count also covers a point mass with added mass at one.
    """
    with localcontext() as context:
        context.prec = 90
        low = Decimal.from_float(float(low))
        target = Decimal.from_float(float(target))
        left_count, right_count = Decimal(int(low_count)), Decimal(int(high_count))
        total = left_count + right_count
        left = left_count / total
        right = right_count / total
        mean = left * low + right
        if target <= mean:
            return Decimal(0)
        if target >= 1:
            return Decimal('Infinity')
        projected_left = (1 - target) / (1 - low)
        projected_right = 1 - projected_left
        result = left * (left / projected_left).ln()
        if right:
            result += right * (right / projected_right).ln()
        return +result


def _support(low_count, high_count, capacity, count_dtype):
    low = 1. - 9 * ONE_ULP_BELOW_ONE
    atoms = [low] if high_count == 0 else [low, 1.]
    frequencies = [low_count] if high_count == 0 else [low_count, high_count]
    length = capacity or len(atoms)
    values = np.zeros(length, dtype=np.float64)
    counts = np.zeros(length, dtype=count_dtype)
    values[:len(atoms)] = atoms
    counts[:len(atoms)] = frequencies
    return values, counts


@pytest.mark.parametrize('capacity', [0, 4], ids=['trimmed', 'padded'])
@pytest.mark.parametrize('count_dtype', [np.int64, np.float64], ids=['integer-counts', 'float-counts'])
def test_point_mass_nine_steps_below_one_has_log_nine_information(capacity, count_dtype):
    values, counts = _support(3, 0, capacity, count_dtype)
    target = 1. - ONE_ULP_BELOW_ONE
    expected = float(_primal_information_at_one(values[0], 3, 0, target))
    assert expected == pytest.approx(math.log(9.), abs=1e-15)
    assert dinf(values, counts, target) == pytest.approx(expected, rel=2e-13, abs=2e-13)


@pytest.mark.parametrize('low_count,high_count', [(1, 1), (2, 1), (1, 2)])
@pytest.mark.parametrize('capacity', [0, 4], ids=['trimmed', 'padded'])
@pytest.mark.parametrize('count_dtype', [np.int64, np.float64], ids=['integer-counts', 'float-counts'])
def test_two_point_near_one_matches_decimal_primal_projection(
        low_count, high_count, capacity, count_dtype):
    values, counts = _support(low_count, high_count, capacity, count_dtype)
    target = 1. - ONE_ULP_BELOW_ONE
    expected = float(_primal_information_at_one(values[0], low_count, high_count, target))
    assert expected > 0.
    observed = dinf(values, counts, target)
    assert observed == pytest.approx(expected, rel=2e-13, abs=2e-13)
    # Reversing support enumeration cannot alter the empirical law.
    assert dinf(values[::-1].copy(), counts[::-1].copy(), target) == pytest.approx(expected, rel=2e-13, abs=2e-13)


@pytest.mark.parametrize('low_count,high_count', [(3, 0), (1, 1), (2, 1), (1, 2)])
def test_near_one_inverse_has_finite_primal_budget_and_largest_feasible_float(low_count, high_count):
    values, counts = _support(low_count, high_count, 4, np.int64)
    target = 1. - ONE_ULP_BELOW_ONE
    total = low_count + high_count
    information = _primal_information_at_one(values[0], low_count, high_count, target)
    # A tiny positive budget slack makes the representable target certainly
    # feasible despite rounding the independent Decimal budget to a float.
    budget = total * float(information) + 1e-12
    endpoint = inverse_index(values, counts, budget)
    assert endpoint == target
    actual_budget = Decimal(total) * _primal_information_at_one(
        values[0], low_count, high_count, endpoint)
    assert actual_budget <= Decimal.from_float(budget)
    # The only larger representable candidate is one, with infinite KL cost.
    larger = np.nextafter(endpoint, 1.)
    assert larger == 1.
    assert _primal_information_at_one(values[0], low_count, high_count, larger).is_infinite()


@pytest.mark.parametrize('budget', [0., .1, math.inf])
def test_inverse_actual_all_one_support_returns_one_even_with_padding(budget):
    values = np.array([1., 0., 0., 0.])
    counts = np.array([5, 0, 0, 0], dtype=np.int64)
    assert inverse_index(values, counts, budget) == 1.


@pytest.mark.parametrize('budget', [0., .1, 10.])
def test_inverse_rounded_one_mean_does_not_hide_non_one_support(budget):
    low = np.nextafter(1., 0.)
    values = np.array([low, 1., 0., 0.])
    counts = np.array([1, 4, 0, 0], dtype=np.int64)
    assert values @ counts / counts.sum() == 1.
    endpoint = inverse_index(values, counts, budget)
    # The exact mean is below one. Its rounded value cannot certify one as
    # feasible, even at zero budget; the independent support oracle is infinite.
    assert endpoint == low
    assert _primal_information_at_one(low, 1, 4, endpoint) == 0
    assert _primal_information_at_one(low, 1, 4, 1.).is_infinite()

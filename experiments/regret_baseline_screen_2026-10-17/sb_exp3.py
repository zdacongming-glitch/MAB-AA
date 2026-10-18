"""SB-EXP3-ATGT, Nguyen and Mehta (AISTATS 2024), Algorithm 5.

Source: https://proceedings.mlr.press/v238/nguyen24d/nguyen24d.pdf
PDF pages 33--34 (printed Appendix F): two-level doubling, gamma = 0.
Algorithm 1 / Eqs. (4)--(6), PDF page 4, give the estimator and weights.

This implementation specializes the published algorithm to nested availability:
every new arm remains awake.  Thus the episode union V has size k immediately
after observing the current k arms, even following an episode reset.  No future
arm count or endpoint is passed to the learner.  It neither forces one initial
pull per arm nor substitutes ordinary EXP3's weight update for the sleeping
regret update; both would change the algorithm.

Runner protocol: choose before pulling; update_sb BEFORE the runner updates n,
S or Q.  Aux has shape (capacity+8, 8), is initially all zero, and is private to
this policy.  Rows below capacity store L_i (column 0), p_i (column 1).
Metadata row capacity stores U, b, C, initialized, |V|, previously seen k,
eta, and number of resets in columns 0,...,7.  Reset clears only L_i of already
arrived arms.  Fresh arms start at L_i=0.  All probability calculations use a
stable softmax; L_i themselves retain their absolute values so the initialization
of later arrivals is faithful to the sleeping-bandit algorithm.

kind/p0/p1/p2, births, n/S/Q are accepted for the common runner interface only;
they do not tune this parameter-free, gamma=0 Algorithm 5 implementation.
"""

import math
import numpy as np
from numba import njit


@njit(cache=True)
def choose_sb(n, S, Q, k, t, births, kind, p0, p1, p2, aux):
    capacity = aux.shape[0] - 8
    if aux[capacity, 3] == 0.0:
        aux[capacity, 0] = 0.0  # U: cumulative active-arm count in subepisode
        aux[capacity, 1] = 1.0  # b: active-count doubling exponent
        aux[capacity, 2] = 1.0  # C: log-union-size doubling exponent
        aux[capacity, 3] = 1.0
        aux[capacity, 4] = 0.0
        aux[capacity, 5] = 0.0
        aux[capacity, 7] = 0.0

    previous_k = int(aux[capacity, 5])
    for i in range(previous_k, k):
        aux[i, 0] = 0.0
        aux[i, 1] = 0.0
    U = aux[capacity, 0]
    b = int(aux[capacity, 1])
    C = int(aux[capacity, 2])
    log_k = math.log(k)

    # Algorithm 5, lines 5--12: reset after log |V union A_t| doubles.
    if log_k > 2.0 ** C:
        C += 1
        while log_k > 2.0 ** C:
            C += 1
        U = 0.0
        b = 1
        for i in range(k):
            aux[i, 0] = 0.0
        aux[capacity, 7] += 1.0

    # Algorithm 5, lines 13--20: reset after cumulative |A_t| doubles.
    if U + k > 2.0 ** b:
        b += 1
        while k > 2.0 ** b:
            b += 1
        U = 0.0
        for i in range(k):
            aux[i, 0] = 0.0
        aux[capacity, 7] += 1.0

    U += k
    eta = math.sqrt(2.0 ** (C + 1 - b))
    aux[capacity, 0] = U
    aux[capacity, 1] = b
    aux[capacity, 2] = C
    aux[capacity, 4] = k
    aux[capacity, 5] = k
    aux[capacity, 6] = eta

    maximum = -np.inf
    for i in range(k):
        log_weight = eta * aux[i, 0]
        if log_weight > maximum:
            maximum = log_weight
    total = 0.0
    for i in range(k):
        weight = math.exp(eta * aux[i, 0] - maximum)
        aux[i, 1] = weight
        total += weight
    for i in range(k):
        aux[i, 1] /= total

    draw = np.random.random()
    cumulative = 0.0
    # If rounding leaves the cumulative sum infinitesimally below one, fall
    # back to positive mass rather than a potentially underflowed final arm.
    selected = 0
    for i in range(1, k):
        if aux[i, 1] > aux[selected, 1]:
            selected = i
    for i in range(k):
        cumulative += aux[i, 1]
        if draw < cumulative:
            selected = i
            break
    return selected


@njit(cache=True)
def update_sb(n, S, Q, aux, k, t, a, reward, kind, p0, p1, p2):
    # Algorithm 5 final line, Algorithm 1 Eq. (4), with gamma exactly zero.
    # L_i += observed_loss - observed_loss*1{a=i}/p_i for ALL active i.
    observed_loss = 1.0 - reward
    inverse_probability_loss = observed_loss / aux[a, 1]
    for i in range(k):
        aux[i, 0] += observed_loss
    aux[a, 0] -= inverse_probability_loss

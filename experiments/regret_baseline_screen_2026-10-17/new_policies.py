"""Additional regret-only baselines; no evaluator truth reaches a chooser.

The empirical-distribution implementation stores at most two OBSERVED support
points. This is exact for this test suite, not a Bernoulli approximation to its
two-point bounded case. It raises on a third support point rather than silently
changing the nonparametric IMED / empirical-KL algorithms.

Only kinds 7/8 receive the endpoint, explicitly, as p2. All ties use arrival
order. n, S, Q are actual statistics; updates below occur before their update.
No Numba disk caching: the SciPy C function address is process-local.
"""
from __future__ import annotations

import ctypes
import math
import numpy as np
from numba import njit
from numba.extending import get_cython_function_address
from sb_exp3 import choose_sb, update_sb

METHOD_CODES = {
    "AUER": 1, "UCB-V": 2, "UCB1-Tuned": 3, "KL-UCB+": 4,
    "Bayes-UCB": 5, "IMED-bounded": 6, "MOSS-T-currentK": 7,
    "BL-MOSS-countcap-P": 8, "SB-EXP3-ATGT": 9,
    "TS-Jeffreys": 10, "empirical-KL-UCB": 11, "TS-SMAB-bounded": 12,
}

_beta_inverse = ctypes.CFUNCTYPE(
    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.c_int
)(get_cython_function_address("scipy.special.cython_special", "betaincinv"))


@njit(cache=False)
def bernoulli_kl(p, q):
    if q <= 0.0:
        return 0.0 if p <= 0.0 else np.inf
    if q >= 1.0:
        return 0.0 if p >= 1.0 else np.inf
    ans = 0.0
    if p > 0.0:
        ans += p * math.log(p / q)
    if p < 1.0:
        ans += (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
    return ans


@njit(cache=False)
def empirical_dinf(aux, i, target):
    """max_{0<=v<=1/(1-target)} mean log(1+(target-X)*v)."""
    x, y = aux[i, 2], aux[i, 3]
    nx, ny = aux[i, 4], aux[i, 5]
    count = nx + ny
    if count <= 0.0:
        return 0.0
    mean = (nx * x + ny * y) / count
    if target <= mean:
        return 0.0
    if target >= 1.0:
        return np.inf
    cap = 1.0 / (1.0 - target)
    if ny == 0.0:
        return math.log1p((target - x) * cap)
    a = target - x
    b = target - y
    if b >= 0.0:
        v = cap
    else:
        v = min(cap, max(0.0, -(target - mean) / (a * b)))
    return max(0.0, (nx * math.log1p(a * v) + ny * math.log1p(b * v)) / count)


@njit(cache=False)
def new_choose(n, S, Q, k, t, births, kind, p0, p1, p2, aux):
    if kind == 9:
        return choose_sb(n, S, Q, k, t, births, kind, p0, p1, p2, aux)
    logt = math.log(max(2.0, t))
    allowed = k
    if kind == 8:
        # Ghalme et al. Pareto prescription: alpha*T=T^(1/(1+2*beta)).
        cap = max(1, int(math.ceil(p2 ** (1.0 / (1.0 + 2.0 * p0)))))
        allowed = min(k, cap)
    if kind in (1, 2, 3, 4, 6, 7, 8, 11):
        for i in range(allowed):
            if n[i] == 0:
                return i
    empirical_best = 0.0
    if kind == 6:
        for i in range(k):
            empirical_best = max(empirical_best, S[i] / n[i])
    selected = 0
    best = -np.inf
    for i in range(allowed):
        ni = n[i]
        mu = S[i] / ni if ni > 0 else 0.0
        if kind == 1:
            score = mu + math.sqrt(8.0 * logt / ni)
        elif kind == 2:
            variance = max(0.0, Q[i] / ni - mu * mu)
            score = mu + math.sqrt(2.0 * variance * logt / ni) + 3.0 * logt / ni
        elif kind == 3:
            variance = max(0.0, Q[i] / ni - mu * mu)
            adjusted = min(0.25, variance + math.sqrt(2.0 * logt / ni))
            score = mu + math.sqrt(logt * adjusted / ni)
        elif kind == 4:
            # Empirically standard KL-UCB+ with c=0; clipped negative log.
            target = max(0.0, math.log(t / ni)) / ni
            lo, hi = mu, 1.0
            for _ in range(32):
                mid = (lo + hi) / 2.0
                if bernoulli_kl(mu, mid) > target:
                    hi = mid
                else:
                    lo = mid
            score = hi
        elif kind == 5:
            # Kaufmann et al. Algorithm 1, c=0, uniform Beta(1,1) prior.
            score = _beta_inverse(1.0 + S[i], 1.0 + ni - S[i], 1.0 - 1.0 / t, 1)
        elif kind == 6:
            score = -(ni * empirical_dinf(aux, i, empirical_best) + math.log(ni))
        elif kind == 7 or kind == 8:
            score = mu + math.sqrt(max(0.0, math.log(p2 / (allowed * ni))) / ni)
        elif kind == 10:
            score = np.random.beta(0.5 + S[i], 0.5 + ni - S[i])
        elif kind == 11:
            target = logt / ni
            lo, hi = mu, 1.0
            for _ in range(32):
                mid = (lo + hi) / 2.0
                if empirical_dinf(aux, i, mid) > target:
                    hi = mid
                else:
                    lo = mid
            score = hi
        elif kind == 12:
            score = np.random.beta(1.0 + aux[i, 0], 1.0 + ni - aux[i, 0])
        else:
            raise ValueError("unknown baseline kind")
        if score > best:
            best = score
            selected = i
    return selected


@njit(cache=False)
def update_new(n, S, Q, aux, k, t, a, reward, kind, p0, p1, p2):
    if kind == 9:
        update_sb(n, S, Q, aux, k, t, a, reward, kind, p0, p1, p2)
    elif kind == 6 or kind == 11:
        if n[a] == 0:
            aux[a, 2] = reward
            aux[a, 3] = reward
            aux[a, 4] = 1.0
            aux[a, 5] = 0.0
        elif reward == aux[a, 2]:
            aux[a, 4] += 1.0
        elif aux[a, 5] == 0.0:
            if reward > aux[a, 2]:
                aux[a, 3] = reward
                aux[a, 5] = 1.0
            else:
                aux[a, 3] = aux[a, 2]
                aux[a, 5] = aux[a, 4]
                aux[a, 2] = reward
                aux[a, 4] = 1.0
        elif reward == aux[a, 3]:
            aux[a, 5] += 1.0
        else:
            raise ValueError("empirical implementation requires at most two observed support points")
    elif kind == 12:
        # Agrawal--Goyal bounded-reward reduction. Endpoints are degenerate,
        # so consume an additional uniform variate only for fractional rewards.
        if reward >= 1.0:
            aux[a, 0] += 1.0
        elif reward > 0.0 and np.random.random() < reward:
            aux[a, 0] += 1.0

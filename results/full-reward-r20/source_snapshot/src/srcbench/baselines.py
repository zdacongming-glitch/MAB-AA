"""History-only reward baselines, including the preserved F17 formulas.

The empirical distribution routines use every observed support point. No
distribution label, true mean, future arrival or final arm count is supplied.
Known-horizon MOSS configurations explicitly receive the endpoint.
"""
from __future__ import annotations

import math
import numpy as np
from scipy.special import betaincinv

from .mathcore import dinf, inverse_index, njit, NumericList
from .methods import get_method


@njit(cache=True)
def bernoulli_kl(x, y):
    if y <= 0.:
        return 0. if x <= 0. else math.inf
    if y >= 1.:
        return 0. if x >= 1. else math.inf
    result = 0.
    if x > 0.:
        result += x * math.log(x / y)
    if x < 1.:
        result += (1. - x) * math.log((1. - x) / (1. - y))
    return result


@njit(cache=True)
def bernoulli_upper(mean, budget):
    """Upper endpoint of kl(mean, q) <= budget, with outward bisection."""
    if mean >= 1.:
        return 1.
    if budget <= 0.:
        return float(mean)
    if mean <= 0.:
        return -math.expm1(-budget)
    lo, hi = float(mean), 1.
    for _ in range(48):
        mid = (lo + hi) / 2.
        if bernoulli_kl(mean, mid) > budget:
            hi = mid
        else:
            lo = mid
    return hi


_NUMERIC_CODES = {"UCB1": 0, "AUER": 1, "UCB-conservative": 2,
                  "UCB-V": 3, "UCB1-Tuned": 4, "ACI": 5,
                  "Clipped-ACI": 6, "Growing-MOSS": 7,
                  "MOSS-T-currentK": 8,
                  "KL-UCB": 9, "KL-UCB+": 10}


@njit(cache=True)
def _numeric_scores(n, S, Q, t, base, sigma, allowed, horizon, code, c):
    """Compile the per-arm scalar formulas without fast-math reassociation."""
    k = len(n)
    scores = np.full(k, -math.inf)
    logt = math.log(max(1, t))
    for i in range(allowed):
        ni = n[i]
        if ni == 0:
            scores[i] = 1. if code == 6 else math.inf
            continue
        mu = S[i] / ni
        if code == 0:
            score = mu + math.sqrt(2. * logt / ni)
        elif code == 1:
            score = mu + math.sqrt(8. * logt / ni)
        elif code == 2:
            score = mu + math.sqrt(3. * math.log(2. * t) / ni)
        elif code == 3:
            variance = max(0., Q[i] / ni - mu * mu)
            score = mu + math.sqrt(2. * variance * logt / ni) + 3. * logt / ni
        elif code == 4:
            variance = max(0., Q[i] / ni - mu * mu)
            score = mu + math.sqrt(logt / ni * min(.25, variance + math.sqrt(2. * logt / ni)))
        elif code == 5 or code == 6:
            if k == 1:
                score = 1.
            else:
                score = mu + math.sqrt(max(0., math.log(max(1, t - sigma + 1) / (max(2, 2 * base) * ni))) / ni)
                if code == 6:
                    score = min(1., score)
        elif code == 7:
            score = mu + math.sqrt(max(0., math.log(t / (k * ni))) / ni)
        elif code == 8:
            score = mu + math.sqrt(max(0., math.log(horizon / (allowed * ni))) / ni)
        elif code == 9:
            bound = (logt + c * max(0., math.log(max(1., logt)))) / ni
            score = bernoulli_upper(mu, bound)
        else:
            score = bernoulli_upper(mu, max(0., math.log(t / ni)) / ni)
        scores[i] = score
    return scores


@njit(cache=True)
def _empirical_mean(values, counts):
    total, weighted = 0., 0.
    for j in range(len(values)):
        total += counts[j]
        weighted += counts[j] * values[j]
    return weighted / total if total > 0 else 0.


@njit(cache=True)
def _imed_scores(n, S, values, counts, support_means, coefficient):
    """Bernoulli KL supplies an optimistic score bound, never a replacement."""
    k = len(n)
    target = 0.
    first = 0
    for i in range(k):
        mu = S[i] / n[i]
        if mu > target:
            target, first = mu, i
    scores = np.full(k, -math.inf)
    exact = np.zeros(k, dtype=np.bool_)
    score = -n[first] * dinf(values[first], counts[first], target) - coefficient * math.log(n[first])
    scores[first], exact[first] = score, True
    best = score
    solves = 1
    for i in range(k):
        if i == first:
            continue
        # Data processing: D_inf(F,q) >= kl(mean(F),q) for q>mean(F).
        bound = 0. if support_means[i] >= target else bernoulli_kl(support_means[i], target)
        upper_score = -n[i] * bound - coefficient * math.log(n[i])
        slack = 1e-8 + 5e-12 * n[i]
        if upper_score < best - slack:
            scores[i] = upper_score
            continue
        score = -n[i] * dinf(values[i], counts[i], target) - coefficient * math.log(n[i])
        scores[i], exact[i] = score, True
        solves += 1
        if score > best:
            best = score
    return scores, exact, solves


@njit(cache=True)
def _empirical_kl_scores(n, values, counts, support_means, budget):
    """Select with current-round certificates and the original full solver.

    Only arms separated by a 1e-8 index margin can be pruned. Every contender
    in the numerical overlap, including ties, uses ``inverse_index`` itself.
    The dual at a fixed feasible argument is a lower bound on D_inf even if
    its optimizer has not fully converged. No support or moments are replaced.
    """
    k = len(n)
    first = 0
    for i in range(1, k):
        if support_means[i] > support_means[first]:
            first = i
    scores = np.empty(k)
    exact = np.zeros(k, dtype=np.bool_)
    scores[first] = inverse_index(values[first], counts[first], budget)
    exact[first] = True
    best = scores[first]
    solves = 1
    for i in range(k):
        if i == first:
            continue
        target = max(0., best - 1e-8)
        slack = 1e-9 + 5e-12 * n[i]
        # Testing kl(mean,target)>log(t)/n is equivalent to certifying that
        # the Bernoulli-KL upper envelope lies strictly below target. This
        # single evaluation avoids inverting that envelope for every arm.
        # The certificate is rebuilt at THIS round's budget, never reused.
        if target > support_means[i] and n[i] * bernoulli_kl(support_means[i], target) > budget + slack:
            scores[i] = target
            continue
        if n[i] * dinf(values[i], counts[i], target) > budget + slack:
            scores[i] = target
            continue
        score = inverse_index(values[i], counts[i], budget)
        scores[i], exact[i] = score, True
        solves += 1
        if score > best:
            best = score
    return scores, exact, solves


class BaselineSelector:
    """One chooser per trajectory, with private randomized-policy state.

    ``observe`` updates only that private state; the caller owns all actual
    sample counts, sums, squares and empirical supports. It must follow each
    choice exactly once, regardless of when the caller updates those arrays.
    """

    def __init__(self, method, seed=0, horizon=None):
        self.method = get_method(method) if isinstance(method, str) else dict(method)
        if self.method["family"] != "baseline":
            raise ValueError("BaselineSelector requires a baseline definition")
        self.kernel = self.method["kernel"]
        self.params = self.method.get("params", {})
        self.horizon = horizon
        if self.method.get("known_horizon") and (horizon is None or horizon < 1):
            raise ValueError(f"{self.kernel} requires its declared horizon")
        self.rng = np.random.default_rng(seed)
        self._successes = np.zeros(0)
        self._observations = np.zeros(0, dtype=np.int64)
        self._L = np.zeros(0)
        self._probabilities = np.zeros(0)
        self._U = 0
        self._b = 1
        self._C = 1
        self._pending = None
        self._last_k = 0
        self.last_scores = None
        self.last_score_exact = None
        self.last_full_index_solves = 0
        self._support_values = NumericList()
        self._support_counts = NumericList()
        self._support_means = np.empty(0)
        self._support_seen_n = np.empty(0, dtype=np.int64)
        self._support_seen_S = np.empty(0)

    def _grow(self, k):
        if k < self._last_k:
            raise ValueError("available arms must remain available")
        missing = k - len(self._successes)
        if missing > 0:
            self._successes = np.pad(self._successes, (0, missing))
            self._observations = np.pad(self._observations, (0, missing))
            self._L = np.pad(self._L, (0, missing))
        self._last_k = k

    def _sleeping_choose(self, k):
        # Nguyen--Mehta Algorithm 5 with gamma=0 and nested awake sets.
        if math.log(k) > math.ldexp(1., self._C):
            self._C += 1
            while math.log(k) > math.ldexp(1., self._C):
                self._C += 1
            self._U = 0
            self._b = 1
            self._L[:k] = 0.
        if self._U + k > math.ldexp(1., self._b):
            self._b += 1
            while k > math.ldexp(1., self._b):
                self._b += 1
            self._U = 0
            self._L[:k] = 0.
        self._U += k
        eta = math.sqrt(math.ldexp(1., self._C + 1 - self._b))
        weights = np.exp(eta * (self._L[:k] - np.max(self._L[:k])))
        self._probabilities = weights / weights.sum()
        draw = self.rng.random()
        a = int(np.searchsorted(np.cumsum(self._probabilities), draw, side="right"))
        if a >= k:
            a = int(np.argmax(self._probabilities))
        return a

    def choose(self, n, S, Q, births, t, base, sigma, supports):
        if self._pending is not None:
            raise RuntimeError("observe must follow every choice")
        n, S, Q = np.asarray(n), np.asarray(S), np.asarray(Q)
        k = len(n)
        if k < 1 or t < 1 or len(S) != k or len(Q) != k:
            raise ValueError("invalid observable chooser state")
        self._grow(k)
        if self.kernel == "SB-EXP3-ATGT":
            a = self._sleeping_choose(k)
            self.last_scores = self._probabilities.copy()
            self.last_score_exact = np.ones(k, dtype=bool)
        else:
            scores = self._scores(n, S, Q, t, base, sigma, supports)
            a = int(np.argmax(scores))  # Stable arrival-order tie resolution.
            self.last_scores = scores
        self._pending = a
        return a

    def _scores(self, n, S, Q, t, base, sigma, supports):
        k = len(n)
        kernel = self.kernel
        self.last_score_exact = np.ones(k, dtype=bool)
        self.last_full_index_solves = 0
        if kernel in {"TS", "TS-Jeffreys"}:
            prior = .5 if kernel == "TS-Jeffreys" else 1.
            return self.rng.beta(prior + S, prior + n - S)
        if kernel == "TS-SMAB-bounded":
            return self.rng.beta(1. + self._successes[:k],
                                 1. + self._observations[:k] - self._successes[:k])
        if kernel == "Bayes-UCB":
            if t == 1:
                return np.zeros(k)
            # Complementary tail avoids cancellation at large t.
            return 1. - betaincinv(1. + n - S, 1. + S, 1. / t)

        allowed = k
        scores = np.full(k, -math.inf)
        unobserved = np.flatnonzero(n[:allowed] == 0)
        if len(unobserved):
            # Clipped ACI gives an unobserved arm score one; existing arms
            # can tie at one and must retain their original arrival priority.
            if kernel != "Clipped-ACI":
                scores[unobserved] = math.inf
                return scores

        if kernel in _NUMERIC_CODES:
            return _numeric_scores(n, S, Q, t, base, sigma, allowed,
                                   float(self.horizon or 1), _NUMERIC_CODES[kernel],
                                   self.params.get("loglog_coefficient", 0.))
        if kernel not in {"IMED", "Empirical-KL-UCB"}:
            raise ValueError(f"unrecognized baseline kernel: {kernel}")
        self._sync_supports(n, S, supports)
        if kernel == "IMED":
            scores, exact, solves = _imed_scores(
                n, S, self._support_values, self._support_counts,
                self._support_means, self.params.get("log_coefficient", 1.))
        else:
            scores, exact, solves = _empirical_kl_scores(
                n, self._support_values, self._support_counts,
                self._support_means, math.log(max(1, t)))
        self.last_score_exact, self.last_full_index_solves = exact, int(solves)
        return scores

    def _sync_supports(self, n, S, supports):
        """Refresh only changed histories; the per-arm arithmetic is compiled.

        Typed lists retain the actual observed atoms, including arbitrary
        continuous observations. Reallocated support views are picked up on
        count changes. Detecting changed counts/sums is a vector operation,
        rather than a Python loop over every available arm each round.
        """
        k = len(n)
        old = len(self._support_values)
        if old < k:
            for _ in range(k - old):
                self._support_values.append(np.empty(0, dtype=np.float64))
                self._support_counts.append(np.empty(0, dtype=np.float64))
            self._support_means = np.pad(self._support_means, (0, k - old))
            self._support_seen_n = np.pad(self._support_seen_n, (0, k - old), constant_values=-1)
            self._support_seen_S = np.pad(self._support_seen_S, (0, k - old), constant_values=np.nan)
        changed = np.flatnonzero((self._support_seen_n != n) | (self._support_seen_S != S))
        for i in changed:
            values, counts = supports[int(i)]
            values = np.ascontiguousarray(values, dtype=np.float64)
            counts = np.ascontiguousarray(counts, dtype=np.float64)
            self._support_values[int(i)] = values
            self._support_counts[int(i)] = counts
            self._support_means[i] = _empirical_mean(values, counts)
        self._support_seen_n[:] = n
        self._support_seen_S[:] = S

    def observe(self, index, reward):
        if self._pending != index:
            raise RuntimeError("observation does not match the selected arm")
        if not 0. <= reward <= 1.:
            raise ValueError("rewards must lie in [0, 1]")
        if self.kernel == "SB-EXP3-ATGT":
            loss = 1. - reward
            probability = float(self._probabilities[index])
            if probability <= 0.:
                raise FloatingPointError("selected action has zero numerical probability")
            self._L[:self._last_k] += loss
            self._L[index] -= loss / probability
        elif self.kernel == "TS-SMAB-bounded":
            self._observations[index] += 1
            if reward >= 1. or (reward > 0. and self.rng.random() < reward):
                self._successes[index] += 1.
        self._pending = None

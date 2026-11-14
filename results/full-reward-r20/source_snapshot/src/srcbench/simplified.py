"""Simplified draft §§3–5: FULL, GT_M, lifetime min-count and price gate.

The public policy receives only arrivals and observed rewards. OFF may omit
passive evidence in an explicitly reward-only experiment; report() then raises.
No future horizon, distributions, means, resource LP or service quota is used.
"""
from __future__ import annotations

from fractions import Fraction
import math
import numpy as np

from .mathcore import njit, NumericList, dinf, inverse_index, bernoulli_kl, reporter

FULL_METHOD = dict(id="FULL-R", family="full", kernel="FULL", params={"mode": "OFF"},
                   preference=0., beta_r=None, beta_c=None, known_horizon=False)


def task_bets(eta):
    """Exact dyadic decision for the public rule 1+ceil(log2(2/eta+1+eta/2))."""
    if not math.isfinite(eta) or eta <= 0:
        raise ValueError("eta must be positive and finite")
    if eta >= 1:
        return 1
    e = Fraction.from_float(float(eta))
    target = 2/e + 1 + e/2
    exponent = 0
    while 2**exponent < target:
        exponent += 1
    return 1 + exponent


@njit(cache=True)
def full_budget(v, n):
    z = max(0., math.log(v/n))
    return z + math.log1p(z*z)


@njit(cache=True)
def support_summary(values, counts):
    total, weighted, correction = 0., 0., 0.
    perfect = True
    for j in range(len(values)):
        if counts[j] > 0:
            total += counts[j]
            term = counts[j]*values[j] - correction
            updated = weighted + term
            correction = (updated-weighted)-term
            weighted = updated
            if values[j] < 1:
                perfect = False
    mean = weighted/total if total else 0.
    if not perfect and mean >= 1:
        mean = np.nextafter(1., 0.)
    return mean, perfect


@njit(cache=True)
def full_index(values, counts, mean, perfect, budget):
    if perfect:
        return 1.
    if budget == 0:
        return mean
    return inverse_index(values, counts, budget)


@njit(cache=True)
def full_scores(n, values, counts, means, perfect, v, prune=True):
    """Current-budget certificates only; contenders and ties get full inversion."""
    k = len(n)
    scores = np.zeros(k)
    exact = np.zeros(k, dtype=np.bool_)
    for i in range(k):
        if n[i] == 0:
            scores[i], exact[i] = 1., True
            return i, scores, exact  # Explicit unobserved-first rule.
    first = int(np.argmax(means))
    budgets = np.empty(k)
    for i in range(k):
        budgets[i] = full_budget(v, n[i])
    scores[first] = full_index(values[first], counts[first], means[first], perfect[first], budgets[first])
    exact[first] = True
    best = scores[first]
    winner = first
    for i in range(k):
        if i == first:
            continue
        target = max(0., best-1e-8)
        slack = 1e-9+5e-12*n[i]
        if prune and budgets[i] > 0:
            if target > means[i] and n[i]*bernoulli_kl(means[i], target) > budgets[i]+slack:
                scores[i] = target
                continue
            if n[i]*dinf(values[i], counts[i], target) > budgets[i]+slack:
                scores[i] = target
                continue
        score = full_index(values[i], counts[i], means[i], perfect[i], budgets[i])
        scores[i], exact[i] = score, True
        if score > best or (score == best and i < winner):
            best, winner = score, i
    return winner, scores, exact


@njit(cache=True)
def gt_log_wealth(values, counts, total, n, m, sign, eta, M):
    """Normalized mixture, in log space; zero factors remain zero wealth."""
    components = np.empty(M+1)
    components[0] = -math.log(2.) + 1.5*sign*eta*(total-n*m)-9*n*eta*eta/32
    for j in range(M):
        b = 2.**(-j)
        value = -math.log(2.*M)
        for r in range(len(values)):
            if counts[r] > 0:
                u = sign*b*(values[r]-m)
                if u <= -1:
                    value = -math.inf
                    break
                value += counts[r]*math.log1p(u)
        components[j+1] = value
    largest = np.max(components)
    return largest + math.log(np.sum(np.exp(components-largest)))


@njit(cache=True)
def gt_interval(values, counts, total, n, alpha, eta, M):
    threshold = -math.log(alpha)
    lower, upper = 0., 1.
    if gt_log_wealth(values, counts, total, n, 0., 1., eta, M) > threshold:
        lo, hi = 0., 1.
        for _ in range(53):
            mid = (lo+hi)/2
            if gt_log_wealth(values, counts, total, n, mid, 1., eta, M) > threshold:
                lo = mid
            else:
                hi = mid
        lower = np.nextafter(lo, 0.)
    if gt_log_wealth(values, counts, total, n, 1., -1., eta, M) > threshold:
        lo, hi = 0., 1.
        for _ in range(53):
            mid = (lo+hi)/2
            if gt_log_wealth(values, counts, total, n, mid, -1., eta, M) > threshold:
                hi = mid
            else:
                lo = mid
        upper = np.nextafter(hi, 1.)
    return lower, upper


class FullPolicy:
    def __init__(self, method=None, epsilon=.2, eta=.015, delta=.05, seed=0,
                 *, mode=None, price=None, M=None, track_reports=True):
        params = (method or FULL_METHOD).get("params", {})
        self.mode = mode if mode is not None else params.get("mode", "OFF")
        self.price = float(price if price is not None else params.get("price", 0.))
        self.M = M if M is not None else params.get("M", task_bets(eta))
        if not (0 < epsilon < 1 and eta > 0 and math.isfinite(eta) and 0 < delta < 1):
            raise ValueError("invalid reporting task parameters")
        if self.mode not in ("OFF", "ON") or not math.isfinite(self.price) or self.price < 0:
            raise ValueError("require OFF/ON and finite nonnegative price")
        if not isinstance(self.M, (int, np.integer)) or not 1 <= self.M <= 64:
            raise ValueError("this floating implementation supports integer M in [1,64]")
        if not track_reports and self.mode != "OFF":
            raise ValueError("ON requires evidence and reports")
        self.epsilon, self.eta, self.delta = epsilon, eta, delta
        self.track_reports = bool(track_reports)
        self.rng = np.random.default_rng(seed)
        self.ids, self._positions, self._maps = [], {}, []
        self.n = np.empty(0, dtype=np.int64)
        self.S = np.empty(0)
        self.lower, self.upper = np.empty(0), np.empty(0)
        self.means = np.empty(0)
        self.perfect = np.empty(0, dtype=np.bool_)
        self._values, self._counts = NumericList(), NumericList()
        self._sizes = []
        self.t = self.base = self.sigma = self.dclock = 0
        self._pending = None
        self.failed = False
        self.last_decision = {}
        self.last_scores = self.last_score_exact = None

    def choose(self, new_arms=()):
        if self._pending is not None:
            raise RuntimeError("observe must follow choose")
        items = list(new_arms)
        if not self.ids and not items:
            raise ValueError("an initial arm is required")
        if len(set(items)) != len(items) or any(i in self._positions for i in items):
            raise ValueError("duplicate arm identifiers")
        self.t += 1
        for arm in items:
            self._positions[arm] = len(self.ids)
            self.ids.append(arm)
            self._maps.append({})
            self._sizes.append(0)
            self._values.append(np.zeros(4))
            self._counts.append(np.zeros(4, dtype=np.int64))
        if items:
            m = len(items)
            self.n = np.r_[self.n, np.zeros(m, dtype=np.int64)]
            for field in ("S", "lower", "means"):
                setattr(self, field, np.r_[getattr(self, field), np.zeros(m)])
            self.upper = np.r_[self.upper, np.ones(m)]
            self.perfect = np.r_[self.perfect, np.ones(m, dtype=np.bool_)]
        k = len(self.n)
        if k > 1 and (self.base == 0 or k-1 >= 2*self.base):
            self.base, self.sigma, self.dclock = k-1, self.t, 2*(k-1)
        v = (self.t-self.sigma+1)/self.dclock if k > 1 else 1.
        if k == 1:
            reward_arm, scores, exact = 0, np.ones(1), np.ones(1, dtype=bool)
        else:
            reward_arm, scores, exact = full_scores(self.n, self._values, self._counts,
                                                    self.means, self.perfect, v)
        chosen, service_arm, probability, xi = reward_arm, None, 0., 0.
        if self.mode == "ON" and not self.failed:
            _, work = reporter(self.lower, self.upper, self.epsilon, self.eta)
            busy = int(np.count_nonzero(work))
            if busy:
                eligible = work | (self.upper >= np.max(self.lower))
                options = np.flatnonzero(eligible)
                service_arm = int(options[np.argmin(self.n[options])])
                if not exact[service_arm]:
                    if self.n[service_arm] == 0:
                        scores[service_arm] = 1.
                    else:
                        scores[service_arm] = full_index(self._values[service_arm], self._counts[service_arm],
                            self.means[service_arm], self.perfect[service_arm], full_budget(v, self.n[service_arm]))
                    exact[service_arm] = True
                xi = max(0., scores[reward_arm]-scores[service_arm])
                probability = busy/(busy+self.price*xi)
                if self.rng.random() < probability:
                    chosen = service_arm
        self.last_scores, self.last_score_exact = scores, exact
        self.last_decision = dict(t=self.t, index=int(chosen), arm=self.ids[chosen],
            reward_candidate=int(reward_arm), service_candidate=service_arm,
            branch="service" if service_arm is not None and chosen == service_arm else "reward",
            probability=probability, opportunity_gap=xi)
        self._pending = int(chosen)
        return self.ids[chosen]

    def observe(self, reward):
        if self._pending is None:
            raise RuntimeError("choose must precede observe")
        y = float(reward)
        if not math.isfinite(y) or not 0 <= y <= 1:
            raise ValueError("reward must be finite in [0,1]")
        i = self._pending
        self.n[i] += 1
        self.S[i] += y
        mapping = self._maps[i]
        if y in mapping:
            self._counts[i][mapping[y]] += 1
        else:
            size = self._sizes[i]
            if size == len(self._values[i]):
                self._values[i] = np.r_[self._values[i], np.zeros(size)]
                self._counts[i] = np.r_[self._counts[i], np.zeros(size, dtype=np.int64)]
            self._values[i][size], self._counts[i][size] = y, 1
            mapping[y] = size
            self._sizes[i] += 1
        self.means[i], self.perfect[i] = support_summary(self._values[i], self._counts[i])
        if self.track_reports and not self.failed:
            rank = i+1
            lo, hi = gt_interval(self._values[i], self._counts[i], self.S[i], self.n[i],
                                  self.delta/(4*rank*(rank+1)), self.eta, self.M)
            self.lower[i], self.upper[i] = max(self.lower[i], lo), min(self.upper[i], hi)
            self.failed = bool(self.lower[i] > self.upper[i])
        self._pending = None

    def report(self):
        if not self.track_reports:
            raise RuntimeError("passive reporting was explicitly disabled for reward-only evaluation")
        labels, _ = reporter(self.lower, self.upper, self.epsilon, self.eta, self.failed)
        return tuple([self.ids[i] for i in range(len(self.ids)) if labels[i] == label]
                     for label in (1, -1, 0))

    def state(self):
        return dict(t=self.t, arms=len(self.ids), base=self.base, sigma=self.sigma,
                    mode=self.mode, price=self.price, M=self.M, failed=self.failed,
                    reports_evaluated=self.track_reports)

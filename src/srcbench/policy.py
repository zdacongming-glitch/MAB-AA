"""One-observation-at-a-time no-H8 SRC and SRC-KL allocation state."""
from __future__ import annotations

import math
import numpy as np

from .mathcore import (NumericList, dinf, inverse_index, prefix_interval,
                       reporter, spectrum_scale, reference_indices,
                       information_choice, service_plan)


class Policy:
    """Admit current arrivals, choose one arm, then observe exactly one reward.

    The state never receives true means, future arrivals, or a reward law.
    ``Q`` is the lifetime reward square sum; ``quota`` is the service cap.
    ``supports`` exposes only observed distinct values and their counts.
    """

    def __init__(self, method: dict, epsilon, eta, delta, seed=0, horizon=None):
        if not (0 < eta < epsilon < 1 and 0 < delta < 1):
            raise ValueError('require 0 < eta < epsilon < 1 and 0 < delta < 1')
        self.method = dict(method)
        self.method['params'] = dict(method.get('params', {}))
        self.family = method.get('family', 'src')
        if self.family not in ('src', 'src_kl', 'baseline'):
            raise ValueError('unknown policy family')
        self.epsilon, self.eta, self.delta = float(epsilon), float(eta), float(delta)
        self.preference = float(method.get('preference', 0))
        if not 0 <= self.preference <= 1:
            raise ValueError('preference must be in [0,1]')
        self.beta_r = self._budget(method.get('beta_r', 32))
        self.beta_c = self._budget(method.get('beta_c', 1))
        self.params = self.method['params']
        self.planner = method.get('planner', 'paired')
        if self.planner not in ('paired', 'widest', 'lucb'):
            raise ValueError('unknown classification planner')
        self.reference = self.params.get('reference', 'kl_switch' if self.family == 'src_kl' else 'moss')
        self.reward_cap = self.params.get('reward_cap', 'sublog' if self.family == 'src_kl' else 'spectrum')
        if self.reference not in ('moss', 'kl_switch') or self.reward_cap not in ('spectrum', 'sublog'):
            raise ValueError('unknown reference or reward cap')
        for name, default in [('nu', .02), ('relevance_floor', .02), ('rate_floor', .02), ('backlog_scale', 4), ('cap_multiplier', 1)]:
            value = float(self.params.get(name, default))
            if not math.isfinite(value) or value <= 0:
                raise ValueError(name+' must be positive and finite')
            if name.endswith('_floor') and value > 1:
                raise ValueError(name+' must not exceed one')
        coefficient = float(self.params.get('log_coefficient', .5))
        if not math.isfinite(coefficient) or coefficient < 0:
            raise ValueError('log_coefficient must be nonnegative and finite')
        self.ids, self._id_to_index = [], {}
        self.n = np.empty(0, dtype=np.int64)
        self.S = np.empty(0, dtype=np.float64)
        self.Q = np.empty(0, dtype=np.float64)
        self.births = np.empty(0, dtype=np.int64)
        self.lower = np.empty(0, dtype=np.float64)
        self.upper = np.empty(0, dtype=np.float64)
        self.quota = np.empty(0, dtype=np.int64)
        self.alpha = np.empty(0, dtype=np.float64)
        self.supports = []
        self._values, self._counts = NumericList(), NumericList()
        self._support_maps, self._support_sizes = [], []
        self.t, self.base, self.sigma, self.dclock = 0, 0, 0, 0
        self.phase, self.reward_tax, self.service_tax, self.budget_scale = 0., 0., 0., 0.
        self.failed = False
        self.checkpoint_hits = self.service_pulls = self.reward_pulls = 0
        self.service_attempts = self.service_denials = 0
        self.guard_exclusions = self.guard_changed = 0
        self.service_mass = 0.
        self.last_decision = {}
        self._pending = None
        self._baseline = None
        if self.family == 'baseline':
            from .baselines import BaselineSelector
            self._baseline = BaselineSelector(self.method, seed=seed, horizon=horizon)

    @staticmethod
    def _budget(value):
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or value < 0:
            raise ValueError('budget coefficients must be nonnegative')
        return None if math.isinf(value) else value

    def set_preference(self, preference):
        """Change preference between completed rounds, preserving all history."""
        if self._pending is not None:
            raise RuntimeError('finish the pending observation before changing preference')
        if not 0 <= preference <= 1:
            raise ValueError('preference must be in [0,1]')
        self.preference = float(preference)

    def _admit(self, new_arms):
        items = list(new_arms)
        if len(set(items)) != len(items) or any(arm in self._id_to_index for arm in items):
            raise ValueError('new arm identifiers must be unique and not previously admitted')
        if not items:
            return
        start, count = len(self.ids), len(items)
        for offset, arm in enumerate(items):
            self._id_to_index[arm] = start+offset
        self.ids.extend(items)
        self.n = np.concatenate((self.n, np.zeros(count, dtype=np.int64)))
        for name in ('S', 'Q', 'lower'):
            setattr(self, name, np.concatenate((getattr(self, name), np.zeros(count))))
        self.upper = np.concatenate((self.upper, np.ones(count)))
        self.births = np.concatenate((self.births, np.full(count, self.t, dtype=np.int64)))
        ranks = np.arange(start+1, start+count+1, dtype=np.float64)
        self.alpha = np.concatenate((self.alpha, self.delta/(2*ranks*(ranks+1))))
        quota = np.ceil(32/self.eta**2*np.log(4*ranks*(ranks+1)/self.delta))
        if np.any(quota > np.iinfo(np.int64).max):
            raise ValueError('checkpoint quota exceeds supported integer range')
        self.quota = np.concatenate((self.quota, quota.astype(np.int64)))
        for _ in items:
            values, counts = np.zeros(4), np.zeros(4, dtype=np.int64)
            self._values.append(values)
            self._counts.append(counts)
            self.supports.append((values[:0], counts[:0]))
            self._support_maps.append({})
            self._support_sizes.append(0)

    def _references(self):
        values = reference_indices(self.n, self.S, self.t, self.sigma, self.dclock)
        if self.reference == 'kl_switch' and len(self.n) > 1:
            v = (self.t-self.sigma+1)/self.dclock
            threshold = int(v**.2)
            # Correct a possible floating rounding at perfect fifth powers.
            while (threshold+1)**5 <= v:
                threshold += 1
            while threshold**5 > v:
                threshold -= 1
            for i in np.flatnonzero((self.n > 0) & (self.n <= threshold)):
                logratio = max(0., math.log(v/self.n[i]))
                phi = max(0., math.log(v/self.n[i])+math.log1p(logratio*logratio))
                values[i] = inverse_index(self._values[i], self._counts[i], phi)
        return values

    def choose(self, new_arms=()):
        if self._pending is not None:
            raise RuntimeError('observe the previous choice before choosing again')
        items = list(new_arms)
        if not self.ids and not items:
            raise ValueError('at least one arm must be available on the first round')
        # Validate before advancing the physical clock.
        if len(set(items)) != len(items) or any(x in self._id_to_index for x in items):
            raise ValueError('new arm identifiers must be unique')
        self.t += 1
        self._admit(items)
        k = len(self.n)
        if k > 1 and (self.base == 0 or k-1 >= 2*self.base):
            self.base, self.sigma, self.dclock = k-1, self.t, 2*(k-1)
        self.budget_scale = max(self.budget_scale, float(spectrum_scale(self.births, self.t)))
        reference = self._references()
        deficits = np.max(reference)-reference
        budget_r = math.inf if self.beta_r is None else self.beta_r*self.budget_scale
        if self.reward_cap == 'sublog':
            budget_r = min(budget_r, self.params.get('cap_multiplier', 1)*math.sqrt(math.log(math.e+self.t)))
        budget_c = math.inf if self.beta_c is None else self.beta_c*self.budget_scale
        attempt = denied = classification = False
        probability, chosen, backlog, exclusions, changed = 0., -1, 0, 0, False
        if self.family == 'baseline':
            chosen = int(self._baseline.choose(self.n, self.S, self.Q, self.births,
                                              self.t, self.base, self.sigma, self.supports))
            if not 0 <= chosen < k:
                raise RuntimeError('baseline selected an unavailable arm')
        else:
            if not self.failed and self.preference > 0:
                variant = {'paired': 0, 'widest': 1, 'lucb': 2}[self.planner]
                proposal, boundary, backlog, chat = service_plan(
                    self.n, self.S, self.Q, self.lower, self.upper, self.quota,
                    self.epsilon, self.eta, self.preference, variant,
                    float(self.params.get('nu', .02)), float(self.params.get('relevance_floor', .02)))
                if proposal >= 0 and backlog > 0:
                    p0 = float(self.params.get('rate_floor', .02))
                    weight = p0+(1-p0)*backlog/(backlog+self.params.get('backlog_scale', 4))*self.epsilon/(self.epsilon+chat)
                    probability = boundary*self.preference*weight/(1-self.preference+self.preference*weight)
                    self.phase += probability
                    self.service_mass += probability
                    if self.phase >= 1:
                        self.phase -= 1
                        attempt = True
                        self.service_attempts += 1
                        tolerance_c = 0.0 if budget_c == 0 else 1e-12
                        if self.n[proposal] < self.quota[proposal] and self.service_tax+deficits[proposal] <= budget_c+tolerance_c:
                            chosen, classification = int(proposal), True
                        else:
                            denied = True
                            self.service_denials += 1
            if not classification:
                tolerance_r = 0.0 if budget_r == 0 else 1e-12
                allowed = self.reward_tax+deficits <= budget_r+tolerance_r
                if not np.any(allowed):
                    raise RuntimeError('empty feasible reward set: budget invariant violated')
                coefficient = float(self.params.get('log_coefficient', .5))
                chosen = int(information_choice(self.n, self.S, allowed, self._values, self._counts, coefficient))
                exclusions = int(k-np.count_nonzero(allowed))
                if exclusions:
                    raw = int(information_choice(self.n, self.S, np.ones(k, dtype=np.bool_), self._values, self._counts, coefficient))
                    changed = raw != chosen
                self.guard_exclusions += exclusions
                self.guard_changed += int(changed)
        deficit = float(deficits[chosen])
        if self.family != 'baseline':
            if classification:
                self.service_tax += deficit
            else:
                self.reward_tax += deficit
        self.last_decision = {
            't': self.t, 'index': chosen, 'arm': self.ids[chosen],
            'branch': 'classification' if classification else 'reward',
            'attempt': bool(attempt), 'denied': bool(denied),
            'guard_exclusions': exclusions, 'guard_changed': bool(changed),
            'reference_deficit': deficit, 'probability': float(probability),
            'reference_index': float(reference[chosen]), 'budget_r': float(budget_r),
            'budget_c': float(budget_c), 'backlog': int(backlog),
        }
        self._pending = chosen
        return self.ids[chosen]

    def observe(self, reward):
        if self._pending is None:
            raise RuntimeError('choose an arm before observing a reward')
        y = float(reward)
        if not math.isfinite(y) or not 0 <= y <= 1:
            raise ValueError('reward must be finite and lie in [0,1]')
        i = self._pending
        self.n[i] += 1
        self.S[i] += y
        self.Q[i] += y*y
        mapping = self._support_maps[i]
        if y in mapping:
            self._counts[i][mapping[y]] += 1
        else:
            length = self._support_sizes[i]
            if length == len(self._values[i]):
                values, counts = np.zeros(2*length), np.zeros(2*length, dtype=np.int64)
                values[:length], counts[:length] = self._values[i], self._counts[i]
                self._values[i], self._counts[i] = values, counts
            self._values[i][length], self._counts[i][length] = y, 1
            mapping[y] = length
            self._support_sizes[i] += 1
        length = self._support_sizes[i]
        self.supports[i] = (self._values[i][:length], self._counts[i][:length])
        if self.n[i] == self.quota[i]:
            self.checkpoint_hits += 1
        if not self.failed:
            lower, upper = prefix_interval(int(self.n[i]), float(self.S[i]), float(self.alpha[i]))
            self.lower[i], self.upper[i] = max(self.lower[i], lower), min(self.upper[i], upper)
            if self.n[i] == self.quota[i]:
                mean = self.S[i]/self.n[i]
                self.lower[i] = max(self.lower[i], mean-self.eta/8, 0.)
                self.upper[i] = min(self.upper[i], mean+self.eta/8, 1.)
            self.failed = bool(self.lower[i] > self.upper[i])
        if self._baseline is not None:
            self._baseline.observe(i, y)
        if self.last_decision['branch'] == 'classification':
            self.service_pulls += 1
        else:
            self.reward_pulls += 1
        self.last_decision['reward'] = y
        self._pending = None

    def report(self):
        labels, _ = reporter(self.lower, self.upper, self.epsilon, self.eta, self.failed)
        return tuple([self.ids[i] for i in range(len(self.ids)) if labels[i] == label]
                     for label in (1, -1, 0))

    def state(self):
        return {'t': self.t, 'arms': len(self.n), 'base': self.base, 'sigma': self.sigma,
                'phase': self.phase, 'reward_tax': self.reward_tax,
                'service_tax': self.service_tax, 'budget_scale': self.budget_scale,
                'arrival_spectrum': float(spectrum_scale(self.births, self.t)),
                'checkpoint_hits': self.checkpoint_hits, 'failed': self.failed,
                'empty_intersection': int(self.failed), 'reward_pulls': self.reward_pulls,
                'service_pulls': self.service_pulls, 'service_attempts': self.service_attempts,
                'service_denials': self.service_denials, 'service_mass': self.service_mass,
                'guard_exclusions': self.guard_exclusions, 'guard_changed': self.guard_changed}

    @property
    def diagnostics(self):
        return self.state()

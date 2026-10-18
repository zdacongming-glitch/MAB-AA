"""Horizon-free, history-preserving MOSS for persistently arriving arms.

The policy API receives only newly available arm labels and observed rewards.
It never receives the horizon, future arrivals, true means, or analysis gaps.
Python >= 3.10; standard library only. See the report for exact guarantees.
"""
from __future__ import annotations

import math
from collections.abc import Hashable, Iterable


class MCMOSS:
    """Clock-only MOSS with an optional reward-range clipping rule.

    Args:
        clip: Clip observed indices at 1 and assign unobserved arms index 1.
              False gives Equation (4.2); True gives Proposition 7.
        cold_reset: Clear all statistics when the competitor count doubles.
                    This is the diagnostic baseline, not the main algorithm.

    Call select(new_arms) exactly once per round, then update(reward).
    Arm labels must be hashable and never reused. Rewards must be in [0, 1].
    Ties are resolved by arrival order, then order within the supplied batch.
    """

    def __init__(self, *, clip: bool = False, cold_reset: bool = False) -> None:
        self.clip = bool(clip)
        self.cold_reset = bool(cold_reset)
        self.t = 0
        self.clock_resets = 0
        self._base = 0
        self._start = 0
        self._denom = 1
        self._n: dict[Hashable, int] = {}
        self._sums: dict[Hashable, float] = {}
        self._lifetime: dict[Hashable, int] = {}
        self._pending: tuple[Hashable, int] | None = None

    def select(self, new_arms: Iterable[Hashable] = ()) -> Hashable:
        if self._pending is not None:
            raise RuntimeError("Supply the pending reward with update() first")
        batch = list(new_arms)
        seen: set[Hashable] = set()
        for arm in batch:
            try:
                hash(arm)
            except TypeError as exc:
                raise TypeError("Arm labels must be hashable") from exc
            if arm in seen or arm in self._n:
                raise ValueError(f"Duplicate or previously registered arm: {arm!r}")
            seen.add(arm)
        if not self._n and not batch:
            raise ValueError("The first round must contain at least one arm")
        for arm in batch:
            self._n[arm] = 0
            self._sums[arm] = 0.0
            self._lifetime[arm] = 0
        self.t += 1
        k = len(self._n)
        if k == 1:
            chosen = next(iter(self._n))
        else:
            if self._base == 0 or k - 1 >= 2 * self._base:
                self._base = k - 1
                self._start = self.t
                self._denom = 2 * self._base
                self.clock_resets += 1
                if self.cold_reset:
                    for arm in self._n:
                        self._n[arm] = 0
                        self._sums[arm] = 0.0
            s = self.t - self._start + 1
            maximum = -math.inf
            chosen = next(iter(self._n))
            for arm, n in self._n.items():
                if n == 0:
                    index = 1.0 if self.clip else math.inf
                else:
                    ratio = s / (self._denom * n)
                    bonus = math.sqrt(math.log(ratio) / n) if ratio > 1.0 else 0.0
                    index = self._sums[arm] / n + bonus
                    if self.clip:
                        index = min(1.0, index)
                if index > maximum:
                    maximum, chosen = index, arm
        self._pending = (chosen, self.t)
        return chosen

    def update(self, reward: float) -> None:
        if self._pending is None:
            raise RuntimeError("Call select() before supplying a reward")
        value = float(reward)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError("Reward must be finite and in [0, 1]")
        arm, _ = self._pending
        self._n[arm] += 1
        self._sums[arm] += value
        self._lifetime[arm] += 1
        self._pending = None

    @property
    def lifetime_counts(self) -> dict[Hashable, int]:
        """A copy: external callers cannot change the algorithm's counts."""
        return dict(self._lifetime)

    @property
    def statistical_counts(self) -> dict[Hashable, int]:
        """Equal to lifetime counts unless the cold-reset baseline is used."""
        return dict(self._n)

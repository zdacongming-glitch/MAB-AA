"""Evaluator-only environments and paired, lazily generated potential rewards.

No environment object is passed into a policy. Random streams are keyed by
original arm identity and pull number, independently of method and worker order.
The 16 reward laws reproduce the archived numerical definitions, not archived
C++ standard-library random-number bytes.
"""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy

import numpy as np


def stable_seed(*parts) -> int:
    data = json.dumps(parts, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "little")


def record_flags(arms: list[dict]) -> list[bool]:
    """Record status uses the best of the entire simultaneous arrival batch."""
    flags = [False] * len(arms)
    previous_best = 0.0
    i = 0
    while i < len(arms):
        j = i + 1
        while j < len(arms) and arms[j]["arrival"] == arms[i]["arrival"]:
            j += 1
        batch_best = max(previous_best, *(float(a["mean"]) for a in arms[i:j]))
        for k in range(i, j):
            flags[k] = float(arms[k]["mean"]) >= batch_best - 1e-14
        previous_best = batch_best
        i = j
    return flags


def prepare_layout(layout: dict, seed_base: int, law: str, rep: int) -> dict:
    result = deepcopy(layout)
    arms = result["arms"]
    if not arms or arms[0]["arrival"] != 1:
        raise ValueError("A layout must have an initial arm at physical time one")
    if any(int(a["arrival"]) < 1 or int(a["arrival"]) > layout["T"]
           or not 0 <= float(a["mean"]) <= 1 for a in arms):
        raise ValueError("Invalid arm arrival or mean")
    if any(a["arrival"] > b["arrival"] for a, b in zip(arms, arms[1:])):
        raise ValueError("Arms must be in arrival order")
    flags = record_flags(arms)
    for i, a in enumerate(arms):
        a["original_id"] = i
        a["record"] = flags[i]
    rng = np.random.default_rng(stable_seed(seed_base, layout["id"], law, rep, "labels"))
    i = 0
    while i < len(arms):
        j = i + 1
        while j < len(arms) and arms[j]["arrival"] == arms[i]["arrival"]:
            j += 1
        batch = arms[i:j]
        arms[i:j] = [batch[int(k)] for k in rng.permutation(len(batch))]
        i = j
    return result


def sample_reward(rng: np.random.Generator, mu: float, law: str, record: bool) -> float:
    """One iid observation with exactly the declared mean and [0,1] support."""
    h = min(mu, 1.0 - mu)
    if law == "deterministic" or h == 0:
        return mu
    if law == "bernoulli":
        return float(rng.random() < mu)
    if law == "two_point":
        return mu + (-1 if rng.random() < .5 else 1) * min(.045, h)
    if law == "uniform":
        return mu + (2 * rng.random() - 1) * h
    if law == "trunc_normal":
        z = rng.standard_normal()
        while abs(z) > 2:
            z = rng.standard_normal()
        return mu + .5 * h * z
    if law == "spike_mix":
        return float(rng.random() < mu) if rng.random() < .1 else mu
    if law == "endpoint_two":
        a = min(.01, .5 * h)
        b = 1 - a
        return b if rng.random() < (mu - a) / (b - a) else a
    if law in {"rare_jackpot", "hetero_jackpot"}:
        if law == "hetero_jackpot" and not record:
            return mu
        p = min(.02, .5 * mu)
        return 1.0 if rng.random() < p else (mu - p) / (1 - p)
    if law in {"beta02", "beta2", "beta20"}:
        concentration = {"beta02": .2, "beta2": 2.0, "beta20": 20.0}[law]
        return float(rng.beta(concentration * mu, concentration * (1 - mu)))
    sizes = {"binomial4": 4, "binomial16": 16,
             "hetero_best_noisy": 1 if record else 16,
             "hetero_best_quiet": 16 if record else 1}
    if law in sizes:
        n = sizes[law]
        return float(rng.binomial(n, mu) / n)
    raise ValueError(f"Unknown reward law: {law}")


class PotentialRewards:
    """A shared per-cell cache; generating a reward never advances another arm."""

    def __init__(self, layout: dict, law: str, rep: int, seed_base: int):
        self.layout = prepare_layout(layout, seed_base, law, rep)
        self.law = law
        self.cache: list[list[float]] = [[] for _ in self.layout["arms"]]
        self.rngs = [np.random.default_rng(stable_seed(
            seed_base, layout["id"], law, rep, "reward", a["original_id"]))
            for a in self.layout["arms"]]

    def draw(self, arm: int, pull_index: int) -> float:
        if arm < 0 or arm >= len(self.cache) or pull_index < 0:
            raise ValueError("Invalid potential reward request")
        a = self.layout["arms"][arm]
        buf = self.cache[arm]
        while len(buf) <= pull_index:
            y = sample_reward(self.rngs[arm], a["mean"], self.law, a["record"])
            if not math.isfinite(y) or not 0 <= y <= 1:
                raise ArithmeticError("Reward generator violated bounded support")
            buf.append(y)
        return buf[pull_index]

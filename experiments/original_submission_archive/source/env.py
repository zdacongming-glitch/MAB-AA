from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

MASK64 = (1 << 64) - 1


def _mix_uint64(x: int) -> int:
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9 & MASK64
    x = (x ^ (x >> 27)) * 0x94D049BB133111EB & MASK64
    return (x ^ (x >> 31)) & MASK64


def _seed_from_values(*values: int) -> int:
    state = 0xA0761D6478BD642F
    for value in values:
        state = _mix_uint64(state ^ (int(value) & MASK64))
    return state


def _u01_from_values(*values: int) -> float:
    x = _seed_from_values(*values)
    return ((x >> 11) & ((1 << 53) - 1)) / float(1 << 53)


def _clip01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def _sample_mixture_mean(rng: np.random.Generator, params: Dict[str, float]) -> float:
    pi_good = float(params.get("pi_good", 0.1))
    mu_h = float(params.get("mu_h", 0.9))
    delta = float(params.get("delta", 0.1))
    mu_l = float(params.get("mu_l", 0.1))
    mu_m = float(params.get("mu_m", 0.5))

    if rng.random() < pi_good:
        low = max(0.0, mu_h - delta)
        high = min(1.0, mu_h)
    else:
        low = max(0.0, mu_l)
        high = min(1.0, mu_m)

    if high <= low:
        return _clip01(low)
    return float(rng.uniform(low, high))


def build_replicate_tape(config: Dict, seed: int, replicate: int) -> Dict:
    """Build deterministic arrivals + arm means for one replicate (CRN tape)."""
    T = int(config["T"])
    K0 = int(config["K0"])
    scenario = str(config.get("scenario", "B")).upper()
    scenario_params = dict(config.get("scenario_params", {}))

    arrival_seed = _seed_from_values(seed, replicate, 101)
    mean_seed = _seed_from_values(seed, replicate, 202)
    arrival_rng = np.random.default_rng(arrival_seed)
    mean_rng = np.random.default_rng(mean_seed)

    mode = str(config.get("arrival_mode", "bernoulli")).lower()
    lam = float(config.get("lambda", config.get("lam", 1.0 / 200.0)))
    rho = float(config.get("rho", lam))
    burst_B = int(config.get("B", scenario_params.get("B", 100)))
    t_burst = config.get("T_burst", scenario_params.get("T_burst", []))
    burst_set = set(int(x) for x in t_burst)

    if scenario == "F":
        scenario_params.setdefault("pi_good", 0.02)

    def draw_near_opt_mean() -> float:
        mu_top = float(scenario_params.get("mu_top", 0.8))
        delta_min = float(scenario_params.get("Delta_min", scenario_params.get("delta_min", 0.01)))
        return _clip01(mu_top - mean_rng.uniform(0.0, max(delta_min, 1e-12)))

    def draw_base_mean() -> float:
        if scenario == "D":
            return float(mean_rng.uniform(0.1, 0.4))
        return _sample_mixture_mean(mean_rng, scenario_params)

    def draw_arrival_mean() -> float:
        if scenario == "E":
            p_join_near = float(scenario_params.get("p_join_near", 0.3))
            if mean_rng.random() < p_join_near:
                return draw_near_opt_mean()
        return draw_base_mean()

    forced_by_t: Dict[int, List[float]] = {}
    if scenario == "C":
        gammas = scenario_params.get("gamma", (0.2, 0.5, 0.8))
        delta_step = float(scenario_params.get("Delta_step", scenario_params.get("delta_step", 0.05)))
        r0 = float(scenario_params.get("r0", 0.6))
        for k, g in enumerate(gammas, start=1):
            gval = float(g)
            tau = int(np.floor(gval * T)) if gval <= 1.0 else int(gval)
            tau = max(1, min(T, tau))
            forced_by_t.setdefault(tau, []).append(_clip01(r0 + k * delta_step))

    def sample_arrival_count(t: int) -> int:
        if scenario == "D":
            return burst_B if t in burst_set else 0

        if mode == "bernoulli":
            return int(arrival_rng.random() < lam)
        if mode == "poisson":
            return int(arrival_rng.poisson(rho))
        if mode == "burst":
            return burst_B if t in burst_set else 0
        raise ValueError(f"Unsupported arrival mode: {mode}")

    arm_means: Dict[int, float] = {}
    arrived_time: Dict[int, int] = {}

    initial_arm_ids = list(range(K0))
    if scenario == "E":
        m0 = int(scenario_params.get("m0", 5))
        for i in range(K0):
            arm_means[i] = draw_near_opt_mean() if i < m0 else draw_base_mean()
            arrived_time[i] = 1
    else:
        for i in range(K0):
            arm_means[i] = draw_base_mean()
            arrived_time[i] = 1

    next_arm_id = K0
    arrival_arm_ids_by_t: Dict[int, List[int]] = {t: [] for t in range(1, T + 1)}

    for t in range(1, T + 1):
        means_this_t: List[float] = []
        regular_cnt = sample_arrival_count(t)

        if scenario == "D" and regular_cnt > 0:
            p_spike = float(scenario_params.get("p_spike", 0.5))
            high_mean = float(scenario_params.get("high_mean", 0.8))
            if arrival_rng.random() < p_spike:
                means_this_t.append(_clip01(high_mean))
                for _ in range(max(0, regular_cnt - 1)):
                    means_this_t.append(float(mean_rng.uniform(0.1, 0.4)))
            else:
                for _ in range(regular_cnt):
                    means_this_t.append(float(mean_rng.uniform(0.1, 0.4)))
        else:
            for _ in range(regular_cnt):
                means_this_t.append(draw_arrival_mean())

        if scenario == "C":
            means_this_t.extend(forced_by_t.get(t, []))

        for mean in means_this_t:
            arm_means[next_arm_id] = _clip01(mean)
            arrived_time[next_arm_id] = t
            arrival_arm_ids_by_t[t].append(next_arm_id)
            next_arm_id += 1

    return {
        "T": T,
        "K0": K0,
        "scenario": scenario,
        "arrival_mode": mode,
        "initial_arm_ids": initial_arm_ids,
        "arrival_arm_ids_by_t": arrival_arm_ids_by_t,
        "arm_means": arm_means,
        "arrived_time": arrived_time,
        "num_total_arms": len(arm_means),
    }


@dataclass
class StepResult:
    t: int
    reward: int
    action_arm_id: int
    chosen_mean: float
    r_star: float
    done: bool
    visible_new_arm_ids: List[int]
    arrived_new_arm_ids: List[int]
    arrived_arms_count: int


class DynamicArmsEnv:
    def __init__(self, config: Dict, tape: Dict, seed: int, replicate: int):
        self.config = dict(config)
        self.tape = tape
        self.seed = int(seed)
        self.replicate = int(replicate)

        self.T = int(tape["T"])
        self.initial_arm_ids = list(tape["initial_arm_ids"])
        self.arrival_arm_ids_by_t = dict(tape["arrival_arm_ids_by_t"])
        self.arm_means = dict(tape["arm_means"])

        self._r_star_by_t = self._build_r_star_curve()

        self.t = 0
        self.done = False
        self.arrived_arms: set[int] = set()
        self.pull_counts: Dict[int, int] = {}

        self.reset()

    def _build_r_star_curve(self) -> np.ndarray:
        curve = np.zeros(self.T + 1, dtype=float)
        current_best = 0.0
        if self.initial_arm_ids:
            current_best = max(float(self.arm_means[a]) for a in self.initial_arm_ids)
        for t in range(1, self.T + 1):
            for arm_id in self.arrival_arm_ids_by_t.get(t, []):
                current_best = max(current_best, float(self.arm_means[arm_id]))
            curve[t] = current_best
        return curve

    def reset(self) -> Dict:
        self.t = 0
        self.done = False
        self.arrived_arms = set(self.initial_arm_ids)
        self.pull_counts = {arm_id: 0 for arm_id in self.arm_means.keys()}
        return {
            "t": self.t,
            "arrived_arms": sorted(self.arrived_arms),
            "num_arrived_arms": len(self.arrived_arms),
        }

    def get_arm_mean(self, arm_id: int) -> float:
        return float(self.arm_means[arm_id])

    def get_r_star(self, t: int) -> float:
        t_int = int(max(0, min(self.T, t)))
        return float(self._r_star_by_t[t_int])

    def _draw_reward(self, arm_id: int) -> int:
        pull_index = self.pull_counts.get(arm_id, 0) + 1
        u = _u01_from_values(self.seed, self.replicate, arm_id, pull_index, 303)
        return int(u < self.arm_means[arm_id])

    def step(self, action_arm_id: int, awareness: str, arrival_buffer: Optional[List[int]] = None) -> Dict:
        if self.done:
            raise RuntimeError("Environment already finished.")
        if action_arm_id not in self.arrived_arms:
            raise ValueError(f"Arm {action_arm_id} is not available at t={self.t + 1}.")

        t_now = self.t + 1
        new_arm_ids = list(self.arrival_arm_ids_by_t.get(t_now, []))
        for arm_id in new_arm_ids:
            self.arrived_arms.add(arm_id)

        awareness_l = str(awareness).lower()
        visible_new_arm_ids: List[int] = []
        if awareness_l == "buffered":
            if arrival_buffer is not None:
                arrival_buffer.extend(new_arm_ids)
        elif awareness_l == "immediate":
            visible_new_arm_ids = list(new_arm_ids)
        else:
            raise ValueError(f"Unsupported awareness mode: {awareness}")

        reward = self._draw_reward(action_arm_id)
        self.pull_counts[action_arm_id] = self.pull_counts.get(action_arm_id, 0) + 1

        self.t = t_now
        self.done = self.t >= self.T

        result = StepResult(
            t=self.t,
            reward=reward,
            action_arm_id=action_arm_id,
            chosen_mean=float(self.arm_means[action_arm_id]),
            r_star=self.get_r_star(self.t),
            done=self.done,
            visible_new_arm_ids=visible_new_arm_ids,
            arrived_new_arm_ids=new_arm_ids,
            arrived_arms_count=len(self.arrived_arms),
        )
        return result.__dict__.copy()

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

import numpy as np


def _safe_log_term(x: float) -> float:
    return float(max(np.log(max(1.0 + 1e-12, x)), 1e-12))


class BaseAlgo:
    name = "base"

    def __init__(self, algo_cfg: Optional[Dict] = None, exp_cfg: Optional[Dict] = None):
        self.algo_cfg = dict(algo_cfg or {})
        self.exp_cfg = dict(exp_cfg or {})
        self.counts: Dict[int, int] = {}
        self.reward_sums: Dict[int, float] = {}

    def _ensure_arm(self, arm_id: int) -> None:
        if arm_id not in self.counts:
            self.counts[arm_id] = 0
            self.reward_sums[arm_id] = 0.0

    def _update_stats(self, arm_id: int, reward: int) -> None:
        self._ensure_arm(arm_id)
        self.counts[arm_id] += 1
        self.reward_sums[arm_id] += float(reward)

    def _emp_mean(self, arm_id: int) -> float:
        n = self.counts.get(arm_id, 0)
        if n <= 0:
            return 0.0
        return self.reward_sums.get(arm_id, 0.0) / float(n)

    def _best_empirical(self, candidates: Iterable[int]) -> int:
        cand = list(candidates)
        if not cand:
            raise ValueError("No candidate arm to select.")
        best_arm = cand[0]
        best_val = self._emp_mean(best_arm)
        for arm in cand[1:]:
            val = self._emp_mean(arm)
            if (val > best_val) or (val == best_val and arm < best_arm):
                best_arm = arm
                best_val = val
        return int(best_arm)

    def _record_step(self, tracker, result: Dict, active_size: Optional[int] = None) -> None:
        if active_size is not None and hasattr(tracker, "set_active_size"):
            tracker.set_active_size(active_size)
        tracker.record_step(step_result=result)

    def run(self, env, T: int, tracker):
        raise NotImplementedError


class BufferedRoundEliminationBase(BaseAlgo):
    def __init__(self, algo_cfg: Optional[Dict] = None, exp_cfg: Optional[Dict] = None):
        super().__init__(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
        self.effective_M = int(self.algo_cfg.get("M", self.exp_cfg.get("M", 8)))
        self.N = 1
        self.n_by_p: Dict[int, int] = {}
        self.rad_by_p: Dict[int, float] = {}

    def _delta_for_scale(self, p: int) -> float:
        return 1.0 / float(2 ** max(0, p))

    def _prepare_precision_grid(self, T: int) -> None:
        M = int(self.effective_M)
        delta_M = self._delta_for_scale(M)
      ##  self.N = int(max(1, T))
        self.N = float( np.e / (delta_M**2))

        while True:
            delta_M = self._delta_for_scale(M)
            nM = int(np.ceil(2.0 * _safe_log_term(self.N * (delta_M**2)) / (delta_M**2)))
            nM = max(1, nM)
            if nM <= 0.2 * T or M <= 0:
                break
            M -= 1

        self.effective_M = int(max(M, 0))

        self.n_by_p = {}
        self.rad_by_p = {}
        for p in range(self.effective_M + 1):
            delta_p = self._delta_for_scale(p)
            n_p = int(np.ceil(2.0 * _safe_log_term(self.N * (delta_p**2)) / (delta_p**2)))
            n_p = max(1, n_p)
            rad = float(np.sqrt(_safe_log_term(self.N * (delta_p**2)) / (2.0 * n_p)))
            self.n_by_p[p] = n_p
            self.rad_by_p[p] = rad

    def _pull_and_update(self, env, arm_id: int, tracker, buf: List[int]) -> Dict:
        result = env.step(arm_id, awareness="buffered", arrival_buffer=buf)
        self._update_stats(arm_id, int(result["reward"]))
        self._record_step(tracker, result)
        return result

    def _elim(self, S: Set[int], R: Set[int], p: int, env, tracker, buf: List[int]) -> Set[int]:
        if not S:
            return set()
        if not R:
            R = set(S)

        p_eff = int(min(max(p, 0), self.effective_M))
        n_target = int(self.n_by_p[p_eff])
        rad = float(self.rad_by_p[p_eff])

        for arm_id in sorted(S):
            self._ensure_arm(arm_id)
            while self.counts.get(arm_id, 0) < n_target and not env.done:
                self._pull_and_update(env, arm_id, tracker, buf)

            if env.done:
                break

        ref_lcbs = []
        for arm_id in R:
            mu = self._emp_mean(arm_id)
            ref_lcbs.append(mu - rad)
        threshold = max(ref_lcbs) if ref_lcbs else -np.inf

        survivors = {arm_id for arm_id in S if (self._emp_mean(arm_id) + rad) >= threshold}
        if not survivors and S:
            survivors = {self._best_empirical(S)}
        return survivors

    def _run_round(self, m: int, C_prev: Set[int], A_m: List[int], env, tracker, buf: List[int]) -> Set[int]:
        raise NotImplementedError

    def run(self, env, T: int, tracker):
        self._prepare_precision_grid(T)

        A_m = sorted(set(env.initial_arm_ids))
        C_prev: Set[int] = set()
        buf: List[int] = []

        if hasattr(tracker, "set_active_size"):
            tracker.set_active_size(len(A_m))

        for m in range(self.effective_M + 1):
            if env.done:
                break

            C_prev = self._run_round(m=m, C_prev=C_prev, A_m=A_m, env=env, tracker=tracker, buf=buf)

            if hasattr(tracker, "set_active_size"):
                tracker.set_active_size(len(C_prev))
            if hasattr(tracker, "record_round_state"):
                tracker.record_round_state(t=env.t, round_id=m, active_size=len(C_prev))

            A_m = sorted(set(buf))
            buf.clear()

            if env.done:
                break

        exploit_pool = set(C_prev) if C_prev else set(env.arrived_arms)
        if not exploit_pool:
            exploit_pool = set(env.initial_arm_ids)

        while not env.done:
            available = sorted(set(exploit_pool).intersection(env.arrived_arms))
            if not available:
                available = sorted(env.arrived_arms)
            action = self._best_empirical(available)
            result = env.step(action, awareness="buffered", arrival_buffer=buf)
            self._update_stats(action, int(result["reward"]))
            self._record_step(tracker, result)

        return {
            "effective_M": self.effective_M,
            "N": self.N,
            "survivor_size": len(C_prev),
        }


class CustomEliminationAlgo(BufferedRoundEliminationBase):
    name = "custom_elim"

    def _run_round(self, m: int, C_prev: Set[int], A_m: List[int], env, tracker, buf: List[int]) -> Set[int]:
        Bp: Dict[int, Set[int]] = {0: set(C_prev).union(A_m)}

        if len(A_m) > 0 and m >= 2:
            A_cur = set(A_m)
            for p in range(0, m - 1):
                A_cur = self._elim(A_cur, Bp[p], p, env, tracker, buf)
                Bp[p + 1] = set(C_prev).union(A_cur)
                if env.done:
                    break

        if env.done:
            return set(C_prev) if C_prev else set(Bp.get(m, set()))

        if m == 0:
            Bp[1] = self._elim(Bp[0], Bp[0], 0, env, tracker, buf)
        else:
            for p in (m - 1, m):
                S_in = set(Bp.get(p, set(C_prev).union(A_m)))
                R_ref = set(C_prev) if C_prev else set(S_in)
                Bp[p + 1] = self._elim(S_in, R_ref, p, env, tracker, buf)
                if env.done:
                    break

        C_curr = set(Bp.get(m + 1, set()))
        if not C_curr:
            C_curr = set(C_prev) if C_prev else set(Bp.get(m, set()))
        return C_curr


class GrowingUCB(BaseAlgo):
    name = "ucb"

    def run(self, env, T: int, tracker):
        known_arms: Set[int] = set(env.initial_arm_ids)
        if hasattr(tracker, "set_active_size"):
            tracker.set_active_size(len(known_arms))

        while not env.done:
            unpulled = sorted([a for a in known_arms if self.counts.get(a, 0) == 0])
            if unpulled:
                action = unpulled[0]
            else:
                t_now = max(2, env.t + 1)
                best_score = -np.inf
                action = min(known_arms)
                for arm_id in sorted(known_arms):
                    n = self.counts.get(arm_id, 0)
                    mu = self._emp_mean(arm_id)
                    bonus = np.sqrt(2.0 * np.log(t_now) / max(1, n))
                    score = mu + bonus
                    if (score > best_score) or (score == best_score and arm_id < action):
                        best_score = score
                        action = arm_id

            result = env.step(action, awareness="immediate")
            self._update_stats(action, int(result["reward"]))
            known_arms.update(result["visible_new_arm_ids"])
            self._record_step(tracker, result, active_size=len(known_arms))

        return {"known_arms_final": len(known_arms)}


class GrowingMOSS(BaseAlgo):
    name = "moss"

    def run(self, env, T: int, tracker):
        known_arms: Set[int] = set(env.initial_arm_ids)

        if hasattr(tracker, "set_active_size"):
            tracker.set_active_size(len(known_arms))

        while not env.done:
            unpulled = sorted([a for a in known_arms if self.counts.get(a, 0) == 0])
            if unpulled:
                action = unpulled[0]
            else:
                t_now = max(2, env.t + 1)
                best_score = -np.inf
                action = min(known_arms)
                for arm_id in sorted(known_arms):
                    n = max(1, self.counts.get(arm_id, 0))
                    mu = self._emp_mean(arm_id)
                    K_t = max(1, len(known_arms))
                    ratio = max(1.0, t_now / float(K_t * n))
                    bonus = np.sqrt(max(0.0, np.log(ratio)) / n)
                    score = mu + bonus
                    if (score > best_score) or (score == best_score and arm_id < action):
                        best_score = score
                        action = arm_id

            result = env.step(action, awareness="immediate")
            self._update_stats(action, int(result["reward"]))
            known_arms.update(result["visible_new_arm_ids"])
            self._record_step(tracker, result, active_size=len(known_arms))

        return {"known_arms_final": len(known_arms)}


class NaiveRoundElim(BufferedRoundEliminationBase):
    name = "naive_elim"

    def _run_round(self, m: int, C_prev: Set[int], A_m: List[int], env, tracker, buf: List[int]) -> Set[int]:
        B_m = set(C_prev).union(A_m)
        if not B_m:
            return set()

        current = self._elim(B_m, B_m, m, env, tracker, buf)

        if not current:
            current = set(C_prev) if C_prev else set(B_m)
        return current


class EpochRestartedSuccessiveElimination(BaseAlgo):
    name = "erse"

    def __init__(self, algo_cfg: Optional[Dict] = None, exp_cfg: Optional[Dict] = None):
        super().__init__(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
        self.gamma = float(self.algo_cfg.get("gamma", 1.0))

    def _u(self, tau: int, horizon: int) -> float:
        tau_eff = max(1, int(tau))
        horizon_eff = max(1, int(horizon))
        ratio = max(1.0, horizon_eff / float(tau_eff))
        return float(2.0 * np.sqrt(2.0 * np.log(ratio) / float(tau_eff)))

    def _local_emp_mean(self, arm_id: int, local_counts: Dict[int, int], local_reward_sums: Dict[int, float]) -> float:
        n = int(local_counts.get(arm_id, 0))
        if n <= 0:
            return 0.0
        return float(local_reward_sums.get(arm_id, 0.0)) / float(n)

    def _local_best_empirical(self, candidates: Iterable[int], local_counts: Dict[int, int], local_reward_sums: Dict[int, float]) -> int:
        cand = list(candidates)
        if not cand:
            raise ValueError("No candidate arm to select.")
        best_arm = cand[0]
        best_val = self._local_emp_mean(best_arm, local_counts, local_reward_sums)
        for arm in cand[1:]:
            val = self._local_emp_mean(arm, local_counts, local_reward_sums)
            if (val > best_val) or (val == best_val and arm < best_arm):
                best_arm = arm
                best_val = val
        return int(best_arm)

    def _ensure_local_arm(
        self,
        arm_id: int,
        local_counts: Dict[int, int],
        local_reward_sums: Dict[int, float],
    ) -> None:
        local_counts.setdefault(arm_id, 0)
        local_reward_sums.setdefault(arm_id, 0.0)

    def _shared_local_count(self, candidates: Iterable[int], local_counts: Dict[int, int]) -> int:
        cand = list(candidates)
        if not cand:
            return 0
        return min(int(local_counts.get(arm_id, 0)) for arm_id in cand)

    def _record_round_step(self, tracker, result: Dict, active_size: int) -> None:
        self._record_step(tracker, result, active_size=active_size)

    def _pull_round_arm(
        self,
        env,
        tracker,
        arm_id: int,
        local_counts: Dict[int, int],
        local_reward_sums: Dict[int, float],
        buffer: List[int],
        active_size: int,
    ) -> None:
        self._ensure_local_arm(arm_id, local_counts, local_reward_sums)
        result = env.step(arm_id, awareness="buffered", arrival_buffer=buffer)
        reward = int(result["reward"])
        self._update_stats(arm_id, reward)
        local_counts[arm_id] = local_counts.get(arm_id, 0) + 1
        local_reward_sums[arm_id] = local_reward_sums.get(arm_id, 0.0) + float(reward)
        self._record_round_step(tracker, result, active_size=active_size)

    def _se_eliminate(
        self,
        active: Set[int],
        local_counts: Dict[int, int],
        local_reward_sums: Dict[int, float],
        horizon: int,
    ) -> Set[int]:
        if not active:
            return set()

        tau = max(1, self._shared_local_count(active, local_counts))
        threshold_gap = self.gamma * self._u(tau=tau, horizon=horizon)
        best_mean = max(self._local_emp_mean(arm_id, local_counts, local_reward_sums) for arm_id in active)
        survivors = {
            arm_id
            for arm_id in active
            if self._local_emp_mean(arm_id, local_counts, local_reward_sums) >= (best_mean - threshold_gap)
        }
        if not survivors:
            survivors = {self._local_best_empirical(active, local_counts, local_reward_sums)}
        return survivors

    def run(self, env, T: int, tracker):
        C_prev: Set[int] = set(env.initial_arm_ids).intersection(env.arrived_arms)
        A_next: Set[int] = set()
        local_counts: Dict[int, int] = {arm_id: 0 for arm_id in C_prev}
        local_reward_sums: Dict[int, float] = {arm_id: 0.0 for arm_id in C_prev}
        round_id = 0

        if hasattr(tracker, "set_active_size"):
            tracker.set_active_size(len(C_prev))

        while not env.done:
            current = set(C_prev).union(A_next)
            if not current:
                current = set(env.arrived_arms)
            current = current.intersection(env.arrived_arms)
            if not current:
                break

            for arm_id in current:
                self._ensure_local_arm(arm_id, local_counts, local_reward_sums)

            round_id += 1
            round_buffer: List[int] = []
            old_survivors = set(C_prev).intersection(current)
            new_arrivals = set(A_next).intersection(current)

            if old_survivors and new_arrivals:
                target_count = self._shared_local_count(old_survivors, local_counts)
                stage_active_size = len(current)
                for arm_id in sorted(new_arrivals):
                    while local_counts.get(arm_id, 0) < target_count and not env.done:
                        self._pull_round_arm(
                            env=env,
                            tracker=tracker,
                            arm_id=arm_id,
                            local_counts=local_counts,
                            local_reward_sums=local_reward_sums,
                            buffer=round_buffer,
                            active_size=stage_active_size,
                        )

                if not env.done:
                    current = self._se_eliminate(
                        active=current,
                        local_counts=local_counts,
                        local_reward_sums=local_reward_sums,
                        horizon=T,
                    )

            if not env.done:
                stage_active = set(current)
                stage_active_size = len(stage_active)
                for arm_id in sorted(stage_active):
                    if env.done:
                        break
                    self._pull_round_arm(
                        env=env,
                        tracker=tracker,
                        arm_id=arm_id,
                        local_counts=local_counts,
                        local_reward_sums=local_reward_sums,
                        buffer=round_buffer,
                        active_size=stage_active_size,
                    )

                if stage_active:
                    current = self._se_eliminate(
                        active=stage_active,
                        local_counts=local_counts,
                        local_reward_sums=local_reward_sums,
                        horizon=T,
                    )

            C_prev = set(current)
            if hasattr(tracker, "set_active_size"):
                tracker.set_active_size(len(C_prev))
            if hasattr(tracker, "record_round_state"):
                tracker.record_round_state(t=env.t, round_id=round_id, active_size=len(C_prev))

            A_next = set(round_buffer)

        exploit_pool = set(C_prev) if C_prev else set(env.arrived_arms)
        if not exploit_pool:
            exploit_pool = set(env.initial_arm_ids)

        tail_buffer: List[int] = []
        while not env.done:
            available = sorted(set(exploit_pool).intersection(env.arrived_arms))
            if not available:
                available = sorted(env.arrived_arms)
            action = self._best_empirical(available)
            result = env.step(action, awareness="buffered", arrival_buffer=tail_buffer)
            self._update_stats(action, int(result["reward"]))
            self._record_step(tracker, result, active_size=len(exploit_pool))

        return {
            "num_rounds_completed": round_id,
            "gamma": self.gamma,
            "survivor_size": len(C_prev),
        }


def build_algo(name: str, algo_cfg: Optional[Dict] = None, exp_cfg: Optional[Dict] = None) -> BaseAlgo:
    key = str(name).lower()
    if key in {"custom", "custom_elim", "customeliminationalgo"}:
        return CustomEliminationAlgo(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    if key in {"ucb", "growing_ucb", "growingucb"}:
        return GrowingUCB(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    if key in {"moss", "growing_moss", "growingmoss"}:
        return GrowingMOSS(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    if key in {"naive", "naive_elim", "naiveroundelim"}:
        return NaiveRoundElim(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    if key in {"erse", "epoch_restarted_se", "epochrestartedsuccessiveelimination"}:
        return EpochRestartedSuccessiveElimination(algo_cfg=algo_cfg, exp_cfg=exp_cfg)
    raise ValueError(f"Unknown algorithm: {name}")

"""Read-only audit of the submitted source and archived simulation.

Writes only inside this review directory. Run with python -B.
No revised/exploratory algorithms enter the numerical comparisons.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
SIM = Path("D:/博士学习/科研/Projects/Bandit with Arriving Arms/simulation_final")
SKILL = Path("C:/Users/12701/.codex/skills/statistical-innovation-assessment")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Tracker:
    def __init__(self):
        self.regret = 0.0
        self.rounds = []

    def set_active_size(self, active_size):
        pass

    def record_step(self, step_result):
        self.regret += step_result["r_star"] - step_result["chosen_mean"]

    def record_round_state(self, t, round_id, active_size):
        self.rounds.append(dict(t=t, round=round_id, active=active_size))


def main():
    files = [
        ROOT / "JASA-template/mab_aa_main.tex",
        ROOT / "JASA-template/mab_aa_main.pdf",
        ROOT / "JASA-template/bibliography.bib",
        ROOT / "Reviews_JASA-RA-2026-0866.pdf",
        ROOT / "revision_notes/review_audit_evidence_2026-09-23.json",
        SIM / "algos.py", SIM / "env.py",
        SKILL / "SKILL.md", SKILL / "references/rubric.md",
        SKILL / "references/examples.md",
    ]
    for scenario in ("C", "E"):
        archive = SIM / "outputs/final" / f"scenario_{scenario}"
        files.extend([archive / "config.json", archive / "raw_final.csv"])
        for suffix in ("dynamic_regret_vs_t", "wasted_pulls_eps_0_1", "arm_set_size_vs_t"):
            name = f"scenario_{scenario}_{suffix}.png"
            files.extend([ROOT / "JASA-template" / name, archive / "plots" / name])
    before = {str(p): sha(p) for p in files}
    assert before[str(files[0])] == "d81d24cda29e9137fa85a622244be374d880480aca267eb62d17caafaa249f6f"
    previous = json.loads((ROOT / "revision_notes/review_audit_evidence_2026-09-23.json").read_text(encoding="utf-8"))
    previous_hash_checks = {}
    for name, expected in previous["source_file_sha256"].items():
        path = Path(name)
        previous_hash_checks[str(path)] = sha(path) == expected
    assert all(previous_hash_checks.values())

    algos = load_module("review_original_algos", SIM / "algos.py")
    envmod = load_module("review_original_env", SIM / "env.py")
    summaries = {}
    replays = []
    figure_checks = {}
    for scenario in ("C", "E"):
        archive = SIM / "outputs/final" / f"scenario_{scenario}"
        config = json.loads((archive / "config.json").read_text(encoding="utf-8"))
        data = pd.read_csv(archive / "raw_final.csv")
        metrics = ["dynamic_regret", "wasted_pulls_eps_0_1", "final_active_size"]
        table = data.groupby("algo")[metrics].mean()
        paired = data.pivot(index="replicate", columns="algo", values="dynamic_regret")
        assert len(paired) == 100 and not paired.isna().any().any()
        assert (data.steps_completed == 60000).all()
        diff = paired.custom_elim - paired.moss
        mean, se = float(diff.mean()), float(diff.std(ddof=1) / np.sqrt(len(diff)))
        ordinary = float(student_t.ppf(0.975, len(diff)-1))
        simultaneous = float(student_t.ppf(1-0.05/(2*2), len(diff)-1))
        summaries[scenario] = dict(
            n=100, horizon=60000, configuration=config,
            mean_metrics=table.to_dict(orient="index"),
            paired_difference_UCBAA_minus_MOSS=mean,
            paired_standard_error=se,
            paired_95_t_interval=[mean-ordinary*se, mean+ordinary*se],
            two_case_bonferroni_95_t_interval=[mean-simultaneous*se, mean+simultaneous*se],
            regret_ratio=float(paired.custom_elim.mean()/paired.moss.mean()),
        )
        exp = config["best_config"]
        tape = envmod.build_replicate_tape(exp, config["seed"], 1)
        env = envmod.DynamicArmsEnv(exp, tape, seed=config["seed"], replicate=1)
        tracker = Tracker()
        algorithm = algos.CustomEliminationAlgo({"M": exp["M"]}, exp)
        info = algorithm.run(env, exp["T"], tracker)
        target = float(paired.loc[1, "custom_elim"])
        assert math.isclose(tracker.regret, target, rel_tol=1e-12, abs_tol=1e-9)
        replays.append(dict(scenario=scenario, replicate=1, regret=tracker.regret,
                            archived_regret=target, algorithm_info=info,
                            round_endpoints=tracker.rounds,
                            arrived=len(env.arrived_arms),
                            sampled=len(algorithm.counts),
                            last_round_end=tracker.rounds[-1]["t"]))
        for suffix in ("dynamic_regret_vs_t", "wasted_pulls_eps_0_1", "arm_set_size_vs_t"):
            name = f"scenario_{scenario}_{suffix}.png"
            figure_checks[name] = sha(ROOT / "JASA-template" / name) == sha(archive / "plots" / name)
    assert all(figure_checks.values())

    compression = []
    for M in (8, 12, 16, 20):
        scale = 4**M
        nM = 16*scale
        for _ in range(200):
            updated = math.ceil(2*scale*math.log(30*nM/scale))
            if updated == nM:
                break
            nM = updated
        else:
            raise RuntimeError("No fixed point.")
        N = 30*nM
        nprev = math.ceil(2*4**(M-1)*math.log(N/4**(M-1)))
        old_gap = 2.0**(-M)
        final_gap = 0.4 + old_gap
        leading = nprev*old_gap
        claimed = 32*math.log(N*final_gap**2)/final_gap + 4*final_gap
        compression.append(dict(M=M, nM=nM, N=N, actual_S=leading,
                                claimed_upper_bound=claimed, ratio=leading/claimed))
    assert compression[0]["ratio"] < 1 and all(x["ratio"] > 1 for x in compression[1:])

    T, tau = 60000, 30000
    tape = dict(T=T, initial_arm_ids=[0], arm_means={0: 0.0, 1: 1.0},
                arrived_time={0: 1, 1: tau},
                arrival_arm_ids_by_t={t: ([1] if t == tau else []) for t in range(1, T+1)})
    env = envmod.DynamicArmsEnv({"T": T}, tape, seed=20260923, replicate=1)
    tracker = Tracker()
    algorithm = algos.CustomEliminationAlgo({"M": 5}, {"T": T})
    algorithm.run(env, T, tracker)
    assert tracker.regret == 30001 and env.pull_counts[1] == 0
    stopped = dict(T=T, tau=tau, regret=tracker.regret,
                   new_arm_pulls=env.pull_counts[1], round_endpoints=tracker.rounds,
                   scope="Original archived implementation under unrestricted exogenous arrivals; not a counterexample satisfying all paper assumptions.")

    after = {str(p): sha(p) for p in files}
    assert before == after
    result = dict(
        scope="Official source only; no exploratory algorithms included.",
        manuscript_sha256=before[str(files[0])], source_hashes=before,
        source_mtime_ns={str(p): p.stat().st_mtime_ns for p in files},
        previous_source_hash_checks=previous_hash_checks,
        original_inputs_unchanged=True,
        figure_matches=figure_checks, archived_statistics=summaries,
        fresh_original_algorithm_replays=replays, gap_compression_checks=compression,
        stopped_admission_counterexample=stopped,
        intervals_note="Approximate paired t Monte Carlo intervals; two-case Bonferroni is reported separately. No claim of correcting unknown historical tuning or selection.",
        credit_cards_used=0,
    )
    (OUT / "evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dict(summary=summaries, replays=replays,
                          compression=compression, original_inputs_unchanged=True,
                          stopped_regret=tracker.regret), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

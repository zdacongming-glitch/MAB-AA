"""Frozen method definitions shared by simulation, scheduling and analysis.

Only the current, unmodified no-H8 SRC and its KL variant are candidate
families. Aliases document historical names without adding comparator rows.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path


def _method(identifier, family, kernel, *, params=None, preference=0.0,
            beta_r=None, beta_c=None, planner="paired", known_horizon=False):
    return dict(id=identifier, family=family, kernel=kernel, params=params or {},
                preference=float(preference), beta_r=beta_r, beta_c=beta_c,
                planner=planner, known_horizon=bool(known_horizon))


METHODS = {}
_source_params = dict(log_coefficient=.5, nu=.02, relevance_floor=.02,
                      rate_floor=.02, backlog_scale=4.0)
_modes = [("R", 0., None), ("L010", .1, 1.), ("L030", .3, 1.),
          ("L060", .6, 1.), ("L090", .9, 1.), ("L100", 1., 1.),
          ("area", 1., None)]
SRC_IDS = []
KL_IDS = []
for _prefix, _family, _ids in [("SRC", "src", SRC_IDS),
                               ("SRC-KL", "src_kl", KL_IDS)]:
    for _suffix, _preference, _cap in _modes:
        _identifier = f"{_prefix}-{_suffix}"
        METHODS[_identifier] = _method(
            _identifier, _family, "IMED", params=deepcopy(_source_params),
            preference=_preference, beta_r=32., beta_c=_cap)
        _ids.append(_identifier)

MATCHED_CONTROL_IDS = []
for _prefix, _family in [("SRC", "src"), ("SRC-KL", "src_kl")]:
    for _planner in ["widest", "lucb"]:
        _identifier = f"{_prefix}-{_planner}-L060"
        METHODS[_identifier] = _method(
            _identifier, _family, "IMED", params=deepcopy(_source_params),
            preference=.6, beta_r=32., beta_c=1., planner=_planner)
        MATCHED_CONTROL_IDS.append(_identifier)

_baseline_specs = [
    ("IMED", "IMED", {"log_coefficient": 1.}),
    ("UCB1", "UCB1", {}),
    ("AUER", "AUER", {}),
    ("Growing-MOSS", "Growing-MOSS", {}),
    ("ACI", "ACI", {}),
    ("Clipped-ACI", "Clipped-ACI", {}),
    ("TS", "TS", {}),
    ("KL-UCB-c0", "KL-UCB", {"loglog_coefficient": 0.}),
    ("KL-UCB-c3", "KL-UCB", {"loglog_coefficient": 3.}),
    ("KL-UCB+", "KL-UCB+", {}),
    ("UCB1-Tuned", "UCB1-Tuned", {}),
    ("UCB-V", "UCB-V", {}),
    ("Bayes-UCB", "Bayes-UCB", {}),
    ("Empirical-KL-UCB", "Empirical-KL-UCB", {}),
    ("SB-EXP3-ATGT", "SB-EXP3-ATGT", {}),
    ("UCB-log2t-c3", "UCB-conservative", {}),
    ("MOSS-T-currentK", "MOSS-T-currentK", {}),
    ("TS-Jeffreys", "TS-Jeffreys", {}),
    ("TS-SMAB-bounded", "TS-SMAB-bounded", {}),
]
BASELINE_IDS = []
for _identifier, _kernel, _params in _baseline_specs:
    METHODS[_identifier] = _method(
        _identifier, "baseline", _kernel, params=_params,
        known_horizon=_kernel == "MOSS-T-currentK")
    BASELINE_IDS.append(_identifier)

ALIASES = {
    "UCB-conservative": "UCB-log2t-c3",
    "MC-MOSS": "ACI", "MC-MOSS-clipped": "Clipped-ACI",
    "Clipped_ACI": "Clipped-ACI", "Growing_MOSS": "Growing-MOSS",
    "Thompson": "TS", "F-R-TS-exact": "TS",
    "KL-UCB": "KL-UCB-c3", "KL_UCB_c0": "KL-UCB-c0",
    "KL_UCB_c3": "KL-UCB-c3", "KL_UCB_plus": "KL-UCB+",
    "UCB_Tuned": "UCB1-Tuned", "UCB_V": "UCB-V",
    "Bayes_UCB": "Bayes-UCB", "Empirical_KL_UCB": "Empirical-KL-UCB",
    "empirical-KL-UCB": "Empirical-KL-UCB", "SB_EXP3_ATGT": "SB-EXP3-ATGT",
}

REWARD_METHOD_IDS = ["SRC-R", "SRC-KL-R", *BASELINE_IDS]
JOINT_METHOD_IDS = [*SRC_IDS, *KL_IDS, *MATCHED_CONTROL_IDS]
TAIL_METHOD_IDS = ["SRC-R", "SRC-KL-R", "IMED", "Empirical-KL-UCB"]
NEWLY_EVALUATED_IDS = ["MOSS-T-currentK", "TS-Jeffreys", "TS-SMAB-bounded"]


def get_method(identifier):
    """Return a detached definition, resolving only documented aliases."""
    canonical = ALIASES.get(identifier, identifier)
    return deepcopy(METHODS[canonical])


def validate_registry(path=None):
    """Reject divergence between the executable and frozen method registry."""
    path = Path(path or Path(__file__).resolve().parents[2] / "configs" / "methods.json")
    with path.open(encoding="utf-8") as stream:
        frozen = json.load(stream)
    if frozen.get("methods") != METHODS or frozen.get("aliases") != ALIASES:
        raise ValueError("configs/methods.json differs from the executable method registry")
    if frozen.get("baseline_count") != len(BASELINE_IDS):
        raise ValueError("frozen baseline count differs from the executable registry")
    return True


validate_registry()

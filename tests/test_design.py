import hashlib
import json
from collections import Counter

import pytest

from srcbench.design import (CONFIG_ROOT, build_tasks, load_layouts,
                             preview, record_flags)
from srcbench.methods import BASELINE_IDS, METHODS, ALIASES


@pytest.fixture(scope="module")
def full_tasks():
    return build_tasks("full")


def test_canonical_snapshot_integrity_and_original_examples():
    layouts = load_layouts()
    assert Counter(s["group"] for s in layouts) == dict(f17=12, adaptive=12, dense=18, scale=3)
    manifest = json.loads((CONFIG_ROOT / "provenance.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((CONFIG_ROOT / "layouts.json").read_bytes()).hexdigest() == manifest["canonical_layouts_sha256"]
    for s in layouts:
        payload = {k: s[k] for k in ["T", "epsilon", "eta", "delta", "arms"]}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        assert digest == s["metadata"]["canonical_sha256"]
        assert [a["record"] for a in s["arms"]] == record_flags(s["arms"])
        assert all(1 <= a["arrival"] <= s["T"] and 0 <= a["mean"] <= 1 for a in s["arms"])
    few = next(s for s in layouts if s["id"] == "f17__few_arrivals")
    assert few["T"] == 12000
    assert [(a["arrival"], a["mean"]) for a in few["arms"]] == [(1, .565), (4013, .785), (4013, .295)]


def test_batch_record_definition_excludes_fake_within_batch_records():
    arms = [dict(arrival=1, mean=.5), dict(arrival=1, mean=.9),
            dict(arrival=2, mean=.8), dict(arrival=3, mean=.95),
            dict(arrival=3, mean=.95)]
    assert record_flags(arms) == [False, True, False, True, True]


def test_full_cell_and_workload_counts(full_tasks):
    assert len(full_tasks) == 16224
    assert len({t["cell_id"] for t in full_tasks}) == 540
    assert len({t["task_id"] for t in full_tasks}) == len(full_tasks)
    assert sum(len(t["methods"]) for t in full_tasks) == 418560
    assert all(t["seed_base"] == (2026103101 if t["cohort"] == "main" else 2026103102) for t in full_tasks)


def test_joint_uses_matched_replications_instead_of_all_reward_endpoints(full_tasks):
    selected = [t for t in full_tasks if t["layout"]["id"] == "f17__two_close"]
    paired = [t for t in selected if "joint" in t["suites"]]
    assert len(paired) == 8 * 16
    for task in paired:
        assert task["rep"] < 16
        assert "joint" in task["method_suites"]["SRC-R"]
        assert "joint" in task["method_suites"]["SRC-KL-R"]
        assert "joint" in task["method_suites"]["IMED"]
        assert task["methods"].count("SRC-R") == 1
        assert task["method_suites"]["SRC-L060"] == ["joint"]
    unpaired = next(t for t in selected if t["law"] == "bernoulli" and t["rep"] == 16)
    assert unpaired["method_suites"]["SRC-R"] == ["reward"]
    assert "SRC-L060" not in unpaired["methods"]


def test_smoke_derivatives_leave_full_settings_intact():
    small = build_tasks("smoke-small")
    dense = build_tasks("smoke-dense")
    assert len(small) == len(dense) == 16
    assert sum(len(t["methods"]) for t in small) == 448
    assert sum(len(t["methods"]) for t in dense) == 176
    assert all(t["layout"]["T"] == 1000 and len(t["methods"]) == 28 for t in small)
    assert all(t["layout"]["T"] == 800 and len(t["layout"]["arms"]) == 40 for t in dense)
    late = next(t["layout"] for t in dense if "late_regime_records" in t["layout"]["name"])
    assert {round(a["mean"], 2) for a in late["arms"] if a["record"]} == {.62, .82, .92}
    assert all(t["cohort"] == "smoke" and "derivative" in t["layout"]["metadata"] for t in small + dense)
    original = next(s for s in load_layouts() if s["id"] == "dense__d_late_regime_records_K100")
    assert original["T"] == 8000 and len(original["arms"]) == 100
    assert "derivative" not in original["metadata"]


def test_tail_is_a_separate_seed_cohort():
    tasks = build_tasks("tail")
    assert len(tasks) == 6 * 2 * 128
    assert sum(len(t["methods"]) for t in tasks) == 6144
    assert all(t["cohort"] == "tail" and t["seed_base"] == 2026103102 for t in tasks)
    assert all(t["suites"] == ["tail"] for t in tasks)


def test_frozen_protocol_is_the_actual_expansion_driver(tmp_path):
    protocol = json.loads((CONFIG_ROOT / "protocol.json").read_text(encoding="utf-8"))
    protocol["smoke_profiles"]["smoke-small"]["replications"] = 1
    protocol["seed_bases"]["smoke_small"] = 88231
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    tasks = build_tasks("smoke-small", protocol_path=path)
    assert len(tasks) == 4
    assert all(t["seed_base"] == 88231 and t["rep"] == 0 for t in tasks)


def test_frozen_method_registry_drift_is_rejected(tmp_path):
    from srcbench.methods import validate_registry
    frozen = json.loads((CONFIG_ROOT / "methods.json").read_text(encoding="utf-8"))
    frozen["methods"]["SRC-R"]["beta_r"] = 999
    path = tmp_path / "methods.json"
    path.write_text(json.dumps(frozen), encoding="utf-8")
    with pytest.raises(ValueError, match="differs"):
        validate_registry(path)


def test_registry_has_no_h8_or_legacy_candidate_and_no_duplicate_alias_rows():
    assert len(BASELINE_IDS) == 22 and len(METHODS) == 40
    assert ALIASES["MC-MOSS"] == "ACI"
    assert "MC-MOSS" not in METHODS
    assert all("H8" not in name and "H16" not in name and not name.startswith("F-") for name in METHODS)
    frozen = json.loads((CONFIG_ROOT / "methods.json").read_text(encoding="utf-8"))
    assert frozen["methods"] == METHODS
    assert preview("smoke-small")["no_simulation_performed"] is True

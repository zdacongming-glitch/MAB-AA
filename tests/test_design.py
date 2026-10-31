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
    assert sum(len(t["methods"]) for t in full_tasks) == 374496
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
    assert sum(len(t["methods"]) for t in small) == 400
    assert sum(len(t["methods"]) for t in dense) == 160
    assert all(t["layout"]["T"] == 1000 and len(t["methods"]) == 25 for t in small)
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


@pytest.fixture(scope="module")
def screen_tasks():
    return build_tasks("screen-all")


def test_screen_all_covers_every_cell_and_method_with_four_paired_reps(screen_tasks):
    assert len(screen_tasks) == 2160
    assert len({t["cell_id"] for t in screen_tasks}) == 540
    assert len({t["layout"]["id"] for t in screen_tasks}) == 45
    assert sum(len(t["methods"]) for t in screen_tasks) == 79920
    assert all(set(t["methods"]) == set(METHODS) for t in screen_tasks)
    assert all(t["cohort"] == "screen" and t["seed_base"] == 2026103105 for t in screen_tasks)
    assert all(t["suites"] == ["joint", "reward"] for t in screen_tasks)
    assert all(v == ["reward", "joint"] for t in screen_tasks for v in t["method_suites"].values())
    assert all(t["rep"] in {0, 1, 2, 3} for t in screen_tasks)


def test_screen_preserves_source_record_identities_and_arrival_batches(screen_tasks):
    originals = {s["id"]: s for s in load_layouts()}
    derivatives = {t["layout"]["id"]: t["layout"] for t in screen_tasks}
    for s in derivatives.values():
        d = s["metadata"]["derivative"]
        parent = originals[d["parent_id"]]
        indices = d["selected_parent_indices"]
        mandatory = {0, len(parent["arms"])-1}
        mandatory.update(i for i, a in enumerate(parent["arms"]) if a["record"])
        assert mandatory.issubset(indices)
        assert len(s["arms"]) == d["actual_arm_count"]
        assert s["T"] == d["actual_T"] == 400
        assert d["parent_T"] == parent["T"]
        assert d["record_status_changes"] == []
        assert [a["mean"] for a in s["arms"]] == [parent["arms"][i]["mean"] for i in indices]
        source_births = [parent["arms"][i]["arrival"] for i in indices]
        actual_births = [a["arrival"] for a in s["arms"]]
        assert actual_births[0] == 1
        for old_a, old_b, new_a, new_b in zip(source_births, source_births[1:], actual_births, actual_births[1:]):
            assert (old_a == old_b) == (new_a == new_b)
            assert old_a == old_b or new_a < new_b
        for key in ["epsilon", "eta", "delta"]:
            assert s[key] == parent[key]
        if s["group"] in {"f17", "adaptive"}:
            assert len(indices) == len(parent["arms"])


def test_screen_keeps_whole_bursts_and_expands_k100_when_records_require_it(screen_tasks):
    originals = {s["id"]: s for s in load_layouts()}
    bursts = {t["layout"]["id"]: t["layout"] for t in screen_tasks
              if t["layout"]["metadata"].get("family") == "bursty_reservoir"}
    assert len(bursts) == 3
    for s in bursts.values():
        counts = Counter(a["arrival"] for a in s["arms"])
        assert set(counts.values()) == {5}
        d = s["metadata"]["derivative"]
        parent = originals[d["parent_id"]]
        selected = set(d["selected_parent_indices"])
        for i in selected:
            batch_birth = parent["arms"][i]["arrival"]
            assert all(j in selected for j, a in enumerate(parent["arms"]) if a["arrival"] == batch_birth)
        if d["parent_arm_count"] == 100:
            assert d["requested_arm_count"] == 20
            assert d["actual_arm_count"] == 30
            assert d["expansion_reason"]
        else:
            assert d["actual_arm_count"] == d["requested_arm_count"]


def test_screen_has_minimal_diagnostics_and_changes_only_its_profile(screen_tasks):
    assert all(t["diagnostics"] == dict(trajectory_replications=1, linear_points=21,
                log_points=10, per_arm_methods=[], smoke_all_methods=False) for t in screen_tasks)
    assert preview("full")["unique_paths"] == 374496
    assert preview("smoke-small")["unique_paths"] == 400
    assert preview("smoke-dense")["unique_paths"] == 160
    assert preview("screen-all")["small_derivatives"] is True


def test_screen_configuration_drives_its_replications_and_seed(tmp_path):
    protocol = json.loads((CONFIG_ROOT / "protocol.json").read_text(encoding="utf-8"))
    protocol["screen_all"]["replications"] = 1
    protocol["screen_all"]["unique_paths"] = 19980
    protocol["seed_bases"]["screen_all"] = 71321
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    tasks = build_tasks("screen-all", protocol_path=path)
    assert len(tasks) == 540
    assert all(t["seed_base"] == 71321 and t["rep"] == 0 for t in tasks)


def test_registry_has_no_h8_or_legacy_candidate_and_no_duplicate_alias_rows():
    assert len(BASELINE_IDS) == 19 and len(METHODS) == 37
    assert not any(name.startswith("BL-MOSS") for name in METHODS)
    assert not any(name.startswith(("BL-MOSS", "BL_MOSS")) for name in ALIASES)
    assert ALIASES["MC-MOSS"] == "ACI"
    assert "MC-MOSS" not in METHODS
    assert all("H8" not in name and "H16" not in name and not name.startswith("F-") for name in METHODS)
    frozen = json.loads((CONFIG_ROOT / "methods.json").read_text(encoding="utf-8"))
    assert frozen["methods"] == METHODS
    assert preview("smoke-small")["no_simulation_performed"] is True

"""Only invented tiny worlds exercise the standalone frozen-snapshot entry."""
from copy import deepcopy
import csv
import gzip
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

from srcbench.design import _task
from srcbench.methods import get_method
from srcbench.runner import atomic_json, input_files, task_records, verify
from srcbench.simulation import simulate_task

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("parameter_replay_test_entry", ROOT / "replay_parameter_check.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


@pytest.fixture
def tiny_config(tmp_path):
    methods = {name:get_method(name) for name in ["SRC-KL-R", "SRC-R", "IMED", "Empirical-KL-UCB"]}
    primary = []
    for coefficient in [.5, 1.]:
        candidate = get_method("SRC-KL-R")
        candidate["id"] = "fixture-c" + str(coefficient)
        candidate["params"].update(cap_multiplier=4., log_coefficient=coefficient)
        methods[candidate["id"]] = candidate
        primary.append(candidate["id"])
    layouts, tasks = [], []
    for group in ["f17", "adaptive"]:
        layout = dict(id="invented-"+group, name="invented", group=group, T=8,
            epsilon=.1, eta=.02, delta=.05, metadata={},
            arms=[dict(arrival=1, mean=.4), dict(arrival=3, mean=.7)])
        layouts.append(layout)
        for rep in range(2):
            task = _task(layout, "bernoulli", rep, 718, "invented-replay",
                         {name:["parameter-check"] for name in methods})
            task["diagnostics"] = dict(primary_candidate_ids=primary,
                primary_comparison_family_size=8, study_phase="invented-validation",
                study_revision="invented-producer", numba_cache={"old_cache":"do-not-reuse"},
                study_driver_sha256="old-producer-hash", validation_plan_sha256="old-plan-hash",
                trajectory_replications=2, per_arm_methods=["SRC-R"], linear_points=3, log_points=2)
            tasks.append(task)
    config = dict(profile="invented-validation", layouts=layouts, methods=methods,
        expected_runs=len(tasks)*len(methods), tasks=task_records(tasks), source_files=input_files())
    path = tmp_path / "frozen.json"
    atomic_json(path, config)
    return path, config, tasks


def test_prepare_preserves_science_and_does_not_consult_git(tiny_config, monkeypatch):
    path, config, original = tiny_config
    original_check_output = subprocess.check_output
    def no_git(command, *args, **kwargs):
        first = command.split()[0] if isinstance(command, str) else command[0]
        if Path(str(first)).stem.lower() == "git":
            pytest.fail("Git must not be consulted")
        return original_check_output(command, *args, **kwargs)
    monkeypatch.setattr(subprocess, "check_output", no_git)
    tasks, methods, meta, snapshots = replay.prepare(path)
    assert methods == config["methods"]
    assert meta["origin_config_sha256"] == replay.digest(path.read_bytes())
    assert snapshots["origin_config.json"] == path.read_bytes()
    for before, after in zip(original, tasks):
        assert {k:v for k,v in before.items() if k != "diagnostics"} == {
            k:v for k,v in after.items() if k != "diagnostics"}
        old, new = before["diagnostics"], after["diagnostics"]
        assert new["origin_diagnostics"] == old
        assert "study_driver_sha256" not in new and "validation_plan_sha256" not in new
        assert new["numba_cache"] != old["numba_cache"]
        for key in replay.SCIENTIFIC_DIAGNOSTICS & old.keys():
            assert new[key] == old[key]


def test_tiny_run_analyze_resume_and_exact_scientific_replay(tiny_config, tmp_path, monkeypatch):
    path, config, original = tiny_config
    expected_shards = [simulate_task(task, config["methods"]) for task in original]
    output = tmp_path / "replay"
    manifest = replay.run(path, output, workers=2, render=True)
    assert manifest["status"] == "PASS"
    assert verify(output, check_current=True)["unique_trajectories"] == 24
    for table in ["runs", "trajectories", "counts"]:
        expected = [row for shard in expected_shards for row in shard[table]]
        with gzip.open(output / (table + ".csv.gz"), "rt", encoding="utf-8", newline="") as stream:
            actual = list(csv.DictReader(stream))
        assert len(actual) == len(expected)
        for expected_row, actual_row in zip(expected, actual):
            for field, value in expected_row.items():
                if field == "runtime_seconds":
                    continue
                if isinstance(value, (int, float)):
                    assert float(actual_row[field]) == float(value)
                else:
                    assert actual_row[field] == str(value)
    analysis = json.loads((output / "parameter_analysis/summary.json").read_text(encoding="utf-8"))
    assert analysis["primary_family_size"] == 8
    assert len(analysis["primary_candidates"]) == 2
    assert {Path(name).suffix for name in analysis["figures"]} == {".pdf", ".png", ".svg"}
    before = {name:(output / name).read_bytes() for name in ["runs.csv.gz", "trajectories.csv.gz", "counts.csv.gz"]}
    monkeypatch.setattr("srcbench.runner._worker", lambda *a, **k:pytest.fail("Resume must reuse all shards"))
    resumed = replay.run(path, output, workers=1, resume=True)
    assert resumed["resume_count"] == 1
    assert resumed["formal_experiment"] is False
    for name, data in before.items():
        assert (output / name).read_bytes() == data


def test_resume_rejects_changed_entry_and_provenance(tiny_config, tmp_path, monkeypatch):
    path, config, original = tiny_config
    output = tmp_path / "replay"
    replay.run(path, output, workers=1)
    changed = tmp_path / "changed_entry.py"
    changed.write_bytes(replay.ENTRY_PATH.read_bytes() + b"\n# simulated entry change\n")
    with monkeypatch.context() as scoped:
        scoped.setattr(replay, "ENTRY_PATH", changed)
        with pytest.raises(ValueError, match="changed replay entry"):
            replay.run(path, output, workers=1, resume=True)
    assets = replay.asset_bytes()
    assets["tools/parameter_statistics.py"] += b"\n# simulated live analysis change\n"
    with monkeypatch.context() as scoped:
        scoped.setattr(replay, "asset_bytes", lambda:dict(assets))
        with pytest.raises(ValueError, match="changed replay entry"):
            replay.run(path, output, workers=1, resume=True)
    altered = tmp_path / "same_configuration_new_bytes.json"
    altered.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="origin configuration"):
        replay.run(altered, output, workers=1, resume=True)
    snapshot = output / "replay_inputs/tools/parameter_statistics.py"
    snapshot.write_bytes(snapshot.read_bytes() + b"\n# tampered snapshot\n")
    with pytest.raises(ValueError, match="snapshot changed"):
        replay.run(path, output, workers=1, resume=True)
    with pytest.raises(ValueError, match="checksum mismatch"):
        replay.analyze(output)


@pytest.mark.parametrize("change", ["source", "seed", "count"])
def test_rejects_changed_scientific_fingerprint(tiny_config, change):
    path, config, original = tiny_config
    broken = deepcopy(config)
    if change == "source":
        broken["source_files"]["run_main.py"] = "bad-source-sha"
    elif change == "seed":
        broken["tasks"][0]["seed_base"] += 1
    else:
        broken["expected_runs"] += 1
    atomic_json(path, broken)
    with pytest.raises(ValueError):
        replay.prepare(path)


def test_cli_preview_does_not_create_output(tiny_config, tmp_path):
    path, config, original = tiny_config
    output = tmp_path / "preview-only"
    plan = replay.main(["run", "--config", str(path), "--output", str(output), "--dry-run"])
    assert plan["unique_trajectories"] == 24
    assert not output.exists()


@pytest.mark.parametrize("field,value", [("primary_alpha", .1),
    ("primary_groups", ["dense", "scale"]), ("primary_baselines", ["IMED", "SRC-R"])])
def test_nondefault_inference_is_rejected_before_execution(tiny_config, field, value):
    path, config, original = tiny_config
    config["tasks"][0]["diagnostics"][field] = value
    atomic_json(path, config)
    with pytest.raises(ValueError, match=field):
        replay.prepare(path)

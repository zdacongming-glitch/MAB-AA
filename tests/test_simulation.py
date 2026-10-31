from copy import deepcopy
import concurrent.futures
import json
import multiprocessing

import pytest

from srcbench.methods import METHODS
from srcbench.runner import run, verify
from srcbench.simulation import simulate_task


def fixture_task():
    return {"task_id": "tiny_fixture", "cell_id": "tiny__bernoulli", "cohort": "smoke",
            "law": "bernoulli", "rep": 0, "seed_base": 2026103151,
            "layout": {"id": "tiny", "name": "tiny", "group": "f17", "T": 45,
                       "epsilon": .2, "eta": .05, "delta": .05,
                       "arms": [{"arrival": 1, "mean": .25}, {"arrival": 1, "mean": .6},
                                {"arrival": 22, "mean": .8}]},
            "methods": ["SRC-R", "SRC-KL-L060", "TS", "TS-SMAB-bounded"],
            "suites": ["reward", "joint"],
            "method_suites": {m: ["reward", "joint"] for m in [
                "SRC-R", "SRC-KL-L060", "TS", "TS-SMAB-bounded"]}}


def scientific_rows(result):
    return {row["method"]: {k: v for k, v in row.items() if k != "runtime_seconds"}
            for row in result["runs"]}


def test_method_order_does_not_change_scientific_results():
    task = fixture_task()
    first = simulate_task(task, METHODS)
    reverse = deepcopy(task)
    reverse["methods"].reverse()
    assert scientific_rows(first) == scientific_rows(simulate_task(reverse, METHODS))
    for row in first["runs"]:
        assert row["service_pulls"] + row["service_denials"] == row["service_attempts"]
        assert row["area"] <= row["eligible_arm_time"]
    for method in task["methods"]:
        counts = [r for r in first["counts"] if r["method"] == method and r["t"] == 45]
        assert sum(r["n"] for r in counts) == 45


def test_worker_count_preserves_potential_world():
    task = fixture_task()
    reference = scientific_rows(simulate_task(task, METHODS))
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,
            mp_context=multiprocessing.get_context("spawn")) as pool:
        result = pool.submit(simulate_task, task, METHODS).result(timeout=90)
    assert reference == scientific_rows(result)


def test_diagnostic_subset_does_not_remove_endpoints():
    from srcbench.runner import _validate_shard
    task = fixture_task()
    task.update(rep=8, cohort="main", diagnostics={"trajectory_replications": 4,
                "linear_points": 41, "log_points": 20,
                "per_arm_methods": ["SRC-R", "SRC-KL-R"]})
    result = simulate_task(task, METHODS)
    assert len(result["runs"]) == 4
    assert result["trajectories"] == []
    assert {row["method"] for row in result["counts"]} == {"SRC-R"}
    assert {row["t"] for row in result["counts"]} == {45}
    assert sum(row["n"] for row in result["counts"]) == 45
    _validate_shard(result, task)


def test_manifest_resume_checks_source_and_shard_integrity(tmp_path, monkeypatch):
    import srcbench.design as design
    import srcbench.runner as runner
    monkeypatch.setattr(design, "build_tasks", lambda profile: [fixture_task()])
    out = tmp_path / "run"
    run("smoke-small", out, workers=1, render=False)
    assert verify(out)["unique_trajectories"] == 4
    initial_hash = runner.sha256(out / "shards" / "tiny_fixture.json.gz")
    run("smoke-small", out, workers=1, resume=True, render=False)
    assert runner.sha256(out / "shards" / "tiny_fixture.json.gz") == initial_hash
    monkeypatch.setattr(runner, "input_files", lambda: {"changed.py": "new-hash"})
    with pytest.raises(ValueError, match="changed source"):
        run("smoke-small", out, workers=1, resume=True, render=False)
    with (out / "shards" / "tiny_fixture.json.gz").open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        verify(out)

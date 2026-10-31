"""Scientific aggregation checks: aliases, pairing, weighting, flags, counts."""
import csv
import gzip
import json
import math
from pathlib import Path

import pytest

from srcbench.analysis import analyze, _read


def _row(layout, rep, method, regret, *, cohort="main", suites="reward;joint", flag=0):
    return dict(cohort=cohort, group="f17", layout_id=layout, law="bernoulli", rep=rep,
                method=method, suites=suites, T=100, K=2, epsilon=.15, eta=.03, delta=.05,
                regret=regret, area=100, area_all=120, eligible_arm_time=200, all_arm_time=200,
                final_unresolved=1, final_all_unresolved=1, service_pulls=0, service_attempts=0,
                service_denials=0, guard_exclusions=0, guard_changed=0, label_error=0,
                coverage_error=flag, empty_intersection=0, reward_tax=0, service_tax=0,
                budget_scale=10, checkpoint_hits=0, never_sampled=0, action_hash="123",
                runtime_seconds=.01)


def _write(path, rows):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "wt", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def _fixture(tmp_path, rows, **manifest):
    (tmp_path / "manifest.json").write_text(json.dumps(dict(status="PASS", expected_runs=len(rows), **manifest)))
    (tmp_path / "config.json").write_text(json.dumps(dict(profile="smoke-small", expected_runs=len(rows))))
    _write(tmp_path / "runs.csv.gz", rows)
    return tmp_path


def test_equal_cell_weighting_paired_variance_and_aliases(tmp_path):
    rows = []
    for layout, src_values, differences in (("a", [10, 20], [1, 3]),
                                            ("b", [90, 100, 110, 120], [2, 4, 6, 8])):
        for rep, (src, difference) in enumerate(zip(src_values, differences)):
            rows.append(_row(layout, rep, "SRC-R", src, flag=int(layout == "a" and rep == 0)))
            rows.append(_row(layout, rep, "SRC-KL-R", src + difference))
    out = _fixture(tmp_path, rows)
    result = analyze(out)
    assert result["unique_trajectories"] == 12
    assert result["suite_memberships"] == 24
    assert result["scientific_status"] == "SMOKE_ONLY_FULL_NOT_RUN"
    modules = _read(out / "analysis/module_summary.csv")
    src = next(x for x in modules if x["suite"] == "reward" and x["method"] == "SRC-R")
    assert float(src["regret_mean"]) == pytest.approx((15 + 105) / 2)
    assert int(src["coverage_error_paths"]) == 1
    comparisons = _read(out / "analysis/paired_differences.csv")
    paired = next(x for x in comparisons if x["suite"] == "reward" and x["contrast"] == "direct_kl_src")
    assert float(paired["difference"]) == pytest.approx(3.5)
    assert float(paired["mcse"]) == pytest.approx(math.sqrt((1 + (20/3)/4) / 4))
    assert int(paired["pairs"]) == 6
    assert int(paired["unmatched_left"]) == 0
    assert int(paired["unmatched_right"]) == 0
    assert "SMOKE / PIPELINE CHECK ONLY" in (out / "analysis/report.html").read_text(encoding="utf-8")


def test_cohorts_are_never_pooled_and_unmatched_paths_are_visible(tmp_path):
    rows = [_row("a", i, m, i + offset, cohort=cohort, suites="reward")
            for cohort in ("main", "tail") for m, offset in (("SRC-R", 0), ("SRC-KL-R", 1)) for i in range(2)]
    rows.append(_row("a", 2, "SRC-R", 1, suites="reward"))
    analyze(_fixture(tmp_path, rows))
    modules = _read(tmp_path / "analysis/module_summary.csv")
    assert {r["cohort"] for r in modules} == {"main", "tail"}
    assert len(modules) == 4
    paired = _read(tmp_path / "analysis/paired_differences.csv")
    main = next(r for r in paired if r["cohort"] == "main")
    assert int(main["unmatched_right"]) == 1
    assert int(main["pairs"]) == 2


def test_duplicate_endpoints_are_rejected(tmp_path):
    row = _row("a", 0, "SRC-R", 1)
    with pytest.raises(ValueError, match="Duplicate trajectory key"):
        analyze(_fixture(tmp_path, [row, row]))


def test_counts_support_multiple_checkpoints_and_analytic_constants(tmp_path):
    out = _fixture(tmp_path, [_row("two_close", 0, "SRC-R", 1)])
    counts = [dict(cohort="main", group="f17", layout_id="two_close", law="bernoulli", rep=0,
                   method="SRC-R", arm=1, birth=1, mean=.4, n=t//2, final_gap=.2, current_gap=.2, t=t, T=100)
              for t in (10, 100)]
    _write(out / "counts.csv.gz", counts)
    analyze(out)
    records = _read(out / "analysis/theory_counts.csv")
    assert len(records) == 2
    assert {float(r["t"]) for r in records} == {10, 100}
    assert float(records[0]["src_count_constant"]) == pytest.approx(25)
    kl = .4*math.log(.4/.6) + .6*math.log(.6/.4)
    assert float(records[0]["kl_count_constant"]) == pytest.approx(1/kl)


def test_main_joint_primary_and_finite_area_modes_stay_distinct(tmp_path):
    methods = ["SRC-R", "SRC-KL-R", "SRC-L060", "SRC-KL-L060", "SRC-L100", "SRC-KL-L100",
               "SRC-area", "SRC-KL-area", "SRC-widest-L060", "SRC-KL-widest-L060", "IMED"]
    rows = [_row("a", rep, method, rep + idx, suites="joint")
            for idx, method in enumerate(methods) for rep in range(2)]
    out = _fixture(tmp_path, rows)
    analyze(out)
    comparisons = _read(out / "analysis/paired_differences.csv")
    assert not any(x["contrast"] == "reward_baselines" for x in comparisons)
    direct = [x for x in comparisons if x["contrast"] == "direct_kl_src" and x["metric"] == "regret"]
    assert any(x["left"] == "SRC-KL-L060" and x["primary"] == "True" for x in direct)
    assert any(x["left"] == "SRC-KL-L100" for x in direct)
    assert any(x["left"] == "SRC-KL-area" for x in direct)
    assert any(x["contrast"] == "matched_planner" for x in comparisons)


def test_streaming_snapshots_keep_cell_weights_and_last_arrival_regime(tmp_path):
    rows = [_row(layout, rep, "SRC-R", value, suites="reward")
            for layout, values in (("a", [10, 20]), ("b", [90, 100, 110, 120]))
            for rep, value in enumerate(values)]
    out = _fixture(tmp_path, rows)
    config = json.loads((out / "config.json").read_text())
    config["layouts"] = [dict(id="a", arms=[dict(arrival=1)]), dict(id="b", arms=[dict(arrival=20)])]
    (out / "config.json").write_text(json.dumps(config))
    snapshots = [dict(**{k: row[k] for k in ("cohort", "group", "layout_id", "law", "rep", "method", "suites")},
                      t=t, regret=row["regret"], area=100, area_all=120,
                      unresolved=1, unresolved_all=1, service_pulls=0, never_sampled=0, budget_scale=10, K=2)
                 for row in rows for t in (10, 100)]
    _write(out / "trajectories.csv.gz", snapshots)
    analyze(out)
    results = _read(out / "analysis/trajectories_summary.csv")
    early = next(r for r in results if float(r["t"]) == 10)
    late = next(r for r in results if float(r["t"]) == 100)
    assert float(early["regret_mean"]) == pytest.approx(60)
    assert float(early["regret_over_log_t_mean"]) == pytest.approx(15/math.log(10))
    assert float(late["regret_over_log_t_mean"]) == pytest.approx(60/math.log(100))


def test_spectrum_normalization_uses_current_value_not_running_maximum(tmp_path):
    rows = [_row("a", rep, "SRC-R", regret, suites="reward")
            for rep, regret in enumerate((40, 60))]
    out = _fixture(tmp_path, rows)
    snapshots = []
    for row in rows:
        for t, current, running, regret in ((10, 4, 8, 10 + 10*row["rep"]),
                                             (100, 5, 20, row["regret"])):
            snapshots.append(dict(
                **{k: row[k] for k in ("cohort", "group", "layout_id", "law", "rep", "method", "suites")},
                t=t, regret=regret, area=100, area_all=120, unresolved=1, unresolved_all=1,
                service_pulls=0, never_sampled=0, budget_scale=running, arrival_spectrum=current, K=2))
    _write(out / "trajectories.csv.gz", snapshots)
    analyze(out)
    results = _read(out / "analysis/trajectories_summary.csv")
    early = next(r for r in results if float(r["t"]) == 10)
    late = next(r for r in results if float(r["t"]) == 100)
    assert float(early["regret_over_spectrum_mean"]) == pytest.approx(15/4)
    assert float(late["regret_over_spectrum_mean"]) == pytest.approx(50/5)
    assert float(late["regret_over_spectrum_mcse"]) == pytest.approx(2)
    # The separately retained running budget scale would give 50/20.
    assert float(late["budget_scale_mean"]) == 20
    assert float(late["regret_over_spectrum_mean"]) != pytest.approx(50/20)


def test_plot_exports_three_formats_and_honest_smoke_caption(tmp_path):
    from srcbench.plotting import plot
    rows = [_row("a", rep, method, rep + idx, suites="joint")
            for idx, method in enumerate(("SRC-R", "SRC-KL-R", "SRC-L100", "SRC-KL-L100", "SRC-area", "SRC-KL-area"))
            for rep in range(2)]
    out = _fixture(tmp_path, rows)
    paths = plot(out)
    assert paths and {Path(p).suffix for p in paths} == {".png", ".pdf", ".svg"}
    assert all(Path(p).is_file() for p in paths)
    captions = _read(out / "figures/captions.csv")
    assert all("SMOKE ONLY" in r["caption"] for r in captions)
    assert any("uncapped area is a separate star" in r["caption"] for r in captions)

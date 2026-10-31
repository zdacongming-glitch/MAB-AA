"""Regression checks for paired percentages and source-density provenance."""
import csv
import gzip
import json
from pathlib import Path

import pytest

from srcbench.relative_regret import (COLUMNS, SECTIONS, TARGETS, _estimate, _label, _layout_metadata,
                                     analyze_relative)


def _cell(section, candidate, comparator):
    return dict(section=section, candidate=list(candidate), comparator=list(comparator))


def test_percentage_is_ratio_of_macro_means_not_mean_of_percentages():
    cells = {("a", "law"): _cell("f17", [2]*4, [1]*4),
             ("b", "law"): _cell("f17", [50]*4, [100]*4)}
    result = _estimate(cells)
    assert result["candidate_regret"] == 26
    assert result["comparator_regret"] == 50.5
    assert result["percent_change"] == pytest.approx(100*(26/50.5-1))
    assert result["percent_change"] != pytest.approx((100-50)/2)


def test_ratio_interval_keeps_pair_covariance():
    cells = {("a", "law"): _cell("f17", [2, 4, 6, 8], [1, 2, 3, 4])}
    result = _estimate(cells)
    assert result["percent_change"] == 100
    assert result["percent_mcse"] == 0
    assert result["percent_ci_low"] == result["percent_ci_high"] == 100
    assert result["difference_mcse"] > 0


def test_equal_cell_primary_and_equal_section_secondary_are_distinct():
    cells = {("a", "law"): _cell("f17", [1]*4, [2]*4),
             ("b", "law"): _cell("f17", [1]*4, [2]*4),
             ("c", "law"): _cell("adaptive", [9]*4, [3]*4)}
    assert _estimate(cells)["percent_change"] == pytest.approx(100*(11/7-1))
    assert _estimate(cells, balanced=True)["percent_change"] == 100


def test_zero_comparator_is_undefined_without_epsilon_substitution():
    result = _estimate({("a", "law"): _cell("f17", [1, 2, 3, 4], [0]*4)})
    assert result["percent_change"] is None
    assert result["percent_mcse"] is None
    assert result["percent_status"].startswith("undefined")
    assert result["regret_difference"] == 2.5


def test_labels_preserve_parent_density_and_report_actual_arm_count_range():
    layouts = [dict(id=f"dense{i}", group="dense", T=400, arms=[{}]*k,
                    metadata=dict(derivative=dict(parent_arm_count=100, parent_T=8000, parent_id=f"source{i}")))
               for i, k in enumerate((20, 30))]
    meta = _layout_metadata(layouts)
    assert {r["section"] for r in meta.values()} == {"dense_K100"}
    assert _label("dense_K100", meta) == "Dense\nK 100 → 20–30"


def _write(path, rows):
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def _read(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_all_method_exports_and_two_panel_three_format_artifacts(tmp_path):
    from srcbench.methods import METHODS, BASELINE_IDS
    layouts = []
    for i, section in enumerate(SECTIONS):
        group = section.split("_K")[0]
        source_k = int(section.split("_K")[1]) if "_K" in section else 2
        layouts.append(dict(id=f"layout{i}", group=group, T=400, arms=[{}]*2,
                            metadata=dict(derivative=dict(parent_arm_count=source_k, parent_T=8000,
                                                          parent_id=f"original{i}"))))
    rows = []
    for layout in layouts:
        for rep in range(4):
            for index, method in enumerate(METHODS):
                rows.append(dict(cohort="screen", group=layout["group"], layout_id=layout["id"], law="bernoulli",
                                 rep=rep, method=method, suites="reward;joint", T=400, K=2,
                                 regret=index+rep+1, area=100, area_all=120, eligible_arm_time=200,
                                 all_arm_time=200, never_sampled=0, coverage_error=int(len(rows) == 0),
                                 label_error=0, empty_intersection=0))
    (tmp_path / "config.json").write_text(json.dumps(dict(profile="screen-all", layouts=layouts, methods=METHODS,
                                                          expected_runs=len(rows))), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps(dict(status="PASS", expected_runs=len(rows))), encoding="utf-8")
    _write(tmp_path / "runs.csv.gz", rows)
    summary = analyze_relative(tmp_path)
    assert summary["unique_trajectories"] == len(SECTIONS)*4*len(METHODS)
    assert summary["all_six_sections_present"]
    assert summary["scientific_flag_paths"]["coverage_error"] == 1
    assert len(summary["comparators"]) == len(BASELINE_IDS)
    assert summary["comparator_count"] == len(BASELINE_IDS)
    assert not summary["stars"]
    assert {Path(p).suffix for p in summary["figures"]} == {".png", ".pdf", ".svg"}
    assert all(Path(p).is_file() for p in summary["figures"])
    out = tmp_path / "relative_regret"
    cells = _read(out / "all_cell_methods.csv")
    assert len(cells) == len(SECTIONS)*len(METHODS)
    assert {r["method"] for r in cells} == set(METHODS)
    assert sum(int(r["coverage_error_paths"]) for r in cells) == 1
    matrix = _read(out / "percent_matrix.csv")
    assert len(matrix) == len(TARGETS)*len(BASELINE_IDS)*len(COLUMNS)
    wide = _read(out / "percent_matrix_SRC-KL-R.csv")
    assert len(wide) == len(BASELINE_IDS)
    assert "all_cells" in wide[0] and "balanced_sections" in wide[0]
    all_methods = _read(out / "all_method_relative_overall.csv")
    assert {r["candidate"] for r in all_methods} == set(METHODS)
    direct = _read(out / "direct_KL_minus_SRC.csv")
    assert {r["comparator"] for r in direct} == {"SRC-R"}
    report = (out / "report.html").read_text(encoding="utf-8")
    assert f"{len(BASELINE_IDS)} canonical baseline configurations" in report
    assert f"all {len(METHODS)} executed methods" in report

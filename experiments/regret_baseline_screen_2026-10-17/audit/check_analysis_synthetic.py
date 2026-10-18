"""Synthetic CSV accounting checks; never run any bandit policy."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("screen_analysis", ROOT / "analyze.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)
original = json.loads((ROOT.parent / "fccp_frozen/protocols/holdout-freeze.json").read_text())
OUT = ROOT / "audit/synthetic-analysis"
OUT.mkdir(parents=True, exist_ok=True)
protocol = OUT / "protocol.json"
protocol.write_text(json.dumps(dict(reps=96, methods=[dict(id="fr", name="F-R"), dict(id="toy", name="synthetic")])), encoding="utf-8")
phash = hashlib.sha256(protocol.read_bytes()).hexdigest()
rows = []
for si, s in enumerate(original["scenarios"]):
    for r in range(96):
        reference = 2 + si + r / 96
        for method in ["F-R", "synthetic"]:
            counts = [s["T"]] + [0] * (len(s["means"]) - 1)
            rows.append(dict(scenario_index=si, scenario=s["name"], rep=r, method=method, T=s["T"], K=len(counts),
                regret=reference if method == "F-R" else reference + .1 + .05 * math.sin(r),
                status="ok", total_pulls=s["T"], counts=json.dumps(counts), runtime_seconds=.01,
                protocol_sha256=phash, source_payload_sha256="a" * 64, means_sha256=f"mu-{si}-{r}",
                rewards_sha256=f"rewards-{si}-{r}", policy_seed=si * 10000 + r, reward_seed=si * 10000 + r,
                frozen_regret=np.nan, difference_from_frozen=np.nan))
raw = pd.DataFrame(rows)


def save(frame):
    for p in OUT.glob("runs-[0-9][0-9].csv"):
        p.unlink()
    for si, d in frame.groupby("scenario_index"):
        d.to_csv(OUT / f"runs-{si:02d}.csv", index=False)


def run(frame):
    save(frame)
    with contextlib.redirect_stdout(io.StringIO()):
        return analysis.analyze(OUT, protocol)


summary, paired, suite = run(raw)
# A second pass must not re-import its own derived runs-all.csv.
with contextlib.redirect_stdout(io.StringIO()):
    analysis.analyze(OUT, protocol)
delta = .1 + .05 * np.sin(np.arange(96))
expected_mean = delta.mean()
expected_se = delta.std(ddof=1) / np.sqrt(96)
toy = paired[paired.method == "synthetic"]
assert np.allclose(toy.paired_difference, expected_mean, rtol=0, atol=1e-14)
assert np.allclose(toy.paired_mcse, expected_se, rtol=0, atol=1e-14)
assert np.all(toy.ci95_low > 0)
assert np.all(toy.simultaneous95_low < toy.ci95_low)
suite_toy = suite[suite.method == "synthetic"].iloc[0]
assert abs(suite_toy.paired_mcse - expected_se / np.sqrt(12)) < 1e-14
checks = ["full_synthetic_matrix", "paired_MCSE", "Bonferroni_widens_CI", "stratified_suite_MCSE", "repeat_analysis_excludes_derived_CSV"]


def rejects(name, frame, message):
    try:
        run(frame)
    except RuntimeError as exc:
        assert message in str(exc), (name, str(exc))
        checks.append(name)
    else:
        raise AssertionError("Failed to reject: " + name)


rejects("balanced_but_missing_last_rep", raw[raw.rep != 95], "full 12 x 96")
rejects("duplicate_success_row", pd.concat([raw, raw.iloc[[0]]]), "Duplicate")
debug = raw.copy()
debug["T"] = 600
debug["total_pulls"] = 600
rejects("debug_horizon_not_formal", debug, "Debug horizon")
bad = raw.copy(); bad.loc[0, "rewards_sha256"] = "unpaired"
rejects("unpaired_potential_streams", bad, "exactly paired")
bad = raw.copy(); bad.loc[0, "counts"] = json.dumps([-1] + [0] * (int(raw.K.iloc[0]) - 1))
rejects("invalid_count_vector", bad, "Per-arm counts")
bad = raw.copy(); bad.loc[0, "status"] = "error"
rejects("error_row", bad, "Errored")
bad = raw.copy(); bad.loc[0, "protocol_sha256"] = "another"
rejects("mixed_protocol_versions", bad, "Mixed source/protocol")
save(raw)
report = dict(passed=True, checks=checks, n_synthetic_rows=len(raw), no_bandit_policies_executed=True,
    expected_difference=float(expected_mean), expected_paired_mcse=float(expected_se),
    analysis_sha256=hashlib.sha256((ROOT / "analyze.py").read_bytes()).hexdigest())
(ROOT / "audit/analysis-synthetic-check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))

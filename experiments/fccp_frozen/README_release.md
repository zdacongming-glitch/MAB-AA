# F-CCP frozen numerical release

The current portable entry is `../../reproduce.py`, run from the manuscript project root. The complete article, including the supplement, is now in the single `manuscript.tex`. The earlier numerical source, protocol and result identities below are preserved.

This directory contains exact computational copies from the supplied F-CCP research package, together with the three complete original ZIP archives in `original-archives/`. The original research directories were read only during manuscript revision. The complete archives preserve the research reports, theoretical notes, development snapshots, failed-compilation records, superseded comparator, and internal assessments; internal assessment scores are not evidence in the paper.

The authoritative copying record is `../../revision2/analysis/release-manifest.json`. The supplied `MANIFEST.json` is unchanged and describes the complete original F-CCP package, including documents retained inside its ZIP rather than extracted here. The release manifest identifies the extracted subset and the ZIPs individually. All copied computational files retain their original SHA-256 digests.

## Production entries and dependency closure

| Purpose | Entry | Boundary |
|---|---|---|
| Main frozen batch decision | `src/flexible_v2.py::choose_dual` | Two separate optimism-gap ledgers |
| Main frozen batch driver | `src/study_v2.py` | Uses `holdout-freeze.json`; rerunning writes new simulation files |
| Interactive API | `src/flexible_ccp.py::FlexibleCCP` | Accepts only current arrivals and one chosen-arm observation |
| Corrected ALL decision | `src/flexible_matched.py::choose_dual` | Uses the corrected planner price |
| Corrected ALL driver | `src/study_matched.py` | Uses `matched-all-freeze.json` |
| Corrected planner dispatch | `src/matched_all.py::service_plan_matched` | Same projected-mean price for the adaptive ALL control |
| Shared evidence and numerical tools | `src/ccp_primitives.py`, `src/flexible_engine.py` | Preserved frozen dependencies |
| Historical single-ledger development | `src/flexible_engine.py::choose_flexible` | Archived; not the main production entry |

All `src/*.py`, protocols, numerical results, diagnostics, source snapshots and requirements from the computational package are included. Do not substitute the older single-ledger routine for the production two-ledger routine merely because both have “flexible” in their names. No frozen policy code, confidence constants, tolerance or controller parameter was changed in this revision.

## Data identity

| Dataset | Size | Role |
|---|---:|---|
| `results/holdout-all.csv` | 27,648 | Original frozen main test: 12 scenarios × 24 configurations × 96 paired repetitions |
| `results/matched-all-all.csv` | 1,152 | Subsequent correction of the adaptive ALL price input |
| Both retained together | 28,800 | 25 stored method IDs, including both ALL versions |
| Corrected primary roster | 27,648 | Replace `ALL-auto-0.6` with `ALL-auto-costmatched`; do not average them |
| F-CCP development | 14,016 | Three valid development rounds, separate from testing |

The earlier checkpoint comparison has 5,760 records (four scenarios, nine methods, 160 repetitions). The first CCP study has 13,440 records (ten scenarios, 21 methods, 64 repetitions); the frontier/Shared study has 12,672 (12 scenarios, 22 methods, 48 repetitions). Their complete source archives are retained, and their tests are never pooled with the F-CCP suite. Similar names such as “stable”, “burst”, “ALL” or “CCP” do not establish an identical environment or implementation.

`regret` is the manuscript's cumulative dynamic regret, the sum of current mean gaps. `area` is boundary-separated unresolved arm-time for that scenario's fixed reporting tolerance. `final_unresolved` excludes the boundary band; `final_all_unresolved` includes it. Service attempts equal successful service pulls plus denials. Proposed service mass is not the actual number of service pulls. Virtual optimism-gap ledgers differ from evaluator-computed service regret.

All label-error, confidence-coverage and empty-intersection paths enter the means, areas, empirical quantiles and maxima. The original adaptive ALL records are preserved as a superseded controller diagnostic. Only its proposed-arm cost return was corrected, after separate freezing, with unchanged F-CCP settings, scenarios and seeds. The corrected comparator is not a method that had already been present in the original 24-method freeze.

## Rebuild tables and figures without simulation

From the manuscript project root:

```powershell
python reproduce.py --verify
python reproduce.py --figures
python reproduce.py --smoke
```

These wrappers verify the distributed inputs, reanalyze the stored endpoints, and check the interface in fresh work copies under `_reproduced/`. The figure command invokes the historical reanalyzer with `--release-only`, generating its numerical LaTeX strings, CSV/JSON audit outputs and figures inside the work copy. It creates no new editable `.tex` entry and leaves the complete `manuscript.tex` unchanged. The earlier CCP and frontier data can also be read from their retained original ZIPs.

The verify command invokes the plan's Appendix F verifier in a work copy. It checks frozen input hashes, counts, pull accounting, budgets, phase diagnostics, paired statistics and retained failure counts. This is reanalysis of existing results, not a new experiment or a probability certificate.

The third command imports only the copied source. It checks 600 same-backend compatible actions, 320 API actions across the four modes, ten same-state/same-seed batch action cases and six API validation rejections. Its observations are prescribed API inputs, not new reward-performance trials. Results and the actual local environment are recorded in `revision2/analysis/interface-checks.json`; Numba cache writes are redirected into that revision directory.

The two figures use terminal records only. Diagnostic `*-paths.npz` files preserve the first four replications per scenario on a 200-round grid. They do not provide 96-replication mean learning curves. No new simulations were run during this manuscript revision.

## Interactive use

Add `experiments/fccp_frozen/src` to Python's module path, then:

```python
from flexible_ccp import FlexibleCCP

alg = FlexibleCCP.preset("balanced", epsilon=0.2, eta=0.05, delta=0.05, seed=7)
arm, is_service = alg.choose(new_arms=["A", "B"])
alg.observe(0.7)  # One actual reward from the selected arm.
positive, negative, unresolved = alg.report()
alg.set_priority(1.0)  # Between completed observations only.
```

The task parameters epsilon, eta and delta stay fixed. Priority affects action allocation, not evidence or the definition of the reporting task. Changing priority retains all sample counts, reward sums, confidence intervals, phase and both ledgers. It does not lift an existing certification cap. The `classification` preset starts with no certification cap. `service_budget=None` disables the guard; zero allows only zero-cost service and is not infinite. The pure-reward batch JSON has a null inactive service cap, while its interactive preset uses zero; both disable service through priority zero, and the frozen files were not rewritten to make the encodings look identical.

Compatibility is pathwise only for the same baseline rule, complete initial state, backend and random-number call order. The interactive API uses an owned NumPy Generator; the batch code uses Numba RNG. Equal seeds across those backends do not imply bitwise identical paths. The cold Beta action scores are separate from the valid report evidence.

## Recorded resources and limits

The original F-CCP audit records Python 3.13.5, NumPy 2.3.5 and Numba 0.65.1 on Linux x86-64. Its environment file additionally records pandas 2.2.3, SciPy 1.17.0 and matplotlib 3.10.8. No benchmark CPU was recorded. Original per-run timings and worker logs remain available, but do not define a single comparable end-to-end wall-clock time. The older checkpoint study's Windows environment and 13.5-second timing do not describe F-CCP.

The local revision's short interface check ran under Python 3.11.7, NumPy 1.26.4 and Numba 0.59.0 on Windows; its approximately 16-second duration is a check duration, not the main experiment's runtime. No cross-version bitwise reproduction claim follows.

The production numerical implementation retains the $10^{-12}$ guard tolerance, frozen planner regularization and outward confidence inversion. The 1,035 historical phase-boundary delays are retained. The exact arithmetic mathematical contract is distinct from those finite-precision diagnostics. The direct pairwise planner/reporter has quadratic pair work per round; machine integer checkpoints and the fixed 64 spectrum bins limit this implementation. No code or parameter change was made to conceal those limits.

This release accompanies the manuscript in its Git project. No public repository, DOI or permanent accession is claimed. Full reruns use `python reproduce.py --simulate --suite fccp` in a fresh isolated workspace; they remain separate from the read-only checks and preserve the distributed frozen outputs.

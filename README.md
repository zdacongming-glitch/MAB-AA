# MAB-AA numerical reproduction

Numerical code, frozen experiment settings, raw simulation results, summaries and figures for the UCB-AA / F-CCP study. This repository is dedicated to computation; the manuscript and the author's complete research archive are maintained separately.

## Install and reproduce

Use Python 3.11 and the versions recorded in `requirements-reproduce.txt`:

```bash
python -m pip install -r requirements-reproduce.txt
python reproduce.py --verify
python reproduce.py --figures
python reproduce.py --smoke
```

`--verify` checks distributed file hashes, the lossless historical data archives and F-CCP endpoint accounting. `--figures` recomputes numerical summaries and redraws the F-CCP, checkpoint and expanded-baseline figures from stored results. `--smoke` checks algorithm interfaces and driver imports. These commands create separate runs under `_reproduced/` and leave the distributed code, settings and results unchanged. They do not require TeX or any manuscript files, and do not run a full performance experiment.

To rerun a complete frozen test suite:

```bash
python reproduce.py --simulate --suite fccp --workers 4
python reproduce.py --simulate --suite ccp --workers 4
python reproduce.py --simulate --suite frontier --workers 4
python reproduce.py --simulate --suite checkpoint --workers 4
python reproduce.py --simulate --suite baseline --workers 4
python reproduce.py --simulate --suite original --workers 4
```

`--suite all` runs the first five suites; the historical original-submission experiment is selected separately with `--suite original`. Each simulation uses a fresh work copy and the stored settings. Full runs can take substantially longer than verification, plotting or interface checks. Historical Python versions and hardware records are retained in each experiment's environment files; identical output bytes across numerical-library versions are not promised.

## Code and stored results

| Location | Contents |
| --- | --- |
| `experiments/fccp_frozen/` | F-CCP implementations, development snapshots, frozen protocols, paired test runs and numerical summaries. The main suite has 27,648 records; the corrected ALL comparator adds 1,152 separately retained records. |
| `experiments/ccp_frozen/` | Earlier CCP code, development results and 13,440 test records, with sampling paths and plots. |
| `experiments/frontier_frozen/` | Frontier-study simulations, 12,672 test records and small-instance enumeration/optimization code and results. Its `prior/` modules are runtime dependencies. |
| `experiments/results/` | Checkpoint experiment: 5,760 records, configurations, summaries and paths. Drivers are in `experiments/`. |
| `experiments/pilot/` | Earlier numerical pilot outputs, kept separate from the final tests. |
| `experiments/regret_baseline_screen_2026-10-17/` | Expanded regret comparison: 12 scenarios, 17 configurations, 96 paired repetitions, 19,584 records, analysis code and figures. |
| `experiments/original_submission_archive/` | Original C/E simulation drivers, settings, outcomes and plots. Large checkpoint CSVs are stored as lossless `.csv.gz` files. |
| `analysis/` | Standalone numerical analysis, plotting and interface-check programs; `analysis/results/` contains stored reanalysis CSVs. |
| `figures/` | Numerical visualizations and the checkpoint plotting program. Current F-CCP plots are in `figures/fccp/`; further plots remain with their experiment suite. |
| `metadata/` | Numerical file checksums and verification results. |

The primary F-CCP analysis replaces the superseded ALL configuration with its corrected version. Both sets of raw records remain available. Development and pilot outcomes are retained separately and are not combined with frozen test outcomes. The expanded-baseline comparison reuses previously examined scenarios; it is a descriptive extension, rather than a new holdout test.

## Individual plotting commands

These examples write to new directories:

```bash
python analysis/plot_fccp.py --data-root experiments/fccp_frozen --output-dir _reproduced/fccp_plots
python analysis/plot_baselines.py --results-dir experiments/regret_baseline_screen_2026-10-17/results --output-dir _reproduced/baseline_plots
```

The suite-specific analysis and plotting programs are also retained beside their inputs. Some historical programs write into their own directories; run them in a copy, or use `reproduce.py` to create one. A historical F-CCP exploration failed before successful compilation and has no complete engine snapshot; it is not part of the reproducible final test results.

Frozen policy implementations, seeds and raw numerical results retain their original bytes. Standalone entry and plotting scripts provide the numerical-only interface. The repository has no dependency on a parent `proposal/` directory or Overleaf checkout.

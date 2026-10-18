# Historical checkpoint numerical comparisons

This README describes the earlier four-scenario checkpoint study. The complete resubmission also distributes C16, P16, F17 and original-submission archives in the neighboring subdirectories. Start from `../README.md` and use `python reproduce.py --verify`, `--figures`, `--build` or `--simulate --suite checkpoint` at the manuscript root; the wrapper runs all writing operations in an isolated work copy.

The production results use protocol version 1.1, four fixed Bernoulli environments, nine methods, 160 paired replications per environment, and 20,000 physical pulls per run: 5,760 runs in total. All eight-arm means, arrival times, seeds, and policy parameters are in `results/config.json`. They are descriptive mechanism and finite-budget diagnostics; these environments are not the restricted asymptotic theorem family.

Run from the manuscript directory:

```powershell
python -X utf8 experiments/run_experiments.py
python -X utf8 figures/gen_fig_performance.py
```

Dependencies are Python, NumPy, Numba, pandas, SciPy, and matplotlib; their actual versions are pinned in `requirements.txt`. `results/manifest.json` records the actual versions, original CP source hash, runner hash, configuration hash, and run/path hashes. The unmodified original CP implementation is copied into `reference_cp_ucb_aa.py`, so the manuscript folder is self-contained. Its repository origin and byte hash are recorded in the manifest. The original implementation and research package were read without modification. The resource detector found 28 logical CPU cores, 20 physical cores, about 11.9 GB available RAM and an NVIDIA GPU. These small loops use compiled CPU execution and do not need GPU allocation or multiprocessing. The first resource invocation needed Python UTF-8 mode on Windows because the detector prints emoji.

The configuration uses the same nominal parameters $\varepsilon=.30$, $\eta=.10$, $\delta=.05$ and the same available-arm report target for every method. Potential Bernoulli reward streams are shared by arm label and lifetime pull number within each replication. A method receives only current arrivals and observed history. True means, future arrivals, the final number of arms, and the evaluation endpoint do not enter its action rule; arrays are preallocated for simulation storage.

The CP setting $\rho=.04$ has $2\rho<\eta$ and hence all separated arms are resolvable once every checkpoint is complete on the coverage event. Its eight quotas sum to 73,083, exceeding the physical budget. The setting $\rho=.12$ has total quota 8,123 and is a coarser engineering choice. It still has reliable fixed-checkpoint labels, but cannot guarantee completeness for every arm more than $.10$ from the relative boundary. The results never label the latter choice as theorem-safe completeness at $\eta=.10$.

The confidence-driven all-good-arm adaptation is a newly specified retained-history comparator; it is not a reproduction of FAREAST or ST2. Growing-MOSS uses an explicitly specified anytime index with the current available-arm count. It does not inherit offline MOSS optimality. Batch100-UCB implements the reviewer's suggested short-period admission and confidence retirement comparison and reports on all physically arrived arms, including those awaiting admission. Its three recorded regret components separate admission delay, historical retirement loss, and within-active loss.

The initial eight-method configuration completed 5,120 preliminary runs. Before examining the comparative outcomes, the parent's request to add Growing-MOSS led to version 1.1. At the same time, the noninitial arrival times were shifted 36 pulls from the 100-pull grid: the initial schedule had inadvertently admitted every batch without waiting. This avoids evaluating Batch100 only at its most favorable alignment. Three regret decomposition fields were also added. No mean, precision, seed, service period, or horizon was selected using comparative outcomes. All methods were rerun together under version 1.1. The main claims use only its 5,760 runs. `pilot/` holds a two-replication implementation smoke run and is not part of the paper's numerical evidence.

Files:

- `results/runs.csv`: one row for every scenario, seed and method, including final per-arm counts, full-path label errors, unresolved areas, forced pulls, and regret decomposition.
- `results/paths.npz`: per-replication cumulative regret, unresolved count, cumulative area, and total unresolved count at a common time grid including every arrival.
- `results/summary.csv`: means, Monte Carlo standard errors, observed error counts, one-sided exact 95% binomial upper bounds, and completion frequencies.
- `results/paired_differences.csv`: checkpoint allocation minus comparator differences and paired Monte Carlo standard errors.
- `results/source_parity.json`: 20,000-round source-class comparison, checking actions, service flags, every available-arm count, and C/D/V reports at each round. It calls the original `CheckpointUCBAA` public interface.
- `results/verification.json`: row completeness, exact regret decomposition check, quotas and explicit inferential limits.
- All manuscript tables, including supplementary tables, are embedded directly in the single `../manuscript.tex`. The previous generated TeX snapshots were archived under `../audit/source_layout_2026-10-16/components/experiments/results/`. The plotting script can regenerate `results/table_main.tex` and `results/table_allocation.tex`; those files do not enter manuscript compilation automatically. Use `--figures-only` to redraw without generating table snapshots.
- `../figures/fig_cost_area.pdf`, `../figures/fig_paths.pdf`: vector figures with 1.96 Monte Carlo standard error bars or bands, plus 300 dpi PNG versions.

The production results include important negative evidence. The finer checkpoints have poor completion at this budget. The coarser FIFO construction is dominated by the strong confidence-driven adaptation in both regret and unresolved area in the stable-benchmark and burst environments. Growing-MOSS has the smallest regret but much larger unresolved areas. The evidence supports a distinction between regret and maintenance costs, and does not support a universal numerical advantage for CP-UCB-AA.

All 5,760 runs had no incorrect report. For a single fixed method and environment, zero failures in 160 replications yields an exact one-sided 95% upper confidence bound of 0.01855. This is not evidence of uniform reliability over untested environments or infinite time. The theoretical guarantee remains a mathematical statement.

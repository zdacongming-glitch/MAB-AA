# Numerical integration record

The manuscript revision used frozen simulation records only. No policy was retuned, no new comparative simulation was run, and no original research file was written. Numerical results were reanalyzed without conditioning on successful reporting. Article prose and tables are delivered as JSON strings for insertion in the two complete authoring files.

| Task | Status | Evidence |
|---|---|---|
| R2-20 frozen algorithm and names | DONE | `release-manifest.json`, `method-mapping.csv`, `production-branch-map.csv`, exact source copies and three complete original ZIPs |
| R2-21 data generations | DONE | `dataset-inventory.json`; 5,760 / 13,440 / 12,672 / 27,648 + 1,152 records separately checked |
| R2-22 protocol and baselines | DONE | JSON main section and S15; parameters read from the two exact freezes |
| R2-23 pure reward results | DONE | Recomputed 12 × 6 means/SE; 60 paired comparisons; 59 / 52 / 54 counts and 11/12 scenario result |
| R2-24 preference and matched ALL | DONE | Fixed certification-budget preference points; uncapped star separate; full paired comparisons and diagnostics |
| R2-25 failures and tails | DONE | `all-failure-records.csv`; all 300 method–scenario rows include q95/max and all paths; main text retains the three adverse tail cases and 1/1,152 default-mode label error |
| R2-26 new table and figure inputs | DONE | `generated/reward-paired.{pdf,png}`, `generated/preference-tradeoff.{pdf,png}`, visually inspected; old study migration belongs to the main integration task |
| R2-29 numerical release and resources | DONE | `experiments/fccp_frozen/README_release.md`, complete frozen computational dependency closure, original archives, historical/Linux and local/Windows environments distinguished |
| R2-30 numerical and short interface checks | DONE | Plan Appendix F script passed; source manifest 175 entries matched; 600 API-compatible actions, 320 mode actions, ten Numba compatibility cases and six API validation rejections passed |

The article-level build, cross-references, mathematical claim attribution and final page rendering are checked by the main integration task, not asserted complete by this numerical record.

## Executed commands

From the repository root:

```powershell
python ucbaa_jasa_resubmission_2026-10-15/revision2/analysis/reanalyze_fccp.py
python ucbaa_jasa_resubmission_2026-10-15/revision2/analysis/check_revision2_data.py --f-root F-CCP_2026-10-17 --out ucbaa_jasa_resubmission_2026-10-15/revision2/analysis/fccp-checks.json
python ucbaa_jasa_resubmission_2026-10-15/revision2/analysis/check_fccp_interface.py
python ucbaa_jasa_resubmission_2026-10-15/revision2/analysis/reanalyze_fccp.py --release-only
```

The first reanalysis attempt encountered the local pandas version's unsupported `include_groups` argument. Only the new reanalysis script was made compatible; no frozen policy or data changed. The first Appendix F extraction attempt encountered PowerShell's Unicode pipe encoding; extracting by an ASCII glob resolved the path without altering the task's verifier. These execution failures did not produce new simulation records. Final successful arithmetic and interface outputs are stored in the JSON files listed above.

## Verified results and limits

The exact equal-scenario F-R mean regret is 60.73109114583333. Relative to Thompson's equal-scenario mean, the reduction is 19.484622855875145%, rounded to 19.5% in the manuscript. It is a ratio of two scenario-mean averages, not the average of within-scenario percentage changes. The two-close-arms exception and the empirical burst/ceiling/larger-pool tail disadvantages remain visible.

The stored dataset has 28,800 records and 25 method IDs. Replacing the original adaptive ALL configuration by the cost-matched correction gives 27,648 primary records and 24 IDs. No old ALL record was discarded from the archive. The original summary's mean discrepancies are below $2\times10^{-11}$; the Appendix F hash and accounting checks all pass. The label/coverage/empty counts for the default balanced mode are 1/7/1 of 1,152, with common streams making failures across methods dependent.

The phase residual reaches 1.000000002899469 and 1,035 stored records have an integer-boundary delay. Exact arithmetic statements and floating-point implementation diagnostics remain separate. No all-machine-time or independent probability certificate is inferred.

No material proof–implementation conflict was found in the interfaces inspected here. Two already disclosed differences were retained explicitly: inactive service-cap encodings differ between batch and interactive pure modes, and the two implementations use different RNG backends. The old adaptive ALL zero-price error is preserved as a superseded diagnostic and corrected only in the separately frozen comparator. Complete mathematical verification remains outside this numerical check's scope.

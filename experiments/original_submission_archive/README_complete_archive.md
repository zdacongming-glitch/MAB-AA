# Original submission computational archive

The final C/E experiment is historical evidence and is separate from the revised F-CCP study. The final five-method source is `source/ce_five_algo_runner.py`; `source/manual_ce_final.py` records a different earlier four-method exploration. The original final configurations record 100 repetitions, seed 20260309 and 60,000 rounds per scenario.

The archive now includes the formerly omitted raw checkpoint data, losslessly compressed as `scenario_C/raw_checkpoint.csv.gz` and `scenario_E/raw_checkpoint.csv.gz`. Both decompressed byte lengths and SHA-256 digests were checked against the original CSVs. Complete aggregate checkpoint tables, saved original plots, final summary and the missing historical source/README were also preserved. No original source or data was changed.

The older `metadata.json` is retained as a historical record of the archive before this addition. Current provenance and exact compression mappings are in `../../reproducibility/numerical-import-manifest.json`. Commands, dependencies and limits are in `../../reproducibility/NUMERICAL_SOURCES.md`.

`summarize_archive.py` reads the locally preserved terminal CSVs by default. Its `--collect` option points to the original author's local machine and is an archival collection function; it is unnecessary on another computer. The default historical summarizer also emits a TeX table snapshot. That snapshot is not an input to the single editable manuscript.

Run full simulations in a new copied directory so the frozen records remain available for comparison. Cross-platform byte-for-byte equality of newly simulated output is not promised. This archive does not repair the historical policy's theoretical or implementation discrepancies, which remain described in `metadata.json`.

#!/usr/bin/env python3
"""Read-only verification of the frozen F-CCP results. No policy is run.
Usage: python check_revision2_data.py --f-root /path/F-CCP_2026-10-17 \
       --out /path/revision2/analysis/fccp-checks.json
Requires numpy, pandas, scipy. Input files are never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

HASHES = {
    'results/holdout-all.csv': 'f7e77d4df069477ca5b4708a73e6f2898d8df4251514510eb93c017f78a63d90',
    'results/matched-all-all.csv': '35d20a058abbe34ea8bf4248de97ba95f6cbd7b25ead7e798ab37e50b9f2e4dd',
    'results/holdout-summary.csv': 'b996f557f56db86013d7d3770fb37a11dc1a4f650188c589e0da48d56c2bf97c',
    'protocols/holdout-freeze.json': '7d4b8536869250ce3b19ad5f15ddf388c16ed17ca058a94171b694ad29229668',
    'protocols/matched-all-freeze.json': '69bac0a73fb6f3af7525e61036673ff26dbccc25ef7345148c83ada1892c9689',
}
BASES = ['UCB1', 'Growing-MOSS', 'MC-MOSS', 'Thompson', 'KL-UCB']

def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--f-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.f_root.resolve(), args.out.resolve()
    require(not out.is_relative_to(root), 'Output must be outside the frozen source tree.')
    require(not out.exists(), 'Output already exists; choose a new audit filename.')
    actual_hashes = {}
    for rel, expected in HASHES.items():
        path = root / rel
        require(path.is_file(), f'Missing input: {rel}')
        actual_hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual_hashes[rel] == expected, f'Input version mismatch: {rel}')
    freeze = json.loads((root/'protocols/holdout-freeze.json').read_text(encoding='utf-8'))
    correction = json.loads((root/'protocols/matched-all-freeze.json').read_text(encoding='utf-8'))
    d0 = pd.read_csv(root/'results/holdout-all.csv')
    dc = pd.read_csv(root/'results/matched-all-all.csv')
    require(len(d0) == 27648 and len(dc) == 1152, 'Unexpected run count.')
    require(set(dc.method) == {'ALL-auto-costmatched'}, 'Wrong corrected comparator.')
    d = pd.concat([d0, dc], ignore_index=True)
    keys = ['scenario', 'rep', 'method']
    require(not d.duplicated(keys).any(), 'Duplicate trajectory keys.')
    require(d.scenario.nunique() == 12 and d.method.nunique() == 25, 'Unexpected suite.')
    require((d.groupby(['scenario','method']).size() == 96).all(), 'Missing repeats.')
    require((d.total_pulls == d['T']).all(), 'Physical pull count differs from endpoint.')
    for scenario in freeze['scenarios']:
        g = d[d.scenario == scenario['name']]
        require((g['T'] == scenario['T']).all(), 'Mixed endpoint in a scenario.')
        require((g.K == len(scenario['means'])).all(), 'Wrong final count.')
    primary = d[d.method != 'ALL-auto-0.6']
    require(len(primary) == 27648 and primary.method.nunique() == 24,
            'Corrected primary roster must replace, not duplicate, the old ALL.')
    stored = pd.read_csv(root/'results/holdout-summary.csv').set_index(['scenario','method'])
    recomputed = d.groupby(['scenario','method'])[['regret','area']].mean()
    error = {}
    for metric in ['regret','area']:
        error[metric] = float(np.max(np.abs(recomputed[metric] - stored[metric+'_mean'])))
        require(error[metric] < 1e-7, f'Summary mean mismatch: {metric}')
    require(np.max(np.abs(d.tax-d.reward_tax-d.service_tax)) < 1e-8, 'Ledger mismatch.')
    require((d.service_attempts == d.service_pulls+d.service_denials).all(), 'Attempt mismatch.')
    residual = d.service_mass-d.service_attempts
    require(residual.min() >= -1e-7 and residual.max() <= 1+1e-7, 'Phase mismatch.')
    policies = {p['name']:p for p in freeze['policies']+correction['policies']}
    for name, p in policies.items():
        g = d[d.method == name]
        for key, col in [('beta_r','reward_tax'), ('beta_s','service_tax')]:
            if p[key] is not None:
                require((g[col] <= p[key]*g.spectrum_max+1e-8).all(), f'Budget: {name}/{col}')
        if p['priority'] == 0:
            require((g.service_pulls == 0).all(), f'Pure-reward method has service: {name}')
    for scenario in freeze['scenarios']:
        k, eta, delta = len(scenario['means']), scenario['eta'], scenario['delta']
        q = sum(np.ceil(32/eta**2*np.log(4*i*(i+1)/delta)) for i in range(1,k+1))
        require((d[d.scenario == scenario['name']].service_pulls <= q).all(), 'Quota charge mismatch.')
    # Endpoint equality is checked here, not asserted to prove pathwise equivalence.
    compat_cols = ['regret','area','service_pulls','label_error','coverage_error',
                   'empty_intersection','tax','final_unresolved','final_all_unresolved']
    def indexed(name: str) -> pd.DataFrame:
        return d[d.method == name].set_index(['scenario','rep'])[compat_cols].sort_index()
    require(indexed('F-R-TS-exact').equals(indexed('Thompson')), 'Compatibility record mismatch.')
    pairs = []
    for scenario, g in d.groupby('scenario'):
        p = g.pivot(index='rep',columns='method',values='regret')
        f = p['F-R'].to_numpy()
        for b in BASES:
            base = p[b].to_numpy(); x = f-base; n = len(x)
            se = x.std(ddof=1)/np.sqrt(n)
            ni = f-1.05*base-2
            pairs.append({'scenario':scenario, 'baseline':b, 'delta':float(x.mean()),
                'upper60':float(x.mean()+student_t.ppf(1-.05/60,n-1)*se),
                'relaxed_upper60':float(ni.mean()+student_t.ppf(1-.05/60,n-1)*ni.std(ddof=1)/np.sqrt(n))})
    wins = sum(p['delta'] < 0 for p in pairs)
    strict = sum(p['upper60'] < 0 for p in pairs)
    relaxed = sum(p['relaxed_upper60'] < 0 for p in pairs)
    require((len(pairs),wins,strict,relaxed) == (60,59,52,54), 'Paired counts differ.')
    failures = d.groupby('method')[['label_error','coverage_error','empty_intersection']].sum().astype(int)
    require(failures.loc['F-auto-0.6'].tolist() == [1,7,1], 'F-auto failure records differ.')
    require(failures.loc['F-R'].tolist() == [0,6,1], 'F-R failure records differ.')
    require(failures.loc['F-area'].tolist() == [0,8,0], 'F-area failure records differ.')
    suite = recomputed.groupby('method').mean()
    require(abs(suite.loc['F-R','regret']-60.73109114583333) < 1e-6, 'F-R sentinel differs.')
    report = {'kind':'read-only reanalysis; no new simulation or probability certificate',
        'input_sha256':actual_hashes, 'main_rows':len(d0), 'correction_rows':len(dc),
        'all_retained_rows':len(d), 'corrected_primary_rows':len(primary),
        'scenarios':12, 'replications_per_method_scenario':96,
        'summary_max_abs_error':error, 'paired_comparisons':len(pairs),
        'mean_wins':wins, 'strict_family60_upper_below_zero':strict,
        'relaxed_family60_upper_below_zero':relaxed,
        'relaxed_margin':'5% of comparator plus 2; not the literal zero-margin target',
        'phase_residual_range':[float(residual.min()),float(residual.max())],
        'phase_integer_boundary_cases':int((d.service_attempts != np.floor(d.service_mass+1e-8)).sum()),
        'compatibility_endpoint_pairs':1152,
        'failure_counts':failures.to_dict(orient='index'),
        'suite_means':suite.to_dict(orient='index')}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['main_rows','correction_rows','all_retained_rows',
        'corrected_primary_rows','summary_max_abs_error','mean_wins',
        'strict_family60_upper_below_zero','relaxed_family60_upper_below_zero']},indent=2))

if __name__ == '__main__':
    main()

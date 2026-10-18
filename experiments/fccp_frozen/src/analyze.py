"""Summarize ALL completed runs without selection on favorable paths.
Monte Carlo intervals describe fixed simulated environments, not model-wide safety.
"""
from pathlib import Path
import json, re, hashlib
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
config=json.loads((ROOT/'protocols/holdout-freeze.json').read_text())
files=sorted(f for f in R.glob('holdout-*.csv') if re.fullmatch(r'holdout-\d+',f.stem))
d=pd.concat([pd.read_csv(f) for f in files],ignore_index=True)
assert len(files)==len(config['scenarios'])==12
assert len(d)==12*24*96
assert (d.groupby(['scenario','method']).size()==96).all()
assert (d.total_pulls==d['T']).all()
d.to_csv(R/'holdout-all.csv',index=False)
matched=list(f for f in R.glob('matched-all-*.csv') if re.fullmatch(r'matched-all-\d+',f.stem))
if len(matched)==12:
 m=pd.concat([pd.read_csv(f) for f in matched],ignore_index=True)
 if len(m)==12*96:
  m.to_csv(R/'matched-all-all.csv',index=False);d=pd.concat([d,m],ignore_index=True)
metrics=['regret','area','service_pulls','service_regret','service_denials','reward_projections','service_mass','active_service_rounds','final_unresolved','final_all_unresolved']
rows=[]
for (sc,method),g in d.groupby(['scenario','method']):
 row=dict(scenario=sc,method=method,n=len(g),T=int(g['T'].iloc[0]),K=int(g.K.iloc[0]))
 for key in metrics:
  v=g[key].to_numpy();row[key+'_mean']=float(v.mean());row[key+'_se']=float(v.std(ddof=1)/len(v)**.5);row[key+'_q95']=float(np.quantile(v,.95));row[key+'_max']=float(v.max())
 for key in ['label_error','coverage_error','empty_intersection']:row[key+'_count']=int(g[key].sum())
 active=g.active_service_rounds.sum();row['average_rate_when_active']=float(g.service_mass.sum()/active) if active else 0.
 rows.append(row)
s=pd.DataFrame(rows);s.to_csv(R/'holdout-summary.csv',index=False)
s.groupby('method')[[x+'_mean' for x in ['regret','area','service_pulls','service_denials','reward_projections']]].mean().sort_values('regret_mean').to_csv(R/'suite-means.csv')
comparators=['UCB1','Growing-MOSS','MC-MOSS','Thompson','KL-UCB']
prs=[]
for sc,g in d.groupby('scenario'):
 piv=g.pivot(index='rep',columns='method',values='regret');f=piv['F-R'].to_numpy()
 for b in comparators:
  base=piv[b].to_numpy();x=f-base;n=len(x);se=x.std(ddof=1)/np.sqrt(n)
  ni=f-1.05*base-2.;seni=ni.std(ddof=1)/np.sqrt(n)
  prs.append(dict(scenario=sc,baseline=b,n=n,F_mean=f.mean(),baseline_mean=base.mean(),delta_mean=x.mean(),delta_se=se,
    delta_l95=x.mean()-student_t.ppf(.975,n-1)*se,delta_u95=x.mean()+student_t.ppf(.975,n-1)*se,
    delta_upper95_family60=x.mean()+student_t.ppf(1-.05/60,n-1)*se,
    relaxed_ni_mean=ni.mean(),relaxed_ni_upper95_family60=ni.mean()+student_t.ppf(1-.05/60,n-1)*seni,
    mean_better=bool(x.mean()<=0),path_win_fraction=float(np.mean(x<0))))
pd.DataFrame(prs).to_csv(R/'pure-regret-paired.csv',index=False)
# Full diagnostics for prespecified comparisons, with no omission of adverse cases.
pairs=[('F-auto-0.6','CCP-original'),('F-auto-0.6','ALL-auto-costmatched'),('F-area','ALL-area'),('F-area','F-auto-0.6'),('F-auto-0.6','F-R'),('F-R','Cold-TS-unprotected')]
res=[]
for f,b in pairs:
 for sc,g in d.groupby('scenario'):
  for metric in ['regret','area','service_pulls']:
   pp=g.pivot(index='rep',columns='method',values=metric)
   if f not in pp or b not in pp:continue
   x=(pp[f]-pp[b]).to_numpy();se=x.std(ddof=1)/np.sqrt(len(x));t=student_t.ppf(.975,len(x)-1)
   res.append(dict(candidate=f,baseline=b,scenario=sc,metric=metric,delta_mean=x.mean(),se=se,lower95=x.mean()-t*se,upper95=x.mean()+t*se))
pd.DataFrame(res).to_csv(R/'joint-paired.csv',index=False)
# Equality check: no matching merely of rounded averages.
pp=d[d.method.isin(['F-R-TS-exact','Thompson'])].set_index(['scenario','rep','method'])
keys=[x for x in ['regret','area','service_pulls','label_error','coverage_error','empty_intersection','tax','final_unresolved','final_all_unresolved']]
a=pp.xs('F-R-TS-exact',level='method')[keys].sort_index();b=pp.xs('Thompson',level='method')[keys].sort_index()
assert a.equals(b)
pols={p['name']:p for p in config['policies']}
assert np.max(np.abs(d.tax-d.reward_tax-d.service_tax))<1e-8
assert np.max(np.abs(d.service_attempts-(d.service_pulls+d.service_denials)))==0
phase_residual=d.service_mass-d.service_attempts
assert phase_residual.min()>=-1e-7 and phase_residual.max()<=1+1e-7
phase_integer_delays=int((d.service_attempts != np.floor(d.service_mass+1e-8)).sum())
for method,p in pols.items():
 g=d[d.method==method]
 if p['beta_r'] is not None:assert (g.reward_tax<=p['beta_r']*g.spectrum_max+1e-8).all()
 if p['beta_s'] is not None:assert (g.service_tax<=p['beta_s']*g.spectrum_max+1e-8).all()
for sc,g in d.groupby('scenario'):
 pars=next(x for x in config['scenarios'] if x['name']==sc);K=len(pars['means']);eta=pars['eta'];delta=pars['delta']
 Q=sum(np.ceil(32/eta**2*np.log(4*i*(i+1)/delta)) for i in range(1,K+1))
 assert (g.service_pulls<=Q).all()
checks=dict(valid_main_runs=27648,completed_correction_runs=len(d)-27648,all_pulls_match_endpoint=True,
  fixed_TS_compatibility_identical=1152,paired_comparisons=60,
  strict_mean_wins=sum(x['mean_better'] for x in prs),strict_upper_fwer_below_zero=sum(x['delta_upper95_family60']<0 for x in prs),
  relaxed_NI_upper_fwer_below_zero=sum(x['relaxed_ni_upper95_family60']<0 for x in prs),
  alpha_family=.05,relaxed_margin='5% of comparator mean plus 2 regret units; not literal non-inferiority',
  all_failure_paths_retained=True, phase_integer_boundary_delays=phase_integer_delays, phase_residual_range=[float(phase_residual.min()),float(phase_residual.max())])
(R/'analysis-checks.json').write_text(json.dumps(checks,indent=2,default=int));print(json.dumps(checks,indent=2,default=int))
print(pd.DataFrame(prs)[pd.DataFrame(prs).baseline=='Thompson'][['scenario','delta_mean','delta_l95','delta_u95','delta_upper95_family60','relaxed_ni_upper95_family60']].round(3).to_string(index=False))

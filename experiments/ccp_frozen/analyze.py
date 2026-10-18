from pathlib import Path
import numpy as np, pandas as pd, json, hashlib
from scipy.stats import t as student_t
from protocol import ROOT, TEST
parts=[]
for s in range(10):
 for offset in [0,16,32,48]:
  f=ROOT/f'test-s{s}-r{offset}.csv'; d=pd.read_csv(f)
  assert len(d)==336, (f,len(d)); parts.append(d)
df=pd.concat(parts,ignore_index=True)
assert len(df)==13440 and not df.duplicated(['scenario','rep','method']).any()
assert (df.groupby(['scenario','method']).size()==64).all()
freeze=json.loads((ROOT/'test-freeze-record.json').read_text())
for path,expected in freeze['hashes'].items(): assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
df.to_csv(ROOT/'test-results.csv',index=False)
metrics=['regret','area','final_unresolved','service_pulls','service_regret','optimistic_tax','budget_denials']
records=[]
for (sc,met),g in df.groupby(['scenario','method'],sort=False):
 row=dict(scenario=sc,method=met,n=len(g))
 for m in metrics:
  a=g[m].values; row[m+'_mean']=a.mean();row[m+'_se']=a.std(ddof=1)/np.sqrt(len(a));row[m+'_q95']=np.quantile(a,.95)
 row['label_failures']=int(g.label_error.sum());row['interval_failures']=int(g.interval_miss.sum());row['empty_intersections']=int(g.empty_intersection.sum())
 records.append(row)
sumdf=pd.DataFrame(records);sumdf.to_csv(ROOT/'test-summary.csv',index=False)
paired=[]
for sc in [s['name'] for s in TEST]:
 a=df[(df.scenario==sc)&(df.method=='CCP-beta1')].set_index('rep')
 b=df[(df.scenario==sc)&(df.method=='ALLplus-beta1')].set_index('rep')
 for m in ['regret','area']:
  delta=a[m]-b[m];se=delta.std(ddof=1)/8
  paired.append(dict(scenario=sc,metric=m,difference=delta.mean(),se=se,lo95=delta.mean()-student_t.ppf(.975,63)*se,hi95=delta.mean()+student_t.ppf(.975,63)*se,relative_change=delta.mean()/b[m].mean()))
pd.DataFrame(paired).to_csv(ROOT/'paired-primary.csv',index=False)
print(sumdf[sumdf.method.isin(['CCP-beta1','ALLplus-beta1','MC-report','ALLplus-unlimited','CCP-unlimited'])][['scenario','method','regret_mean','area_mean','area_q95','label_failures']].to_string(index=False,float_format=lambda x:f'{x:.1f}'))
print('\nFailures:',df[['label_error','interval_miss','empty_intersection']].sum().to_dict())
print('\nPaired:\n',pd.DataFrame(paired).to_string(index=False,float_format=lambda x:f'{x:.3f}'))
# Secondary, predeclared scalarizations, not the risk protocol.
scalar=[]
for w in freeze['secondary_scores_weights']:
 for sc in [s['name'] for s in TEST]:
  gg=sumdf[sumdf.scenario==sc]
  vals=gg.regret_mean+w*gg.area_mean
  i=vals.idxmin()
  ca=gg[gg.method=='CCP-beta1'].iloc[0]; ba=gg[gg.method=='ALLplus-beta1'].iloc[0]
  ccp=gg[gg.method.isin(freeze['family'])]
  allf=gg[gg.method.isin(['ALLplus-beta0.25','ALLplus-beta0.5','ALLplus-beta1','ALLplus-beta2'])]
  scalar.append(dict(weight=w,scenario=sc,best_test_point=sumdf.loc[i,'method'],best_score=vals.min(),ccp_default=ca.regret_mean+w*ca.area_mean,all_default=ba.regret_mean+w*ba.area_mean,ccp_family=(ccp.regret_mean+w*ccp.area_mean).min(),all_family=(allf.regret_mean+w*allf.area_mean).min()))
pd.DataFrame(scalar).to_csv(ROOT/'secondary-scores.csv',index=False)

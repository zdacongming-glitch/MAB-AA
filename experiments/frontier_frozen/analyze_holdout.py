from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy.stats import t
P=Path(__file__).parent
fr=json.loads((P/'holdout-freeze.json').read_text())
assert all(hashlib.sha256((P/f).read_bytes()).hexdigest()==h for f,h in fr['hashes'].items())
df=pd.concat([pd.read_csv(P/f'holdout-{i}.csv') for i in range(len(fr['scenarios']))],ignore_index=True)
assert len(df)==len(fr['scenarios'])*len(fr['policies'])*fr['reps']
assert not df.duplicated(['scenario','rep','method']).any()
assert df.groupby(['scenario','method']).size().eq(fr['reps']).all()
df.to_csv(P/'holdout-all.csv',index=False)
rows=[]
for (s,m),g in df.groupby(['scenario','method']):
 row=dict(scenario=s,method=m,n=len(g))
 for col in ['regret','area','final_unresolved','service_pulls','service_regret','tax','denials','runtime']:
  row[col+'_mean']=g[col].mean();row[col+'_se']=g[col].std(ddof=1)/np.sqrt(len(g));row[col+'_q95']=g[col].quantile(.95)
 for col in ['label_error','coverage_error','empty_intersection']:row[col+'_runs']=int((g[col]>0).sum())
 rows.append(row)
su=pd.DataFrame(rows);su.to_csv(P/'holdout-summary.csv',index=False)
rows=[]
for other in ['CCP-b1.0','ALLplus-b1.0']:
 for scen,g in df.groupby('scenario'):
  a=g[g.method=='Shared-b1.0'].set_index('rep');b=g[g.method==other].set_index('rep')
  row=dict(scenario=scen,comparator=other)
  for col in ['regret','area']:
   d=a[col]-b[col];se=d.std(ddof=1)/np.sqrt(len(d));rad=t.ppf(.975,len(d)-1)*se
   row[col+'_diff']=d.mean();row[col+'_lo']=d.mean()-rad;row[col+'_hi']=d.mean()+rad;row[col+'_rel']=d.mean()/b[col].mean()
  rows.append(row)
pd.DataFrame(rows).to_csv(P/'holdout-paired.csv',index=False)
print(su.groupby('method')[['regret_mean','area_mean']].mean().sort_values('area_mean').to_string())
print('\npaired vs CCP\n',pd.DataFrame(rows).query("comparator=='CCP-b1.0'").to_string(index=False))
print('\nall errors\n',su.groupby('method')[['label_error_runs','coverage_error_runs','empty_intersection_runs']].sum().to_string())

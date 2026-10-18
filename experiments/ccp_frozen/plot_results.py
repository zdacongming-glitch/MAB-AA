"""Reproduce the two displayed descriptive trade-off plots (not optimal frontiers)."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
s=pd.read_csv(ROOT/'test-summary.csv')
for scenario,title in [('burst','Burst arrivals: independent test'),('near_upper_boundary','Near the reward ceiling: independent test')]:
 fig,ax=plt.subplots(figsize=(7.2,4.8))
 for prefix,label,marker in [('CCP-beta','Certificate-Cost Planning','o'),('ALLplus-beta','ALL-epsilon, same reporting and budget','s')]:
  rows=[s[(s.scenario==scenario)&(s.method==prefix+b)].iloc[0] for b in ['0.25','0.5','1','2']]
  ax.errorbar([r.regret_mean for r in rows],[r.area_mean/1000 for r in rows],
              xerr=[1.96*r.regret_se for r in rows],yerr=[1.96*r.area_se/1000 for r in rows],
              marker=marker,capsize=3,label=label)
 ax.set_xlabel('Mean cumulative pseudo-regret');ax.set_ylabel('Mean unresolved arm-time (thousands)')
 ax.set_title(title);ax.legend();ax.grid(alpha=.25)
 fig.text(.5,.01,'64 paired runs; error bars = 1.96 Monte Carlo SE. Lines connect fixed budget settings.',ha='center',fontsize=8)
 fig.tight_layout(rect=(0,.035,1,1));fig.savefig(ROOT/f'tradeoff-{scenario}.png',dpi=180);plt.close(fig)

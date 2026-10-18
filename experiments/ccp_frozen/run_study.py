from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from engine import simulate
from protocol import ROOT,DEV,TEST,streams,policy


def dev_policies():
    ps=[policy('CP-original-004',reward=0,scheduler=0,conf=2,exact=False,band=False,cap=True,rho=.04),
        policy('CP-original-012',reward=0,scheduler=0,conf=2,exact=False,band=False,cap=True,rho=.12),
        policy('ALL-prefix-UCB',reward=0,scheduler=1,conf=0,exact=False,band=False,cap=False)]
    for rw,nm in [(0,'UCB'),(1,'GMOSS'),(2,'MC'),(3,'TS'),(4,'KLUCB')]:
        ps.append(policy(f'{nm}-report',reward=rw,scheduler=-1))
        ps.append(policy(f'ALLplus-{nm}',reward=rw,scheduler=1))
    for sh,nm in [(0,'FIFOplus'),(2,'leastcount'),(3,'ST2plus'),(4,'easy-pair'),(6,'progress')]:
        ps.append(policy(nm,reward=2,scheduler=sh))
    for sh,nm in [(5,'cost-pair'),(7,'cost-progress'),(8,'label-info')]:
        for pr in [.02,.1,.5]: ps.append(policy(f'{nm}-{pr}',scheduler=sh,price=pr))
    for rw,nm in [(0,'UCB'),(3,'TS'),(4,'KLUCB'),(5,'safeTS'),(6,'safeGreedy')]:
        ps.append(policy(f'cost-pair-{nm}',reward=rw,scheduler=5,price=.1))
    return ps

def run(stage,nrep,output,policies,scenario_select=None,offset=0):
    scens=DEV if stage=='dev' else TEST
    rr=110000 if stage=='dev' else 910000
    pp=210000 if stage=='dev' else 1010000
    rows=[];tt=time.time();saved_paths={};saved_counts={}
    (ROOT/(output+'-policies.json')).write_text(json.dumps(policies,indent=2))
    for si,sc in enumerate(scens):
        if scenario_select is not None and si!=scenario_select: continue
        mu=np.array(sc['means'],float); tau=np.array(sc['arrivals'],np.int64)
        for rep in range(offset,offset+nrep):
            data=streams(sc,rr+1000*si+rep)
            for pi,p in enumerate(policies):
                start=time.time()
                out,snap,cnts=simulate(data,mu,tau,sc['epsilon'],sc['eta'],sc['delta'],sc['T'],
                    p['reward'],p['scheduler'],p['period'],p['price'],p['xi'],p['conf'],p['exact'],p['band'],p['cap'],
                    p['rho'] if p['rho'] else sc['eta']/4, pp+1000*si+rep,200,p.get('budget_scale',1e100),p.get('budget_mode',0))
                row=dict(stage=stage,scenario=sc['name'],rep=rep,method=p['name'],regret=out[0],area=out[1],final_unresolved=out[2],
                    service_pulls=out[3],service_regret=out[4],label_error=out[5],interval_miss=out[6],empty_intersection=out[7],optimistic_tax=out[8],budget_denials=out[9],runtime_sec=time.time()-start)
                rows.append(row)
                saved_counts[f"{sc['name']}|{p['name']}|{rep}"]=cnts
                if p['name'] in ['CCP-beta1','ALLplus-beta1','CP-original-012','MC-report']:
                    saved_paths[f"{sc['name']}|{p['name']}|{rep}"]=snap
            if rep%4==3:
                pd.DataFrame(rows).to_csv(ROOT/(output+'.csv'),index=False)
                print(stage,sc['name'],rep+1,'elapsed',round(time.time()-tt,1),flush=True)
        pd.DataFrame(rows).to_csv(ROOT/(output+'.csv'),index=False)
    df=pd.DataFrame(rows)
    summary=df.groupby(['scenario','method']).agg(regret=('regret','mean'),area=('area','mean'),fail=('label_error','sum')).reset_index()
    summary.to_csv(ROOT/(output+'-summary.csv'),index=False)
    if stage=='test':
        np.savez_compressed(ROOT/(output+'-counts.npz'),**saved_counts)
        np.savez_compressed(ROOT/(output+'-paths.npz'),**saved_paths)
    print('DONE',len(df),round(time.time()-tt,1),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['dev','test'],default='dev');ap.add_argument('--rep',type=int,default=12)
    ap.add_argument('--out',default='development-screen');ap.add_argument('--policies');ap.add_argument('--scenario',type=int);ap.add_argument('--offset',type=int,default=0); a=ap.parse_args()
    ps=dev_policies() if not a.policies else json.loads(Path(a.policies).read_text())
    if a.stage=='test' and not a.policies: raise ValueError('Test requires frozen configurations file')
    run(a.stage,a.rep,a.out,ps,a.scenario,a.offset)

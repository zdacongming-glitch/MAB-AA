"""Exact finite-model chance-constrained frontier with a FIXED valid reporter.

This is NOT the unrestricted unknown-horizon or continuous-model frontier.
The solver knows the finite candidate environments, horizon and arrival schedule.
All actions remain nonanticipating. Reports use an anytime-valid raw beta-mixture
confidence sequence, valid on the full bounded iid model. Returned LP optima are
numerically solved; residuals and independently propagated risks are recorded.
"""
from __future__ import annotations
import argparse,json,time,math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix,csr_matrix,vstack,hstack
from scipy.optimize import linprog
from engine_base import beta_mix_interval, labels_work


def build(T=14,epsilon=.80,eta=.05,delta=.1,arrival=1):
    mu=np.array([[.01,.99],[.99,.01],[.4,.6],[.6,.4]],float)
    for t in range(1,T+1):
        kk=1 if t<arrival else 2
        assert np.all(np.abs(np.max(mu[:,:kk],axis=1)[:,None]-mu[:,:kk]-epsilon)>eta)
    # Use half the target failure budget for the full-model report.
    intervals={}
    for i in range(2):
        alpha=(delta/2)/((i+1)*(i+2))
        for n in range(T+1):
            for s in range(n+1):intervals[(i,n,s)]=beta_mix_interval(n,float(s),alpha)
    root=(0,0,0,0,0,0)
    states=[root];layer=[0];edges=[];stateid={root:0};layers=[layer]
    Lcache={};rcache={}
    def lik(st):
        key=st[:4]
        if key not in Lcache:
            n0,s0,n1,s1=key
            logs=s0*np.log(mu[:,0])+(n0-s0)*np.log1p(-mu[:,0])+s1*np.log(mu[:,1])+(n1-s1)*np.log1p(-mu[:,1])
            # The common likelihood baseline is the uniform candidate prior.
            ll=np.exp(logs);Lcache[key]=ll
        return Lcache[key]
    def report(st,k):
        key=(*st[:4],k)
        if key not in rcache:
            l=np.array([intervals[(0,st[0],st[1])][0],intervals[(1,st[2],st[3])][0]])
            u=np.array([intervals[(0,st[0],st[1])][1],intervals[(1,st[2],st[3])][1]])
            labs=labels_work(l,u,k,epsilon,eta,True,False)[0]
            unresolved=int(np.sum(labs==0));mask=0
            for th in range(len(mu)):
                good=np.max(mu[th,:k])-mu[th,:k]<=epsilon
                if np.any((labs==1)&(~good)) or np.any((labs==-1)&good):mask|=1<<th
            rcache[key]=(unresolved,mask)
        return rcache[key]
    for t in range(T):
        newlayer=[];k=1 if t+1<arrival else 2
        for si in layer:
            st=states[si];prior=lik(st);den=prior.mean()
            for i in range(k):
                dest=[]
                for y in [0,1]:
                    ss=list(st);ss[2*i]+=1;ss[2*i+1]+=y
                    un,mask=report(ss,k);ss[4]+=un;ss[5]|=mask;ss=tuple(ss)
                    if ss not in stateid:
                        stateid[ss]=len(states);states.append(ss);newlayer.append(stateid[ss])
                    child=stateid[ss]
                    pred=float(np.mean(lik(ss))/den)
                    dest.append((child,pred))
                assert abs(sum(p for _,p in dest)-1)<1e-10
                edges.append((si,i,dest))
        layer=newlayer;layers.append(layer)
        print('layer',t+1,'states',len(layer),'total',len(states),flush=True)
    # Allocate one action variable per edge, and one flow variable per terminal.
    E=len(edges);term=layers[-1];zvar={s:E+j for j,s in enumerate(term)};nvar=E+len(term)
    rows=[];cols=[];vals=[]
    for j,(s,i,dest) in enumerate(edges):
        rows.append(s);cols.append(j);vals.append(1.)
        for child,p in dest:rows.append(child);cols.append(j);vals.append(-p)
    for s in term:rows.append(s);cols.append(zvar[s]);vals.append(1.)
    Aeq=coo_matrix((vals,(rows,cols)),shape=(len(states),nvar+1)).tocsr();beq=np.zeros(len(states));beq[0]=1.
    rr=np.zeros((len(mu),len(term)));rat=np.zeros_like(rr);masks=np.zeros(len(term),int);area=np.zeros(len(term),int)
    Bsum=np.zeros(len(mu))
    for t in range(1,T+1):Bsum+=np.max(mu[:,:1 if t<arrival else 2],axis=1)
    for j,s in enumerate(term):
        st=states[s];ll=lik(st);rat[:,j]=ll/ll.mean();rr[:,j]=rat[:,j]*(Bsum-mu[:,0]*st[0]-mu[:,1]*st[2]);masks[j]=st[5];area[j]=st[4]
    baseR=csr_matrix((rr.ravel(),(np.repeat(np.arange(len(mu)),len(term)),np.tile(np.arange(E,nvar),len(mu)))),shape=(len(mu),nvar+1))
    baseR=baseR+coo_matrix((-np.ones(len(mu)),(np.arange(len(mu)),np.full(len(mu),nvar))),shape=(len(mu),nvar+1)).tocsr()
    return dict(T=T,epsilon=epsilon,eta=eta,delta=delta,arrival=arrival,mu=mu,states=states,layers=layers,edges=edges,term=term,zvar=zvar,nvar=nvar,Aeq=Aeq,beq=beq,rr=rr,rat=rat,masks=masks,area=area,baseR=baseR)


def solve(model,a):
    m=len(model['mu']);E=len(model['edges']);V=model['nvar'];terms=len(model['term'])
    fail=np.empty((m,terms))
    # Explicit parentheses, avoid Python bitwise comparison precedence.
    for th in range(m):fail[th]=model['rat'][th]*((((model['masks']>>th)&1)!=0) | (model['area']>a))
    F=csr_matrix((fail.ravel(),(np.repeat(np.arange(m),terms),np.tile(np.arange(E,V),m))),shape=(m,V+1))
    Aub=vstack([model['baseR'],F],format='csr');bub=np.r_[np.zeros(m),np.full(m,model['delta'])]
    c=np.zeros(V+1);c[-1]=1.
    res=linprog(c,A_ub=Aub,b_ub=bub,A_eq=model['Aeq'],b_eq=model['beq'],bounds=(0,None),method='highs',options={'primal_feasibility_tolerance':1e-8,'dual_feasibility_tolerance':1e-8})
    row=dict(T=model['T'],arrival=model['arrival'],area_budget=a,success=res.success,status=res.status,nstates=len(model['states']),nvariables=V+1)
    if not res.success:return row,None
    row.update(regret_opt=res.fun,equality_residual=float(np.max(np.abs(model['Aeq']@res.x-model['beq']))),inequality_violation=float(max(0,np.max(Aub@res.x-bub))),duality_gap=float(abs(c@res.x-(bub@res.ineqlin.marginals+model['beq']@res.eqlin.marginals))))
    # Reconstruct the common behavioral policy and evaluate it from scratch.
    actionmap={}
    for e,(s,i,dest) in enumerate(model['edges']):actionmap.setdefault(s,[]).append((e,i,dest))
    probs=np.zeros((m,len(model['states'])));probs[:,0]=1.
    for layer in model['layers'][:-1]:
      for stid in layer:
        aa=actionmap[stid];mass=sum(res.x[e] for e,_,_ in aa)
        for e,i,dest in aa:
          pa=res.x[e]/mass if mass>1e-15 else 1/len(aa)
          for y,(ch,_) in enumerate(dest):
            py=model['mu'][:,i] if y else 1-model['mu'][:,i]
            probs[:,ch]+=probs[:,stid]*pa*py
    termp=probs[:,model['term']]
    n0=np.array([model['states'][s][0] for s in model['term']]);n1=np.array([model['states'][s][2] for s in model['term']]);Bsum=np.zeros(m)
    for t in range(1,model['T']+1):Bsum+=np.max(model['mu'][:,:1 if t<model['arrival'] else 2],axis=1)
    risk=np.sum(termp*(Bsum[:,None]-model['mu'][:,0,None]*n0-model['mu'][:,1,None]*n1),axis=1)
    failure=np.array([np.sum(termp[th]*((((model['masks']>>th)&1)!=0)|(model['area']>a))) for th in range(m)])
    row.update(verified_max_regret=float(max(risk)),verified_max_failure=float(max(failure)),verified_mass_error=float(np.max(np.abs(np.sum(termp,axis=1)-1))),model_regrets=json.dumps(risk.tolist()),model_failures=json.dumps(failure.tolist()))
    return row,res.x

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--T',type=int,default=12);ap.add_argument('--arrival',type=int,default=1);ap.add_argument('--out',default='exact-static');args=ap.parse_args()
    P=Path(__file__).parent;start=time.time();md=build(T=args.T,arrival=args.arrival)
    rows=[]; solved={}
    lo=-1;hi=2*args.T
    # Feasibility is monotone in the integer area budget.
    while hi-lo>1:
        a=(lo+hi)//2
        row,x=solve(md,a);solved[a]=row
        print('binary a',a,'success',row['success'],'time',round(time.time()-start,1),flush=True)
        if row['success']:hi=a
        elif row['status']==2:lo=a
        else:raise RuntimeError('Unresolved numerical solver status')
    for a in range(hi,2*args.T+1):
        if a not in solved:solved[a],_=solve(md,a)
        print('a',a,'success',solved[a]['success'],'r',solved[a].get('regret_opt'),'time',round(time.time()-start,1),flush=True)
    for a in range(2*args.T+1):
        row=solved.get(a,dict(T=args.T,area_budget=a,success=False,status=2,inferred_from_monotonicity=True))
        rows.append(row)
    pd.DataFrame(rows).to_csv(P/(args.out+'.csv'),index=False)
    (P/(args.out+'-meta.json')).write_text(json.dumps({k:v for k,v in md.items() if k in ['T','epsilon','eta','delta','arrival']},indent=2))

from engine_base import *
from witness_scheduler import witness_service
@njit(cache=True)
def simulate(rewards,means,arrivals,eps,eta,delta,T,
             reward,scheduler,period,price,xi,conf,exact,band,cap,rho,seed,stride=200,budget_scale=1e100,budget_mode=0):
    """conf: 0 full-prefix Hoeffding; 1 beta mixture + cap; 2 original frozen CP.
    scheduler=-1 means no designated services.
    Returned evaluations never enter reward_choice/service_choice.
    """
    np.random.seed(seed)
    K=len(means)
    n=np.zeros(K,np.int64); S=np.zeros(K); l=np.zeros(K); u=np.ones(K)
    q=np.empty(K,np.int64)
    for i in range(K): q[i]=math.ceil(2/rho**2*math.log(4*(i+1)*(i+2)/delta))
    k=0; base=0; segstart=1; busy=0; scount=0
    reg=0.0; area=0; service_reg=0.0; tax=0.0; denials=0; label_fail=0; cover_fail=0; stalled=0
    report_failure=False; running_spectrum=0.0
    snapshots=np.zeros((T//stride+1,5))
    for t in range(1,T+1):
        while k<K and arrivals[k]<=t: k+=1
        if k>1 and (base==0 or k-1>=2*base): base=k-1; segstart=t
        lab,work,gl,gu=labels_work(l,u,k,eps,eta,exact,band)
        todo=np.any(work)
        service=False; a=-1
        if scheduler>=0:
            if conf==2:
                if t%period==0:
                    for j in range(k):
                        if n[j]<q[j]: a=j; service=True; break
            elif todo and not report_failure:
                busy+=1
                if busy%period==0:
                    a=witness_service(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart)
                    service=a>=0
        if not service:
            a=reward_choice(n,S,k,t,reward,base,segstart,xi)
        tidx=clipped_moss_indices(n,S,k,t,base,segstart)
        actiontax=max(0.0,np.max(tidx)-tidx[a])
        if budget_mode==1:
            running_spectrum=max(running_spectrum,current_spectrum(arrivals,k,t))
            limit=budget_scale*running_spectrum
        else:
            limit=budget_scale*math.sqrt(k*t)
        if tax+actiontax>limit:
            a=np.argmax(tidx);actiontax=0.0
            if service: denials+=1
            service=False
        if service: scount+=1
        tax+=actiontax
        x=rewards[a,n[a]]
        n[a]+=1; S[a]+=x
        if conf==2:
            if n[a]==q[a]:
                l[a]=max(0.0,S[a]/n[a]-rho/2);u[a]=min(1.0,S[a]/n[a]+rho/2)
        elif not report_failure:
            if conf==0:
                r=math.sqrt(math.log((16 if cap else 8)*(a+1)**2*n[a]**2/delta)/(2*n[a]))
                lo=max(0.0,S[a]/n[a]-r); up=min(1.0,S[a]/n[a]+r)
            else:
                alpha=delta/(2*(a+1)*(a+2))
                lo,up=beta_mix_interval(n[a],S[a],alpha)
            l[a]=max(l[a],lo); u[a]=min(u[a],up)
            if cap and n[a]==q[a]:
                l[a]=max(l[a],S[a]/n[a]-rho/2,0.0)
                u[a]=min(u[a],S[a]/n[a]+rho/2,1.0)
            if l[a]>u[a]:
                report_failure=True
        if report_failure:
            lab=np.zeros(k,np.int64)
        else:
            lab,work,gl,gu=labels_work(l,u,k,eps,eta,exact,band)
        B=np.max(means[:k])
        cost=B-means[a]; reg+=cost
        if service: service_reg+=cost
        unresolved=0
        for i in range(k):
            gap=B-means[i]
            if (lab[i]==1 and gap>eps+1e-12) or (lab[i]==-1 and gap<=eps+1e-12): label_fail=1
            if lab[i]==0 and abs(gap-eps)>eta+1e-12: unresolved+=1
            if means[i]<l[i]-1e-10 or means[i]>u[i]+1e-10: cover_fail=1
        area+=unresolved
        if t%stride==0:
            snapshots[t//stride,:]=np.array([float(t),reg,float(area),float(unresolved),float(scount)])
    return np.array([reg,float(area),float(unresolved),float(scount),service_reg,float(label_fail),float(cover_fail),(1.0 if report_failure else 0.0),tax,float(denials)]),snapshots,n

"""Experimental policies for reliable arriving-arm set maintenance.

The selection function sees ONLY currently available observation statistics.
Reward streams, means, future arrivals and evaluation endpoints are simulator inputs,
not selection inputs. All new algorithms in this module are research candidates.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit

@njit(cache=True)
def kl(x, y):
    if y <= 0.0:
        return 0.0 if x <= 0.0 else 1e300
    if y >= 1.0:
        return 0.0 if x >= 1.0 else 1e300
    ans = 0.0
    if x > 0.0: ans += x * math.log(x / y)
    if x < 1.0: ans += (1.0-x) * math.log((1.0-x)/(1.0-y))
    return ans

@njit(cache=True)
def beta_mix_interval(n, S, alpha):
    if n == 0: return 0.0, 1.0
    x = min(1.0,max(0.0,S/n))
    c = math.lgamma(S+0.5)+math.lgamma(n-S+0.5)-math.lgamma(n+1.0)-2*math.lgamma(0.5)
    ll = 0.0
    if S>0.0: ll += S*math.log(x)
    if n-S>0.0: ll += (n-S)*math.log(1.0-x)
    target = (math.log(1.0/alpha)-c+ll)/n
    # Outward endpoints: lower 'a' is rejected, upper 'b' is rejected.
    a=0.0; b=x
    for _ in range(35):
        z=(a+b)/2.0
        if kl(x,z)>target: a=z
        else: b=z
    lower=a
    a=x; b=1.0
    for _ in range(35):
        z=(a+b)/2.0
        if kl(x,z)>target: b=z
        else: a=z
    return lower,b

@njit(cache=True)
def kl_ucb_index(n,S,t):
    if n==0: return 1e100
    x=S/n
    target=(math.log(max(2.0,t))+3.0*math.log(max(1.0,math.log(max(2.0,t)))))/n
    a=x; b=1.0
    for _ in range(22):
        z=(a+b)/2
        if kl(x,z)>target: b=z
        else: a=z
    return b

@njit(cache=True)
def gap_bounds(l,u,k):
    gl=np.zeros(k); gu=np.zeros(k)
    if k==1: return gl,gu
    for i in range(k):
        L=0.0; U=0.0
        for j in range(k):
            if j!=i:
                L=max(L,l[j]); U=max(U,u[j])
        gl[i]=max(0.0,L-u[i]); gu[i]=max(0.0,U-l[i])
    return gl,gu

@njit(cache=True)
def labels_work(l,u,k,eps,eta,report_exact,band_gate):
    lab=np.zeros(k,np.int64); work=np.zeros(k,np.bool_)
    if report_exact:
        gl,gu=gap_bounds(l,u,k)
    else:
        gl=np.zeros(k); gu=np.zeros(k)
        L=np.max(l[:k]); U=np.max(u[:k])
        for i in range(k):
            gl[i]=max(0.0,L-u[i]); gu[i]=max(0.0,U-l[i])
    for i in range(k):
        if gu[i] <= eps: lab[i]=1
        elif gl[i] > eps: lab[i]=-1
        else:
            lab[i]=0
            band=(gl[i]>=eps-eta and gu[i]<=eps+eta)
            work[i]=not (band_gate and band)
    return lab,work,gl,gu

@njit(cache=True)
def phi_one(a,b,eps,eta):
    # Distance to the nearest certified label or certified tolerance band.
    if b <= eps or a > eps: return 0.0
    return max(0.0,min(b-eps,eps-a,max(eps-eta-a,b-eps-eta)))

@njit(cache=True)
def clipped_moss_indices(n,S,k,t,base,segstart):
    idx=np.ones(k)
    if k<=1: return idx
    for i in range(k):
        if n[i]>0:
            idx[i]=min(1.0,S[i]/n[i]+math.sqrt(max(0.0,math.log((t-segstart+1)/(max(2,2*base)*n[i])))/n[i]))
    return idx

@njit(cache=True)
def reward_choice(n,S,k,t,reward,base,segstart,xi):
    idx=np.empty(k)
    if reward==7:
        return np.argmax(clipped_moss_indices(n,S,k,t,base,segstart))
    if reward==3:
        for i in range(k): idx[i]=np.random.beta(1.0+S[i],1.0+n[i]-S[i])
        return np.argmax(idx)
    for i in range(k):
        if n[i]==0: idx[i]=1e100
        elif reward==0:
            idx[i]=S[i]/n[i]+math.sqrt(3*math.log(2*t)/n[i])
        elif reward==4: idx[i]=kl_ucb_index(n[i],S[i],t)
        else:
            if reward==1:
                clock=t; capacity=k
            else:
                clock=t-segstart+1; capacity=max(2,2*base)
            idx[i]=S[i]/n[i]+math.sqrt(max(0.0,math.log(clock/(capacity*n[i])))/n[i])
    best=np.argmax(idx)
    if reward==5 or reward==6:
        prop=np.empty(k)
        for i in range(k):
            if reward==5: prop[i]=np.random.beta(1.0+S[i],1.0+n[i]-S[i])
            else: prop[i]=(S[i]+0.5)/(n[i]+1)
        j=np.argmax(prop)
        if n[best]==0:
            return j if n[j]==0 else best
        slack=xi*min(1.0,math.sqrt(max(2,2*base)/(t-segstart+1)))
        if idx[j]>=idx[best]-slack: return j
    return best

@njit(cache=True)
def pair_plan(ni,nj,ri,rj,ci,cj,h):
    # Exact solution of min c_i(x_i-n_i)+c_j(x_j-n_j),
    # a_i/sqrt(x_i)+a_j/sqrt(x_j) <= h, x >= max(1,n).
    ni=max(1.0,float(ni)); nj=max(1.0,float(nj))
    ai=max(1e-12,ri)*math.sqrt(ni); aj=max(1e-12,rj)*math.sqrt(nj)
    if ri+rj<=h: return ni,nj,0.0
    z=(ai**(2/3)*ci**(1/3)+aj**(2/3)*cj**(1/3))/h
    mi=z*z*(ai/ci)**(2/3); mj=z*z*(aj/cj)**(2/3)
    if mi<ni:
        mi=ni; mj=max(nj,(aj/max(1e-12,h-ri))**2)
    elif mj<nj:
        mj=nj; mi=max(ni,(ai/max(1e-12,h-rj))**2)
    return mi,mj,ci*(mi-ni)+cj*(mj-nj)

@njit(cache=True)
def service_choice(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart):
    eligible=np.zeros(k,np.bool_)
    for i in range(k): eligible[i]=(not cap or n[i]<q[i])
    if not np.any(eligible): return -1
    if scheduler==0: # capped FIFO
        for i in range(k):
            if eligible[i]: return i
    widths=u[:k]-l[:k]
    mids=np.empty(k)
    for i in range(k):
        mids[i]=min(u[i],max(l[i],(S[i]+0.5)/(n[i]+1)))
    b=np.argmax(mids)
    upperbest=np.argmax(u[:k])
    if scheduler==1 or scheduler==2:
        # widest-in-unresolved UNION optimistic reference, faithful natural adaptation
        # scheduler 2 uses least count rather than widest
        best=-1; score=-1e300
        for i in range(k):
            if eligible[i] and (work[i] or i==upperbest):
                z=widths[i] if scheduler==1 else -float(n[i])
                if z>score+1e-14 or (abs(z-score)<=1e-14 and (best<0 or n[i]<n[best])):
                    best=i; score=z
        if best>=0: return best
    if scheduler==3: # ST2-style three roles, adapted to one pull
        good=-1; bad=-1; vg=1e300; vb=-1e300
        for i in range(k):
            if work[i] and eligible[i]:
                if mids[i]>=mids[b]-eps:
                    if l[i]<vg: good=i; vg=l[i]
                else:
                    if u[i]>vb: bad=i; vb=u[i]
        role=scount%3
        if role==0 and good>=0: return good
        if role==1 and bad>=0: return bad
        if eligible[upperbest]: return upperbest
        if good>=0: return good
        if bad>=0: return bad
    if scheduler==4 or scheduler==5: # easy pair / regret-cost aware easy pair
        best=-1; valbest=1e300
        for i in range(k):
            if not work[i]: continue
            j=-1; uj=-1e300
            for a in range(k):
                if a!=i and u[a]>uj: j=a; uj=u[a]
            if j<0: continue
            gap=mids[b]-mids[i]
            # Select a negative witness if empirically bad, or max-upper blocker if good.
            if gap>eps: j=b
            if j==i: continue
            margin=max(eta/2, abs(mids[j]-mids[i]-eps))
            # Band targets should not be resolved below their tolerance scale.
            if abs(gap-eps)<eta/2: margin=max(margin,eta-abs(gap-eps))
            ri=max(mids[i]-l[i],u[i]-mids[i]); rj=max(mids[j]-l[j],u[j]-mids[j])
            target=0.48*margin
            ai=max(0.0,max(1.0,n[i])*(ri/target)**2-n[i])
            aj=max(0.0,max(1.0,n[j])*(rj/target)**2-n[j])
            ci=1.0; cj=1.0
            if scheduler==5:
                ci=price+max(0.0,mids[b]-mids[i]); cj=price+max(0.0,mids[b]-mids[j])
            job=ci*ai+cj*aj+1e-9
            # Choose remaining pair component with largest reduction per sampling price.
            zi=ri/(max(1.0,n[i])*ci) if eligible[i] else -1.0
            zj=rj/(max(1.0,n[j])*cj) if eligible[j] else -1.0
            a=i if zi>=zj else j
            if not eligible[a]: continue
            if job<valbest: valbest=job; best=a
        if best>=0: return best
    if scheduler>=9 and scheduler<=13:
        tidx=clipped_moss_indices(n,S,k,t,base,segstart)
        tmax=np.max(tidx)
        best=-1; bestcost=1e300
        for i in range(k):
            if not work[i]: continue
            j=-1; uj=-1e300
            for a in range(k):
                if a!=i and u[a]>uj: j=a; uj=u[a]
            if j<0: continue
            gap=mids[b]-mids[i]
            if gap>eps: j=b
            if j==i: continue
            dd=abs(mids[j]-mids[i]-eps)
            margin=max(dd,eta-dd)*0.95
            ri=max(mids[i]-l[i],u[i]-mids[i]); rj=max(mids[j]-l[j],u[j]-mids[j])
            ci=price+max(0.0,mids[b]-mids[i]); cj=price+max(0.0,mids[b]-mids[j])
            if scheduler==13:
                ci=price+tmax-tidx[i]; cj=price+tmax-tidx[j]
            if scheduler==12:
                affected=0
                for a in range(k):
                    if work[a]: affected+=1
                cj=cj/math.sqrt(max(1,affected))
            mi,mj,cost=pair_plan(n[i],n[j],ri,rj,ci,cj,margin)
            ei=eligible[i] and mi>n[i]+1e-8
            ej=eligible[j] and mj>n[j]+1e-8
            if not ei and not ej: continue
            if scheduler==10:
                zi=mi/max(1,n[i]) if ei else -1.0
                zj=mj/max(1,n[j]) if ej else -1.0
            elif scheduler==11:
                zi=(mi-n[i])*np.random.random() if ei else -1.0
                zj=(mj-n[j])*np.random.random() if ej else -1.0
            else:
                zi=ri/(max(1.0,n[i])*ci) if ei else -1.0
                zj=rj/(max(1.0,n[j])*cj) if ej else -1.0
            a=i if zi>=zj else j
            if cost<bestcost:
                bestcost=cost;best=a
        if best>=0: return best
    if scheduler==6 or scheduler==7: # smooth certificate-progress, optionally priced
        gl,gu=gap_bounds(l,u,k)
        potential=np.empty(k)
        for i in range(k): potential[i]=phi_one(gl[i],gu[i],eps,eta) if work[i] else 0.0
        best=-1; vb=-1.0
        for j in range(k):
            if not eligible[j]: continue
            # A fixed geometric look-ahead; only its first observation is executed.
            h=max(1.0,0.5*n[j]); factor=math.sqrt(max(1.0,n[j])/(max(1.0,n[j])+h))
            lj=max(l[j],mids[j]-(mids[j]-l[j])*factor)
            uj=min(u[j],mids[j]+(u[j]-mids[j])*factor)
            gain=0.0
            for i in range(k):
                if not work[i]: continue
                li=lj if j==i else l[i]; ui=uj if j==i else u[i]
                L=0.0; U=0.0
                for a in range(k):
                    if a!=i:
                        L=max(L,lj if a==j else l[a]); U=max(U,uj if a==j else u[a])
                ph=phi_one(max(0.0,L-ui),max(0.0,U-li),eps,eta)
                gain+=max(0.0,potential[i]-ph)/(potential[i]+eta/8.0+1e-12)
            cost=1.0 if scheduler==6 else price+max(0.0,mids[b]-mids[j])
            score=gain/(h*cost)
            if score>vb: vb=score; best=j
        if best>=0 and vb>1e-15: return best
    if scheduler==8: # Monte Carlo label-information gain per regret cost
        draws=40
        mus=np.empty((draws,k)); zs=np.zeros((draws,k),np.int64)
        for r in range(draws):
            mx=-1.0
            for j in range(k):
                mus[r,j]=np.random.beta(1.0+S[j],1.0+n[j]-S[j]); mx=max(mx,mus[r,j])
            for i in range(k):
                g=mx-mus[r,i]
                zs[r,i]=0 if g<eps-eta/2 else (2 if g>eps+eta/2 else 1)
        scores=np.zeros(k)
        for j in range(k):
            if not eligible[j]: continue
            p=np.mean(mus[:,j]); H=entropy(p)
            gain=0.0
            for i in range(k):
                if not work[i]: continue
                cond=0.0
                for z in range(3):
                    zc=0; zsmean=0.0
                    for r in range(draws):
                        if zs[r,i]==z: zc+=1; zsmean+=mus[r,j]
                    if zc>0: cond+=zc/draws*entropy(zsmean/zc)
                gain+=max(0.0,H-cond)
            scores[j]=gain/(price+max(0.0,mids[b]-mids[j]))
        a=np.argmax(scores)
        if scores[a]>1e-15: return a
    # Safe fallback: widest incomplete interval, then earliest label.
    best=-1; vb=-1e300
    for i in range(k):
        if eligible[i]:
            v=widths[i]
            if v>vb: vb=v; best=i
    return best

@njit(cache=True)
def entropy(x):
    if x<=0.0 or x>=1.0: return 0.0
    return -x*math.log(x)-(1-x)*math.log(1-x)

@njit(cache=True)
def simulate(rewards,means,arrivals,eps,eta,delta,T,
             reward,scheduler,period,price,xi,conf,exact,band,cap,rho,seed,stride=200,budget_scale=1e100):
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
    report_failure=False
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
                    a=service_choice(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart)
                    service=a>=0
        if not service:
            a=reward_choice(n,S,k,t,reward,base,segstart,xi)
        tidx=clipped_moss_indices(n,S,k,t,base,segstart)
        actiontax=max(0.0,np.max(tidx)-tidx[a])
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

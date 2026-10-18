"""Candidate shared-certificate and joint-information planners. Research versions."""
import math
import numpy as np
from numba import njit
from engine_base import pair_plan, clipped_moss_indices, labels_work, service_choice, phi_one, gap_bounds

@njit(cache=True)
def projected_work_value(l,u,mids,k,eps,eta,work,i,j,mi,mj,n):
    lp=l[:k].copy(); up=u[:k].copy()
    for a,target in [(i,mi),(j,mj)]:
        factor=math.sqrt(max(1.0,n[a])/max(max(1.0,n[a]),target))
        rr=max(mids[a]-l[a],u[a]-mids[a])*factor
        lp[a]=max(l[a],mids[a]-rr)
        up[a]=min(u[a],mids[a]+rr)
    lab,w,gl,gu=labels_work(lp,up,k,eps,eta,True,True)
    oldgl,oldgu=gap_bounds(l,u,k)
    done=0.;progress=0.
    for a in range(k):
        if work[a]:
            if not w[a]: done+=1.
            old=phi_one(oldgl[a],oldgu[a],eps,eta)
            new=phi_one(gl[a],gu[a],eps,eta)
            progress+=max(0.,old-new)/(old+eta/8+1e-12)
    return done,progress

@njit(cache=True)
def service_new(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart):
    if scheduler<20:
        return service_choice(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart)
    eligible=np.zeros(k,np.bool_)
    for a in range(k):eligible[a]=(not cap or n[a]<q[a])
    if not np.any(eligible):return -1
    mids=np.empty(k);radius=np.empty(k)
    for a in range(k):
        mids[a]=min(u[a],max(l[a],(S[a]+.5)/(n[a]+1)))
        radius[a]=max(mids[a]-l[a],u[a]-mids[a])
    b=np.argmax(mids)
    idx=clipped_moss_indices(n,S,k,t,base,segstart);imax=np.max(idx)
    pricevec=price+imax-idx
    best=-1;bestscore=1e300
    if scheduler>=20 and scheduler<=25:
        for i in range(k):
            if not work[i]:continue
            j=-1;mx=-1.
            for a in range(k):
                if a!=i and u[a]>mx:j=a;mx=u[a]
            if mids[b]-mids[i]>eps:j=b
            if j<0 or j==i:continue
            dd=abs(mids[j]-mids[i]-eps)
            h=.95*max(dd,eta-dd)
            ci=pricevec[i];cj=pricevec[j]
            mi,mj,cost=pair_plan(n[i],n[j],radius[i],radius[j],ci,cj,h)
            ei=eligible[i] and mi>n[i]+1e-8
            ej=eligible[j] and mj>n[j]+1e-8
            if not ei and not ej:continue
            done,prog=projected_work_value(l,u,mids,k,eps,eta,work,i,j,mi,mj,n)
            if scheduler==20:benefit=max(1.,done)
            elif scheduler==21:benefit=max(1.,prog)
            elif scheduler==22:benefit=max(.25,done+.25*prog)
            elif scheduler==23:benefit=max(1.,prog)**.5
            elif scheduler==24:benefit=max(1.,prog)**2
            else:benefit=max(1.,done+.1*prog)
            score=cost/benefit
            zi=radius[i]/(max(1.,n[i])*ci) if ei else -1.
            zj=radius[j]/(max(1.,n[j])*cj) if ej else -1.
            a=i if zi>=zj else j
            if score<bestscore:bestscore=score;best=a
    elif scheduler>=26 and scheduler<=29:
        # Local Gaussian information deficit: pairwise effective sample information.
        scorevec=np.zeros(k)
        for i in range(k):
            if not work[i]:continue
            j=-1;mx=-1.
            for a in range(k):
                if a!=i and u[a]>mx:j=a;mx=u[a]
            if mids[b]-mids[i]>eps:j=b
            if j<0 or j==i:continue
            dd=abs(mids[j]-mids[i]-eps);h=.95*max(dd,eta-dd)
            ni=max(1.,n[i]);nj=max(1.,n[j]);ri=radius[i];rj=radius[j]
            mi,mj,cost=pair_plan(ni,nj,ri,rj,pricevec[i],pricevec[j],h)
            # Weigh every active certificate, avoid near-zero denominator runaway.
            weight=1./max(1.,cost)
            if scheduler==27:weight=1./math.sqrt(max(1.,cost))
            if scheduler==28:weight=1./max(1.,cost)**1.5
            if scheduler==29:weight=1.
            if eligible[i]:scorevec[i]+=weight*ri/(ni*pricevec[i])
            if eligible[j]:scorevec[j]+=weight*rj/(nj*pricevec[j])
        if np.max(scorevec)>0:best=np.argmax(scorevec)
    elif scheduler==30 or scheduler==31:
        # Posterior label-vector information, using observed reward statistics only.
        R=48; mus=np.empty((R,k)); codes=np.zeros(R,np.int64)
        for z in range(R):
            mm=-1.
            for a in range(k):
                mus[z,a]=np.random.beta(1.+S[a],1.+n[a]-S[a]);mm=max(mm,mus[z,a])
            code=0
            for a in range(k):
                if work[a] and mm-mus[z,a]<=eps:code|=(1<<a)
            codes[z]=code
        scores=np.zeros(k)
        for a in range(k):
            if not eligible[a]:continue
            pred=np.mean(mus[:,a]);gain=ent(pred)
            used=np.zeros(R,np.bool_)
            for z in range(R):
                if used[z]:continue
                cnt=0;tot=0.
                for zz in range(R):
                    if codes[zz]==codes[z]:used[zz]=True;cnt+=1;tot+=mus[zz,a]
                gain-=cnt/R*ent(tot/cnt)
            cost=pricevec[a]
            scores[a]=max(0.,gain)/(cost if scheduler==30 else cost*cost)
        if np.max(scores)>0:best=np.argmax(scores)
    elif scheduler>=32 and scheduler<=35:
        # Joint convex allocation surrogate: one active blocking pair per task.
        pi=np.empty(k,np.int64);pj=np.empty(k,np.int64);hs=np.empty(k);L=0
        for i in range(k):
            if not work[i]:continue
            j=-1;mx=-1.
            for a in range(k):
                if a!=i and u[a]>mx:j=a;mx=u[a]
            if mids[b]-mids[i]>eps:j=b
            if j<0 or j==i:continue
            dd=abs(mids[j]-mids[i]-eps)
            pi[L]=i;pj[L]=j;hs[L]=.95*max(dd,eta-dd);L+=1
        if L>0:
            aa=np.empty(k);nn=np.empty(k)
            for a in range(k):nn[a]=max(1.,n[a]);aa[a]=max(1e-12,radius[a])*math.sqrt(nn[a])
            lam=np.zeros(L);ws=np.zeros(k)
            for sweep in range(12):
                for z in range(L):
                    i=pi[z];j=pj[z];h=hs[z]
                    wi=max(0.,ws[i]-lam[z]);wj=max(0.,ws[j]-lam[z])
                    lo=0.;hi=max(1.,lam[z]*2)
                    for it in range(45):
                        xi=max(nn[i],(aa[i]*(wi+hi)/(2*pricevec[i]))**(2/3))
                        xj=max(nn[j],(aa[j]*(wj+hi)/(2*pricevec[j]))**(2/3))
                        if aa[i]/math.sqrt(xi)+aa[j]/math.sqrt(xj)<=h:break
                        hi*=2
                    for it in range(20):
                        md=(lo+hi)/2
                        xi=max(nn[i],(aa[i]*(wi+md)/(2*pricevec[i]))**(2/3))
                        xj=max(nn[j],(aa[j]*(wj+md)/(2*pricevec[j]))**(2/3))
                        if aa[i]/math.sqrt(xi)+aa[j]/math.sqrt(xj)>h:lo=md
                        else:hi=md
                    lam[z]=hi;ws[i]=wi+hi;ws[j]=wj+hi
            vals=np.full(k,-1e300)
            for a in range(k):
                if not eligible[a]:continue
                target=max(nn[a],(aa[a]*ws[a]/(2*pricevec[a]))**(2/3))
                if scheduler==32:vals[a]=target/nn[a]
                elif scheduler==33:vals[a]=(target-nn[a])/pricevec[a]
                elif scheduler==34:vals[a]=ws[a]*radius[a]/(nn[a]*pricevec[a])
                else:vals[a]=(target-nn[a])/max(1.,target)
            if np.max(vals)>1e-10:best=np.argmax(vals)
    if best>=0:return best
    return service_choice(n,S,l,u,k,eps,eta,work,q,1,price,scount,cap,t,base,segstart)

@njit(cache=True)
def ent(x):
    if x<=0 or x>=1:return 0.
    return -x*math.log(x)-(1-x)*math.log(1-x)

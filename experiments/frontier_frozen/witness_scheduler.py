"""Exploratory multi-witness certificate planning; reporting remains unchanged."""
from engine_base import *
from new_schedulers import service_new
@njit(cache=True)
def witness_service(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart):
    if scheduler<36:return service_new(n,S,l,u,k,eps,eta,work,q,scheduler,price,scount,cap,t,base,segstart)
    eligible=n[:k]<q[:k] if cap else np.ones(k,np.bool_)
    mid=np.empty(k);r=np.empty(k)
    for i in range(k):
        x=(S[i]+.5)/(n[i]+1)
        if scheduler==40:x=np.random.beta(1+S[i],1+n[i]-S[i])
        mid[i]=max(l[i],min(u[i],x));r[i]=max(u[i]-mid[i],mid[i]-l[i])
    idx=clipped_moss_indices(n,S,k,t,base,segstart);cost=price+np.max(idx)-idx
    b=np.argmax(mid);best=-1;bv=1e300
    gl,gu=gap_bounds(l,u,k)
    for i in range(k):
        if not work[i]:continue
        if mid[b]-mid[i]>eps:
            neg=True
        else:neg=False
        blocker=-1;uu=-1.
        for j in range(k):
            if j!=i and u[j]>uu:blocker=j;uu=u[j]
        for j in range(k):
            if i==j:continue
            if neg:
                if mid[j]-mid[i]<=eps:continue
            else:
                if j!=blocker:continue
            d=abs(mid[j]-mid[i]-eps);h=.95*max(d,eta-d)
            ni,nj,C=pair_plan(n[i],n[j],r[i],r[j],cost[i],cost[j],h)
            ei=eligible[i] and ni>n[i]+1e-8;ej=eligible[j] and nj>n[j]+1e-8
            if not ei and not ej:continue
            zi=r[i]/(max(1,n[i])*cost[i]) if ei else -1.
            zj=r[j]/(max(1,n[j])*cost[j]) if ej else -1.
            if scheduler==39:
                zi=(ni-n[i])/max(1,ni) if ei else -1.
                zj=(nj-n[j])/max(1,nj) if ej else -1.
            a=i if zi>=zj else j
            benefit=1.
            if scheduler==37 or scheduler==38:
                ll=l[:k].copy();up=u[:k].copy()
                ri=r[i]*math.sqrt(max(1,n[i])/ni);rj=r[j]*math.sqrt(max(1,n[j])/nj)
                ll[i]=max(ll[i],mid[i]-ri);up[i]=min(up[i],mid[i]+ri)
                ll[j]=max(ll[j],mid[j]-rj);up[j]=min(up[j],mid[j]+rj)
                ngl,ngu=gap_bounds(ll,up,k);gain=0.
                for z in range(k):
                    if work[z]:
                        old=phi_one(gl[z],gu[z],eps,eta);new=phi_one(ngl[z],ngu[z],eps,eta)
                        if scheduler==37:gain+=1. if new<=1e-12 else 0.
                        else:gain+=max(0.,old-new)/max(1e-8,old)
                benefit=max(1.,gain)
            v=C/benefit
            if v<bv:bv=v;best=a
    if best>=0:return best
    return service_choice(n,S,l,u,k,eps,eta,work,q,1,price,scount,cap,t,base,segstart)

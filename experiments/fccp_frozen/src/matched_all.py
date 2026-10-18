"""Correction limited to ALL adaptive controller's observed cost input.
The initial ALL service_plan returned 0 as its second value, which is harmless for
fixed-rate or priority=1 modes but not for the adaptive cost-sensitive controller.
The F-CCP proposals/controllers and all pure reward baselines are unchanged.
"""
from numba import njit
from flexible_engine import service_plan

@njit(cache=False)
def service_plan_matched(n,S,l,u,k,eps,eta,work,q,idx,priority,price,scheduler):
    a,gap=service_plan(n,S,l,u,k,eps,eta,work,q,idx,priority,price,scheduler)
    if scheduler==1 and a>=0:
        top=-1.;chosen=0.
        for i in range(k):
            mid=min(u[i],max(l[i],(S[i]+.5)/(n[i]+1)))
            if mid>top:top=mid
            if i==a:chosen=mid
        gap=max(0.,top-chosen)
    return a,gap

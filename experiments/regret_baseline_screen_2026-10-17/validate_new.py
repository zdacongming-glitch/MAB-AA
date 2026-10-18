"""Numerical correctness checks on synthetic states, not performance screening."""
from pathlib import Path
import ctypes
import json
import math
import sys
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import betaincinv, cython_special
from numba import njit
import new_policies as policy


def main():
    rng = np.random.default_rng(612091)
    result = {"passed": False, "seed": 612091, "performance_trials": False}
    name = ctypes.pythonapi.PyCapsule_GetName
    name.restype = ctypes.c_char_p
    name.argtypes = [ctypes.py_object]
    result["scipy_c_signature"] = name(cython_special.__pyx_capi__["betaincinv"]).decode()
    assert result["scipy_c_signature"] == "double (double, double, double, int __pyx_skip_dispatch)"

    max_dinf_error = 0.0
    max_binary_error = 0.0
    cases = 0
    for _ in range(600):
        x, y = sorted(rng.uniform(0.0, 1.0, 2))
        if cases % 3 == 0:
            x, y = 0.0, 1.0
        nx, ny = rng.integers(1, 20000, 2)
        mean = (nx * x + ny * y) / (nx + ny)
        target = mean + (1.0 - mean) * rng.uniform(.001, .999)
        aux = np.zeros((9, 8))
        aux[0, 2:6] = x, y, nx, ny
        # Independent bounded scalar maximization on z=nu*(1-target).
        def objective(z):
            return -float((nx * np.log1p((target - x) * z / (1 - target))
                        + ny * np.log1p((target - y) * z / (1 - target))) / (nx + ny))
        opt = minimize_scalar(objective, bounds=(0., 1.), method="bounded", options={"xatol": 1e-13})
        expected = max(0.0, -opt.fun, -objective(0.))
        if y < 1.0:
            expected = max(expected, -objective(1.))
        actual = policy.empirical_dinf(aux, 0, target)
        max_dinf_error = max(max_dinf_error, abs(actual - expected))
        assert abs(actual - expected) < 2e-8, (x, y, nx, ny, target, actual, expected)
        if x == 0.0 and y == 1.0:
            binary = policy.bernoulli_kl(mean, target)
            max_binary_error = max(max_binary_error, abs(actual - binary))
            assert abs(actual - binary) < 1e-10
        cases += 1
    result["empirical_dinf"] = dict(cases=cases, max_independent_optimizer_error=max_dinf_error, max_bernoulli_KL_error=max_binary_error)

    # Boundary values and observed-support bookkeeping; no true support input.
    for x in (0., .4, 1.):
        aux = np.zeros((9, 8)); aux[0, 2:6] = x, x, 7., 0.
        assert policy.empirical_dinf(aux, 0, x) == 0.
        if x < 1:
            target = (x + 1.) / 2
            assert abs(policy.empirical_dinf(aux, 0, target) - math.log((1-x)/(1-target))) < 1e-12
            assert np.isinf(policy.empirical_dinf(aux, 0, 1.))
    for observations in ([.3,.7,.3,.7,.7],[.7,.3,.3,.7],[0.,1.,1.,0.],[1.,1.],[.4,.4]):
        n=np.zeros(1,np.int64); S=np.zeros(1); Q=np.zeros(1); aux=np.zeros((9,8))
        for reward in observations:
            policy.update_new(n,S,Q,aux,1,1,0,reward,6,0.,0.,0.)
            n[0]+=1; S[0]+=reward; Q[0]+=reward*reward
        assert aux[0,4]+aux[0,5] == len(observations)
        assert abs(aux[0,2]*aux[0,4]+aux[0,3]*aux[0,5]-sum(observations)) < 1e-12
    result["empirical_support_and_boundary_checks"] = "passed"

    # Compare actual Bayes-UCB argmax with scipy's public inverse-beta ufunc.
    max_quantile_error = 0.0
    for t in (1,2,10,1000,16000):
        for _ in range(30):
            n=rng.integers(0,10000,7,dtype=np.int64)
            S=rng.uniform(0.,1.,7)*n; Q=S.copy(); aux=np.zeros((15,8))
            expected=betaincinv(1+S,1+n-S,1-1/t)
            actual=policy.new_choose(n,S,Q,7,t,np.ones(7,np.int64),5,0.,0.,0.,aux)
            assert actual==int(np.argmax(expected))
            for i in range(7):
                v=policy._beta_inverse(1+S[i],1+n[i]-S[i],1-1/t,1)
                max_quantile_error=max(max_quantile_error,abs(v-expected[i]))
    result["bayes_ucb_public_scipy_match"] = dict(states=150,max_quantile_error=max_quantile_error)

    # Independent formulas for ordinary index families on generated histories.
    for _ in range(150):
        t=int(rng.integers(20,20000)); k=7
        n=rng.integers(1,t,7,dtype=np.int64)
        S=rng.uniform(.01,.99,7)*n; Q=S.copy(); mu=S/n
        variance=np.maximum(0,Q/n-mu**2)
        formulas={1:mu+np.sqrt(8*np.log(t)/n),
                  2:mu+np.sqrt(2*variance*np.log(t)/n)+3*np.log(t)/n,
                  3:mu+np.sqrt(np.log(t)/n*np.minimum(.25,variance+np.sqrt(2*np.log(t)/n)))}
        for kind,scores in formulas.items():
            a=policy.new_choose(n,S,Q,k,t,np.ones(k,np.int64),kind,0.,0.,0.,np.zeros((k+8,8)))
            assert a==int(np.argmax(scores))
        T=20000.
        for beta in (.5,1.,2.):
            cap=max(1,int(math.ceil(T**(1/(1+2*beta)))))
            available=min(k,cap)
            scores=mu[:available]+np.sqrt(np.maximum(0,np.log(T/(available*n[:available])))/n[:available])
            a=policy.new_choose(n,S,Q,k,t,np.ones(k,np.int64),8,beta,0.,T,np.zeros((k+8,8)))
            assert a==int(np.argmax(scores))
    result["index_formula_states"] = 150
    result["passed"] = True
    out=Path(__file__).parent/'audit'/'new-policy-numerical-validation.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

"""Reproducible diagnostic checks; analytic proofs are in the Markdown report."""
from __future__ import annotations
import itertools
import json
import math
import random
from pathlib import Path
from fractions import Fraction
from geometry import spectrum, fixed_point, capacity, count_segments, compatible_scales

ROOT = Path(__file__).resolve().parent
rng = random.Random(20261012)
summary = {"seed": 20261012, "exhaustive_small_schedules": 0,
           "random_schedules": 0, "jitter_checks": 0, "duality_checks": 0,
           "clock_charging_checks": 0, "scale_selection_checks": 0}
max_rel_dual = 0.0
max_s_over_c = 0.0
max_q_over_gamma = 0.0


def check(hs, T):
    global max_rel_dual, max_s_over_c, max_q_over_gamma
    sp = spectrum(hs, T)
    cap = capacity(hs, T)
    S, Q, C = sp['S'], sp['Q'], cap['C']
    g = fixed_point(hs, T)
    eps = 1e-9*(1+S)
    assert S/4-eps <= C <= S+eps
    if g:
        assert g <= math.ceil(Q+1e-12)
        assert Q <= 3*g+eps
        assert S <= 4*g+g*math.sqrt(2*max(0, math.ceil(math.log2(T))-math.ceil(math.log2(g))))+eps
        max_s_over_c = max(max_s_over_c, S/C)
        max_q_over_gamma = max(max_q_over_gamma, Q/g)
    err = abs(C-cap['dual'])/(1+C)
    max_rel_dual = max(max_rel_dual, err)
    assert err < 1e-9
    summary['duality_checks'] += 1
    # Explicit per-dyadic-block feasible allocation.
    if hs:
        ns = [Fraction(1 << (h-1).bit_length(), 4*sp['bins'][1 << (h-1).bit_length()]) for h in hs]
        for x in sorted(set(hs)):
            assert sum(n for h, n in zip(hs, ns) if h <= x) <= x
    seg = count_segments(hs, T)
    stop = next((j for j,z in enumerate(seg) if z['c'] >= z['H']), len(seg))
    charge = sum(math.sqrt(z['c']*z['h']) for z in seg[:stop])
    assert charge <= (2*math.sqrt(2)/(1-1/math.sqrt(2)))*S+eps
    if stop < len(seg):
        assert seg[stop]['H'] <= S+eps
    summary['clock_charging_checks'] += 1
    ss = compatible_scales(hs, T)
    assert ss['selected_weight']+eps >= 3/(10*math.sqrt(2))*ss['S_high']
    assert sum(row[-1] for row in ss['selected']) <= 2+eps
    if hs:
        assert ss['S_rest'] <= 8*math.sqrt(max(hs))+eps
    summary['scale_selection_checks'] += 1

for T in range(1, 7):
    for k in range(0, 7):
        for hs in itertools.combinations_with_replacement(range(1, T+1), k):
            check(list(hs), T)
            summary['exhaustive_small_schedules'] += 1

for z in range(10000):
    T = rng.randint(1, 10000)
    k = rng.randint(0, 100)
    hs = [rng.randint(1, T) for _ in range(k)]
    if z % 4 == 0 and k:
        scales = [1 << rng.randint(0, (T-1).bit_length()) for _ in range(rng.randint(1, 8))]
        hs = [min(T, rng.choice(scales)) for _ in range(k)]
    check(hs, T)
    summary['random_schedules'] += 1
    d = rng.randint(0, max(1, T//4))
    hp = [min(T, max(1, h+rng.randint(-d, d))) for h in hs]
    C1, C2 = capacity(hs, T)['C'], capacity(hp, T)['C']
    assert abs(C1-C2) <= d + 1e-8*(1+C1+C2)
    summary['jitter_checks'] += 1
    if hs:
        hd = [rng.randint(1,h) for h in hs]
        assert spectrum(hd,T)['S'] <= 2*spectrum(hs,T)['S']+1e-8
    # A one-round extension may add a giant batch of lifetime-one arms.
    hn = [h+1 for h in hs]+[1]*rng.randint(0,20)
    cn = capacity(hn,T+1)['C']
    assert C1-1e-8 <= cn <= C1+1+1e-8

summary.update(max_relative_primal_dual_gap=max_rel_dual,
               max_S_over_C=max_s_over_c,
               max_Q_over_Gamma=max_q_over_gamma,
               status='all diagnostic assertions passed')
(ROOT/'geometry_results.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))

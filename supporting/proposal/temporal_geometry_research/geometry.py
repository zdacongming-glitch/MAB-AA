"""Arrival-only complexity calculations and exact feasibility certificates.

No reward means are used. These are theorem-diagnostic utilities, not a proof.
The input lists the remaining lifetimes of NON-ANCHOR arms at a fixed horizon.
"""
from __future__ import annotations
import math
from fractions import Fraction
from typing import Iterable


def _validate(lifetimes: Iterable[int], horizon: int) -> list[int]:
    if not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    values = list(lifetimes)
    if any(not isinstance(h, int) or not 1 <= h <= horizon for h in values):
        raise ValueError("each lifetime must be an integer in [1, horizon]")
    return values


def spectrum(lifetimes: Iterable[int], horizon: int) -> dict:
    hs = _validate(lifetimes, horizon)
    bins: dict[int, int] = {}
    for h in hs:
        b = 1 << (h - 1).bit_length()
        bins[b] = bins.get(b, 0) + 1
    components = {b: min(float(b), math.sqrt(k * b)) for b, k in bins.items()}
    s = sum(components.values())
    q = math.sqrt(sum(x*x for x in components.values()))
    return {"S": s, "Q": q, "D_eff": s*s/(q*q) if q else 0.0,
            "bins": bins, "components": components}


def fixed_point(lifetimes: Iterable[int], horizon: int) -> int:
    hs = _validate(lifetimes, horizon)
    if not hs:
        return 0
    lo, hi = 1, horizon
    while lo < hi:
        r = (lo + hi)//2
        if sum(h for h in hs if h > r) <= r*r:
            hi = r
        else:
            lo = r + 1
    return lo


def phi(x: float) -> float:
    if x < 0:
        raise ValueError("phi is defined for nonnegative inputs")
    return min(x, math.sqrt(x))


def conjugate(c: float) -> float:
    if c <= 0:
        return math.inf
    if c < 0.5:
        return 1/(4*c)
    if c <= 1:
        return 1-c
    return 0.0


def capacity(lifetimes: Iterable[int], horizon: int) -> dict:
    """Compute C by the lower convex hull of (r, H_(r)).

    Hull slope comparisons are exact integer cross products. Returned n_star
    and all prefix feasibility checks use fractions, not floating-point tests.
    """
    hs = sorted(_validate(lifetimes, horizon))
    if not hs:
        return {"C": 0.0, "n_star": [], "blocks": [], "dual": 0.0,
                "lambda": [], "sorted_lifetimes": []}
    hull = [(0, 0)]
    for r, h in enumerate(hs, 1):
        hull.append((r, h))
        while len(hull) >= 3:
            a, b, c = hull[-3:]
            left = (b[1]-a[1])*(c[0]-b[0])
            right = (c[1]-b[1])*(b[0]-a[0])
            if left >= right:
                hull.pop(-2)
            else:
                break
    n_star = [Fraction(0)]*len(hs)
    blocks = []
    p = []
    for (r0, h0), (r1, h1) in zip(hull[:-1], hull[1:]):
        slope = Fraction(h1-h0, r1-r0)
        assert slope > 0
        n_star[r0:r1] = [slope]*(r1-r0)
        blocks.append((r0, r1, slope))
        q = float(slope)
        p.append(1.0 if q <= 1 else 1/(2*math.sqrt(q)))
    prefix = Fraction(0)
    for h, n in zip(hs, n_star):
        prefix += n
        assert prefix <= h
    assert prefix == hs[-1]
    lambdas = [0.0]*len(hs)
    for b, (_, r1, _) in enumerate(blocks):
        lambdas[r1-1] = p[b] - (p[b+1] if b+1 < len(p) else 0.0)
        assert lambdas[r1-1] >= -1e-12
    costs = [0.0]*len(hs)
    csum = 0.0
    for i in range(len(hs)-1, -1, -1):
        csum += lambdas[i]
        costs[i] = csum
    value = sum(phi(float(n)) for n in n_star)
    dual = sum(h*l for h, l in zip(hs, lambdas)) + sum(conjugate(c) for c in costs)
    return {"C": value, "n_star": n_star, "blocks": blocks, "dual": dual,
            "lambda": lambdas, "sorted_lifetimes": hs}


def count_segments(lifetimes: Iterable[int], horizon: int) -> list[dict]:
    hs = _validate(lifetimes, horizon)
    births: dict[int, int] = {}
    for h in hs:
        t = horizon-h+1
        births[t] = births.get(t, 0)+1
    count = base = 0
    segments = []
    for t, k in sorted(births.items()):
        count += k
        if base == 0 or count >= 2*base:
            if segments:
                segments[-1]["h"] = t-segments[-1]["start"]
            base = count
            segments.append({"start": t, "c": count, "H": horizon-t+1})
    if segments:
        segments[-1]["h"] = horizon-segments[-1]["start"]+1
    return segments


def compatible_scales(lifetimes: Iterable[int], horizon: int) -> dict:
    spec = spectrum(lifetimes, horizon)
    eligible = []
    rest = high = 0.0
    for b, k in spec["bins"].items():
        s = spec["components"][b]
        ell = b.bit_length()-1
        if ell >= 2 and k >= 2:
            v = min(1.0, math.sqrt((k-1)/b))
            eligible.append((ell, b, k, v))
            high += s
        else:
            rest += s
    weights = [sum(b*v for ell, b, k, v in eligible if ell % 2 == parity)
               for parity in (0, 1)]
    parity = int(weights[1] > weights[0])
    selected = []
    for row in sorted(eligible, reverse=True):
        ell, b, k, v = row
        if ell % 2 != parity:
            continue
        if not selected or v > 2*selected[-1][-1]:
            selected.append(row)
    return {"selected": selected, "S_rest": rest, "S_high": high,
            "selected_weight": sum(b*v for _, b, _, v in selected)}

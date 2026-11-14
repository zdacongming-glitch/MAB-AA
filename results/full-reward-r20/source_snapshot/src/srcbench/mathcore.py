"""Numerical primitives shared by allocation, inference, and comparators.

All empirical KL calculations retain the actual bounded observations.  Numba
only compiles arithmetic; omitting Numba leaves the same Python functions.
"""
from __future__ import annotations

import math
import numpy as np

try:
    from numba import njit
    from numba.typed import List as NumericList
    NUMBA_AVAILABLE = True
except ImportError:  # The small-experiment interface also works without Numba.
    NUMBA_AVAILABLE = False
    NumericList = list

    def njit(*args, **kwargs):
        def decorate(function):
            return function
        return decorate


@njit(cache=True)
def bernoulli_kl(p, q):
    if p == q:
        return 0.0
    value = 0.0
    if p > 0:
        if q <= 0:
            return math.inf
        value += p * math.log(p / q)
    if p < 1:
        if q >= 1:
            return math.inf
        value += (1-p) * math.log((1-p)/(1-q))
    return value


@njit(cache=True)
def dinf(values, counts, target):
    """Normalized D_inf(empirical distribution, target), on support [0,1]."""
    total = 0.0
    shifted = 0.0
    distinct = 0
    first = 0.0
    second = 0.0
    for j in range(len(values)):
        if counts[j] > 0:
            total += counts[j]
            shifted += counts[j]*(target-values[j])
            if distinct == 0:
                first = values[j]
            elif distinct == 1:
                second = values[j]
            distinct += 1
    if total == 0:
        return 0.0
    # The left-limit convention at one is determined by the actual support,
    # even if an empirical mean rounds to one in floating arithmetic.
    if target >= 1:
        for j in range(len(values)):
            if counts[j] > 0 and values[j] < 1:
                return math.inf
        return 0.0
    # Compare centered observations. An absolute mean tolerance is unsafe
    # near one, where an ulp-sized gap can have order-one information.
    if shifted <= 0:
        return 0.0
    if distinct == 1:
        return math.log((1-first)/(1-target))
    inv = 1/(1-target)
    nu = 1.0
    if distinct == 2:
        a, b = (target-first)*inv, (target-second)*inv
        if a*b < 0:
            nu = min(1.0, max(0.0, -(shifted/total)*inv/(a*b)))
    else:
        end = 0.0
        second_moment = 0.0
        for j in range(len(values)):
            if counts[j] > 0:
                a = (target-values[j])*inv
                second_moment += counts[j]*a*a
                den = 1+a
                if den <= 0:
                    end = -math.inf
                    break
                end += counts[j]*a/den
        if end < 0:
            lo, hi, current = 0.0, 1.0, 0.5
            # Start near the stationary point when the target is close to
            # the empirical mean; retain the same safeguarded solver.
            if second_moment > 0 and math.isfinite(second_moment):
                initial = shifted*inv/second_moment
                if initial > 0 and math.isfinite(initial):
                    current = min(0.5, initial)
            converged = False
            for _ in range(80):
                gradient, curvature = 0.0, 0.0
                for j in range(len(values)):
                    if counts[j] > 0:
                        a = (target-values[j])*inv
                        ratio = a/(1+current*a)
                        gradient += counts[j]*ratio
                        curvature -= counts[j]*ratio*ratio
                if abs(gradient) <= 1e-12*total:
                    nu, converged = current, True
                    break
                if gradient > 0:
                    lo = current
                else:
                    hi = current
                if hi-lo < 1e-12:
                    nu, converged = (lo+hi)/2, True
                    break
                proposed = current-gradient/curvature
                pad = .02*(hi-lo)
                current = proposed if (math.isfinite(proposed) and lo+pad < proposed < hi-pad) else (lo+hi)/2
            if not converged:
                nu = (lo+hi)/2
    value = 0.0
    for j in range(len(values)):
        if counts[j] > 0:
            value += counts[j]*math.log1p(nu*(target-values[j])*inv)
    return max(0.0, value/total)


@njit(cache=True)
def inverse_index(values, counts, budget):
    """Supremum m with n*D_inf(F,m)<=budget (budget is NOT normalized)."""
    n = 0.0
    perfect = True
    for j in range(len(values)):
        n += counts[j]
        if counts[j] > 0 and values[j] < 1:
            perfect = False
    if n == 0 or budget == math.inf or perfect:
        return 1.0
    budget = max(0.0, budget)
    # Zero is feasible and one is infeasible for every finite budget with
    # non-perfect support, even when a rounded empirical mean equals one.
    lo, hi = 0.0, 1.0
    for _ in range(53):
        mid = (lo+hi)/2
        if mid == hi or mid == lo:
            break
        if n*dinf(values, counts, mid) > budget:
            hi = mid
        else:
            lo = mid
    # A midpoint of adjacent floats can round to the infeasible endpoint.
    return lo


@njit(cache=True)
def prefix_interval(n, total, alpha):
    """Outward-rounded inversion of the bounded-data beta-mixture process."""
    if n == 0:
        return 0.0, 1.0
    mean = total/n
    threshold = math.log(1/alpha)
    constant = math.lgamma(total+.5)+math.lgamma(n-total+.5)-math.lgamma(n+1.0)-math.log(math.pi)
    lower, upper = 0.0, 1.0
    if total > 0:
        lo, hi = 0.0, mean
        for _ in range(48):
            mid = (lo+hi)/2
            value = constant-total*math.log(mid)
            if total < n:
                value -= (n-total)*math.log1p(-mid)
            if value > threshold:
                lo = mid
            else:
                hi = mid
        lower = np.nextafter(lo, 0.0)
    if total < n:
        lo, hi = mean, 1.0
        for _ in range(48):
            mid = (lo+hi)/2
            value = constant-(n-total)*math.log1p(-mid)
            if total > 0:
                value -= total*math.log(mid)
            if value > threshold:
                hi = mid
            else:
                lo = mid
        upper = np.nextafter(hi, 1.0)
    return lower, upper


@njit(cache=True)
def pair_plan(vi, vj, ni, nj, ci, cj, target):
    """Exact two-endpoint convex proxy, including active lower bounds."""
    bi, bj = float(max(1, ni)), float(max(1, nj))
    vi, vj = max(1e-12, vi), max(1e-12, vj)
    ai, aj = vi*math.sqrt(bi), vj*math.sqrt(bj)
    xi, xj = bi, bj
    if vi+vj > target:
        scale = (ai**(2/3)*ci**(1/3)+aj**(2/3)*cj**(1/3))/target
        xi = scale*scale*(ai/ci)**(2/3)
        xj = scale*scale*(aj/cj)**(2/3)
        if xi < bi:
            xi = bi
            xj = max(bj, (aj/max(1e-300, target-vi))**2)
        elif xj < bj:
            xj = bj
            xi = max(bi, (ai/max(1e-300, target-vj))**2)
    return xi, xj, ci*(xi-bi)+cj*(xj-bj)


@njit(cache=True)
def top_two(values):
    first, second = -1, -1
    for i in range(len(values)):
        if first < 0 or values[i] > values[first]:
            second, first = first, i
        elif second < 0 or values[i] > values[second]:
            second = i
    return first, second


@njit(cache=True)
def reporter(lower, upper, epsilon, eta, failed=False):
    """Self-excluding membership labels and pending-work mask in O(K)."""
    k = len(lower)
    labels = np.zeros(k, dtype=np.int8)
    work = np.zeros(k, dtype=np.bool_)
    if failed:
        return labels, work
    if k == 1:
        labels[0] = 1
        return labels, work
    a, b = top_two(lower)
    c, d = top_two(upper)
    for i in range(k):
        low = max(0.0, lower[b if i == a else a]-upper[i])
        high = max(0.0, upper[d if i == c else c]-lower[i])
        if high <= epsilon:
            labels[i] = 1
        elif low > epsilon:
            labels[i] = -1
        elif not (low >= epsilon-eta and high <= epsilon+eta):
            work[i] = True
    return labels, work


@njit(cache=True)
def spectrum_scale(births, t):
    bins = np.zeros(64, dtype=np.int64)
    for i in range(1, len(births)):
        age = t-births[i]+1
        value, ell = age-1, 0
        while value > 0:
            ell += 1
            value >>= 1
        bins[ell] += 1
    value = 0.0
    for ell in range(64):
        if bins[ell] > 0:
            length = 2.0**ell
            value += min(length, math.sqrt(bins[ell]*length))
    return value


@njit(cache=True)
def reference_indices(n, sums, t, sigma, dclock):
    result = np.ones(len(n), dtype=np.float64)
    if len(n) <= 1:
        return result
    v = (t-sigma+1)/dclock
    for i in range(len(n)):
        if n[i] > 0:
            result[i] = min(1.0, sums[i]/n[i]+math.sqrt(max(0.0, math.log(v/n[i]))/n[i]))
    return result


@njit(cache=True)
def information_choice(n, sums, allowed, values, counts, coefficient):
    """First feasible empirical-information maximizer, with safe KL pruning."""
    best_mean = 0.0
    for i in range(len(n)):
        if n[i] > 0:
            best_mean = max(best_mean, sums[i]/n[i])
    # Unobserved arms have infinite reward score.
    for i in range(len(n)):
        if allowed[i] and n[i] == 0:
            return i
    incumbent, selected = math.inf, -1
    # Seed pruning with a feasible arm's actual cost. A rounded empirical
    # mean near one does not imply zero D_inf at the boundary target one.
    for i in range(len(n)):
        if allowed[i] and n[i] > 0 and sums[i]/n[i] >= best_mean-1e-15:
            cost = n[i]*dinf(values[i], counts[i], best_mean)+coefficient*math.log(n[i])
            incumbent = min(incumbent, cost)
    for i in range(len(n)):
        if not allowed[i]:
            continue
        mean = sums[i]/n[i]
        logn = coefficient*math.log(n[i])
        bound = logn if mean >= best_mean-1e-15 else n[i]*bernoulli_kl(mean, best_mean)+logn
        # D_inf(F,m) >= kl(mean(F),m); strict pruning preserves all ties.
        if bound > incumbent+1e-9+2e-12*n[i]:
            continue
        index = n[i]*dinf(values[i], counts[i], best_mean)+logn
        if selected < 0 or index < incumbent:
            selected, incumbent = i, index
    if selected < 0:
        # Degenerate all-infinite scores still obey arrival-order tie breaking.
        for i in range(len(n)):
            if allowed[i]:
                return i
    return selected


@njit(cache=True)
def service_plan(n, sums, squares, lower, upper, quotas, epsilon, eta, preference,
                 variant=0, nu=.02, relevance_floor=.02):
    """Directional paired planner (0), widest control (1), or LUCB control (2)."""
    labels, work = reporter(lower, upper, epsilon, eta, False)
    k = len(n)
    backlog = 0
    for i in range(k):
        backlog += int(work[i])
    if k < 2 or backlog == 0:
        return -1, 0.0, backlog, 0.0
    centers, variances = np.empty(k), np.empty(k)
    best = 0
    for i in range(k):
        smooth = (sums[i]+.5)/(n[i]+1)
        centers[i] = min(upper[i], max(lower[i], smooth))
        variances[i] = max(0.0, (squares[i]+.5)/(n[i]+1)-smooth*smooth)/(n[i]+2)
        if centers[i] > centers[best]:
            best = i
    relevance, price = np.ones(k), np.empty(k)
    boundary = relevance_floor
    for i in range(k):
        price[i] = nu+(1-preference)*max(0.0, centers[best]-centers[i])
        if work[i]:
            gap = max(0.0, centers[best]-centers[i])
            sd = math.sqrt(max(1e-14, variances[i]+variances[best]))
            below = .5*math.erfc(-(epsilon-eta-gap)/(sd*math.sqrt(2)))
            above = .5*math.erfc((epsilon+eta-gap)/(sd*math.sqrt(2)))
            relevance[i] = min(1.0, max(relevance_floor, below+above))
            boundary = max(boundary, relevance[i])
    first, second = top_two(upper)
    chosen = -1
    if variant == 1:
        width = -1.0
        for i in range(k):
            if labels[i] == 0 and n[i] < quotas[i] and upper[i]-lower[i] > width:
                chosen, width = i, upper[i]-lower[i]
    elif variant == 2:
        hardest, candidate, reference = -math.inf, -1, -1
        for i in range(k):
            if labels[i] != 0:
                continue
            j = second if i == first else first
            priority = upper[j]-lower[i]-epsilon+upper[i]-lower[i]
            if priority > hardest:
                hardest, candidate, reference = priority, i, j
        if candidate >= 0:
            chosen = candidate if upper[candidate]-lower[candidate] >= upper[reference]-lower[reference] else reference
            if n[chosen] >= quotas[chosen]:
                chosen = -1
    else:
        references = np.full(k, -1, dtype=np.int64)
        vi, vj, targets, shares = np.zeros(k), np.zeros(k), np.zeros(k), np.zeros(k)
        for i in range(k):
            if not work[i]:
                continue
            j = best if centers[best]-centers[i] > epsilon else (second if i == first else first)
            references[i] = j
            d = centers[j]-centers[i]-epsilon
            band = eta-abs(d)
            if band > abs(d):
                vi[i] = max(centers[i]-lower[i], upper[i]-centers[i])
                vj[i] = max(centers[j]-lower[j], upper[j]-centers[j])
            elif d > 0:
                vi[i], vj[i] = upper[i]-centers[i], centers[j]-lower[j]
            else:
                vi[i], vj[i] = centers[i]-lower[i], upper[j]-centers[j]
            vi[i], vj[i] = max(1e-12, vi[i]), max(1e-12, vj[i])
            targets[i] = max(1e-9, .95*max(abs(d), band))
            shares[i] += relevance[i]
            shares[j] += relevance[i]
        for i in range(k):
            shares[i] = math.sqrt(max(1.0, shares[i]))
        best_priority = math.inf
        for i in range(k):
            j = references[i]
            if j < 0:
                continue
            xi, xj, cost = pair_plan(vi[i], vj[i], n[i], n[j], price[i], price[j], targets[i])
            legal_i = n[i] < quotas[i] and xi > n[i]+1e-8
            legal_j = n[j] < quotas[j] and xj > n[j]+1e-8
            if not legal_i and not legal_j:
                continue
            priority = cost/(max(shares[i], shares[j])*relevance[i])
            if priority < best_priority:
                si = vi[i]*shares[i]/(max(1, n[i])*price[i])
                sj = vj[i]*shares[j]/(max(1, n[j])*price[j])
                chosen = j if not legal_i else (i if not legal_j or si >= sj else j)
                best_priority = priority
    if chosen < 0:
        width = -1.0
        for i in range(k):
            if n[i] < quotas[i] and upper[i]-lower[i] > width:
                chosen, width = i, upper[i]-lower[i]
    loss = 0.0 if chosen < 0 else max(0.0, centers[best]-centers[chosen])
    return chosen, boundary, backlog, loss

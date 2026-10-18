# Read-only review of BL-MOSS and empirical IMED

Reviewed 2026-10-17. No runtime source was changed, and no real test simulation was run in this review. The review covers `new_policies.py` kinds 6, 7 and 8 and the relevant state updates in `runner.py`.

Reviewed `new_policies.py` SHA-256: `3b97f8b623c7b1b21b66d0b7e12d59fa840e33e145475ede18a258ee0bf23132`.

## BL-MOSS: passes the declared count-cap adaptation

Primary reference: Ghalme et al., *Ballooning multi-armed bandits*, Artificial Intelligence 296 (2021), [institutional full text](https://research.chalmers.se/publication/522732/file/522732_Fulltext.pdf). The locally saved PDF and page images in `literature/ballooning/` were examined directly. PDF page 11 defines the MOSS index; PDF page 12 contains Algorithm 1 and Section 5.1.

The published Pareto prescription is $\alpha=T^{-2\beta/(1+2\beta)}$, hence the retained-arm count is

$$
m=\lceil\alpha T\rceil=\left\lceil T^{1/(1+2\beta)}\right\rceil.
$$

Kind 8 computes exactly this cap using the supplied endpoint `p2` and supplied tail-sensitivity parameter `p0`. It sets `allowed=min(k,cap)` and selects only in that prefix. Kind 7 sets `allowed=k`, giving a useful all-arrivals, known-horizon reference. Both use

$$
\widehat r_i+\sqrt{\frac{\max\{\log(T/(K_t^{\rm accepted}n_i)),0\}}{n_i}},
$$

with the current accepted-set size, not the eventual cap. Unobserved accepted arms receive initialization pulls first. All original observations and physical rounds are retained. These are the declared choices; there is no reset, future mean, future reward, artificial reward or extra observation in the chooser.

The runner's arrivals are nondecreasing in every one of the 12 frozen scenarios. Within each equal-time batch, the existing arm-label order is used, after the original replication-specific permutation of means among those labels. Therefore the prefix is an arrival-order prefix and does not sort on quality. All three beta values must remain predeclared sensitivities and must not be selected using final test results.

The batch behavior is an explicit adaptation. The original formal model permits at most one new arm per round; the current suite permits gaps and batches. Section 5.1 specifies the earliest arms, which supports a count cap, while Algorithm 1 also uses a time-indexed set at the cutoff. The implementation resolves that ambiguity by using an arrival-order cap. It should therefore retain the name `BL-MOSS-countcap-P`, rather than claiming literal coverage of arbitrary batches by the original theorem. The test suite supplies neither a random best-arm arrival distribution nor a valid known tail parameter, so the original sublinear-regret theorem is not asserted for these scenarios.

### Exact duplication at beta 0.5 and 1

| Scenario | Horizon | Total arms | Cap, beta 0.5 | Cap, beta 1 | Cap, beta 2 |
|---|---:|---:|---:|---:|---:|
| two_close | 12000 | 2 | 110 | 23 | 7 |
| few_arrivals | 12000 | 3 | 110 | 23 | 7 |
| stable | 12000 | 8 | 110 | 23 | 7 |
| successive_improvements | 14000 | 11 | 119 | 25 | 7 |
| burst | 14000 | 14 | 119 | 25 | 7 |
| membership_boundary | 14000 | 9 | 119 | 25 | 7 |
| many_close_means | 12000 | 13 | 110 | 23 | 7 |
| late_improvement | 14000 | 8 | 119 | 25 | 7 |
| rare_rewards | 12000 | 9 | 110 | 23 | 7 |
| ceiling | 12000 | 9 | 110 | 23 | 7 |
| larger_pool | 16000 | 20 | 127 | 26 | 7 |
| bounded_low_variance | 12000 | 10 | 110 | 23 | 7 |

For beta 0.5 and 1, the cap is above the total arm count in every scenario. Thus their actions are identical to kind 7 under the same data and tie rule, by induction on the rounds: the accepted sets, indices, actions and subsequent updates coincide. These are duplicate trajectories, not independent evidence or separate algorithmic wins. Beta 2 also duplicates kind 7 in the two scenarios with at most seven total arms. It truncates in the remaining ten scenarios.

## Empirical D-inf: two-observed-point closed form is correct

Primary reference: Honda and Takemura, *Non-Asymptotic Analysis of a New Bandit Algorithm for Semi-Bounded Rewards*, JMLR 16 (2015), [original paper](https://www.jmlr.org/papers/volume16/honda15a/honda15a.pdf). Algorithm 1, equation (2) and Proposition 1 appear on PDF page 5, printed page 3725. Theorem 2 on the next page establishes the equivalence for the semi-bounded model.

For target $u<1$, the implemented quantity is the paper's bounded-support divergence

$$
D_{\inf}(F,u)=\max_{0\le v\le 1/(1-u)}
E_F\log\{1+(u-X)v\}.
$$

Let the observed empirical support be $x\le y$, its weights be $p=n_x/(n_x+n_y)$ and $1-p$, and its mean be $\bar x=px+(1-p)y$. With $a=u-x$ and $b=u-y$, the objective is

$$
f(v)=p\log(1+av)+(1-p)\log(1+bv),
$$

and its derivative is

$$
f'(v)=\frac{u-\bar x+abv}{(1+av)(1+bv)}.
$$

The function is concave. If $u\le\bar x$, its maximum is zero at $v=0$. If $u>\bar x$ and $b\ge0$, it is increasing up to the admissible endpoint. If $u>\bar x$ and $b<0$, its stationary point is

$$
v_0=-\frac{u-\bar x}{ab},
$$

clipped to the admissible interval. These are exactly the branches of `empirical_dinf`. For a one-point empirical law the endpoint expression is

$$
D_{\inf}(\delta_x,u)=\log\left(\frac{1-x}{1-u}\right),\qquad x<u<1,
$$

also exactly implemented through `log1p`. This is the full bounded-support empirical divergence for the observed law; it does not assume that the unknown true distribution has only the observed support. In particular, its admissible alternatives can put probability at the known upper bound 1. It is not a Bernoulli approximation to fractional rewards.

The support-update code stores actual observed values, keeps the lower value first, transfers all previous counts when the second observed value is lower, and updates each count once before the physical sample count is increased. It raises an error on an additional distinct support point. The frozen suite has 11 Bernoulli scenarios and one two-point scenario, so the storage restriction is exact for this study and is explicitly guarded rather than silently approximated.

Kind 6 minimizes

$$
n_iD_{\inf}(\widehat F_i,\max_j\widehat r_j)+\log n_i,
$$

by maximizing its negative. It initializes unobserved current arms first. This matches IMED's empirical-best target and index, with the current arrived set substituted for the original fixed arm set. No endpoint is required. The original fixed-arm regret theorem is not claimed unchanged for arriving arms.

### Endpoint convention and numerical scope

The source identity is stated for $u<1$. At $u=1$, the implementation uses its limiting extension: zero for the empirical point mass at 1, and positive infinity for an empirical law with mean below 1. This keeps an empirical leader selectable when early Bernoulli observations are all successes. It should not be described as evaluating the literal strict-mean variational definition at $u=1$, whose feasible alternative set is empty. Values below 1 are the formula reviewed above.

Floating-point sums can differ slightly from count-weighted empirical means. The nonnegative clamp avoids small negative objective values but is not a replacement for numerical validation near 1 or at an active endpoint. This review establishes the algebra and information boundary; independent numerical optimization tests remain the parent's validation task. No runtime modification is requested by this review.

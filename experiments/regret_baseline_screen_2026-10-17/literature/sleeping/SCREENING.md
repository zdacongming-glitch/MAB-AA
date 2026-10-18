# Sleeping-bandit baseline screening

Date: 2026-10-17. Scope: stationary independent bounded-reward arms, arbitrary deterministic arrival batches, each arm permanently awake after arrival, and regret against the best currently available mean. This note records literature screening and implementation provenance; it does not modify the manuscript or tune a policy using the frozen tests.

## Decisions

| Candidate | Decision in this setting | Primary source |
|---|---|---|
| AUER | Include as a classic sleeping-UCB radius sensitivity, not a new mechanism relative to available-arm UCB1. Its original radius is larger than the usual UCB1 radius. | [Kleinberg, Niculescu-Mizil and Sharma, COLT 2008 version, Algorithm 2, PDF p. 8](https://www.cs.cornell.edu/~rdk/papers/colt08.pdf) |
| TS-SMAB | Existing Beta Thompson sampling already covers the Bernoulli scenarios; do not count an identical renamed run as another baseline. For bounded non-Bernoulli rewards, the published extension uses Bernoulli randomization, which differs from fractional Beta updating. | [Chatterjee et al., UAI 2017, Algorithm 1 and Section 3.2](https://proceedings.mlr.press/r15/chatterjee17a.html) |
| SB-EXP3-ATGT | Include the exact online unknown-horizon/unknown-arm-count version, with the unbiased estimator. Implementation is `../../sb_exp3.py`. | [Nguyen and Mehta, AISTATS 2024, Algorithm 5, Appendix F](https://proceedings.mlr.press/v238/nguyen24d/nguyen24d.pdf) |
| FTARL with half-Tsallis entropy | Not a faithful main baseline without an a priori total arm count. A known-capacity diagnostic could be labeled separately. Dynamic insertion into the simplex changes the published algorithm. Negative Shannon FTARL is equivalent to SB-EXP3, so adds no distinct comparator. | [Nguyen and Mehta, Algorithm 2, Sections 3.2 and G](https://proceedings.mlr.press/v238/nguyen24d/nguyen24d.pdf) |
| Sleeping-EXP3 | Exclude as a direct matched baseline: it estimates a fixed distribution of iid availability sets; permanent arrivals are not sampled from that model. | [Saha, Gaillard and Valko, ICML 2020, Section 2](https://proceedings.mlr.press/v119/saha20a/saha20a.pdf) |
| Sleeping FPL / Bandit-SFPL | Same availability-model mismatch: the analysis assumes stochastic action availability. | [Kanade, McMahan and Bryan, AISTATS 2009](https://proceedings.mlr.press/v5/kanade09a.html) |
| SI-EXP3 | Known finite arm universe, $K(K-1)$ experts, and an $O(K^3)$ per-round fixed-point solve; not a priority over the cheaper SB-EXP3 in this screen. | [Gaillard, Saha and Dan, AISTATS 2023, Algorithm 1 and Section 3.1](https://proceedings.mlr.press/v206/gaillard23a/gaillard23a.pdf) |
| Follow the Awake Leader | Exclude: receives every awake arm's reward, unlike our one-observation-per-round experiment. | [Kleinberg et al., Algorithm 1](https://www.cs.cornell.edu/~rdk/papers/colt08.pdf) |

The stochastic AUER and TS-SMAB comparator agrees with the best currently available mean. SB-EXP3 instead guarantees per-action sleeping regret: comparison with one fixed arm only over that arm's awake rounds. We may evaluate SB-EXP3 on the same dynamic regret metric, but its original theorem is not a theorem for our changing best-available-arm comparator.

## AUER: exact index and information requirements

For a currently available arm $i$, let $n_i$ and $S_i$ denote physical pulls and reward sum before the current pull. Choose an available unpulled arm first; otherwise maximize

$$
\frac{S_i}{n_i}+\sqrt{\frac{8\log t}{n_i}}.
$$

The numerator constant is 8 in the downloaded original COLT version. The common UCB1 expression uses 2, so these are the same mechanism with different exploration radii. Preserve old arm statistics on arrival and initialize only new arms. Neither $T$ nor a future arm count is needed. With simultaneous arrivals, unpulled arms are handled one physical pull at a time.

## TS-SMAB: what is already represented

Sample independently over current arms from

$$
\theta_i\sim\operatorname{Beta}(1+S_i,1+n_i-S_i)
$$

and select the largest sample. Bernoulli observations produce the usual posterior counts. For bounded observations $x\in[0,1]$, the cited extension first draws $B\sim\operatorname{Bernoulli}(x)$ and updates success/failure using $B$. It therefore preserves means while discarding the lower observation variance. This is distinct from adding fractional success $x$ directly. [Agrawal and Goyal, COLT 2012, Algorithm 2](https://proceedings.mlr.press/v23/agrawal12/agrawal12.pdf).

## SB-EXP3-ATGT implementation mapping

The implementation uses Algorithm 5 with $\gamma=0$. Nested availability makes the episode union equal to the current available set immediately after it is observed. New arms start at zero cumulative estimated regret. Both prescribed doubling levels reset the scores; scores are otherwise retained across arrivals.

After sampling arm $a$ with probability $p_a$ and observing reward $x$, use loss $\ell=1-x$ and update all currently available scores by

$$
L_i\leftarrow L_i+\ell-\frac{\ell\mathbf 1\{i=a\}}{p_a}.
$$

With the current doubling exponents $C,b$, sampling probabilities are proportional to $\exp(\eta L_i)$ with $\eta=\sqrt{2^{C+1-b}}$. The absolute scores must be retained: subtracting a common shift and then initializing later arrivals at zero would change the algorithm. The code applies stable softmax only when constructing probabilities.

The common runner's `n`, `S`, `Q`, `births`, and free parameter arguments do not enter the SB-EXP3 policy. Its private state is `aux`; `update_sb` is called before the runner's physical reward statistics are updated. No held-out mean, seed outcomes, future arrivals, horizon, or future arm count is read.

Validation: 80 synthetic rounds with $k=1,3,9,20$ at successive arrival batches, including both doubling resets, matched an independent direct reference for scores, normalizers, and probabilities to $10^{-10}$. This check is numerical implementation validation, not a performance experiment.

Downloaded PDFs and their SHA256 hashes are recorded in `sources.json`. No canonical author-code repository was identified from the proceedings links during this screen; `sb_exp3.py` is a fresh translation of the cited pseudocode.

# Ballooning baseline screen

Screened on 2026-10-17. This note concerns reward regret only. No manuscript content or frozen experiments were changed.

## Main eligible candidate: BL-MOSS

Ganesh Ghalme, Swapnil Dhamal, Shweta Jain, Sujit Gujar and Y. Narahari, *Ballooning multi-armed bandits*, Artificial Intelligence 296 (2021), 103485. Primary sources: [institutional full text](https://research.chalmers.se/publication/522732/file/522732_Fulltext.pdf), [author-submitted arXiv record](https://arxiv.org/abs/2001.10055), [publisher record](https://doi.org/10.1016/j.artint.2021.103485).

The full text is saved as `ghalme_2021_ballooning_fulltext.pdf`. The page images `algorithm1_page11.png` and `algorithm1_page12.png` show the MOSS definition and Algorithm 1, respectively. These are PDF pages 11 and 12, carrying printed page numbers 10 and 11. The `.txt` file is a local `pdftotext -layout` extraction for searching.

The model has bounded stationary rewards, arrivals followed by permanent availability, and regret against the best currently available arm. It is therefore directly related to the current setting. However, its formal arrival model permits at most one new arm each round, and its guarantees require a tail condition on the terminal best arm's arrival time. The time horizon and a tail parameter are inputs. These conditions are additional information, not supplied by the current deterministic test suite.

For the sub-exponential and sub-Pareto cases, Algorithm 1 sets, respectively,

$$
\alpha_{\rm E}=\frac{W(2\lambda T)}{2\lambda T},\qquad
\alpha_{\rm P}=T^{-2\beta/(1+2\beta)}.
$$

The resulting arm cap is $m=\lceil\alpha T\rceil$. Section 5.1 specifies an arrival-order cap. Conditional on the retained arms, the method uses the ordinary horizon-dependent MOSS index

$$
U_i(t)=\widehat r_i(t-1)+
\sqrt{\frac{\max\{\log(T/(kN_i(t-1))),0\}}{N_i(t-1)}}.
$$

Unobserved eligible arms are sampled before finite-index arms. Ties may be broken by any rule; the numerical implementation should use the existing replicate's label order and should not consult means.

### Honest batch adaptation

The suggested name is **BL-MOSS-countcap-P(beta=...)**. At round $t$:

1. Sort arrived arms by arrival time, with the existing fixed arm label as the within-batch tie breaker.
2. Retain the earliest $m$ arms, or all arrived arms if fewer than $m$ have arrived.
3. Use the MOSS index above on the retained set, with $k$ equal to its current size.
4. Observe exactly one reward and keep all historical statistics. Ignore arrivals outside the cap.

Step 3 follows the original calls to MOSS on the current accepted set. The original MOSS definition uses its arm-set size in the denominator. Using the eventual cap in the denominator before that many arms are available would be a different adaptation. There is no instruction in the paper to reset the statistics after each call.

Algorithm 1 contains a time/set notation ambiguity away from its dense one-arrival-per-round illustration: it compares the current number of arms with the cap but then refers to the arm set at the cap's time index. Section 5.1 resolves the intended selection as an arrival-order cap. The count-cap adaptation above makes the batch behavior explicit instead of claiming that the paper already specifies arbitrary simultaneous batches.

Predeclared Pareto sensitivity values $\beta\in\{0.5,1,2\}$ yield

$$
m_{0.5}=\lceil T^{1/2}\rceil,\qquad
m_1=\lceil T^{1/3}\rceil,\qquad
m_2=\lceil T^{1/5}\rceil.
$$

These values are sensitivity settings, not estimates of a true tail distribution. They must be shared across all scenarios, with no choice made after viewing test regrets. If the cap exceeds all available arms, the method reduces exactly to the corresponding horizon-dependent growing-set MOSS implementation; this duplication should be reported rather than concealed. The sub-exponential formula is also implementable, but choosing its parameter from test arrival times or from the known best arm would give privileged information.

A birth-time cutoff can be examined separately, but it is not the same count-cap adaptation when arrivals are sparse or batched. It is not recommended as the main implementation under the BL-MOSS name.

## Screened but not added as distinct main baselines

| Method or family | Primary source | Reason |
|---|---|---|
| BL-UCB / BL-TS / BL-KL-UCB | Ghalme et al. (2021), immediately after Algorithm 1 | The paper mentions replacing the internal learner as future work. It does not give these methods as separately defined classical algorithms with tuned cutoff formulas. Do not present them as established baselines. |
| Double-UCB-BL / Conservative-UCB-BL | [Qi et al., author-submitted v2](https://arxiv.org/abs/2501.14314v2) | They use a similarity feedback graph: pulling one arm reveals rewards of neighbors. Even the variants that learn graph structure use the richer observation model. Giving these observations would violate the current one-observation setting; deleting them would change the published algorithm. |
| UCB-L / AG-L | [Traca, Rudin and Yan, PMLR 115 (2020)](https://proceedings.mlr.press/v115/traca20a.html) | The distinct mechanism uses an arm's known or estimated remaining lifetime. Current arms do not die. Substituting an arbitrary artificial expiration time would introduce a different setting. |
| Streaming bandits with limited arm memory | [Li et al., author-submitted paper](https://arxiv.org/abs/2306.07903) | They restrict memory and may allow multiple passes through an arm stream. The current experiment retains all available arms and observations. This is a different resource model. |
| Infinite-reservoir methods | Ghalme et al. (2021), Section 1.1 and related work | They normally let the learner draw fresh arms from a quality reservoir. Here arrivals are exogenous and qualities and times are fixed by each scenario. No reservoir prior or sampling oracle should be supplied. |

The newer graph-feedback paper is saved as `qi_2025_graph_feedback_v2.pdf`; the mortal-bandit paper is saved as `traca_2020_mortal.pdf`. These were inspected to verify the exclusion reasons. The search did not establish that another distinct BL-UCB algorithm is a standard baseline. This is a bounded literature screen, not a proof that no other algorithm exists.

## Practical conclusion for this experiment

Implement BL-MOSS count caps as the directly relevant ballooning family, explicitly mark the batch adaptation and tail-parameter mismatch, and add strong stationary reward baselines from their own primary papers through the separate screen. Distinct names alone do not justify extra baselines when their action rule reduces to an existing method.

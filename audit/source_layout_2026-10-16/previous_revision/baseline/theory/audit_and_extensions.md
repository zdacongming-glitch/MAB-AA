# Independent theory audit and extensions

Date: 2026-10-15. Status: **complete proofs within the explicitly stated families**; the general instancewise frontier remains open. The audit follows the user-invoked theorem-proving skill, its proof protocol, and its adversarial audit. It does not certify novelty or replace external review.

## Scope and assumptions

The audited source is the complete 2026-10-14 continuous-maintenance research folder, including its Chinese theorem record, `cp_ucb_aa.py`, `diagnostics.py`, and existing audit. The underlying model has independent stationary reward streams in $[0,1]$, deterministic exogenous permanent arrivals, finite numbers of arms at finite times, and one adaptively selected observation per physical round. Reports follow the current observation. Reliability is simultaneous familywise coverage over the entire time axis. Area counts unresolved arm--time pairs outside the boundary band. Regret is pseudo-regret relative to the best currently available mean.

No theorem below imports the temporal-geometry paper. The candidate signs used in lower bounds form one compatible product prior; independent references do not encode those signs. No result conditions old observations into fresh independent data.

## Audit decisions

| Source result | Decision | Important restriction or repaired presentation |
| --- | --- | --- |
| T2 and L2 | Accepted in the stated range | Select the hard arm from expected counts, hence as a deterministic label. All times use the same reference environment. Subtract final service rounds of busy periods because reports are after observations. |
| L3 | Accepted with the documented finite two-way KL assumption | Posterior coordinates factorize after the action and stopping kernels cancel. Counts need not be independent. For small $m$, use the coordinate-flip bound rather than the large-$m$ logarithm. |
| T4 | Accepted | The area-success event forces completion in enough windows; this is not an extra deadline axiom. All windows use the same prior, and distinct candidate observations are charged once. |
| T5 | Accepted on its separated-window family | The condition $H_e\ge2S_e$ is required for birth-window quota charging. Reference identities are unknown to the algorithm. Exclusion does not disable the UCB reward layer. |
| T6 | Accepted on its explicitly chosen horizon | The rapid-maintenance upper bound uses the pathwise $R_T\le2\varepsilon T$ and $T$ proportional to fine-checkpoint work. It does not extend unchanged to arbitrarily long windows. The loose endpoint has an upper bound, not a matching lower bound. |
| T7 | Accepted for eventually finite arrivals and strict boundary separation | Raw revisable intervals are necessary for almost sure correction of early errors. A fixed-confidence irreversible rule alone would not prove almost sure consistency. |
| T8 | Accepted | The lower bound is a first-round static burst; the upper bound accommodates arbitrary arrivals. This is worst-schedule area optimality, not a solution for each individual schedule. |
| T9 | Accepted with its quantifiers | The adverse reward environment may depend on the selected endpoint. The theorem concerns an envelope uniform over environments on one fixed schedule. |

No fatal mathematical counterexample was found within these claims' stated assumptions. This assessment is independent of the source's internal numerical diagnostics; those diagnostics are not universal proofs. The supplementary file supplies full English derivations rather than treating the Chinese audit as a mathematical dependency.

## New result 1: a regret-quantile lower bound under the existing area protocol

In the repeated-update family, put $V=JMH$. If a policy is reliable and satisfies

$$
P_\sigma(E_{\rm lab},\mathcal A_T(\eta)\le V/8)\ge1-\delta
$$

for every sign configuration, then one fixed configuration satisfies

$$
P_\sigma\left(R_T\ge2^{-20}\frac{\varepsilon JM}{d^2}\log\frac M\delta\right)\ge\frac{11}{80}.
$$

This is stronger in probability mode than the source's expected-regret lower bound. Since $11/80>\delta$ for the permitted $\delta\le1/16$, it also yields a matching-order lower bound for a joint high-probability regret-and-area criterion. The source's rapid strategy supplies a deterministic regret upper bound at its specified horizon, so the rapid endpoint closes under that stronger common risk criterion as well.

The key budget lemma uses

$$
L=\frac{m\log(m/\delta)}{1024\kappa},\qquad q=\lfloor L/2\rfloor.
$$

If $L\ge4$, the probability of completing half of a batch with at most $q$ candidate observations is less than one half. Stop at the first half-completion, the endpoint, or the $(q+1)$st candidate sample. Its candidate sample count is at most $q+1<L$. The partial-recovery lemma therefore precludes half-completion with probability one half. A direct stop at the $q$th sample would be wrong: reference observations acquired later could determine candidates without changing the candidate count.

On area success, at least $3J/4$ windows complete. The expected number of cheap completions is at most $J/2$. Markov's inequality gives probability at least $1/5$ that at most $5J/8$ completions are cheap. Intersecting with area success costs only $\delta$, leaving $11/80$. At least $J/8$ windows then use more than $L_0/2$ candidate samples, with $L_0=M\log(M/\delta)/(32768d^2)$. Every such sample loses at least $\varepsilon/2$. This proves the constant $2^{-20}$ without any independence assertion between completion events.

Full theorem, proof, and quantile-frontier corollary: `extensions.tex`, labels `lem:budget_completion`, `thm:quantile_lower`, and `cor:joint_quantile`.

## New result 2: compatible window truncation on arbitrary horizons

For a compatible family of sign-classification tasks, let batch $e$ have $m_e$ candidates, a validity window of length $H_e$ starting at that batch's arrival round, and two-way KL at most $0<\kappa_e<\infty$. Set

$$
h_e=\min\left\{H_e,\left\lceil\frac{m_e\log(m_e/\delta)}{1024\kappa_e}\right\rceil-1\right\},\qquad S=\sum_e m_eh_e.
$$

When $S>0$, one fixed full configuration satisfies

$$
P(\mathcal A_T(\eta)\ge S/8)\ge1/7.
$$

All windows must be realized by a single experiment and all counted candidate--time pairs must have boundary distance exceeding $\eta$. Overlap is allowed for distinct arms when their relative-goodness structures can coexist. The proof adds expectations under the one common prior and then uses a bounded-variable probability argument. It does not add the worst environments of incompatible tasks. This extension formalizes horizon truncation and multiple task expirations; it is an auxiliary strengthening rather than a claim to a complete instance complexity.

## Unclosed obligations

1. A computable matching frontier for arbitrary overlapping arrivals and heterogeneous boundary distances is not established.
2. The coarse endpoint's logarithmic-in-horizon regret upper bound is not accompanied by a matching lower bound in this family.
3. Automatic selection of the optimal service precision without known scale parameters remains unproved.
4. No strict advantage over every history-retaining ALL-epsilon adaptation is shown.
5. An eventually finite, exactly-on-boundary arm is excluded from the complete-classification conclusion; uniform finite-time exact boundary classification is not claimed.

## Adversarial checks

The proof was rederived with post-observation report timing, noninteger half-batch thresholds, $J=1$, $M=2$, arbitrary dependence of completion events across windows, and later reference observations after candidate sampling stops. The quantile proof uses only the same area-success event and a common prior. A fixed configuration is selected only after the complete multiwindow probability bound. The stopped candidate count includes the one-sample overshoot and is strictly below the recovery threshold. All constants are universal in the stated parameter range.

Markdown formula delimiters in this file use single-dollar inline formulas and standalone double-dollar display delimiters.

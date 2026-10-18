# P16 English integration: independent interface review

Review date: 2026-10-17. Scope: the `s12` and `s13` strings in `retained_supplement.json`, compared directly with `frontier_research_2026-10-16/theory_frontier.md` and `proof_audit.md`. This is an additional source and proof-interface review during manuscript integration. It is not external peer review, a formal proof certificate, or a claim that all results of the three research packages have been independently verified. No research input, integration JSON, or main manuscript was edited in this review.

Status: no substantive transcription error or BLOCKED_PROOF_INTERFACE found in these two sections. The conditions, constants, information distinctions, and bad-event treatment requested in the revision plan are retained.

## S12: schedule information and the two feasibility witnesses

The English statement uses the same three Bernoulli means, $\varepsilon=1/8$, $v=1/32$, $0<\delta\le1/16$, $0<d\le1/1024$, and $\eta=d/2$. The definitions of $Q_f,h,L_d,w,a,T$ agree with the research source. The early and late arrival times are $h+1$ and $T$; endpoint, task parameters, area budget, and final arm count coincide.

The lower proof only transfers a distribution across schedules through physical time $h$. At $t_0=a+1$, failure to have ever classified candidate 1 costs $a+1$ area in the late schedule. Joint success therefore supplies an event $F$ with $P_-F\ge1-\delta$ and $P_+F\le\delta$. Binary KL gives $E_-N_1(t_0)\ge L_d$. Removing the $w+1$ subsequent slots gives $E_-N_1(h)\ge L_d/2-1$. In the early negative world every such common-prefix pull costs at least $\varepsilon$. No new reference information is used before it exists.

Both feasibility arguments remain present. The late fine witness uses at most $4Q_f$ rounds and area $8Q_f+3<a$ for small $d$. The early coarse witness keeps $Q_c=\lceil128v^{-2}\log(48/\delta)\rceil$ independent of $d$, gives area at most $h+10Q_c\le h+w$, and has at most $3Q_c$ designated observations plus $O_v(\log T)$ ordinary UCB cost. All comparisons use confidence intervals valid on the full bounded model, not labels supplied by knowledge of the performance family. The English text correctly restricts feasibility and the comparison upper bound to sufficiently small $d$.

The statement does not equate a policy optimized separately for each known schedule with a single policy facing an unknown schedule class. It expressly preserves the existence of the latter causal minimax problem. The subsequent finite-spectrum-protection paragraph is a compatibility consequence of the older rapid lower bound; it does not transfer that lower bound or its witness to F-CCP.

Optional clarification for the integrating author: immediately before the first occurrence of the schedule-informed value, add ?Let $\Theta$ denote the two sign environments just specified.? The current definition is recoverable from the displayed $\sigma\in\{-1,+1\}$ family; this is a local notation clarification, not a mathematical blocker.

## S13: arbitrary-subset recovery

The statement preserves independent uniform sign coordinates, finite two-way KL, arbitrary interleaving, independent policy randomness, bounded stopping, and a bound on any reported error under every fixed sign configuration. Its recovery event is $\overline P(|S|\ge s)\ge1/2$, and its lower bound is $s\log(s/\delta)/(48\kappa)$.

The proof conditions on the complete stopped history, so action, stopping, and reporting kernels are common factors and cancel. The likelihood factors by sign without requiring random sample counts to be independent. Including the report/randomization state in that history makes a data-selected set $S$ legitimate. The conditional complete-correctness probability is bounded by the product of the selected posterior maxima. Thus Markov's inequality and the recovery event intersect with probability at least $1/4$.

The information-drift calculation uses the nonnegative conditional expectation

$$
E(\sigma_iL_i\mid H_\tau)=f(e_i),\qquad f(e)=(1-2e)\log((1-e)/e).
$$

Direct differentiation gives $f''(e)=1/[e^2(1-e)^2]$. The required monotonicity, Jensen step, and $k\ge s$ comparison are valid for $0<e\le1/2$. With $v_\delta=-\log(1-4\delta)\le16\delta/3$, the constants follow from

$$
f(v_\delta/s)\ge\frac13\log\frac{s}{8\delta}\ge\frac1{12}\log\frac{s}{\delta},\qquad s/\delta\ge16.
$$

Multiplication by $1/4$ gives $1/48$. No subtraction by the full number of coordinates is introduced, and finite two-way KL with bounded stopping controls likelihood-increment integrability. This checks the small-$s$ interface rather than substituting the older half-recovery result.

The area lower bound retains only first definite labels within the candidates' own validity windows. It still charges all later candidate observations in the KL count; each retains regret at least $\varepsilon/2$. Combining $\kappa\le32d^2$ with $1/48$ and the gap cost gives the exact $1/3072$ constant. The impossibility case is included by assigning infinite value to an infeasible budget.

## S13: ABM activation and unconditional reward interface

The algorithm receives a fine-candidate budget $s$, not $T,H,J,M,K$, future arrivals, true means, or reference identities. Coarse confidence allocations are by arrival rank. After a batch's coarse data choose its empirical best and fine candidates, new fine allocations are by activation rank. Fine blocks start strictly after activation; in particular, the observation triggering activation is excluded. Ordinary UCB observations can contribute only if that task was already active before the observation. This is the predictable fresh-suffix interface needed for the conditional Hoeffding bound. Existing observations remain in reward estimates and coarse evidence but are not recycled as newly selected fine prefixes.

The task count is at most $s$ candidates plus at most $s$ references. Queue ordering, one actual pull per round, saved interval intersections, and persistent all-unresolved reporting on empty intersections are specified. Queue and reward operations remain defined on failed-report paths. Thus the finite service counts used in the expectation bound are not restricted to coverage success.

The workload and window quantities match the source: $Q_c$, $Q_f(r)$, $L_c=2(M+1)Q_c$, $L=L_c+2(M+1)Q_f(2m)$, and the renamed recovery constant

$$
B_{\rm rec}=L_c\left\{\frac{(J+1)(J+2)}2+JM\right\},\qquad H\ge4(L+B_{\rm rec}).
$$

The change from source $B$ to $B_{\rm rec}$ removes a symbol conflict only. The sufficient-window argument prevents backlog before a new batch. Coarse coverage identifies the true reference, fine coverage resolves selected signs because $2\rho_f<d$, and $d+2\rho_c<v$ removes the preceding cohort by saved evidence. The recovery-area sum equals $B_{\rm rec}$. The nonselected candidates retain their own-window $H$ charges.

The expectation proof preserves

$$
R_0(T)=2\varepsilon KQ_c+128\left(\frac m\varepsilon+\frac{J^2}{v}\right)\log(2T)+1
$$

and the additional $4\varepsilon sQ_f(2s)$ term. It counts coarse and designated fine samples pathwise and applies full-history UCB counting to the remainder, with summable bad-round loss. It never conditions the expected regret on confidence success, so no hidden $\delta T$ term is omitted. The candidate/reference gap bounds used for the constant 128 agree with the performance family; ABM does not inherit a spectral MC-MOSS reward claim.

## S13: intermediate interval and limits

The English theorem retains $A_{\min}=mL+B_{\rm rec}$ and the entire stated interval $A_{\min}\le a<V$. Its calibration

$$
s(a)=\left\lceil\frac{V+B_{\rm rec}-a}{H-L}\right\rceil
$$

satisfies $1\le s(a)\le m$ and $s(a)\le2k(a)$. The upper constant chain $Q_f(2s)\le97d^{-2}\log(s/\delta)$, $388$ to $970$ to $1024$, is preserved. The additive $R_0(T)$ is retained throughout. The explicitly calibrated choice $H=16(L+B_{\rm rec})$ gives the quoted $A_{\min}/V\le3/32<1/8$, using $m=JM\ge2$.

The final qualifications are accurate: this result leaves $a<A_{\min}$, $[V,V+B_{\rm rec})$, arbitrary overlapping arrivals, and the full unknown-schedule frontier open. The operational procedure given $s$ is future-free, while selecting $s(a)$ uses the performance-family values $m,H$. The conditional fixed-parameter asymptotic remark does not suppress $R_0$ in joint growth regimes. No part of this theorem is attributed to F-CCP.

## Snapshot identities

- `frontier_research_2026-10-16/theory_frontier.md`: SHA-256 `b1d14cc64e3b64fc7594576b987b77f411d4bfaab74dc81233bdc6a9494c63b5`.
- `frontier_research_2026-10-16/proof_audit.md`: SHA-256 `d65a0b147c48fcaf4ffda2efced38652932901baaa70b9aeead12b2538ede92d`.
- Reviewed integration JSON snapshot: SHA-256 `91b3d247a2d22952a4fc126b1f810f992e1a71984af36c1ad840c65c73d42e38`; only fields `s12` and `s13` were reviewed.

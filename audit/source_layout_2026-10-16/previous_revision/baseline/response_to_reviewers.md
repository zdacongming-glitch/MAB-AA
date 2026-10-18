# Response to the review reports

Working draft, 15 October 2026. This document accompanies a revision based on the original UCB-AA paper for JASA Theory and Methods. It retains the original arriving-arm setting, regret objective, statistical motivation, and two-stage screening architecture. The disputed arguments are replaced by an analysis of actual sample counts; reliable set maintenance is developed as a further main-text contribution within the same model. The numerical evidence distinguishes the original archived implementation from the new reporting construction. The repaired UCB-AA procedure has not yet been rerun. Page and line references are omitted until pagination is final.

The detailed report supplied in `Reviews_JASA-RA-2026-0866.pdf` contains a Summary, Major Comments 1(a) to 4(c), and two Minor Comments. It does not identify a referee number in the document. We answer that report first. A separate section addresses the sleeping-bandit and novelty concerns recorded in the earlier response materials. Those materials are an author's summary and working response, not a substitute for the verbatim earlier report or decision letter.

The source references used below are:

| Main-text section | Source label |
|---|---|
| 1. Introduction | `sec:introduction` |
| 2. Multi-armed bandit problem with arriving arms | `sec:model`, `sec:problem` |
| 3. UCB for Arriving Arms (UCB-AA) | `sec:algorithm` |
| 4. Regret lower bounds in representative arrival regimes | `sec:retained_regret_lower_bounds` |
| 5. Reliable maintenance of the near-optimal set | `sec:reporting_task`, `sec:method` |
| 6. The burden of continual certification | `sec:maintenance` |
| 7. Temporary membership questions and their regret cost | `sec:tradeoff` |
| 8. Numerical studies | `sec:numerical`, `sec:experiments` |
| 9. Discussion | `sec:discussion` |

The result labels include `thm:ucbaa_main_fixed_budget`, `thm:retained_distractors`, `thm:retained_progressive`, `prop:reporting`, `thm:broadcast`, `cor:growth`, `thm:worst_area`, `thm:reuse`, `thm:tradeoff`, and `thm:quantile_main`. The physical-time restart proof is in the supplement. This source index is provided for the authors' final cross-reference check and can be removed from the submitted letter.

## Opening response

We thank the reviewer for the careful analysis and the independent implementation. The report identifies substantive problems in the submitted proofs, as well as discrepancies between the algorithm, the simulation specifications, and the interpretation of the results. We agree that these problems cannot be resolved by clarifying notation alone.

The revision retains the stationary reward model with exogenous permanent arrivals and regret relative to the best currently available arm. It also retains arrival information discrepancy (AID), the drifting benchmark (DB), and UCB-AA's preliminary screening followed by formal elimination. Section 3 replaces the defective proof with an analysis at a fixed physical budget that charges actual sample counts and keeps admission delay explicit. Section 4 retains the static, distractor, and progressive lower-bound mechanisms, with their assumptions and feasible parameter ranges stated.

Sections 5 to 7 add a reporting task: identify which available arms are certified as relatively near optimal, certified as outside that set, or unresolved, with joint correctness over arms and time and an explicit cost for unresolved time. This develops the statistical purpose of screening beyond internal active-set size. CP-UCB-AA is a separate construction for its upper bounds. It admits arms at every sampling time and interleaves prespecified checkpoint certification with full-history UCB. All available arms remain eligible for reward selection, including negatively reported arms. Its reporting guarantees do not replace the regret guarantee for the two-stage UCB-AA algorithm.

We withdraw the proofs and guarantees as originally justified by the defective decomposition, the $G_3$ gap compression, the data-dependent elimination-chain bound, and the auxiliary-stage conversion. The repaired UCB-AA bound uses none of these steps. The additional maintenance results quantify the effect of one uncertain arrival on old reports, worst-case unresolved area, and the regret cost of prompt versus deferred classification in a specified multiple-update family. A fixed-probability regret lower bound uses the same rapid-service requirement. These additional results remain substantive main-text contributions, restricted to their stated parameter ranges and instance classes.

Section 8 retains the original two scenarios and their archived results, including favorable and unfavorable comparisons, and separately reports 5,760 reporting-study runs: four environments, nine methods, and 160 replications per environment-method pair at $T=20{,}000$. Those runs expose substantial costs of conservative checkpoints. A confidence-based all-near-optimal adaptation improves both regret and unresolved area in two environments, while Growing MOSS has the smallest mean regret in all four and leaves larger unresolved areas. These are experiments on the reporting constructions; neither the archived results nor the new CP study constitutes a rerun of repaired UCB-AA.

## Detailed report: Major Comment 1(a)

The reviewer observes that $D_M=R_{T_0}-R_M$ includes loss from earlier elimination as well as loss from delayed admission.

We agree. Let $B_m$ be the active set at the beginning of an original round, let $\mathcal{A}^{\mathrm{adm}}_m$ contain all arms admitted by then, and write $L_m$ for the round length. The correct pathwise identity is

$$
R_{T_0}
=R_M
+\sum_m\sum_{t\ \mathrm{in\ round}\ m}
\left(\max_{i\in\mathcal{A}_t}r_i-\max_{i\in\mathcal{A}^{\mathrm{adm}}_m}r_i\right)
+\sum_m L_m
\left(\max_{i\in\mathcal{A}^{\mathrm{adm}}_m}r_i-\max_{i\in B_m}r_i\right).
$$

The second sum is the arrival-delay contribution. The third sum is the loss of an admitted benchmark through earlier elimination. Defining their sum as $D_M$ is algebraically valid, but identifying that sum with arrival increments alone is not. The third term may remain positive when arrivals cease. Small error probabilities do not remove the term from the identity, and with a random completion time they do not justify replacing its expectation by a product of an expected horizon and an error probability.

We therefore do not retain Proposition 1 or Theorem 2 with their original justification. Sections 2 and 3 state the complete three-part account at actual physical endpoints. For the repaired UCB-AA comparisons, a best admitted arm survives on one simultaneous prefix-coverage event, so the historical-loss term is zero on that event. The expectation bound explicitly charges the complementary event by $\delta T$. Admission delay remains a separate nonnegative term, including the last unfinished round. The distinct CP construction in Section 5 has no admission or reward-retirement loss on any path because every available arm remains eligible for reward selection.

## Major Comment 1(b)

The reviewer requests separate numerical accounting for learning within rounds, delayed admission, and earlier elimination.

The new reporting study implements this accounting for Batch100-UCB, the short-admission confidence-retirement comparator described in Comment 2(b). Section 8 records the within-active learning loss, admission delay, and deficit from earlier reward retirement on the same realized path. The admission-delay contributions in the four environments are $0$, $33.92$, $16.00$, and $22.40$. No deficit from historical retirement occurred in these runs. Across all 5,760 runs, the largest discrepancy between total regret and the sum of the three recorded components was below $3.1\times10^{-12}$.

For methods that admit immediately and retain every available arm for reward selection, the admission and retirement terms are identically zero. The released records also separate designated certification pulls and their regret from reward-selection pulls, and include unresolved paths and report errors. A negative report is not counted as a reduction in the reward policy's available set. The original figures and endpoint records are preserved as archived evidence, but do not contain the complete three-part accounting. Repaired UCB-AA has not yet been rerun, so this requested numerical check remains to be completed for that procedure.

## Major Comment 2(a)

The reviewer shows that exponentially increasing round targets can place the later rounds far beyond a budget of 60,000 pulls.

We agree with the distinction between selecting a terminal round index and reaching it within a given sampling budget. The original resolution is $2^{-m}$, and its target grows on a $4^m$ scale. Consequently, a larger prescribed $M$ does not imply that later rounds are observed in a fixed-budget experiment. The original theoretical calibration of $N$ can increase this mismatch further.

The repaired UCB-AA analysis in Section 3 fixes a deterministic physical budget $T$. It retains the original target formulas but specifies

$$
M_T=\left\lceil\tfrac12\log_2(T+1)\right\rceil,\qquad
N=8T4^{M_T}/\delta,\qquad
n_p=\left\lceil2\cdot4^p\log(N4^{-p})\right\rceil.
$$

Each $n_p$ is a cumulative sample target. The algorithm stops at the actual pull $T$, including inside a phase, and makes no elimination based on an incomplete phase. Since $n_{M_T}>T$, the finite phase range covers the execution. This does not presume that the prescribed rounds have been completed. The original theoretical and smaller empirical calibrations are distinguished from this repaired calibration. Its regret bound contains both actual-count learning cost and explicit arrival delay; a large target is not interpreted as work already performed.

The separate checkpoint experiment in Section 8 also displays the cost of conservative targets. For eight arms, the total quotas are 73,083 at $\rho=.04$ and 8,123 at $\rho=.12$. In all 640 fine-precision runs, every available arm stays unresolved at every time step. The final five-to-eight counts in the charged metric exclude arms inside the boundary band; they do not indicate successful classifications. The coarser configuration retains label reliability but does not guarantee completeness at $\eta=.10$. These reporting results neither validate nor invalidate the repaired two-stage procedure.

## Major Comment 2(b)

The reviewer questions the long admission intervals and suggests a short-interval UCB policy with confidence elimination.

We agree that waiting for an increasingly long elimination round is a design choice, rather than an observation constraint. We retain the original preliminary-screening and formal-elimination architecture, but remove the unsupported claim that its saved exploration always compensates for buffering. Section 3 charges the resulting arrival delay explicitly and states the sufficient condition needed for it to be sublinear. The fixed-budget learning bound alone does not imply sublinear total regret under arbitrary arrivals.

We also agree that simple UCB with a sound reporting or elimination layer is an essential comparator. Our contribution is not the observation that confidence bounds can screen an inferior arm. Permanent availability means that a valid certificate of inferiority to an already available arm remains valid later. What changes for positive near-optimality reports is the reference level: an uncertain new arm can prevent many old arms from being certified relative to the current best, even when the old means and observations have not changed.

Sections 5 to 7 additionally quantify this shared reporting burden and the regret cost of meeting specified timeliness requirements. A competing policy with the same reporting obligation can reuse the same evidence. The reporting study in Section 8 includes full-history UCB with a checkpoint report, UCB with full-prefix confidence reports, a retained-history ALL-$\varepsilon$ adaptation, and Batch100-UCB with short admission intervals and confidence retirement. Batch100-UCB admits at pulls $1,101,201,\ldots$ and reports on all arrived arms, including those waiting. The ALL-$\varepsilon$ rule is an adaptation, not FAREAST or $(\mathrm{ST})^2$. These comparisons are relevant to reporting costs. A matched short-interval comparison and no-pre-elimination ablation for the repaired original UCB-AA procedure still require new runs.

## Major Comment 2(c)

The reviewer observes that the completed auxiliary stage may require far more pulls than the actual experiment.

We agree. The old proof bounds regret by extending an unfinished stage, then defines $T$ using the expected length of that extension. It does not establish a comparable bound in the actual number of pulls. In particular, doubling a round index is not doubling a sample budget when the final sample target contains $4^{2^\ell}$. We withdraw the interpretation of Corollary 2 as an anytime bound in the actual budget.

For UCB-AA, Section 3 and its supplement replace that argument with epochs of actual physical budgets $1,2,4,\ldots$. Each epoch restarts the two-stage procedure, allows all then-available arms to re-enter, and uses fresh within-epoch observations and its own error budget. The last epoch is truncated at the actual endpoint. The statistical costs and epoch admission delays are summed directly; no virtual observations or completed auxiliary stage are used. This wrapper does not retain observations across restarts. Separately, CP-UCB-AA in Section 5 runs indefinitely without restarts and has simultaneous reporting reliability. None of these statements turns a pointwise expected-regret bound into an arbitrary-stopping-time bound.

## Major Comment 3(a)

The reviewer identifies an invalid change of index in the $G_3$ bound and provides a counterexample satisfying the stated gap stability assumption.

We agree. The defining relation compares $\widetilde\Delta_{\widetilde m_i}$ with $\Delta_i(m_i)$; it does not compare $\widetilde\Delta_{m_i}$ with that gap. In the $G_3$ case the two indices can be far apart. The submitted compression can therefore understate samples acquired at a small historical gap before a later large benchmark increase. The counterexample directly invalidates that intermediate inequality under the stated assumptions.

We withdraw Corollary 1 and the simplified conclusions that depend on this step, including the affected online derivation. We do not describe this as a typographical correction, and we do not replace the missing argument with a stronger gap condition chosen after seeing the counterexample.

The repaired UCB-AA proof in Section 3 charges the actual lifetime count. A new arm sampled in phase $p\ge1$ has survived the preceding comparison in the same round, so its roundwise gap is at most $4b_{p-1}$. Incumbents already have the target count in formal phase $m-1$; their new phase-$m$ observations follow a comparison against the current merged active set and obey the same bound. The $n$th observation is thus charged at most $4\sqrt{(2\log N+1)/n}$. Summing these distinct charges gives an $8\sqrt{(2\log N+1)K_TT}$ learning bound, with separate admission delay and failure-event cost. This proof retains the screening design and uses no terminal-gap compression. The additional Section 7 construction distinguishes the regret gap of order $\varepsilon$ from the smaller membership-boundary distance $d$; that is a different, reporting-specific statement.

## Major Comment 3(b)

The reviewer observes that controlling a fixed elimination sequence does not control the event that some data-dependent sequence occurs.

We agree. The bound on an intersection along a fixed sequence is valid, but taking the maximum over sequencewise bounds is not a probability bound for their union. The subsequent numerical optimization lemma does not repair this logical gap. We withdraw the error control that depended on Equation (30).

The repaired UCB-AA proof uses one simultaneous event for the actual potential prefixes $\hat r_i(n_p)$. At most $T$ arm streams are first observed before physical endpoint $T$. Independence of an unrevealed stream from the history that first selects it and Hoeffding's inequality give the global bound $8T4^{M_T}/(3N)\le\delta$. This covers the adaptively retained references and candidates without enumerating elimination chains. For the distinct reporting proposition in Section 5, $q_i$ is fixed before observing arm $i$'s rewards, and an index-summable allocation gives

$$
\Pr\left(\exists i:\left|\hat r_i(q_i)-r_i\right|>\rho/2\right)
\le\sum_{i\ge1}\frac{\delta}{2i(i+1)}=\delta/2.
$$

Adaptive sampling changes when the checkpoint is reached, not which prefix of that arm's reward stream defines the estimate. On this single event, all reports follow by deterministic interval comparisons at every time. There is no selected elimination chain whose probability is replaced by a maximum.

## Major Comment 3(c)

The reviewer identifies inconsistent definitions of the roundwise optimal arm and a comparison against an eliminated reference that the algorithm does not make.

We agree with both points. An arm defined to belong to $B_{m_i}$ cannot simultaneously have been eliminated before that set was formed. Defining the reference instead over all admitted arms does not, on its own, establish Equation (18): a stored estimate is not necessarily an estimate used in the actual comparison. We withdraw that event inclusion and its consequences.

Sections 2 and 3 distinguish the active-set best $r_{*(m)}=\max_{i\in B_m}r_i$ from the best mean among all admitted arms. The repaired proof preserves an admitted best arm on the common coverage event using the actual comparison rule. Preliminary comparisons use observed incumbent prefixes and the remaining new arms; formal comparisons use the merged active set. No stored but unused eliminated reference is invoked. The separate reporting task in Section 5 uses $\mathcal P_t,\mathcal N_t,\mathcal V_t$, distinct from $B_m$ and $C_m$. Its frozen intervals $[\ell_i,u_i]$ are initialized to $[0,1]$, and every report uses

$$
\underline r^*(t)=\max_{j\in\mathcal{A}_t}\ell_j,\qquad
\overline r^*(t)=\max_{j\in\mathcal{A}_t}u_j,
$$

$$
\mathcal P_t=\{i\in\mathcal{A}_t:\ell_i\ge\overline r^*(t)-\varepsilon\},\qquad
\mathcal N_t=\{i\in\mathcal{A}_t:u_i<\underline r^*(t)-\varepsilon\}.
$$

These reporting comparisons belong to CP-UCB-AA, whose reward-selection steps maximize over all of $\mathcal{A}_t$. Its compiled implementation was checked against the supplied CP `choose/observe/report` reference for 20,000 successive steps: actions, service indicators, counts, and labels agreed. This validates that implementation interface; it is not a parity check or numerical validation of the repaired original UCB-AA algorithm.

## Major Comment 4(a)

The reviewer asks for a balanced comparison with Growing MOSS and evidence for the value of a smaller active set.

We agree that the submitted evidence does not show an overall regret advantage over Growing MOSS. We remove statements that treat the original experiments as demonstrating uniform superiority or a uniformly modest price for screening. A smaller internal set alone does not establish reduced storage, less computation, correct exclusion, or complete evaluation of all arrivals. In particular, an arm that was never admitted cannot be counted as statistically eliminated.

The revised reporting task supplies a measurable statistical benefit: reliable knowledge of the current relative near-optimal set with an explicit cost for unresolved reports. Its cost is assessed jointly with regret. A reward-only baseline is informative about the price of reporting, but it is not required to meet a task it was not designed to perform. Comparisons of service efficiency must attach the same reporting requirement to the competing reward policies or use a set-identification baseline with the same reliability target.

The archived comparisons are retained in Section 8 with their actual implementation identity. UCB-AA has mean regret 5139.94 against Growing MOSS-t's 2036.72 in Scenario C, and 1880.88 against 2043.75 in Scenario E. Its regret and wasted pulls improve on the archived UCB, naive-elimination, and dynamic-SE methods in both scenarios. These favorable observations remain, alongside the large disadvantage against MOSS in C. The finite-round archive stops admitting later arms, so its small survivor pool does not establish screening coverage for every arrival or verify the repaired implementation.

The additional separation in Section 7 compares fast and deferred configurations on the same arms, arrivals, endpoint, tolerance, and error probability, with different permitted maintenance areas. The rapid endpoint has matching bounds; the deferred endpoint has an achievable upper bound. It quantifies the cost of requested reporting speed, rather than proving dominance of either algorithm under the same service budget.

The separate CP study in Section 8 is unfavorable to any claim of uniform checkpoint superiority. Under a stable benchmark, coarser CP-FIFO has mean regret 3629.9 and unresolved area 49,718; ALL-$\varepsilon$ adaptation has 1367.8 and 11,306. The paired differences, CP-FIFO minus the adaptation, are 2262.1 (Monte Carlo standard error 11.7) for regret and 38,411.7 (standard error 241.9) for area. The adaptation also improves both quantities in the burst environment. Under successive improvements, CP-FIFO has regret 1194.7 and area 14,743, against 2905.8 and 9525: lower regret accompanies slower reporting. Growing MOSS has the lowest mean regret in all four environments, between 52.0 and 77.3, and larger unresolved areas. These points do not isolate the effect of task expiration: the adaptation uses all 10,000 service pulls while coarse CP uses about 5,786, and some remaining questions are inside the unpenalized boundary band. A comparator with the same tolerance and service requirement is needed to separate that mechanism from different rules for stopping reporting work.

No incorrect positive or negative report occurred in the 5,760 runs. For a single environment-method pair, zero failures in 160 replications gives a one-sided 95% upper confidence bound of 0.0186 on its failure probability. The absence of observed failures does not verify the all-environment, all-time guarantee. Nor do four eight-arm experiments validate the asymptotic lower bounds or an optimal frontier; they assess fixed-budget costs and competing implementations.

## Major Comment 4(b)

The reviewer identifies inconsistent environment parameters and inconsistent uses of $T$ and $t$ in Growing MOSS.

We agree that these choices alter either the environment or the method and cannot be dismissed as notation. The submitted main text and supplement are insufficient to identify a unique reproducible experiment. We do not repair this by selecting whichever specification gives the most favorable comparison.

For the original archive, Section 8 and its supplied metadata identify the configurations that actually generated the figures: Bernoulli background arrivals with probability .005, C's step starting level .7, E's near-optimal interval $[.75,.90]$, and the current-time MOSS variant. The raw results, configuration files, and source code are copied without alteration. These are historical specifications, not newly rerun corrected experiments.

The separate reporting configuration fixes the arrival times, means, seed scheme, tolerances, and all nine policies. It uses Bernoulli rewards, $T=20{,}000$, $\varepsilon=.30$, $\eta=.10$, and $\delta=.05$. Methods share each arm's potential reward stream within a replication; arrivals precede the action and reports follow the observation. The evaluation horizon is not supplied to these reporting policies. The fixed-budget UCB-AA calibration in Section 3 does use $T$, and is not one of these nine experimental methods.

The new study's Growing-MOSS rule is explicitly the current-time variant with bonus $\sqrt{\max\{\log(t/(K_tn)),0\}/n}$ and infinite index at zero samples. It is not labelled as the horizon-based $T$ rule, and we assume no inherited minimax guarantee. The other index and service formulas, tie rules, and endpoint behavior are fixed in the released code. New tables and figures derive from that configuration. The original six figures are retained separately in the supplement with their archived-implementation qualification; they are not relabelled as results for repaired UCB-AA or CP-UCB-AA.

## Major Comment 4(c)

The reviewer requests the original simulation value of $M$ and the numbers and lengths of completed rounds.

We agree that these quantities are necessary for interpreting the original results. The preserved raw configurations record $M=5$ for Scenario C and $M=4$ for Scenario E. The archived procedure stops admission after its prescribed rounds and leaves later arrivals buffered; its small active set cannot be interpreted as successful screening of every arrival. We preserve those runs with this limitation and do not reconstruct all unreported round lengths from endpoint CSV files. The repair in Section 3 uses the explicit $M_T$ calibration, rather than treating the archive's fixed $M$ values as the repaired specification.

CP-UCB-AA has no $M$ parameter and admits until the endpoint. All four reporting environments have eight arms by pull 20,000. Their records contain checkpoint completion, unresolved paths, service counts and regret, and available-arm counts. At $\rho=.04$, all available arms remain unresolved throughout all 640 runs. A checkpoint completion is not a completed classification, because another arm's upper bound can still block a positive report. The final five-to-eight counts in the charged metric reflect its boundary-band exemption. The confidence-based adaptation resolves every boundary-separated arm by the endpoint in all replications. These observations concern the added reporting task, not completed rounds of repaired UCB-AA.

## Minor Comment 1

We accept the suggestions on notation and algorithm presentation. For the retained two-stage method, we state $\widetilde\Delta_p=2^{-p}$, define a phase before using phase ranges, describe rounds $0,\ldots,M$ as $M+1$ rounds, specify empty-batch no-ops and strict elimination comparisons, and define empirical means by the prefixes used. Actual physical truncation is stated separately from completion of an algorithmic round. Per-arm regret is written as an explicit sum when needed.

The revised paper follows the submitted problem formulation: $\mathcal{A}$ is the arm pool, $\mathcal{A}_t$ the available set, $r_i$ an arm's mean, $r^*(t)$ the current best mean, and $\Delta_i(t)=r^*(t)-r_i$ the suboptimality gap. It uses $\hat r_i(n)$ for the mean of the first $n$ observations of arm $i$, retains $\tau_i$ for its physical arrival time, and calls $R_T$ cumulative dynamic regret; $\mathbb E R_T$ is its expectation. The model remains the multi-armed bandit problem with arriving arms (MAB-AA), with arrival information discrepancy (AID) and a drifting benchmark (DB).

We retain $K_t=|\mathcal{A}_t|$, already used in the original numerical section, and $N_i(t)$ for lifetime counts. These differ from the original known round-based count bound $K(m)$ and phase target $n_p$. Physical time $t$ and deterministic endpoint $T$ differ from algorithmic round $m$ and random completion time $T_0(\pi)$. Arrivals are observed before an action; their admission to reward competition follows the specified policy. UCB-AA buffers within-round arrivals, whereas CP admits immediately and reports after the observation. The new confidence calibration does not require a future arm-count bound.

New reporting objects have separate notation: the true relative near-optimal set is $\mathcal G_t^\varepsilon$, the reported categories are $\mathcal P_t,\mathcal N_t,\mathcal V_t$, and cumulative unresolved area is $\mathcal U_T(\eta)$. In particular, these categories do not redefine the original active set $B_m$ or surviving set $C_m$. We distinguish the near-optimality tolerance $\varepsilon$, the excluded boundary width $\eta$, and the configured reporting precision $\rho$, and keep the certification queue separate from every arm set.

## Minor Comment 2

We accept the suggestion. The new reporting figures in Section 8 use the manuscript's mathematical notation, identify the physical sampling clock, and specify 1.96 Monte Carlo standard error bars or bands. One figure includes all nine methods; the path figure displays six, with all nine retained in the records. Original figures are identified as historical, and the recomputed archive tables use pointwise Student $t$ intervals. Captions distinguish simulation uncertainty from theoretical reliability. Page layout requires the final compilation check.

## Earlier novelty and positioning concerns

This section addresses the concerns recorded in the 24 September author response materials. It should be reconciled with the exact earlier report and editor's decision before submission; we do not invent reviewer numbering or quote unavailable wording.

### Inclusion in sleeping and ballooning bandits

We agree that a finite arrival prefix is a sleeping-bandit instance in which each arm becomes available once and then remains available. Under stationary means, the ordering that ranks arms by their true means selects a best currently available arm at every time. We do not claim a new regret comparator. Ghalme et al. already study permanent arrivals and this reward objective, so neither the arrival model nor that comparator is presented as our contribution.

A growing number of arms matters when interpreting fixed-arm rates, but does not make UCB inapplicable: a UCB policy can initialize an arm when it arrives. We therefore treat growing UCB/AUER as baseline reward methods. Our additional question is how reliably and promptly the complete relative near-optimal set can be reported during that reward collection. We relate this task to existing all-near-optimal identification and joint regret-identification work and locate the new claims in the maintenance-area lower bounds and the specified multiple-update tradeoff.

### Extra assumptions and generic square-root rates

The repaired original UCB-AA analysis obtains an actual-count learning bound at a fixed physical budget without the disputed terminal-gap compression. Its total regret still contains explicit admission delay; sublinearity requires that delay to be sublinear as well. The original gap-stability assumption is not claimed false merely because its former proof failed. We do not assert unconditional sublinear regret for the buffered procedure. The additional reporting results have their own service requirements and restricted families. Their elementary mixture bound is a construction tool, and those requirements cannot be transferred to arbitrary arriving-arm regret problems.

### Lower-bound novelty and matching

Classical KL change of measure and simultaneous testing are established tools. Section 4 retains the static calibration and the distractor mechanism through one local-alternative theorem, proved using half of each remaining horizon. Its growing-family uniform-goodness condition is explicit and may define an empty class under excessive arrival growth; existence is not asserted in those regimes. The progressive lower bound is also retained. With $J$ near-homogeneous blocks, gaps of order $\sqrt{J/T}$ require $J=O(T^{1/3})$ in the bounded ladder. There are $2J$ arms. This is not an unrestricted growing-arm minimax claim or a matching converse to a bound at endogenous random checkpoints.

The new matching claims are narrower and use identical tasks and budgets on their two sides. The worst-case maintenance area is matched over schedules and reward environments with at most $K$ arrived arms. This lower bound can already arise from one initial batch; we do not portray it as intrinsically requiring repeated arrivals. The dynamic contribution is developed separately through the shared uncertainty of new arms and the cost of temporary membership tasks in a multiple-update family. The deferred endpoint has no claimed matching lower bound.

### Final-set consistency requested in the research discussion

The revision includes a separate multiresolution checking construction for eventual set recovery. If arrivals stop, the final number of arms is finite, and no arm lies exactly on the relative near-optimality boundary, its report can eventually equal the true set almost surely while expected regret remains sublinear. It allows early reports to be corrected. This result is not attributed to the fixed-precision checkpoint implementation. We present it as a completeness result; the finite-time reporting-cost analysis supplies the main contribution.

### Clinical motivation and evidence

The NSCLC approval-count figure in the submitted paper is background motivation derived from public regulatory resources. It is not a bandit experiment with patient outcomes. The submitted bandit studies are synthetic, and the original data-availability statement says that no original empirical or human-subject data were collected. We retain no claim of clinical efficacy, validation in an actual trial, or an application finding established by those simulations. The relative near-optimal set refers only to the scalar reward model.

## Remaining submission checks and unavailable source documents

Section labels and numerical claims above refer to the current main source and the recorded revision experiments. Final page and line numbers require the checked compiled manuscript; the journal's current submission requirements require a separate final administrative check.

The numerical comparison of repaired UCB-AA against matched short-admission and no-pre-elimination methods remains unfinished. The retained archive and CP study are not substitutes for that check. The historical innovation assessments in this directory evaluate the earlier frozen checkpoint-centered version; this restored original-based revision has not been reassessed, so those scores are not attributed to its combined contents.

The earlier novelty discussion remains based on the author's 24 September summary. The original editor's decision letter and the verbatim earlier report were not supplied among the documents reviewed here. This response therefore does not establish that the editor invited a resubmission, does not attribute exact wording or a referee number to those unavailable documents, and must be reconciled with them before submission.

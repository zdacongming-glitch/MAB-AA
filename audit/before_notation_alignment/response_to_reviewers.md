# Response to the review reports

Working draft, 15 October 2026. This document accompanies a substantial revision of the UCB-AA paper for JASA Theory and Methods. It records changes in the research formulation, replacement analysis, and completed numerical study. The guarantees belong to the stated new constructions. Section references follow the assembled main source; page and line references are omitted until pagination is final.

The detailed report supplied in `Reviews_JASA-RA-2026-0866.pdf` contains a Summary, Major Comments 1(a) to 4(c), and two Minor Comments. It does not identify a referee number in the document. We answer that report first. A separate section addresses the sleeping-bandit and novelty concerns recorded in the earlier response materials. Those materials are an author's summary and working response, not a substitute for the verbatim earlier report or decision letter.

The source references used below are:

| Main-text section | Source label |
|---|---|
| 2. Observation model and reporting requirement | `sec:model` |
| 3. Lifetime checkpoints and reward selection | `sec:method` |
| 4. The burden of continual certification | `sec:maintenance` |
| 5. Temporary membership questions and their regret cost | `sec:tradeoff` |
| 6. Numerical comparisons at a fixed pull budget | `sec:experiments` |
| 7. Discussion | `sec:discussion` |

The result labels are `prop:reporting`, `thm:broadcast`, `cor:growth`, `thm:worst_area`, `thm:reuse`, `thm:tradeoff`, and `thm:quantile_main`. This source index is provided for the authors' final cross-reference check and can be removed from the submitted letter.

## Opening response

We thank the reviewer for the careful analysis and the independent implementation. The report identifies substantive problems in the submitted proofs, as well as discrepancies between the algorithm, the simulation specifications, and the interpretation of the results. We agree that these problems cannot be resolved by clarifying notation alone.

The revision retains the stationary reward model with exogenous permanent arrivals and regret relative to the best currently available arm. It changes the main statistical task and the construction used to study it. We now require the procedure to report which available arms have been certified as relatively near optimal, which have been certified as outside that set, and which remain unresolved. The reports must be correct jointly over arms and time. We measure their timeliness by cumulative unresolved arm time outside a specified boundary band. This formulation makes precise a purpose that the original manuscript attributed to its smaller active set without providing a corresponding statistical guarantee.

The replacement procedure, CP-UCB-AA, admits arms at every physical sampling time. It interleaves checkpoint certification with UCB selection based on all observations. Certification uses a prespecified sample checkpoint for each arm. The reward policy continues to consider every available arm, including arms reported as non-near-optimal. Thus an erroneous report does not cause permanent exclusion from reward selection. This is a new construction, and its proofs do not rely on the disputed arguments for the original round-based procedure.

We withdraw the original claims supported by the defective decomposition, the gap compression in the $G_3$ case, the data-dependent elimination-chain probability bound, and the auxiliary-stage conversion. Sections 4 and 5 describe joint reward and reporting costs under an explicit service requirement. They include lower bounds for the effect of an uncertain arrival on old reports, a worst-case maintenance-area bound, and a specified family in which prompt classification and permitted deferral have different orders of regret. A further result gives a fixed-probability regret lower bound under the same rapid-service requirement. These claims are restricted to their stated parameter ranges and instance classes.

Section 6 replaces the original numerical study with 5,760 runs: four environments, nine methods, and 160 replications for each environment-method combination, all at $T=20{,}000$. The results expose substantial costs of conservative checkpoints. A confidence-based all-near-optimal adaptation improves both regret and unresolved area in two environments, while Growing MOSS has the smallest mean regret in all four and leaves much larger unresolved areas. We report these failures alongside the cases illustrating a tradeoff between reward and reporting speed.

## Detailed report: Major Comment 1(a)

The reviewer observes that $D_M=R_{T_0}-R_M$ includes loss from earlier elimination as well as loss from delayed admission.

We agree. Let $B_m$ be the active set at the beginning of an original round, let $A^{\mathrm{adm}}_m$ contain all arms admitted by then, and write $L_m$ for the round length. The correct pathwise identity is

$$
R_{T_0}
=R_M
+\sum_m\sum_{t\ \mathrm{in\ round}\ m}
\left(\max_{i\in A_t}\mu_i-\max_{i\in A^{\mathrm{adm}}_m}\mu_i\right)
+\sum_m L_m
\left(\max_{i\in A^{\mathrm{adm}}_m}\mu_i-\max_{i\in B_m}\mu_i\right).
$$

The second sum is the arrival-delay contribution. The third sum is the loss of an admitted benchmark through earlier elimination. Defining their sum as $D_M$ is algebraically valid, but identifying that sum with arrival increments alone is not. The third term may remain positive when arrivals cease. Small error probabilities do not remove the term from the identity, and with a random completion time they do not justify replacing its expectation by a product of an expected horizon and an error probability.

We therefore do not retain Proposition 1 or Theorem 2 as proved guarantees for the original algorithm. Section 2 states the complete reward account. In the policy of Section 3 all arrivals enter $A_t$ before the action at time $t$, and its reward analysis uses $B_t=\max_{i\in A_t}\mu_i$ directly at each pull. Reports and reward eligibility are separate, so incorrect exclusion from a report does not create the original persistent-elimination term in reward selection. The new expected-regret proof accounts for certification pulls explicitly and does not condition away the reporting-error event.

## Major Comment 1(b)

The reviewer requests separate numerical accounting for learning within rounds, delayed admission, and earlier elimination.

The revised study implements this accounting for Batch100-UCB, the short-admission confidence-retirement comparator described in Comment 2(b). Section 6 records the within-active learning loss, admission delay, and deficit from earlier reward retirement on the same realized path. The admission-delay contributions in the four environments are $0$, $33.92$, $16.00$, and $22.40$. No deficit from historical retirement occurred in these runs. Across all 5,760 runs, the largest discrepancy between total regret and the sum of the three recorded components was below $3.1\times10^{-12}$.

For the methods that admit immediately and retain every available arm for reward selection, the admission and retirement terms are identically zero. The released records also separate designated certification pulls and their regret from reward-selection pulls, and include the unresolved paths and report errors. A negative report is not counted as a reduction in the reward policy's available set. The original figures have been replaced; these new data do not reconstruct the original algorithm's unrecorded decomposition.

## Major Comment 2(a)

The reviewer shows that exponentially increasing round targets can place the later rounds far beyond a budget of 60,000 pulls.

We agree with the distinction between selecting a terminal round index and reaching it within a given sampling budget. The original resolution is $2^{-m}$, and its target grows on a $4^m$ scale. Consequently, a larger prescribed $M$ does not imply that later rounds are observed in a fixed-budget experiment. The original theoretical calibration of $N$ can increase this mismatch further.

The new analysis fixes a deterministic physical budget $T$. Every step consists of one action and one observed reward. CP-UCB-AA in Section 3 does not take $T$, a terminal round index, a future arm-count bound, or the future arrival schedule as input. Its checkpoint for arrival-order index $i$ is

$$
q_i=\left\lceil\frac{2}{\rho^2}\log\frac{4i(i+1)}{\delta}\right\rceil.
$$

This is a cumulative sample target. Observations acquired by ordinary reward selection also count toward it. If the experiment ends before a checkpoint is reached, the arm remains unresolved; we do not complete an auxiliary run to obtain a more favorable service guarantee. The maintenance-area bounds charge that unresolved time, including all unfinished work at $T$.

Section 6 shows the practical consequence of the checkpoint calibration as well. For eight arms, the total quotas are 73,083 at $\rho=.04$ and 8,123 at $\rho=.12$. The finer setting cannot complete all quotas in 20,000 pulls and leaves five to eight boundary-separated arms unresolved on average at the endpoint. The coarser setting retains label reliability but does not guarantee completeness at the experiment's $\eta=.10$. We report the settings separately rather than interpret an infeasible theoretical quota as a completed experiment. The new policy replaces the old round schedule; it is not a faster implementation of it.

## Major Comment 2(b)

The reviewer questions the long admission intervals and suggests a short-interval UCB policy with confidence elimination.

We agree that waiting for an increasingly long elimination round is a design choice, rather than an observation constraint imposed by the model. The original paper did not establish that the exploration saved by buffering compensated for the extra admission loss. We have removed that claim. The replacement policy admits each arm as soon as it arrives and retains its complete observation history thereafter.

We also agree that simple UCB with a sound reporting or elimination layer is an essential comparator. Our contribution is not the observation that confidence bounds can screen an inferior arm. Permanent availability means that a valid certificate of inferiority to an already available arm remains valid later. What changes for positive near-optimality reports is the reference level: an uncertain new arm can prevent many old arms from being certified relative to the current best, even when the old means and observations have not changed.

Sections 4 and 5 quantify this shared reporting burden and the regret cost of meeting specified timeliness requirements. A competing policy given the same reporting obligation can use the same old evidence and permanent dominance relation. Section 6 consequently includes full-history UCB with a checkpoint report, UCB with full-prefix confidence reports, a confidence-based ALL-$\varepsilon$ adaptation that retains history, and Batch100-UCB with the reviewer's short admission interval and confidence retirement. Batch100-UCB admits at pulls $1,101,201,\ldots$; its reports cover all physically arrived arms, including those waiting for admission. The ALL-$\varepsilon$ rule is a natural adaptation, not an implementation of FAREAST or $(\mathrm{ST})^2$. Its favorable results are reported explicitly.

## Major Comment 2(c)

The reviewer observes that the completed auxiliary stage may require far more pulls than the actual experiment.

We agree. The old proof bounds regret by extending an unfinished stage, then defines $T$ using the expected length of that extension. It does not establish a comparable bound in the actual number of pulls. In particular, doubling a round index is not doubling a sample budget when the final sample target contains $4^{2^\ell}$. We withdraw the interpretation of Corollary 2 as an anytime bound in the actual budget.

The policy in Section 3 is defined indefinitely without restarts. At every deterministic $T$, the joint bound in Section 4 concerns precisely the first $T$ observed rewards. Reporting reliability holds jointly over all times, while service and expected-regret statements retain their stated quantifiers. A bound at each deterministic endpoint does not by itself give a bound at arbitrary data-dependent stopping times; we make no such inference. The fixed-budget experiments also stop at the actual endpoint without completing auxiliary stages.

## Major Comment 3(a)

The reviewer identifies an invalid change of index in the $G_3$ bound and provides a counterexample satisfying the stated gap stability assumption.

We agree. The defining relation compares $\widetilde\Delta_{\widetilde m_i}$ with $\Delta_i(m_i)$; it does not compare $\widetilde\Delta_{m_i}$ with that gap. In the $G_3$ case the two indices can be far apart. The submitted compression can therefore understate samples acquired at a small historical gap before a later large benchmark increase. The counterexample directly invalidates that intermediate inequality under the stated assumptions.

We withdraw Corollary 1 and the simplified conclusions that depend on this step, including the affected online derivation. We do not describe this as a typographical correction, and we do not replace the missing argument with a stronger gap condition chosen after seeing the counterexample.

The replacement proof in Sections 3 to 5 tracks actual sample counts. For reward selection, an arm's empirical mean uses all its observations. For certification, it uses the first $q_i$ observations at a prespecified checkpoint. The associated reward cost is charged rather than compressed through a terminal gap. In the multiple-update construction of Section 5, we distinguish the regret gap, which is of order $\varepsilon$, from the much smaller distance $d$ to the membership boundary. This explains why prompt classification can be costly even when ordinary reward maximization does not require $d$-level accuracy.

## Major Comment 3(b)

The reviewer observes that controlling a fixed elimination sequence does not control the event that some data-dependent sequence occurs.

We agree. The bound on an intersection along a fixed sequence is valid, but taking the maximum over sequencewise bounds is not a probability bound for their union. The subsequent numerical optimization lemma does not repair this logical gap. We withdraw the error control that depended on Equation (30).

The reporting proposition in Section 3 starts with one simultaneous event for all checkpoint means. The checkpoint $q_i$ is fixed before observing arm $i$'s rewards. By Hoeffding's inequality and an index-summable allocation,

$$
\Pr\left(\exists i:\left|\widehat\mu_{i,q_i}-\mu_i\right|>\rho/2\right)
\le\sum_{i\ge1}\frac{\delta}{2i(i+1)}=\delta/2.
$$

Adaptive sampling changes when the checkpoint is reached, not which prefix of that arm's reward stream defines the estimate. On this single event, all reports follow by deterministic interval comparisons at every time. There is no selected elimination chain whose probability is replaced by a maximum.

## Major Comment 3(c)

The reviewer identifies inconsistent definitions of the roundwise optimal arm and a comparison against an eliminated reference that the algorithm does not make.

We agree with both points. An arm defined to belong to $B_{m_i}$ cannot simultaneously have been eliminated before that set was formed. Defining the reference instead over all admitted arms does not, on its own, establish Equation (18): a stored estimate is not necessarily an estimate used in the actual comparison. We withdraw that event inclusion and its consequences.

Sections 2 and 3 reserve $A_t$ for every arrived arm and $B_t$ for the corresponding true best mean. They use $C_t,D_t,V_t$ only for reported categories. Reporting intervals $[\ell_i,u_i]$ are initialized to $[0,1]$ and are frozen when their checkpoints are reached. Every report uses

$$
\underline B_t=\max_{j\in A_t}\ell_j,\qquad
\overline B_t=\max_{j\in A_t}u_j,
$$

$$
C_t=\{i\in A_t:\ell_i\ge\overline B_t-\varepsilon\},\qquad
D_t=\{i\in A_t:u_i<\underline B_t-\varepsilon\}.
$$

These are the comparisons implemented by the algorithm. At reward-selection steps, UCB also maximizes over all of $A_t$. The compiled experiment implementation was checked against the original `choose/observe/report` interface for 20,000 successive rounds. Actions, service indicators, every available-arm count, and every reported label agreed at each round. This parity check supports implementation fidelity; the statistical guarantee comes from the proposition's simultaneous-event proof.

## Major Comment 4(a)

The reviewer asks for a balanced comparison with Growing MOSS and evidence for the value of a smaller active set.

We agree that the submitted evidence does not show an overall regret advantage over Growing MOSS. We remove statements that treat the original experiments as demonstrating uniform superiority or a uniformly modest price for screening. A smaller internal set alone does not establish reduced storage, less computation, correct exclusion, or complete evaluation of all arrivals. In particular, an arm that was never admitted cannot be counted as statistically eliminated.

The revised reporting task supplies a measurable statistical benefit: reliable knowledge of the current relative near-optimal set with an explicit cost for unresolved reports. Its cost is assessed jointly with regret. A reward-only baseline is informative about the price of reporting, but it is not required to meet a task it was not designed to perform. Comparisons of service efficiency must attach the same reporting requirement to the competing reward policies or use a set-identification baseline with the same reliability target.

The separation in Section 5 compares fast and deferred configurations on the same arms, arrivals, endpoint, tolerance, and reporting-error probability, with different permitted maintenance areas. At the fast endpoint the regret bound is matched. At the deferred endpoint we give an achievable upper bound. It is a result about the cost of requested reporting speed, rather than a claim about the best practical policy.

The completed study in Section 6 is deliberately unfavorable to any claim of uniform checkpoint superiority. Under a stable benchmark, coarser CP-FIFO has mean regret 3629.9 and unresolved area 49,718; ALL-$\varepsilon$ adaptation has 1367.8 and 11,306. The paired differences, CP-FIFO minus the adaptation, are 2262.1 (Monte Carlo standard error 11.7) for regret and 38,411.7 (standard error 241.9) for area. The adaptation also improves both quantities in the burst environment. Under successive improvements, CP-FIFO instead has regret 1194.7 and area 14,743, against 2905.8 and 9525 for the adaptation: lower regret accompanies slower reporting. Growing MOSS has the lowest mean regret in all four environments, between 52.0 and 77.3, and much larger unresolved areas. These outcomes are shown in the main table and both figures, with Monte Carlo uncertainty.

No incorrect positive or negative report occurred in the 5,760 runs. For a single environment-method pair, zero failures in 160 replications gives a one-sided 95% upper confidence bound of 0.0186 on its failure probability. The absence of observed failures does not verify the all-environment, all-time guarantee. Nor do four eight-arm experiments validate the asymptotic lower bounds or an optimal frontier; they assess fixed-budget costs and competing implementations.

## Major Comment 4(b)

The reviewer identifies inconsistent environment parameters and inconsistent uses of $T$ and $t$ in Growing MOSS.

We agree that these choices alter either the environment or the method and cannot be dismissed as notation. The submitted main text and supplement are insufficient to identify a unique reproducible experiment. We do not repair this by selecting whichever specification gives the most favorable comparison.

The executable configuration in the revision fixes the arrival times, mean rewards, seed scheme, tolerances, and all nine policies. Section 6 uses Bernoulli rewards, $T=20{,}000$, $\varepsilon=.30$, $\eta=.10$, and $\delta=.05$ throughout. Methods receive the same potential reward stream for each arm within a replication. Arrivals precede the action and reports follow the observation. The evaluation horizon is not supplied to the policies.

The Growing-MOSS rule is explicitly the current-time variant with bonus $\sqrt{\max\{\log(t/(K_tn)),0\}/n}$ and infinite index at zero samples. It is not labelled as the horizon-based $T$ rule, and we assume no inherited minimax guarantee for this adaptation. The other index and service formulas, tie rules, and endpoint behavior are fixed in the released code. The main table, figures, all replication records, and paired differences have been generated from that configuration. The old figures are omitted from the revised manuscript and remain historical material in the original source folder.

## Major Comment 4(c)

The reviewer requests the original simulation value of $M$ and the numbers and lengths of completed rounds.

We agree that these quantities are necessary for interpreting the original results. The independent local audit records $M=5$ for archived Scenario C and $M=4$ for archived Scenario E, with further discrepancies from the submitted description. These are audit findings, not values inferable from the PDF. The archive can stop admitting arms after its prescribed rounds and leave later arrivals buffered; its small active set therefore cannot be interpreted as successful screening of every arrival. We have replaced those experiments, rather than claim to reconstruct all their unreported round lengths.

The new procedure has no $M$ parameter and admits arms until the endpoint. All four new environments have eight arms by pull 20,000. The released records contain checkpoint completions, sampled actions, unresolved paths, service counts and regret, and the complete available-arm count used in the implementation check. At $\rho=.04$, average final unresolved counts range from five to eight, even though the labels that are issued remain reliable. A checkpoint completion is not a completed classification: another arm's upper bound can still block a positive report. The confidence-based adaptation resolves every boundary-separated arm by the endpoint in all replications of the four environments.

## Minor Comment 1

We accept the suggestions on notation and algorithm presentation. In any retained description of the original method, we state $\widetilde\Delta_m=2^{-m}$, define a phase before referring to phase ranges, describe rounds $0,\ldots,M$ as $M+1$ rounds, and define every empirical mean by the observations it uses. The original per-arm regret notation is replaced by an explicit sum when it is needed.

The revised paper consistently uses $\mu_i$ for an arm's mean, $B_t$ for the current best mean, and $\Delta_i(t)=B_t-\mu_i$. It distinguishes the near-optimality tolerance $\varepsilon$, the excluded boundary width $\eta$, and the configured reporting precision $\rho$. It also distinguishes all available arms from report categories and from the certification queue. A single physical step is defined in order: admit arrivals, select one arm, observe one reward, update its statistics, and issue the report.

## Minor Comment 2

We accept the suggestion. The two new figures in Section 6 use the manuscript's mathematical notation, identify the physical sampling clock, and state that error bars or bands are 1.96 Monte Carlo standard errors. One figure includes all nine methods; the path figure displays six, with all nine retained in the released records. Captions distinguish Monte Carlo uncertainty from the theoretical reliability statement. The exact compiled layout is checked separately from this wording review.

## Earlier novelty and positioning concerns

This section addresses the concerns recorded in the 24 September author response materials. It should be reconciled with the exact earlier report and editor's decision before submission; we do not invent reviewer numbering or quote unavailable wording.

### Inclusion in sleeping and ballooning bandits

We agree that a finite arrival prefix is a sleeping-bandit instance in which each arm becomes available once and then remains available. Under stationary means, the ordering that ranks arms by their true means selects a best currently available arm at every time. We do not claim a new regret comparator. Ghalme et al. already study permanent arrivals and this reward objective, so neither the arrival model nor that comparator is presented as our contribution.

A growing number of arms matters when interpreting fixed-arm rates, but does not make UCB inapplicable: a UCB policy can initialize an arm when it arrives. We therefore treat growing UCB/AUER as baseline reward methods. Our additional question is how reliably and promptly the complete relative near-optimal set can be reported during that reward collection. We relate this task to existing all-near-optimal identification and joint regret-identification work and locate the new claims in the maintenance-area lower bounds and the specified multiple-update tradeoff.

### Extra assumptions and generic square-root rates

We no longer use the original gap-stability and cumulative-jump assumptions to support a generic fixed-budget square-root claim. The replacement results state a fixed physical budget and expose certification work. The elementary mixture bound is a construction tool, not the principal novelty claim. The worst-case maintenance-area statement has its own parameter range, and the fast-versus-deferred regret comparison has an explicitly defined restricted instance family. These assumptions cannot be transferred to an arbitrary arrival environment.

### Lower-bound novelty and matching

Classical KL change of measure and simultaneous testing are established tools. We credit them as such. The old static lower bound is calibration. The progressive-arrival lower bound illustrates how local tests can remain difficult while old arms remain available, but its increasing reference levels are constrained by bounded rewards. With $J$ near-homogeneous blocks, gaps of order $\sqrt{J/T}$ require $J=O(T^{1/3})$ in that construction. It does not provide an unrestricted growing-arm minimax lower bound, and it is not a matching converse to an upper bound measured at endogenous random checkpoints.

The new matching claims are narrower and use identical tasks and budgets on their two sides. The worst-case maintenance area is matched over schedules and reward environments with at most $K$ arrived arms. This lower bound can already arise from one initial batch; we do not portray it as intrinsically requiring repeated arrivals. The dynamic contribution is developed separately through the shared uncertainty of new arms and the cost of temporary membership tasks in a multiple-update family. The deferred endpoint has no claimed matching lower bound.

### Final-set consistency requested in the research discussion

The revision includes a separate multiresolution checking construction for eventual set recovery. If arrivals stop, the final number of arms is finite, and no arm lies exactly on the relative near-optimality boundary, its report can eventually equal the true set almost surely while expected regret remains sublinear. It allows early reports to be corrected. This result is not attributed to the fixed-precision checkpoint implementation. We present it as a completeness result; the finite-time reporting-cost analysis supplies the main contribution.

### Clinical motivation and evidence

The NSCLC approval-count figure in the submitted paper is background motivation derived from public regulatory resources. It is not a bandit experiment with patient outcomes. The submitted bandit studies are synthetic, and the original data-availability statement says that no original empirical or human-subject data were collected. We retain no claim of clinical efficacy, validation in an actual trial, or an application finding established by those simulations. The relative near-optimal set refers only to the scalar reward model.

## Remaining submission checks and unavailable source documents

Section labels and numerical claims above refer to the current main source and the recorded revision experiments. Final page and line numbers require the checked compiled manuscript; the journal's current submission requirements require a separate final administrative check.

The earlier novelty discussion remains based on the author's 24 September summary. The original editor's decision letter and the verbatim earlier report were not supplied among the documents reviewed here. This response therefore does not establish that the editor invited a resubmission, does not attribute exact wording or a referee number to those unavailable documents, and must be reconciled with them before submission.

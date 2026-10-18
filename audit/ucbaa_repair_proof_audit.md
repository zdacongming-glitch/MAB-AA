# Original UCB-AA: physical-budget proof repair

Status: complete proof for the explicitly repaired procedure in `theory/ucbaa_repaired_analysis.tex`. This is not a proof of every implementation compatible with the former pseudocode, its smaller empirical calibration, the withdrawn terminal-gap compression, or the old algorithmic-round doubling argument.

## Target contract and assumptions

| Item | Status | Exact use |
| --- | --- | --- |
| Independent stationary rewards supported on $[0,1]$ | Given | Potential-prefix Hoeffding inequality |
| Deterministic permanent arrivals, finite available sets at finite times | Given scope | Exogenous buffering and finite maxima |
| At least one initially available arm | Explicit nondegeneracy condition | A pull is always available |
| One observation per physical time | Given | At most $T$ exposed streams and lifetime counts summing to $T$ |
| All historical observations retained within an execution | Original algorithm, made explicit | The incumbent's first $n_p$ observations actually exist |
| Strict interval comparison and simultaneous deletion | Explicit repair | A maximum cannot be deleted on coverage, and the formal survivor set is nonempty on every path |
| Sufficient horizon-dependent $N$ calibration | Explicit repair | A single summable failure event across arms and phases |
| Immediate truncation at physical budget | Explicit repair | Counts the unfinished phase and buffered final arrivals |
| Unique best arm | Not needed | Ties survive the strict comparison |
| Terminal-gap stability and cumulative-jump control | Not used | Replaced by actual-prefix counting and an explicit delay term |

The finite-budget result is uniform over the stated reward laws and deterministic arrival schedules. The confidence parameter is fixed before data collection. Its expected-regret bound retains the random admission-delay contribution through its expectation.

## Route registry

| Route | Artifact | Status |
| --- | --- | --- |
| Original terminal-gap compression | Former $G_3$ simplification | Not reinstated; the known counterexample remains relevant |
| Union over random elimination chains | Former maximum-of-chain-probabilities step | Not used |
| Direct roundwise prefix charging | A phase-$p$ pull has current-round gap at most $4b_{p-1}$ after the preceding same-round comparison | Closed |
| Simultaneous unrevealed-stream concentration | At most $T$ first-exposed streams, with a phase union per stream | Closed |
| Physical-time exposure accounting | Exact three-term identity and the admission-delay formula | Closed |
| Physical-budget doubling | Restart at physical times $1,2,4,ldots$ with failure budgets proportional to the inverse squared epoch length | Closed; standard wrapper, not a new core contribution |

## Closed proof obligations

1. The targets increase strictly, all radii are defined, and $n_{M_T}>T$. The last analyzed phase therefore cannot have completed before the physical endpoint.
2. Every preliminary reference prefix exists. At the preceding completed round's end, an incumbent has exactly $n_{m-1}$ observations, exceeding every preliminary target. Its prefix estimate is recomputed or retained from actual observations.
3. Every new current-round maximum survives preliminary screening. Every current maximum survives formal elimination. On the common coverage event, the historical admitted benchmark remains represented and the historical-deficit term is zero.
4. Newly admitted arms receiving phase-$p$ samples have passed phase $p-1$ in that round. Incumbents require no new samples in formal phase $m-1$; their phase-$m$ samples follow the updated current-round comparison. This is the key distinction that prevents a drifting benchmark from invalidating the count bound.
5. For an arm's actual $n$th observation, the gap is bounded using the current round, the previously completed comparison, and $n\le n_p$. The proof does not replace that gap by its terminal value.
6. Distinct lifetime prefixes are charged once, including every draw in an unfinished final target. Summation and Cauchy--Schwarz give the statistical term.
7. The exact regret identity has three nonnegative terms. Arrival delay includes an improvement that is still buffered at the final endpoint. No bookkeeping admission at the end erases that exposure.
8. For the unknown-horizon wrapper, the epoch failure contribution is charged only for that epoch: restarting reintroduces arms and prevents an earlier elimination error from propagating into later epochs. The weighted failure sum is finite.

## Adversarial audit and finite diagnostics

The analytic proof checks the initial two rounds, an empty batch, an empty surviving new batch, a singleton active set, tied maxima, deterministic rewards, a large new benchmark improvement, and a cutoff during the first or any later target. The confidence event is unconditional; selected sample counts are not assumed independent of rewards.

A separate finite diagnostic executed 17 paths with physical budgets $1$, $2$, $2000$, $20000$, $40000$, and $60000$, using both deterministic and Bernoulli reward laws. The cases reached phases zero through five and included empty batches, ties, late benchmark improvements, and incomplete targets. All observed comparison prefixes satisfied their coverage event; no actual-prefix charge violation occurred. The maximum floating-point discrepancy in the three-term identity was below $3.2\times10^{-9}$, and the explicit delay-exposure formula agreed. These are diagnostic counterexample searches, not a proof or a probability certificate.

The mathematical conclusion remains limited: it provides a corrected statistical upper bound plus explicit admission delay. It proves neither arbitrary-arrival sublinear regret nor a matching minimax statement. The newly developed maintenance lower bounds and tradeoff results are separate contributions and are not consequences of renaming this repair.

"""Prepare editorial changes as text data; the only TeX outputs are the two papers."""
from pathlib import Path
import json,re

REV=Path(__file__).resolve().parent
base=(REV/'baseline/manuscript.tex').read_text(encoding='utf-8')
section_starts=list(re.finditer(r'^\\section\{',base,re.M))
parts=[base[m.start():(section_starts[i+1].start() if i+1<len(section_starts) else base.index(r'\section*{Data and code availability}'))] for i,m in enumerate(section_starts)]
header=base[:section_starts[0].start()]
abstract=r'''We study reliable maintenance of all relatively near-optimal arms while
collecting rewards when new arms arrive exogenously and remain available.
Reward laws are stationary, but arrivals change the membership boundary.
Reporting progress is measured by cumulative unresolved arm time outside
a prescribed boundary band, with simultaneous correctness of all labels.
One uncertain arrival can obstruct many earlier certifications. A
common-reference lower bound quantifies this effect, and matching
worst-schedule area bounds yield an arrival-growth boundary for joint
sublinear performance. On specified repeated-update families, temporary
membership tasks impose rapid-maintenance regret costs, while separate
constructions attain deferred and intermediate service levels. We develop
Flexible Certificate-Cost Planning (F-CCP) as a tunable implementation. It
combines sequential evidence and local certificate planning with a chosen
reward kernel and separate observable budgets for reward and
certification. Its guarantees include label reliability, unconditional
expected-regret protection, and service-rate area bounds that retain
budget rejections. Fixed-checkpoint and activation-budgeted constructions
remain distinct analytical witnesses. Frozen paired experiments show
lower mean costs in many finite-budget comparisons, together with
exceptions, heavier regret tails, and nonzero reporting failures. These
results do not characterize a general regret--maintenance frontier.'''
header=re.sub(r'(?<=\\begin\{abstract\})[\s\S]*?(?=\\end\{abstract\})','\n'+abstract+'\n',header)
header=header.replace('dynamic regret; simultaneous inference.','dynamic regret; confidence sequences.')

intro=parts[0]
cut=intro.index('An explicit fixed-precision procedure, Checkpoint-UCB, supplies the')
intro=intro[:cut]
intro=intro.replace('The deferred endpoint has only an upper bound, and the general frontier\nover intermediate budgets and overlapping arrivals remains open.','The deferred endpoint has only an upper bound. A separate activation-budgeted\nwitness covers an intermediate interval on a more strongly separated family;\nthe general causal frontier under overlapping arrivals remains open.')
intro+=r'''
Fixed checkpoints make attainable costs explicit, but their quotas can
consume a moderate budget before useful reports appear. F-CCP uses every
observation to update valid reporting evidence and plans one certificate
observation at a time. A predictable priority controls the proposed
service rate. Separate budgets limit the virtual-index cost of reward
choices and of certification, so exploration by the reward kernel does
not exhaust the certification account. The resulting guarantees concern
reliability, regret protection, and conditional service bounds; the
local planning proxy is not a solution of the full statistical
allocation problem. The fixed-checkpoint witnesses are retained for
their original guarantees in the supplement.

The components have precedents. Betting processes provide time-uniform
inference for bounded means \citep{waudbysmith2024betting}; our particular
mixture and its bounded-reward validity are proved explicitly.
Thompson sampling supplies a flexible reward rule \citep{thompson1933}.
MOTS obtains fixed-arm minimax guarantees by modifying sampled scores
\citep{jin2021mots}. Our protection instead constrains the virtual-index
cost of the actual selected action under arrivals, and does not transfer
MOTS's theorem to a cold-temperature Beta rule. Conservative bandits
control performance against a fixed baseline \citep{wu2016conservative};
the two accounts here control index deficits and are not realized
shortfalls from a separately run baseline. The spectral accounting and
MC-MOSS concentration tools are inputs from the companion work
\citep{temporalgeometry2026}, not a new characterization claimed here.

Information about future task expiration also matters. A schedule-specific
comparator can defer a temporary question in a way that one causal policy
facing an unknown schedule cannot reproduce uniformly. We retain that
information distinction and an activation-budgeted intermediate-regime
result alongside the general maintenance bounds. The latter uses its own
window conditions and is not an optimality claim for F-CCP.

Section~\ref{sec:model} fixes the joint task and separates task parameters
from allocation preferences. Section~\ref{sec:method} presents F-CCP and
its guarantees. Sections~\ref{sec:maintenance} and~\ref{sec:tradeoff}
give the general costs, temporary-task bounds, and information limits.
Section~\ref{sec:experiments} evaluates frozen configurations, including
mean improvements, tail costs, failed reports, and the corrected
same-controller comparison.
'''

model=parts[1]
start=model.index('The task parameters are fixed when comparing policies.')
end=model.index(r'\end{center}',start)+len(r'\end{center}')
model=model[:start]+r'''Task parameters are fixed within a comparison. Allocation preferences
change the strategy, rather than the reporting target. The parameters
used below have the following roles.
\begin{center}
\small
\begin{tabular}{lp{.67\textwidth}}
\toprule
Parameter & Role\\
\midrule
$\varepsilon,\eta\in(0,1)$ & Membership tolerance and exempt boundary width\\
$\delta\in(0,1/2)$ & Simultaneous reporting error budget\\
$\lambda_t\in[0,1]$ & Predictable preference for certification\\
$p_0\in(0,1),\ k_0>0,\ \nu>0$ & Service floor, backlog scale, and planning price floor\\
$\mathsf B,\ \theta>0$ & Reward-score kernel and its temperature\\
$\beta_R,\beta_C\in[0,\infty]$ & Fixed reward and certification guard coefficients\\
$\rho$ & Auxiliary checkpoint precision; F-CCP uses $\eta/4$\\
\bottomrule
\end{tabular}
\end{center}
The fixed-checkpoint witnesses may prescribe other precisions before
observations. Preference switching does not change
$\varepsilon,\eta,\delta$, create observations, or reset accumulated
evidence or budget accounts.
'''+model[end:]
model+=r'''
Arms with close means need not be close to the relative boundary
$r^*(t)-\varepsilon$. Conversely, a candidate near that boundary can
require fine evidence even when its reward gap is appreciable. The
algorithm's observable work set is therefore defined from confidence
intervals, not from the evaluator's true gaps or unresolved area.
'''

costs=parts[3]
costs=costs.replace("It is distinct from the algorithm's FIFO queue $\\mathcal Q^{\\rm srv}$ and\ndoes not impose a pathwise sampling quota on every candidate.","It is distinct from F-CCP's phased service rule and from the\nfixed-checkpoint witness's FIFO queue. It imposes no pathwise sampling\nquota on every candidate.")
costs=costs.replace('Checkpoint-UCB with $\\rho=\\eta/4$ attains the upper order and also satisfies',r'''Checkpoint-UCB with $\rho=\eta/4$ attains the upper order.
\end{theorem}

The same Checkpoint-UCB witness also satisfies''')
# The theorem's former closing delimiter now belongs before the companion bound.
pos=costs.index(r'\label{eq:joint_general}')
close=costs.index(r'\end{theorem}',pos)
costs=costs[:close]+costs[close+len(r'\end{theorem}'):]
needle='this worst-schedule lower construction itself requires no repeated arrivals.'
costs=costs.replace(needle,needle+r'''

The classification-priority mode of F-CCP, with $\lambda=1$ and no
certification guard, attains the same worst-area order by
Theorem~\ref{thm:fccp-area}. Its constants and reward bound are stated
separately. The explicit constants in \eqref{eq:worst_area} and
\eqref{eq:joint_general} continue to refer to the fixed-checkpoint
witness in Supplementary Section~\ref{app:checkpoint_construction}.''')
costs=costs.replace('Proposition~\\ref{prop:reporting}.','Supplementary Proposition~\\ref{prop:reporting}.')

tasks=parts[4]
tasks=tasks.replace(r'\section{Temporary membership tasks and regret trade-offs}',r'\section{Temporary tasks and limits of the regret--maintenance trade-off}')
start=tasks.index(r'\subsection{Shared evidence for area and reward guarantees}')
end=tasks.index(r'\subsection{Rapid and deferred maintenance at the same endpoint}',start)
tasks=tasks[:start]+r'''\subsection{Shared evidence and the two endpoint witnesses}

A saved upper endpoint for an old candidate can be compared with the lower
endpoint of a later reference. In the separated-window construction,
\[
 u_{e,k}<\ell_{e+1,\mathrm{ref}}-\varepsilon
\]
certifies exclusion after the new reference matures. No new observation
of that old candidate is needed for this report, although the reward
layer remains free to select it. Reference identities in this explanation
are analytical roles, not information supplied to the policy.
Supplementary Proposition~\ref{thm:reuse} gives the complete heterogeneous
conditions, unresolved-area bound, and unconditional regret bound for
Checkpoint-UCB. Each quota is charged once over the arm's lifetime, and
the birth-window condition is essential. These guarantees do not apply
to arbitrary F-CCP configurations by renaming the method.

'''+tasks[end:]
tasks=tasks.replace('or that all\nintermediate budgets are characterized.','or that all\nintermediate budgets are characterized on this family and horizon.')
tasks+=r'''
\subsection{Information limits and intermediate service levels}

A policy designed separately for each known schedule has more information
than one causal policy required to work across an unknown schedule class.
Both still lack the true reward means. Supplementary
Theorem~\ref{thm:schedule-separation} constructs early and late improvements
with the same horizon, area budget, final arm count, and common initial
history. Timely service on the late schedule forces an inverse-square
cost on the early schedule, while an early-schedule comparator has a
logarithmic upper bound. This rules out a universal constant-factor
comparison with every separately optimized schedule frontier. It does
not rule out an optimal policy for a common causal minimax problem.

There is also a positive intermediate-budget result on a more strongly
separated repeated-update family. Write $m=JM$, $V=mH$, and
$k(a)=\lceil(V-a)/H\rceil$. The activation-budgeted maintenance witness
(ABM) uses coarse lifetime checkpoints, then at most $s$ fine candidates
and corresponding references. Fine evidence is collected from new
observation blocks after predictable activation, with confidence budgets
assigned by activation rank. Under the separate window conditions in
Supplementary Theorem~\ref{thm:abm-intermediate}, for
$A_{\min}\le a<V$,
\[
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}\delta
 \le\mathfrak R_{\Theta_{\rm ABM}}(a)
 \le R_0(T)+1024\frac{\varepsilon k(a)}{d^2}\log\frac{k(a)}\delta.
\]
The supplement defines $A_{\min}$ and the retained additive reward cost
$R_0(T)$, and gives the full construction and proof. This family uses a
different $H$ from \eqref{eq:chosen_horizon}. Given $s$, the witness does
not need future arrivals; calibrating $s$ from an area target uses the
performance family's $m,H$ and other analysis quantities. The interval
result belongs to ABM, not to the preference parameter of F-CCP, and
leaves smaller budgets and general overlapping arrivals unresolved.
'''

ending=r'''\section{Discussion}
\label{sec:discussion}

Reliable maintenance has costs that reward allocation alone does not
measure. An uncertain arrival can obstruct many positive reports, while
a later improvement can end a fine membership task. The general lower
bounds quantify these effects. The worst-area lower bound answers a
different question and is already attained by an initial static batch;
the fixed-schedule and terminal-count growth consequences retain
different quantifiers.

F-CCP adds an implementable choice of emphasis to this task. Its evidence
layer uses every observation, its certificate planner proposes a single
next observation, and separate accounts control reward and certification
costs. Finite guards protect the spectral regret order but can reject
service; the area bound retains that rejection cost. Classification
priority with no certification guard achieves the worst-area order,
without being fastest on every instance. A compatibility endpoint
recovers a specified baseline from the start under identical state and
randomization. The default cold-temperature reward mode has a different
contract.

The frozen experiments support lower mean reward costs for F-R in most
of the specified comparisons and useful finite-budget trade-offs for
the service modes. They also show an exception in the two-arm close-mean
case, heavier empirical regret tails than Thompson sampling in three
environments, and a nonzero label-error record for the balanced mode.
Pure-reward improvements cannot be attributed to certificate scheduling
that was switched off. The corrected matched-cost ALL comparison is
distinct from the retained superseded controller result. These findings
concern the frozen suite, not uniform dominance or a general frontier.

The activation-budgeted witness characterizes an intermediate interval
on a sufficiently separated family, with an additive reward term and
its own information requirements. General causal frontiers under
unknown and overlapping arrivals remain open. The schedule-information
separation does not make every causal comparison impossible. Likewise,
the one-step zero-remainder counterexample leaves room for comparisons
with an explicit adaptation cost or a restricted performance family.

Automatic precision, reward kernels with better tail behavior, a faithful
adaptation of the original ALL-$\varepsilon$ algorithms, and large-pool
planning costs need further study. The supplement's eventual exact-set
consistency theorem belongs to a separate revisable multiresolution
procedure under finite final arrivals and strict boundary separation.
F-CCP's coverage-event completion outside a boundary band is a different
statement.

\section*{Data and code availability}
The accompanying materials contain simulated data, frozen configurations,
code, and the scripts used to generate the article's tables and figures.
The principal test has 27,648 recorded runs; a subsequent 1,152-run
matched-cost ALL correction is retained separately, together with the
superseded comparator. Replacing that comparator for the principal
analysis leaves 24 configurations and 27,648 records. Earlier checkpoint
comparisons contain 5,760 records and are reported separately in the
supplement; the preceding CCP and frontier research suites retain their
own protocols and archives. All reported failures remain in the analysis.
The available implementation distinguishes the frozen dual-account
production engine from the interactive interface and the development
branches. These materials are provided locally with the project; no
public repository or permanent archive identifier has been verified for
this version.

\bibliographystyle{plainnat}
\bibliography{references}
\end{document}
'''
result={'header':header,'introduction':intro,'model':model,'costs':costs,'temporary_tasks':tasks,'ending':ending}
(REV/'editorial_main.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:len(v) for k,v in result.items()}))

"""Assemble retained supplement modules without creating additional TeX files.

Inputs are the frozen revision-2 baseline and the source research notes.
Only the JSON modules and provenance records in revision2 are written.
"""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "baseline"
main = (BASE / "manuscript.tex").read_text(encoding="utf-8")
supp = (BASE / "supplement.tex").read_text(encoding="utf-8")


def split_sections(source):
    matches = list(re.finditer(r"(?m)^\\section\{", source))
    result = []
    for j, match in enumerate(matches):
        end = matches[j + 1].start() if j + 1 < len(matches) else len(source)
        result.append(source[match.start():end])
    return result


old = split_sections(supp)
ms = split_sections(main)
assert len(old) == 13
assert len(ms) == 7
old[-1] = old[-1].split("\\FloatBarrier\n\\bibliographystyle", 1)[0]


def title(block, replacement):
    return re.sub(r"^\\section\{[^\n]+\}", lambda _: replacement, block, count=1)


header = supp[:supp.index("\\section{Probability tools")]
header = header.replace("\\renewcommand{\\thepage}{S-\\arabic{page}}",
    "\\renewcommand{\\thepage}{S-\\arabic{page}}\n"
    "\\renewcommand{\\thealgorithm}{S\\arabic{algorithm}}\n"
    "\\providecommand{\\theHalgorithm}{S\\arabic{algorithm}}\n"
    "\\renewcommand{\\theHalgorithm}{S\\arabic{algorithm}}")
header += "\\tableofcontents\n\\medskip\n"

tools = old[0]
prefix_start = tools.index("With\n\\[")
checkpoint_start = tools.index("The checkpoint alternative fixes")
kl_start = tools.index("For two Bernoulli mean vectors")
s1 = tools[:prefix_start] + tools[kl_start:]
s1 = title(s1, r"\section{Probability tools and risk conventions}")
s1 += r"""
The primary risk combines an unconditional expectation for $R_T$ with a
joint high-probability requirement for labels and unresolved area at each
fixed deterministic endpoint. A common coverage event can yield upper
bounds simultaneously in all endpoints; it does not change the quantifiers
in the lower-bound risk. The fixed-checkpoint, all-prefix, and mixed-evidence
reporters below have separate failure conventions. In particular, the
historical all-prefix convention in Section~\ref{app:legacy-prefix} is not
the persistent-failure convention of F-CCP.
"""

checkpoint_main = title(ms[2], r"\section{Checkpoint-UCB as an attainability witness}")
checkpoint_main = checkpoint_main.replace(r"\label{sec:method}", r"\label{app:checkpoint_construction}")
checkpoint_main = checkpoint_main.replace(
    "The upper bounds use a fixed-precision construction, Checkpoint-UCB. Its",
    "The original explicit upper bounds use Checkpoint-UCB as a fixed-precision\n"
    "attainability witness. It is distinct from F-CCP in its evidence, service\n"
    "schedule, and reward rule. Its")
proof_intro = checkpoint_main.index("Hoeffding's inequality bounds the failure")
checkpoint_main = checkpoint_main[:proof_intro]
report_proof = tools[tools.index("The sum of coverage failures", checkpoint_start):kl_start]
joint = old[1]
reward_start = joint.index(r"\paragraph{A reward bound")
s5 = checkpoint_main + "\n\\subsection{Reporting proof and fixed-prefix evidence}\n" + report_proof
s5 += "\n\\subsection{Unconditional reward and completion guarantees}\n\\label{app:joint}\n" + joint[reward_start:]

s6 = old[2]
s7 = title(old[3], r"\section{Partial recovery, worst area, and growth}")
s7 += title(old[4], r"\subsection{Worst-schedule area and growth consequences}")
s8 = old[5]
reuse_main = ms[4][ms[4].index(r"\subsection{Shared evidence for area and reward guarantees}"):ms[4].index(r"\subsection{Rapid and deferred maintenance")]
s9 = title(old[6], r"\section{Shared evidence and two endpoint witnesses}")
reuse_proof_start = s9.index(r"\subsection{Shared evidence across separated windows}")
reuse_proof_end = s9.index(r"\subsection{Rapid and deferred endpoints on one family}")
old_reuse_proof = s9[reuse_proof_start:reuse_proof_end]
old_reuse_proof = old_reuse_proof[old_reuse_proof.index("The algorithm is not told"):]
s9 = s9[:reuse_proof_start] + reuse_main + "\n\\begin{proof}\n" + old_reuse_proof + "\\end{proof}\n\n" + s9[reuse_proof_end:]
s9 += title(old[11], r"\subsection{Earlier intermediate configurations and disclosed-reference diagnostic}")
s9 = s9.replace("These are attainable points, not a proof of optimality at every area budget.",
    "These are attainable points, not a proof of optimality at every area budget.\n"
    "They are distinct from the activation-ranked construction in\n"
    "Section~\\ref{app:abm}, which uses a different window contract.")
s10 = old[7]
s11 = title(old[8], r"\section{General lower-bound extensions}")
s11 = s11.replace(r"\label{sec:truncated_extension}",
    "\\label{sec:truncated_extension}\n\\subsection{Compatible-window truncated area}")
s11 += title(old[10], r"\subsection{General information-allocation relaxation}")
s14 = title(old[9], r"\section{A separate exact-consistency extension}")
s14 = s14.replace("than the fixed-checkpoint policy.",
    "than the fixed-checkpoint policy or F-CCP. Its reports are repeatedly\n"
    "recomputed, so it has no persistent reporting-failure state. This\n"
    "almost-sure conclusion is not a property of F-CCP.")

s17 = title(ms[5], r"\section{Earlier checkpoint comparison}")
s17 = s17.replace(r"\label{sec:experiments}", r"\label{app:legacy-checkpoint}")
s17 = s17.replace("The experiments compare reward allocation", "This earlier, separate experiment compares reward allocation")
s17 = s17.replace("The four environments\nare not", "Its four environments\nare not")
s17 = s17.replace("in the main article", "in this section")
s17 = s17.replace("as the main path figure", "as Figure~\\ref{fig:paths}")
s17 = s17.replace("as the main\npath figure", "as Figure~\\ref{fig:paths}")
s17 = s17.replace("in the main path figure", "in Figure~\\ref{fig:paths}")
s17 = s17.replace("The main table displays six methods", "Table~\\ref{tab:simulation} displays six methods")
s17 = s17.replace("main-table methods", "methods in Table~\\ref{tab:simulation}")
s17 = s17.replace("in the main path figure", "in Figure~\\ref{fig:paths}")
s17 = s17.replace("in the main\npath figure", "in Figure~\\ref{fig:paths}")
s17 = s17.replace("main table", "legacy table")
s17 = s17.replace("main path figure", "legacy path figure")
s17 = s17.replace("in the main article", "above")
s17 += title(old[12], r"\subsection{Computational details of the earlier experiment}")
s17 += r"""
\subsection{Historical all-prefix report}
\label{app:legacy-prefix}
The all-prefix reporter in this earlier comparison uses the following
Hoeffding intervals. These are separate from F-CCP's mixed evidence and
its persistent reporting-failure rule.
""" + tools[prefix_start:checkpoint_start]
s17 = s17.replace(r"\caption{Final cumulative dynamic regret", r"\caption{Earlier checkpoint comparison: final cumulative dynamic regret")
s17 = s17.replace("The numerical study has four environments", "This earlier numerical study has four environments")
s17 = s17.replace("In this revision, separate short", "During the first revision, separate short")
s17 = s17.replace("The revision also\nrecomputes", "That revision also\nrecomputed")
s17 = s17.replace("The main table displays six methods", "Table~\\ref{tab:simulation} displays six methods")
s17 = s17.replace("in the main article", "in this section")
s17 = s17.replace("as the main path figure", "as Figure~\\ref{fig:paths}")
s17 = s17.replace("as the main\npath figure", "as Figure~\\ref{fig:paths}")
s17 = s17.replace("main-table rows", "legacy-table rows")
s17 = s17.replace("in the main path figure", "in Figure~\\ref{fig:paths}")
s17 = s17.replace("in the main\npath figure", "in Figure~\\ref{fig:paths}")
s17 = s17.replace(r"\label{tab:simulation}", "\\label{tab:simulation}\n\\label{tab:legacy-checkpoint}")
s17 = s17.replace(r"\label{fig:cost-area}", "\\label{fig:cost-area}\n\\label{fig:legacy-costs}")
s17 = s17.replace(r"\label{fig:paths}", "\\label{fig:paths}\n\\label{fig:legacy-paths}")

S12 = r"""
\section{Schedule information and causal comparison}
\label{app:schedule-information}

Two comparison classes use different schedule information. For a fixed
schedule $\tau$, write $\mathfrak R^{\rm sch}_{T,\tau}(a;\Theta)$ for the
infimum of worst-case expected regret when the policy can be designed
knowing $T$ and $\tau$. It must remain label-reliable on the full bounded
model, and its area requirement is imposed on $\Theta$. In
$\mathfrak R^{\rm causal}_{T,\mathcal T}(a;\Theta)$, one policy sees only
arrivals that have already occurred and must satisfy the area requirement
on every schedule in $\mathcal T$. Neither class is told the realized
reward environment. The following separation concerns simultaneous
comparison with the first class, rather than nonexistence of an optimum
in the second class.

\begin{theorem}[A schedule-information separation]
\label{thm:schedule-separation}
Fix $\varepsilon=1/8$, $v=1/32$, $0<\delta\le1/16$, and take
$0<d\le1/1024$, with $\eta=d/2$. There are three Bernoulli arms with means
\[
 r_0=1/2,\qquad r_1=1/2-\varepsilon+\sigma d,\qquad
 r_2=1/2+v,\qquad \sigma\in\{-1,+1\}.
\]
Arms 0 and 1 arrive at time 1. Define
\[
 Q_f=\left\lceil32d^{-2}\log(24/\delta)\right\rceil,
 \quad h=16Q_f,\quad
 L_d=\frac{\kl(1-\delta,\delta)}
 {\kl(1/2-\varepsilon-d,1/2-\varepsilon+d)},
\]
\[
 w=\lfloor L_d/2\rfloor,\qquad a=h+w,\qquad T=2(a+1).
\]
The early schedule has $\tau_2=h+1$, and the late schedule has $\tau_2=T$.
They have the same endpoint, area budget, final arm count, and task
parameters. Every one causal policy satisfying the joint label--area
requirement on both signs of the late schedule obeys
\[
 E_{-,\rm early}R_T\ge\varepsilon(L_d/2-1)=\Omega_\delta(d^{-2}).
\]
For all sufficiently small $d$, both schedules have feasible area
requirements, while
\[
 \mathfrak R^{\rm sch}_{T,\tau^{\rm early}}(a;\Theta)
       =O_{\varepsilon,v,\delta}(\log(1/d)).
\]
Consequently no universal constant gives one unknown-future policy a
simultaneous constant-factor comparison with the separately optimized
schedule-informed values. This remains so if the policy knows $T,a$,
the two possible schedules, the final count, and the performance family.
\end{theorem}

\begin{proof}
On the late schedule, arm 1's membership through $t_0=a+1<T$ equals its
sign and has boundary distance $d>\eta$. If it has never received a
determinate report by $t_0$, it alone contributes $a+1$ unresolved area.
Joint label--area success therefore forces a correct report by $t_0$.
Let $F$ be the event that arm 1 has been reported non-near-optimal by
$t_0$. Then $P_-F\ge1-\delta$ and $P_+F\le\delta$. Applying the
history-KL identity in \eqref{eq:app_kl_identity} gives
\[
 E_{-,\rm late}N_1(t_0)\ge L_d.
\]
Only $w+1$ observations can occur from $h+1$ through $t_0$, whence
\[
 E_{-,\rm late}N_1(h)\ge L_d-w-1\ge L_d/2-1.
\]
The arrival and reward histories through $h$ have identical laws under
the early and late schedules. The same causal policy therefore has the
same law of $N_1(h)$ on both. Every pull of arm 1 in this common prefix
costs at least $\varepsilon$, proving the lower bound. The Bernoulli
parameters remain in the interior of $[0,1]$, so
$L_d\asymp_\delta d^{-2}$.

It remains to verify feasibility and the early upper bound. On the late
schedule, use Checkpoint-UCB with $\rho_f=d/4$. Each of the first two
quotas is at most $Q_f$, and even-round service completes them within
$4Q_f$ physical rounds. On checkpoint coverage the first two arms are
then classified, so their initial area is at most $8Q_f$. The last-round
arrival contributes at most 3 additional arm--time pairs. Thus
$\mathcal U_T\le8Q_f+3<a$ for small $d$.

On the early schedule, use instead $\rho_c=v/8$ and set
\[
 Q_c=\left\lceil128v^{-2}\log(48/\delta)\right\rceil.
\]
All three quotas are at most $Q_c$, independent of $d$. The initial
coarse evidence is complete within $4Q_c$ rounds. It certifies the old
reference positively; arm 1 may remain unresolved. The new reference
completes its evidence within $2Q_c$ rounds of arrival. Since
$d+2\rho_c<v$, its lower endpoint and arm 1's saved upper endpoint
exclude arm 1, while both reference arms are positively certified.
Consequently
\[
 \mathcal U_T\le h+10Q_c\le h+w=a
\]
for all sufficiently small $d$. Both feasibility statements hold on
the fixed-checkpoint coverage event, whose probability is at least
$1-\delta/2$.

The early coarse policy uses at most $3Q_c$ designated observations.
Every positive gap in this family is at least $v$. The unconditional
UCB counting argument of Section~\ref{app:joint} therefore bounds its
expected regret by $3Q_c+O_v(\log T)$, and $T\asymp_\delta d^{-2}$.
Both policies report through valid full-model confidence intervals;
they do not label arms by inserting the performance family's means.
The lower bound already holds in a fixed negative-sign environment;
no endpoint-dependent selection from a prior is required here.
\end{proof}

The result does not rule out causal minimax optimization over a common
schedule class, nor optimization on a known schedule. It also gives no
claim that F-CCP attains the causal joint frontier.

\paragraph{Finite spectrum protection and very rapid maintenance.}
In the original repeated-update family, fix $J,M,\varepsilon,v,\delta$
and let $d\downarrow0$ under its prescribed endpoint. Then
$T\asymp d^{-2}$ and $K$ is fixed, while the rapid area budget requires
$\Omega(d^{-2})$ expected regret. Any strategy with a fixed-constant
bound $ER_T\le C\mathcal S_T=O(\sqrt T)=O(d^{-1})$ cannot satisfy that
rapid budget. Thus a fixed finite protection coefficient cannot cover
this regime; the allowed coefficient must grow at least on the
$d^{-1}$ scale or the budget mechanism must change. This is a
compatibility consequence of the existing upper and lower bounds,
not a simultaneous attainability statement.
"""

S13 = r"""
\section{Activation-budgeted intermediate maintenance}
\label{app:abm}

This section gives a separate theoretical construction,
Activation-Budgeted Maintenance (ABM). Its confidence allocation is by
fine-task activation rank. ABM is neither F-CCP nor the shared-certificate
scheduler evaluated during development. Its window contract below is
different from the fixed horizon used for the earlier two endpoints.

\subsection{Recovery of an arbitrary number of coordinates}

\begin{theorem}[Arbitrary-subset simultaneous recovery]
\label{thm:any-subset-recovery}
Let $m\ge1$ independent uniform signs specify independent laws
$P_i^+,P_i^-$. Other observations carry no information about the signs.
Sampling may be adaptive and interleaved, with independent policy
randomization and a bounded stopping time $\tau$. Suppose
\[
 0<\kappa=\max_i\max\{D(P_i^+\Vert P_i^-),
                           D(P_i^-\Vert P_i^+)\}<\infty.
\]
At stopping, a data-dependent subset $S$ receives sign reports, with
probability of any reported error at most $0<\delta\le1/16$ under every
sign configuration. If $1\le s\le m$ is an integer and
$\overline P(|S|\ge s)\ge1/2$, then
\[
 \overline E\sum_iN_i(\tau)\ge
                \frac{s}{48\kappa}\log\frac{s}{\delta}.
\]
The bar uses one independent-sign product prior, solely as a proof device.
\end{theorem}

\begin{proof}
Let $L_i$ be coordinate $i$'s observed positive-versus-negative log
likelihood ratio. Conditional on the full stopped history, action,
stopping, and reporting kernels cancel. The likelihood and posterior
factor over signs even though the random sample counts are dependent.
The minimum posterior error for sign $i$ is
\[
 e_i=(1+e^{|L_i|})^{-1}\in(0,1/2].
\]
Any actual report has conditional probability of complete correctness
at most $\prod_{i\in S}(1-e_i)$, hence
\[
 \overline E\left[1-\prod_{i\in S}(1-e_i)\right]\le\delta.
\]
With probability at least $3/4$, this product is at least $1-4\delta$.
On that event,
\[
 \sum_{i\in S}e_i\le v_\delta:=-\log(1-4\delta)
                              \le16\delta/3.
\]
Its intersection with $|S|\ge s$ has probability at least $1/4$.
Define
\[
 f(e)=(1-2e)\log((1-e)/e),\qquad 0<e\le1/2.
\]
The function is nonnegative, decreasing, and convex, with
$f''(e)=1/\{e^2(1-e)^2\}$. Conditional on the stopped history,
$E(\sigma_iL_i\mid H_\tau)=f(e_i)$. Taking conditional expectations
of the successive signed likelihood increments gives
\[
 \overline E\sum_i f(e_i)=\overline E\sum_i\sigma_iL_i
                   \le\kappa\overline E\sum_iN_i(\tau).
\]
Bounded stopping and finite two-way KL make these increments integrable.
On the intersection event, write $k=|S|\ge s$. Convexity and monotonicity
give
\[
 \sum_i f(e_i)\ge k f(v_\delta/k)\ge s f(v_\delta/s).
\]
Here $v_\delta/s\le1/3$, so
\[
 f(v_\delta/s)\ge\frac13\log\frac{s}{8\delta}
                   \ge\frac1{12}\log\frac{s}{\delta}.
\]
The last step uses $s/\delta\ge16$. Multiply by the intersection
probability $1/4$ and use the information-drift bound. In particular,
no subtraction proportional to all $m$ coordinates is needed when
$s\ll m$. Zero posterior errors can be handled by limits; finite
stopping and the integrability just noted exclude uncontrolled infinite
expectations.
\end{proof}

The half-recovery lemma in Section~\ref{app:partial} remains the
dependency for the older constants and probability bounds. The new
constant is used only for the arbitrary-recovery extension below.

\subsection{Area-to-cost lower bound with a free window length}

Let
\[
 J\ge1,\quad M\ge\max\{2,J\},\quad 0<\varepsilon\le1/8,\quad
 0<\delta\le1/16,\quad Jv\le\varepsilon/4,\quad
 0<d\le v/32,\quad\eta=d/2.
\]
Set $m=JM$ and $K=J(M+1)+1$. At time $1+eH$, for
$e=0,\ldots,J-1$, release a reference of mean $b_e=1/2+ev$ and
$M$ candidates of means
\[
 r_{e,k}=b_e-\varepsilon+\sigma_{e,k}d.
\]
At time $1+JH$ release only the final reference $b_J$. Include all
sign configurations and within-batch permutations in the performance
family, denoted $\Theta_H$. Set $T=(J+1)H$ and $V=mH$. Reference
identities are not given to the upper-bound policy. Every candidate
has regret gap at least $\varepsilon-d\ge\varepsilon/2$ at every time
after its arrival.

\begin{theorem}[Necessary cost at any area below $V$]
\label{thm:abm-area-lower}
For $0\le a<V$ and $k(a)=\lceil(V-a)/H\rceil$,
\[
 \mathfrak R_{\Theta_H}(a)\ge
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}{\delta}.
\]
The assertion includes the case of an infeasible area budget, when the
left side is infinite.
\end{theorem}
\begin{proof}
For each candidate retain its first determinate label within its own
birth window, if there is one. Only that label estimates its sign; a
negative report after the next reference arrives is not an answer to
the expired sign question. A candidate never labeled in its window
contributes $H$ area, because its boundary distance there is
$d>\eta$. Thus joint label--area success forces at least $k(a)$
retained labels, all correct.

Use one product prior on all $m$ signs and apply
Theorem~\ref{thm:any-subset-recovery} at deterministic stopping time
$T$. The recovery-count event has probability at least
$1-\delta>1/2$. Interior Bernoulli parameters give two-way KL at most
$32d^2$, so
\[
 \overline E\sum_{e,k}N_{e,k}(T)
       \ge\frac{k(a)}{1536d^2}\log\frac{k(a)}{\delta}.
\]
This count includes observations after each validity window. Such
observations can still encode the old sign and must remain in the KL
accounting; their regret is still at least $\varepsilon/2$ each.
The expected regret under the common prior therefore has the stated
lower bound. At least one fixed sign configuration attains the prior
average, and taking the infimum over feasible policies completes the proof.
\end{proof}

\subsection{ABM and predictable fresh-block evidence}

ABM takes $\varepsilon,\delta,\rho_c,\rho_f$ and an integer fine-candidate
budget $s\ge0$. Its operational inputs contain no horizon, window
length, future arrivals, means, or reference identities. It records
arrival batches and keeps all observations in lifetime reward estimates.
For arrival-order arm $i$, its coarse quota is
\[
 q_i^c=\left\lceil2\rho_c^{-2}
                     \log\{4i(i+1)/\delta\}\right\rceil.
\]
When this lifetime count is first attained, its first $q_i^c$ observations
give a saved coarse interval with radius $\rho_c/2$, clipped to $[0,1]$.
These coarse errors total at most $\delta/2$.

After all coarse checkpoints of a batch complete, choose its largest
saved coarse mean, breaking ties by arrival-order label. From the
remaining arms choose, in label order, at most the remaining fine-candidate
budget. Whenever at least one candidate is selected, also activate a fine
task for that batch's empirical best arm. There are at most $s$ selected
candidates and at most $s$ associated reference tasks. Rank these fine
activations by $r=1,2,\ldots$, placing the empirical best first within its
batch. Activation rank $r$ is assigned the quota
\[
 q_r^f=\left\lceil2\rho_f^{-2}
                       \log\{4r(r+1)/\delta\}\right\rceil.
\]
Its count starts at zero immediately after activation. Only subsequently
observed rewards of that arm enter this block, including ordinary UCB
observations. The observation which completed the coarse batch and
triggered activation is excluded from its new fine block. On reaching
$q_r^f$ fresh observations, save a fine interval of radius $\rho_f/2$.
Old data remain in the lifetime reward estimates and coarse evidence;
they are not recycled as an activation-selected fixed prefix.

At even physical rounds, coarse FIFO tasks have priority, followed by
fine tasks in activation order. At other rounds, or when both queues
are empty, use the full-history UCB rule \eqref{eq:ucb}. Both kinds of
observation update the same lifetime statistics, and an active fine
block receives an observation only if it was active before that
observation. Reports use the intersection of available coarse and fine
intervals and the comparisons \eqref{eq:reports}; negative reporting
does not remove reward eligibility. An empty intersection triggers
all-unresolved reports thereafter, while the prescribed reward and
queue operations remain defined.

\begin{algorithm}[p]
\caption{Activation-Budgeted Maintenance (ABM)}
\label{alg:abm}
\begin{algorithmic}[1]
\Require $\varepsilon,\delta,\rho_c,\rho_f\in(0,1)$; integer $s\ge0$
\State Initialize empty coarse and fine FIFO queues, remaining budget $s$, fine rank $r=0$
\For{physical time $t=1,2,\ldots$}
 \State Receive the new batch; assign arrival-order labels and initialize lifetime counts and sums
 \State Set each new arm's coarse quota $q_i^c$; append it to the coarse queue
 \State Remove completed tasks from the fronts of both queues
 \If{$t$ is even and the coarse queue is nonempty}
   \State Select its front arm
 \ElsIf{$t$ is even and the fine queue is nonempty}
   \State Select its front arm
 \Else
   \State Select a largest full-history UCB index, using smallest-label ties
 \EndIf
 \State Observe one reward and update the selected arm's lifetime statistics
 \State Update its fine block if active before this observation and not yet complete
 \State At a quota crossing, form its corresponding coarse or fine interval
 \If{this observation newly completes all coarse checkpoints in its batch}
   \State Let $j$ be the batch's largest saved coarse mean, with smallest-label ties
   \State Select other batch arms in label order, up to the remaining candidate budget
   \If{at least one candidate was selected}
     \State Activate $j$ first, then the selected candidates, each with the next rank $r$
     \State Give rank $r$ quota $q_r^f$, zero fresh count and sum, and append its task
     \State Decrease the remaining budget by the number of selected candidates
   \EndIf
 \EndIf
 \State Report from saved-interval intersections; an empty intersection gives persistent all-unresolved reports
\EndFor
\end{algorithmic}
\end{algorithm}

The fresh-block Hoeffding bound remains valid conditional on activation
history. The next unrevealed suffix of the selected iid arm stream
retains its iid law, even when its identity and activation time depend
on past data. Apply the conditional bound first at bounded activation
times and then take expectations; a task never activated has no failure
event. Fine-rank errors total at most
$\sum_{r\ge1}\delta/\{2r(r+1)\}=\delta/2$.
Together with coarse coverage, this gives full-model all-time label
reliability at least $1-\delta$. This argument requires fresh
post-activation observations and does not validate reassigning a
smaller error budget to a previously selected old prefix.

\subsection{A sufficiently separated window contract}

On $\Theta_H$, choose $\rho_c=v/8$ and $\rho_f=d/4=\eta/2$.
The coarse precision is a selected service parameter, not an estimate
that automatically learns $v$. Define the analysis quantities
\[
 Q_c=\left\lceil128v^{-2}\log\frac{4K(K+1)}\delta\right\rceil,
 \quad Q_f(r)=\left\lceil32d^{-2}
                         \log\frac{4r(r+1)}\delta\right\rceil,
\]
\[
 L_c=2(M+1)Q_c,\quad L=L_c+2(M+1)Q_f(2m),
\]
\[
 B_{\rm rec}=L_c\left\{\frac{(J+1)(J+2)}2+JM\right\},
 \qquad H\ge4(L+B_{\rm rec}).
\]
Here $B_{\rm rec}$ is a recovery-area constant; it is not a best mean,
reward sum, or F-CCP budget. The displayed condition defines this
performance family and is not future information given to ABM.

\begin{theorem}[ABM area and unconditional reward cost]
\label{thm:abm-upper}
For $0\le s\le m$, ABM on this family satisfies
\[
 P\{E_{\rm lab},\mathcal U_T(\eta)
                   \le(m-s)H+sL+B_{\rm rec}\}\ge1-\delta.
\]
For $s\ge1$,
\[
 \sup_{\Theta_H}ER_T\le R_0(T)+4\varepsilon sQ_f(2s),
\]
where
\[
 R_0(T)=2\varepsilon KQ_c+
 128\left(\frac m\varepsilon+\frac{J^2}{v}\right)\log(2T)+1.
\]
For $s=0$, the upper bound is $R_0(T)$ without a fine-layer term.
\end{theorem}

\begin{proof}
For every reward path, a batch requires at most $(M+1)Q_c$ coarse
observations and $(M+1)Q_f(2m)$ fine fresh observations. Even-round
service, helped by ordinary observations, completes them within $L$
rounds of birth. Since $H\ge4(L+B_{\rm rec})$, induction over batches
leaves no queue backlog at the next arrival. This workload statement
does not rely on choosing the correct empirical reference.

On simultaneous coverage, each candidate is below its batch reference
by at least $\varepsilon-d$, so the saved coarse means select the true
reference. There are exactly $s$ selected candidates. Upon fine
completion, the selected candidate and reference endpoints have errors
at most $\rho_f$; $2\rho_f<d$ resolves their birth-window labels.
No old coarse upper endpoint can obstruct this fine comparison:
successive reference spacing satisfies $v>\rho_c+\rho_f$, and all
candidates are farther below the current reference. Thus these $s$
candidates contribute at most $sL$ in their birth windows, while the
others contribute at most $(m-s)H$.

The new batch's coarse evidence completes within $L_c$ rounds.
Because $d+2\rho_c<v$, its reference lower endpoint and the preceding
batch's saved candidate upper endpoints exclude that older cohort
without further old-candidate observations. Older exclusions persist.
Every reference has gap at most $\varepsilon/4$ and combined coarse
endpoint error at most $2\rho_c<\varepsilon/2$; all references are
therefore positively certified after the current coarse layer
completes. In window $e=0,\ldots,J$, this recovery can temporarily
affect at most $e+1$ references and the preceding candidate batch.
Its total area is bounded by
\[
 L_c\sum_{e=0}^J(e+1+M_{e-1})=B_{\rm rec},
 \qquad M_{-1}=M_J=0.
\]
This proves the joint area bound.

For expected regret, do not condition on interval coverage. Every
observation below its coarse quota is charged among at most $KQ_c$
observations, each with gap at most $2\varepsilon$. All designated
fine observations beyond these coarse counts are bounded by
$2sQ_f(2s)$, and each again costs at most $2\varepsilon$.
The remaining observations are ordinary full-history UCB pulls.
Candidate arms have minimum positive gap at least $3\varepsilon/4$
and maximum gap at most $2\varepsilon$; older references have minimum
positive gap at least $v$ and maximum gap at most $Jv$.
The distinct-count argument in Section~\ref{app:joint}, with its
summable bad-round loss below 1, is bounded by
$128(m/\varepsilon+J^2/v)\log(2T)+1$. First observations were already
charged to the coarse quotas. These counts remain valid on failure
paths, including paths on which a wrong empirical reference is chosen.
This gives the unconditional reward bound.
\end{proof}

\subsection{A matching interval with an explicit additive cost}

\begin{theorem}[Intermediate area budgets on $\Theta_H$]
\label{thm:abm-intermediate}
Set $A_{\min}=mL+B_{\rm rec}$. For
$A_{\min}\le a<V=mH$, let
\[
 s(a)=\left\lceil\frac{V+B_{\rm rec}-a}{H-L}\right\rceil.
\]
Then $1\le s(a)\le m$, ABM with candidate budget $s(a)$ attains area
budget $a$, and
\[
 \frac{\varepsilon k(a)}{3072d^2}\log\frac{k(a)}\delta
 \le\mathfrak R_{\Theta_H}(a)
 \le R_0(T)+1024\frac{\varepsilon k(a)}{d^2}
                                \log\frac{k(a)}\delta.
\]
\end{theorem}
\begin{proof}
The premise $a\ge mL+B_{\rm rec}$ gives $s(a)\le m$, and its
definition guarantees
$(m-s)H+sL+B_{\rm rec}\le a$. If $k=k(a)$, then $V-a\le kH$.
The separation condition gives
\[
 \frac{V+B_{\rm rec}-a}{H-L}
       \le\frac{kH+B_{\rm rec}}{H-L}\le2k.
\]
Since $2k$ is an integer, $s(a)\le2k$. For $s\ge1$,
\[
 \log\frac{4(2s)(2s+1)}\delta\le3\log(s/\delta),
 \quad Q_f(2s)\le97d^{-2}\log(s/\delta).
\]
Also $\log(2k/\delta)\le(5/4)\log(k/\delta)$. The fine term in
Theorem~\ref{thm:abm-upper} is therefore bounded by
\[
 388\varepsilon s d^{-2}\log(s/\delta)
       \le970\varepsilon k d^{-2}\log(k/\delta),
\]
which is at most the stated expression with constant 1024. The lower
bound is Theorem~\ref{thm:abm-area-lower}.
\end{proof}

For the explicit choice $H=16(L+B_{\rm rec})$,
\[
 \frac{A_{\min}}V\le\frac{1+1/m}{16}\le\frac3{32}<\frac18.
\]
Thus this separately calibrated family includes $V/8$ in its matching
interval and extends through intermediate $a<V$. At fixed
$J,M,\varepsilon,v,\delta$ and $d\downarrow0$, it has
$H,T=\Theta(d^{-2})$ and $R_0(T)=O(\log(1/d))$; the fine term is at
least of order $d^{-2}$. The additive $R_0(T)$ remains part of the
finite-sample statement and need not be negligible in joint growth
regimes.

The result does not characterize $a<A_{\min}$, the interval
$[V,V+B_{\rm rec})$, arbitrary overlapping arrivals, or the full
unknown-schedule frontier. For $a\ge V+B_{\rm rec}$, the coarse
strategy supplies an upper bound without a matching lower bound here.
ABM given $s$ uses no future arrivals; calibrating $s(a)$ from $a$
uses the performance-family values $m,H$. It is therefore not an
automatic future-free area-budget controller. Neither ABM's ordinary
UCB guarantee nor this intermediate interval is asserted for F-CCP.
"""

modules = dict(header=header, s1=s1, s5=s5, s6=s6, s7=s7, s8=s8,
               s9=s9, s10=s10, s11=s11, s12=S12, s13=S13,
               s14=s14, s17=s17)
(ROOT / "retained_supplement.json").write_text(
    json.dumps(modules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

claim_rows = []
condition_by_module = {
    "header": "independent iid [0,1] streams; deterministic permanent nonempty finite arrivals; one physical observation; reports after observation; expected regret plus joint high-probability label/area risk",
    "s1": "iid bounded potential prefixes; bounded stopping for KL; finite two-way KL for general laws; label/area probability distinct from expected regret",
    "s5": "0<rho<1 fixed before each arm's data; 0<delta<1/2; even-round FIFO; all-history UCB with 3 log(2t); coverage >=1-delta/2; completion rho=eta/4; arbitrary deterministic arrivals",
    "s6": "0<epsilon<=1/16; 0<delta<=1/16; 0<eta<epsilon/2; same reference environment and all one-candidate alternatives; deterministic difficult label from expected counts; q_- analytical queue; B_T>0 for probability statement",
    "s7": "half recovery: bounded stopping, independent uniform signs, finite two-way KL, delta<=1/16; worst area: K>=2,T>=1,epsilon<=1/8,eta<=epsilon/32,delta<=1/16; fixed schedule vs endpoint-count class quantifiers distinct; original Checkpoint constants 2^-24,256",
    "s8": "one product prior for all windows; each sign labels its candidate within own validity window; half-completion; high-probability area a; homogeneous a=JMH/8 gives original 2^-20 expected-regret constant",
    "s9": "heterogeneous: H_e>=2S_e,b_J-b_0<=epsilon/4,d_e+rho_e+rho_(e+1)<b_(e+1)-b_e,2 max rho_e<=epsilon/2; endpoint: J>=1,M>=max(2,J),epsilon<=1/8,delta<=1/16,Jv<=epsilon/4,d<=v/32,eta=d/2,H=128(M+J+1)q_f; deferred only upper; predetermined intermediate batch selection",
    "s10": "same original endpoint family; area <=JMH/8 with joint probability >=1-delta for every sign; bounded candidate-budget stopping at q+1,not q; L>=4; one fixed environment; probability >=11/80; joint-quantile variant separately defined",
    "s11": "compatible realizable windows; no duplicated candidate-time pair; independent signs; finite two-way KL; delta<=1/16; information relaxation keeps a+delta W and is necessary only",
    "s12": "epsilon=1/8,v=1/32,delta<=1/16,d<=1/1024 and sufficiently small; eta=d/2; same T,a,final count=3; common history through h; early and late each feasible; compares schedule-informed values against one causal policy",
    "s13": "J>=1,M>=max(2,J),epsilon<=1/8,delta<=1/16,Jv<=epsilon/4,d<=v/32,eta=d/2; any-s lemma 1<=s<=m,finite two-way KL,bounded stopping; ABM rho_c=v/8,rho_f=d/4,activation-ranked fresh blocks; H>=4(L+B_rec); intermediate A_min<=a<V; R0 retained; s(a) uses m,H; H differs from original endpoints",
    "s14": "independent multiresolution construction; arrivals eventually stop; finite final K; min_i |max_j r_j-r_i-epsilon|>0 for exact completeness; raw epoch intervals recomputed; no persistent failure absorption; not a property of F-CCP",
    "s17": "legacy data only: 4 scenarios,9 methods,160 paired replications,T=20000,epsilon=.30,eta=.10,delta=.05; 5760 records; fine640 all unresolved; old resource record not F17; legacy exclusion-first only for old prefix reporter",
}
for key, block in modules.items():
    for label in re.findall(r"\\label\{([^}]+)\}", block):
        source = "P16/theory_frontier.md sections 2-5 and abm.py" if key in {"s12", "s13"} else "M3/S3 frozen revision2/baseline"
        attribution = "ABM independent theoretical witness" if key == "s13" else ("schedule-information lower bound" if key == "s12" else "retained; original attribution")
        claim_rows.append({"label": label, "destination": key.upper(), "source": source,
                           "attribution": attribution, "proof_status": "translated and interface-checked" if key in {"s12", "s13"} else "retained proof",
                           "conditions": condition_by_module[key]})
for label, destination, proof_key in [
    ("thm:broadcast", "MAIN section 4; proof S6", "s6"),
    ("thm:worst_area", "MAIN section 4; proof S5/S7", "s7"),
    ("cor:growth", "MAIN section 4; proof S6/S7", "s7"),
    ("thm:tradeoff", "MAIN section 5; proof S8/S9", "s9"),
    ("thm:quantile_main", "MAIN section 5; proof S10", "s10"),
]:
    claim_rows.append({"label": label, "destination": destination,
                       "source": "M3 frozen revision2/baseline/manuscript.tex; S3 retained proof",
                       "attribution": "general lower bound or original Checkpoint witness; never renamed as F-CCP",
                       "proof_status": "retained statement and complete retained proof interface",
                       "conditions": condition_by_module[proof_key]})
with (ROOT / "claim-map-retained.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(claim_rows[0]))
    writer.writeheader(); writer.writerows(claim_rows)
print(json.dumps({"modules": list(modules), "labels": len(claim_rows),
                  "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in [BASE / "manuscript.tex", BASE / "supplement.tex"]}}, indent=2))

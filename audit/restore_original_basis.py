"""One-off record of the original-based revision, not a manuscript build step."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "audit/before_notation_alignment/manuscript.tex"
ORIGINAL = ROOT.parent / "JASA-template/mab_aa_main.tex"


def align(text):
    text = re.sub(r"\\mathcal\s*A_", r"\\mathcal U_", text)
    text = re.sub(r"\\widehat\\mu_\{([^,{}]+),([^{}]+)\}",
                  lambda m: r"\hat r_" + m[1] + "(" + m[2] + ")", text)
    text = text.replace(r"\sup_\mu", r"\sup_{\boldsymbol r}")
    text = text.replace(r"\Prob_\mu", r"\Prob_{\boldsymbol r}")
    text = re.sub(r"\\mu(?![A-Za-z])", "r", text)
    for decoration in ["underline", "overline"]:
        text = text.replace("\\" + decoration + " B_t",
                            "\\" + decoration + " r^*(t)")
    text = text.replace("B_t", "r^*(t)")
    for old, new in [("C_t", r"\mathcal P_t"), ("D_t", r"\mathcal N_t"),
                     ("V_t", r"\mathcal V_t"), ("G_t", r"\mathcal G_t"),
                     ("A_t", r"\mathcal{A}_t"), ("A_1", r"\mathcal{A}_1"),
                     ("S_t", r"\mathcal{A}^{\mathrm{adm}}_t"), ("F_t", "B_t")]:
        text = text.replace(old, new)
    text = text.replace("X_{i,n}", "Y_{i,n}")
    text = text.replace("random pseudo-regret", "cumulative dynamic regret")
    return text


def slice_section(text, start, end):
    return text[text.index(start):text.index(end)]


def original_paragraph(prefix):
    source = ORIGINAL.read_text(encoding="utf-8")
    paragraph = source[source.index(prefix):].split("\n\n", 1)[0]
    paragraph = paragraph.replace(r"\parencite", r"\citep").replace(r"\textcite", r"\citet")
    for old, new in {
        "ghalme2021ballooning": "ghalme2021",
        "10.1007/s10994-010-5178-7": "kleinberg2010",
        "KaufmannCappeGarivier2016": "kaufmann2016",
    }.items():
        paragraph = paragraph.replace(old, new)
    return paragraph


text = align(OLD.read_text(encoding="utf-8"))
header = text[:text.index(r"\begin{abstract}")]
header = re.sub(r"\\title\{.*?\}\n", lambda _: (
    "\\title{Multi-armed bandits with arriving arms:\\\\\n"
    "sequential screening and reliable set maintenance}\n"), header, count=1, flags=re.S)

abstract = r"""
\begin{abstract}
We study a stochastic multi-armed bandit problem in which new arms arrive
exogenously and remain available. Performance is measured against the best
currently available arm. The resulting arrival information discrepancy and
drifting benchmark motivate UCB for Arriving Arms (UCB-AA), which screens new
arms before they enter full competition with incumbents. We retain this
two-stage design and give a finite-budget regret analysis based on the
comparisons and sample prefixes actually used. The analysis separates learning
among admitted arms from delayed admission and loss of an earlier benchmark.
We then ask what statistical benefit can accompany screening beyond a smaller
internal active set. For simultaneous, reliable reporting of the relative
near-optimal set, uncertainty about one arrival can obstruct many earlier
certifications. We characterize a worst-schedule maintenance cost and identify
the polynomial arrival boundary for sublinear unresolved time. A repeated-update
family shows that prompt resolution of temporary membership questions can
require inverse-square regret, whereas allowing more waiting admits a
logarithmic upper bound. The necessary cost also holds with fixed positive
probability. A separate checkpoint construction supplies attainable reporting
bounds. Numerical evidence distinguishes the archived UCB-AA implementation
from this construction and exposes the finite-budget cost of conservative
certification.
\end{abstract}
\noindent\textit{Keywords:} sequential experimentation; adaptive screening;
arriving arms; dynamic regret; arrival information discrepancy; drifting benchmark.
"""

intro = r"""
\section{Introduction}
\label{sec:introduction}

""" + original_paragraph("The classical multi-armed bandit framework") + r"""

\begin{figure}[t]
\centering
\includegraphics[width=.76\textwidth]{figures/original_submission/figure_nsclc_targeted_therapy_arms.png}
\caption{The historical motivating illustration from the original submission:
FDA approval records for targeted therapies and immunotherapies for
non-small cell lung cancer over 2003--2025 \citep{FDA_DrugsFDA}.
The expanding option set motivates arriving-arm experiments. No treatment
outcomes from this illustration enter the bandit simulations.}
\label{fig:nsclc_growth}
\end{figure}

Motivated by such problems, we study the \emph{multi-armed bandit problem with
arriving arms} (MAB-AA). Let $\mathcal A_t$ denote the set of arms available at
time $t$, with $\mathcal A_t\subseteq\mathcal A_{t+1}$. New arms arrive over time
and remain available thereafter. Performance is evaluated against the best arm
currently available, since a terminal best arm need not have been available
earlier.

""" + original_paragraph("Relative to the classical stochastic bandit setting, MAB-AA") + r"""

The setting retains stationary, unstructured reward laws and an external
arrival process. Arms are not drawn on demand from a reservoir
\citep{10.1214/aos/1069362389}, and do not disappear as in mortal bandits
\citep{NIPS2008_788d9869}. Permanent arrivals are a monotone special case of
sleeping-bandit availability \citep{kleinberg2010}. Benchmark changes are caused
by new arms, rather than changes in the reward laws of existing arms as in
nonstationary bandits \citep{Besbes2014,Auer2019ADSWITCH}.
Ballooning bandits already use permanent arrivals and regret against the best
currently available arm \citep{ghalme2021}; we do not claim either as a new model
or comparator.

""" + original_paragraph("From a statistical perspective, multi-armed bandit problems have long been studied as models") .replace(
    "but they focus on a fixed set of treatments or actions, and thus are not applicable to the arising arm setting that we study.",
    "but do not directly study the permanent exogenous arrival setting considered here.") + r"""

""" + original_paragraph("Methodologically, the two challenges call for different but complementary design principles.") + r"""

We retain UCB for Arriving Arms (UCB-AA) as the screening procedure. Its
pre-elimination stage samples an arrival at coarse resolutions before spending
the finer budget used for incumbent arms. Formal elimination then compares the
merged active set. A finite-budget analysis must account for unfinished phases,
arrivals waiting for admission, and any loss of a previously admitted best arm.
We give that accounting explicitly and establish a sample-count bound without
compressing historical gaps into a terminal gap.

The active set alone does not describe what has been learned about all
available arms. An excluded arm may be statistically inferior, or it may never
have been admitted. This distinction leads to a further question within the
same MAB-AA setting: what does it cost to maintain reliable knowledge of the
complete relative near-optimal set while collecting reward? The fixed-arm
version is the ALL-$\varepsilon$ problem \citep{mason2020}. Joint reward and
identification objectives also have established precedents
\citep{degenne2019,yang2026,cho2025}. Our additional requirement concerns
continuing reports under arrivals, with one simultaneous correctness event and
a cumulative cost for unresolved arm time.

Two effects of the drifting benchmark determine that cost. An uncertain new
arm can block positive certification of many well-studied incumbents. A later
improvement can also make a difficult earlier membership question irrelevant.
We prove a common-environment broadcast lower bound and a worst-schedule
maintenance bound, obtaining the polynomial arrival exponent below which
sublinear regret and sublinear unresolved time are jointly possible. In a
repeated-update family, prompt maintenance has matching inverse-square regret
bounds at specified horizons, whereas a larger constant-factor area budget
admits a logarithmic regret upper bound. A fixed-probability lower bound shows
that the necessary cost is not confined to rare paths. These are substantive
extensions of the original regret question, rather than guarantees inferred
from the size of UCB-AA's active set.

For the reporting upper bounds we use a separate checkpoint construction,
CP-UCB-AA. It preserves accumulated observations but does not remove negatively
reported arms from reward selection. We distinguish its guarantees from those
of the two-stage UCB-AA procedure. The numerical study likewise distinguishes
the original archived implementation from the reporting comparisons. It
retains favorable and unfavorable original observations, while showing that
conservative fixed checkpoints can be impractical at moderate budgets.
"""

old_model = slice_section(text, r"\section{Observation model", r"\section{Lifetime checkpoints")
reporting = old_model[old_model.index(r"For $0<\varepsilon<1$"):old_model.index(r"\subsection{Admission")]
account = old_model[old_model.index(r"\subsection{Admission"):]
account = account.replace(
    "Our checkpoint policy uses\n$B_t=\\mathcal{A}^{\\mathrm{adm}}_t=\\mathcal{A}_t$ for reward selection. Its reporting exclusions consequently\n"
    "do not create persistent loss of a reward benchmark.",
    "On a simultaneous confidence event, the revised UCB-AA comparisons preserve\n"
    "a best admitted arm, making the third term zero. The checkpoint construction\n"
    "introduced later uses $B_t=\\mathcal{A}^{\\mathrm{adm}}_t=\\mathcal{A}_t$\n"
    "for reward selection, so its last two terms vanish on every sample path.")

model = r"""
\section{Multi-armed bandit problem with arriving arms}
\label{sec:model}
\label{sec:problem}
\subsection{Problem formulation}

We consider a sequential decision process over time steps $t=1,2,\ldots$.
Let $\mathcal A$ be the possibly infinite set of all arms. At time $t$ only
$\mathcal A_t\subseteq\mathcal A$ is available, where
$\mathcal A_t\subseteq\mathcal A_{t+1}$,
$\mathcal A_1\ne\varnothing$, and $K_t=|\mathcal A_t|<\infty$.
For arm $i$, its arrival time is
\[
 \tau_i=\inf\{t\ge1:i\in\mathcal A_t\}.
\]
Each arm has an unknown stationary reward law on $[0,1]$ with mean $r_i$.
Reward streams are independent across arms, and successive observations of
each arm are independent and identically distributed. The arrival process is
exogenous to the learner and independent of these reward streams. We state
results conditional on a fixed arrival schedule unless otherwise specified.

As in the original formulation, $X_{t,i}$ denotes the reward observed if arm
$i$ is selected at time $t$. A policy is a sequence
$\pi=(\pi_t)_{t\ge1}$ of possibly randomized rules. After seeing
$\mathcal A_t$, it selects $I_t\in\mathcal A_t$ using the observed history
\[
 H_{t-1}=(\mathcal A_s,I_s,X_{s,I_s})_{s=1}^{t-1}
\]
and independent randomization, and then observes $X_{t,I_t}$.
It does not know the arm means or future arrivals.

Write $N_i(t)=\sum_{s\le t}\ind\{I_s=i\}$ for the cumulative number of pulls
of arm $i$. To distinguish pull number from physical time, represent its
successive potential observations by $(Y_{i,n})_{n\ge1}$, so that
$X_{t,I_t}=Y_{I_t,N_{I_t}(t-1)+1}$. Following the original empirical-mean
notation, set
\[
 \hat r_i(n)=\frac1n\sum_{s=1}^nY_{i,s},\qquad
 r^*(t)=\max_{i\in\mathcal A_t}r_i,\qquad
 \Delta_i(t)=r^*(t)-r_i\quad(i\in\mathcal A_t).
\]
For an almost surely finite stopping time $\tau$, the cumulative dynamic regret is
\[
 R_\tau(\pi)=\sum_{t=1}^{\tau}\bigl(r^*(t)-r_{I_t}\bigr).
\]
At a deterministic horizon $T$ we write $R_T(\pi)$, or $R_T$ when the policy
is understood. It is random through the arm selections; $\E R_T$ is its
expectation. A definition at random $\tau$ does not assert that every
deterministic-horizon bound also holds at arbitrary stopping times.
Physical time $t$ always counts actual pulls. Algorithmic rounds are indexed
separately by $m$.

\subsection{Main statistical challenges}

\textbf{Arrival information discrepancy (AID).}
""" + original_paragraph("A first difficulty is arrival information discrepancy.") + r"""

\textbf{Drifting benchmark (DB).}
""" + original_paragraph("In contrast to the classical setting where the best mean reward is fixed,") + "\n\n" + account

checkpoint = slice_section(text, r"\section{Lifetime checkpoints", r"\section{The burden")
checkpoint = checkpoint.replace(r"\section{Lifetime checkpoints and reward selection}",
                                r"\subsection{Lifetime checkpoints and reward selection}", 1)
checkpoint = checkpoint.replace("Choose $0<\\rho<1$ before observing rewards.",
    "For this construction, index arms by arrival order $i=1,2,\\ldots$,\n"
    "with a fixed order within each batch. This is an indexing convention,\n"
    "not an assumption about the reward laws.\n"
    "Choose $0<\\rho<1$ before observing rewards.")
checkpoint = checkpoint.replace("At an even round", "At an even time step")
checkpoint = checkpoint.replace("At every other round", "At every other time step")
checkpoint = checkpoint.replace("service rounds", "service time steps")
checkpoint = checkpoint.replace(
    "The construction retains the screening motivation of UCB-AA but changes its\nalgorithmic clock and its statistical task.",
    "This separate construction addresses the reporting objective and is not a\n"
    "reimplementation of the two-stage screening algorithm in Section~\\ref{sec:algorithm}.")
checkpoint = checkpoint.replace(
    "The guarantees above concern this construction, not the original round-based\nelimination algorithm.",
    "The guarantees above concern CP-UCB-AA. The regret guarantee for UCB-AA is\n"
    "stated separately in Section~\\ref{sec:algorithm}.")
reporting_section = r"""
\section{Reliable maintenance of the near-optimal set}
\label{sec:reporting_task}

We now supplement the original allocation objective with an explicit reporting
objective. The reward model, available arms, and dynamic-regret comparator
remain those of Section~\ref{sec:problem}. Reporting a relative near-optimal
set is an additional statistical task; it is not identified with UCB-AA's
active or surviving set. We use separate report notation to keep that
distinction visible.

\subsection{Reporting reliability and unresolved time}

""" + reporting + "\n" + checkpoint

maintenance = slice_section(text, r"\section{The burden", r"\section{Temporary membership")
tradeoff = slice_section(text, r"\section{Temporary membership", r"\section{Numerical comparisons")
experiments = slice_section(text, r"\section{Numerical comparisons", r"\FloatBarrier")
experiments = experiments.replace(r"\section{Numerical comparisons at a fixed pull budget}",
    r"\subsection{Finite-budget comparisons for reliable set maintenance}", 1)
experiments = experiments.replace(r"\subsection{Protocol", r"\subsubsection{Protocol", 1)
experiments = experiments.replace(r"\subsection{What", r"\subsubsection{What", 1)
experiments = experiments.replace(
    "These comparisons assess finite-budget behavior.",
    "These comparisons assess finite-budget behavior of the reporting construction,\n"
    "not the two-stage UCB-AA procedure.")
experiments = experiments.replace(
    "The finer checkpoint rule leaves between five and eight\n"
    "$\\eta$-unresolved arms on average at the final pull, depending on the\n"
    "environment. Its unresolved area ranges from 74,820 to 111,784.",
    "In all 640 finer-checkpoint runs, every available arm remains unresolved\n"
    "at every time step. Five to eight arms are counted by the final\n"
    "$\\eta$-unresolved metric because that metric exempts the boundary band;\n"
    "the remaining arms have not been classified. The resulting zero-error\n"
    "record therefore does not establish useful classification at this budget.\n"
    "Its charged unresolved area ranges from 74,820 to 111,784.")
experiments = experiments.replace(
    "This is consistent with the distinction\n"
    "between spending pulls to resolve current membership questions and allowing\n"
    "some questions to be superseded by later arrivals. It is not an estimate\n"
    "of an optimal Pareto frontier.",
    "These points do not isolate the benefit of task expiration. The adaptation\n"
    "uses all 10,000 designated service pulls in this environment, while\n"
    "coarse CP uses about 5,786; some remaining questions lie inside the\n"
    "unpenalized boundary band. The lower regret may therefore partly reflect\n"
    "a different stopping rule for reporting work. A comparison with the same\n"
    "boundary tolerance and service requirement is needed to distinguish the\n"
    "mechanisms. These observations do not estimate an optimal frontier.")

archived = r"""
\section{Numerical studies}
\label{sec:numerical}

\subsection{The original two arrival scenarios}

We retain the original simulation designs and their three evaluation
criteria: cumulative dynamic regret $R_T$, wasted pulls
\[
 W_T=\sum_{t=1}^T\ind\{\Delta_{I_t}(t)\ge0.1\},
\]
and active-set size. The latter counts arms retained by an implementation;
it does not by itself establish that every available arm has been evaluated.
Both archived scenarios have $T=60{,}000$ and 100 independent replications.

The progressive step-up scenario starts with ten arms. Background arrivals
occur with Bernoulli probability $0.005$ per time step. Step arms arrive at
$t/T\in\{0.3,0.6,0.9\}$ with means
$\min(1,0.7+0.05k)$, $k=1,2,3$. The near-tied top-set scenario starts with
twenty arms, including five arms drawn from $\operatorname{Uniform}(0.75,0.90)$.
Background arrivals again have probability $0.005$, with probability $0.30$
of being drawn from the near-optimal component. These are the archived
configurations that generated the original figures; the supplied configuration
files specify the remaining mixture components.

The archived UCB-AA implementation uses $M=5$ and $M=4$ in the two scenarios,
respectively, and $N=e/\widetilde\Delta_M^2$. It stops admission after the
prescribed rounds and then exploits a fixed survivor pool. Its formal
comparisons use incumbent references when present and empirical means from
all observations. These details differ from the prefix-based, merged-reference
procedure stated in Section~\ref{sec:algorithm}. We therefore retain these
results as observations about the archived implementation, rather than
claiming that the repaired finite-budget procedure has been rerun.

\input{experiments/original_submission_archive/table_original_archive.tex}

The archived UCB-AA has mean regret 5139.94 in the step-up scenario, compared
with 2036.72 for Growing MOSS. In the near-tied scenario the corresponding
means are 1880.88 and 2043.75. In both scenarios it improves mean regret and
wasted pulls relative to the archived Growing UCB1, dynamic successive
elimination, and no-pre-elimination implementations. Thus the favorable
near-tied result is retained, as is the substantially worse step-up result
against MOSS. A small survivor pool cannot be attributed entirely to
statistical screening: some later arms were never admitted. The original
six figures are retained in the supplement with this implementation
qualification.

To evaluate the repaired UCB-AA procedure itself, the two original environments
need a common implementation of the prefix means, merged references, budget
truncation, and continued admission. Short-interval retained-history
comparisons and best-arm-retention diagnostics are also needed. The reporting
experiments below answer a different, additional question and do not replace
that algorithm comparison.

""" + experiments

discussion = r"""
\FloatBarrier
\section{Discussion}
\label{sec:discussion}

We studied stochastic multi-armed bandits with arriving arms, where the
available action set expands and performance is measured against the best
currently available arm. Arrival information discrepancy and a drifting
benchmark create repeated learning costs even though every arm has a
stationary reward law. The two-stage UCB-AA design addresses the information
imbalance by screening arrivals before full competition with incumbents.
The revised regret account separates learning, admission delay, and loss of
an earlier admitted benchmark. Its finite-budget guarantee is conditional
on the stated calibration and retains the admission-delay term explicitly.

The additional maintenance analysis makes precise a statistical question
that the original active-set comparison left open. A smaller internal set
does not establish reliable knowledge of the complete near-optimal set.
One uncertain arrival can obstruct many earlier certifications, and a
drifting benchmark can make difficult unresolved questions expire. The
broadcast and repeated-update results characterize costs arising from these
two effects. Their assumptions, including the restricted update family and
the different allowed area budgets, are part of the conclusions. The worst
area lower bound already occurs in a static initial batch; the temporary-task
results supply a separate dynamic mechanism.

UCB-AA and CP-UCB-AA serve different purposes in this analysis. The former
retains the original screening architecture. The latter is a constructive
reporting rule whose service precision is fixed in advance and whose
unconditional reward analysis does not require correct reports. Its
conservative checkpoints may be ineffective at moderate budgets, and its
numerical cost is not uniformly competitive. Neither a negative report
nor a smaller reported set is treated as a reduction in total storage.

The supplement preserves the additional quantile lower bound and the
compatible-window truncation result. It also gives eventual exact
classification by a separate revisable multiresolution construction when
arrivals stop, the final arm count is finite, and no arm lies on the
membership boundary. That conclusion does not apply to fixed-precision
checkpoints.

The general frontier under overlapping arrivals, automatic precision
selection, and a matching converse for deferred maintenance remain open.
The archived UCB-AA study also leaves a concrete empirical obligation:
the repaired procedure must be compared under the same admission and
retained-history rules before attributing a numerical gain to pre-elimination.
Contextual information, delayed feedback, and post-arrival reward drift
remain natural extensions of the original MAB-AA formulation.

\section*{Data and code availability}
No original empirical or human-subject outcome data were collected.
The original simulation configurations, endpoint records, source snapshots,
and figures are preserved separately from the new reporting experiments.
The release contains the 5,760 reporting runs, their fixed configuration,
code, and checks. The oncology illustration is the historical motivation
from the original submission, based on public approval records.
"""

algorithm = ROOT / "audit/ucbaa_main_block.tex"
lower = ROOT / "audit/retained_lower_main_block.tex"
assert algorithm.is_file() and lower.is_file(), "Wait for the audited main blocks."
algorithm_text = algorithm.read_text(encoding="utf-8")
algorithm_text = algorithm_text.replace(
    "To give this procedure a fixed-budget guarantee, specify its confidence",
    "Let $s_m$ be the physical start of round $m$. Set $A_0=\\mathcal A_1$ and,\n"
    "for $m\\ge1$, admit the entire buffer, including arrivals at $s_m$:\n"
    "$A_m=\\mathcal A_{s_m}\\setminus A(m-1)$, where\n"
    "$A(m-1)=\\bigcup_{j<m}A_j$. Arrivals during a call are added to the\n"
    "buffer before the current physical action and wait for the next round.\n\n"
    "To give this procedure a fixed-budget guarantee, specify its confidence")
algorithm_title = r"""
\section{UCB for Arriving Arms (UCB-AA)}
\label{sec:algorithm}

""" + original_paragraph("UCB-AA is an elimination-based procedure organized by rounds.") + "\n\n"
algorithm_pseudocode = r"""
\begin{algorithm}[t]
\caption{UCB for Arriving Arms (UCB-AA), with explicit prefix comparisons}
\label{alg:ucb-aa}
\small
\begin{algorithmic}[1]
\Require Physical budget $T$; $M_T,N,n_p,b_p$ from
\eqref{eq:ucbaa_main_calibration}--\eqref{eq:ucbaa_main_targets}
\State Initialize $C_{-1}=\varnothing$ and retain lifetime sample prefixes
\State Stop immediately after pull $T$; an unfinished call performs no elimination
\Procedure{Elim}{$S,R,p$}
    \State Before each physical pull, add newly arriving unadmitted arms to the buffer
    \State Pull each $j\in S$ to $n_p$ total observations
    \State For $j\in R$, set $\mathrm{LCB}_j=\hat r_j(n_p)-b_p$,
           $\mathrm{UCB}_j=\hat r_j(n_p)+b_p$
    \State Remove simultaneously from $S$ every $j$ with
           $\mathrm{UCB}_j<\max_{i\in R}\mathrm{LCB}_i$
    \State \Return $S$
\EndProcedure
\For{$m=0,\ldots,M_T$}
    \State Admit buffered batch $A_m$; set $B_m^0=C_{m-1}\cup A_m$
    \If{$m\ge2$}
        \State Set $A_m^0=A_m$
        \For{$p=0,\ldots,m-2$}
            \If{$A_m^p\ne\varnothing$}
                \State $A_m^{p+1}\gets\Call{Elim}{A_m^p,C_{m-1}\cup A_m^p,p}$
            \Else
                \State $A_m^{p+1}\gets\varnothing$
            \EndIf
            \State $B_m^{p+1}\gets C_{m-1}\cup A_m^{p+1}$
        \EndFor
    \EndIf
    \If{$m=0$}
        \State $B_m^1\gets\Call{Elim}{B_m^0,B_m^0,0}$
    \Else
        \For{$p=m-1,m$}
            \State $B_m^{p+1}\gets\Call{Elim}{B_m^p,B_m^p,p}$
        \EndFor
    \EndIf
    \State $C_m\gets B_m^{m+1}$
\EndFor
\end{algorithmic}
\end{algorithm}

The algorithm retains the original two stages. Pre-elimination applies only
to newly admitted arms and uses the already observed incumbent prefixes.
Formal elimination applies to the merged active set. The empty-batch branch,
strict comparison, and physical-budget stopping rule make those operations
unambiguous; they do not replace screening with the checkpoint construction.
"""
insert_before = r"\subsection{Roundwise regret, historical loss, and arrival delay}"
assert insert_before in algorithm_text
algorithm_text = algorithm_title + algorithm_text.replace(
    insert_before, algorithm_pseudocode + "\n" + insert_before, 1)
result = (header + abstract + intro + model + "\n" +
          algorithm_text + "\n" +
          lower.read_text(encoding="utf-8") + "\n" +
          reporting_section + maintenance + tradeoff + archived + discussion +
          "\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n")
editorial = {
    "We retain this\ntwo-stage design and give": "We analyze this\ntwo-stage design and give",
    "We retain UCB for Arriving Arms (UCB-AA) as the screening procedure.":
        "UCB for Arriving Arms (UCB-AA) implements this screening design.",
    "the original allocation objective": "the allocation objective",
    "under suitable conditions on gap evolution":
        "when arm-count growth and admission delay are controlled",
    "As in the original formulation,": "In physical-time notation,",
    "Following the original empirical-mean\nnotation, set": "Define",
    "We retain the screening architecture of UCB for Arriving Arms (UCB-AA).":
        "UCB for Arriving Arms (UCB-AA) uses two stages of screening.",
    "Retain the original target and radius formulas": "Use the target and radius formulas",
    "These conventions repair the confidence and budget bookkeeping while\npreserving the two original elimination stages.":
        "These conventions specify the confidence comparisons and budget accounting\nfor the two elimination stages.",
    "The guarantee below uses\nthis calibration rather than the smaller empirical calibration in the\nsubmitted manuscript.":
        "The guarantee below uses this calibration; a smaller empirical\ncalibration need not have the same coverage probability.",
    ", as in the original roundwise formulation.": ".",
    "no $G_3$ terminal-gap compression or\nunion over random elimination chains is used.":
        "the argument does not replace intermediate gaps by a terminal gap\nor condition on a selected elimination chain.",
    "This physical-time wrapper is distinct from the withdrawn argument based\non completing geometrically many algorithmic rounds.":
        "Each restart has a prescribed number of physical pulls, so an\nunfinished round is charged at the actual endpoint.",
    "We retain two lower-bound regimes from the original regret formulation.":
        "We consider two representative lower-bound regimes for regret.",
    "The supplement preserves the additional quantile lower bound and the\ncompatible-window truncation result.":
        "The supplement supplies full proofs of the quantile lower bound in\n"
        "Section~\\ref{sec:tradeoff} and the compatible-window truncation result.",
    "For example, retain the original illustration with an initial optimum":
        "For example, consider an initial optimum",
    "All distractors have gap at least $1/4$. This preserves the valid\nfixed-gap conclusion without the withdrawn $G_3$ simplification or a\nclaim that removing preliminary screening forces linear regret.":
        "All distractors have gap at least $1/4$, so the same bound gives\n"
        "$O(K_T\\log(T+1))$ expected regret for this exogenous arrival example.",
    r"\sup_{\tau:K_T\le K}": r"\sup_{\boldsymbol\tau:K_T\le K}",
}
for before, after in editorial.items():
    result = result.replace(before, after)
result = result.replace("fixed-gap conclusion without the withdrawn $G_3$ simplification or a\nterminal-gap stability condition.",
    "fixed-gap conclusion from actual sample counts, without a terminal-gap\nstability condition.")
assert r"\input{sections/" not in result
assert r"\widehat\mu" not in result and r"\mu_i" not in result
assert "pseudo-regret" not in result
(ROOT / "manuscript.tex").write_text(result, encoding="utf-8", newline="\n")

# Retain the original bibliography entries under their original keys.
bib = ROOT / "references.bib"
if not (ROOT / "audit/before_notation_alignment/references.bib").exists():
    shutil.copy2(bib, ROOT / "audit/before_notation_alignment/references.bib")
current = bib.read_text(encoding="utf-8")
keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", current))
original_bib = (ROOT.parent / "JASA-template/bibliography.bib").read_text(encoding="utf-8-sig")
entries = re.split(r"(?m)(?=^@\w+\s*\{)", original_bib)
for entry in entries:
    match = re.match(r"@\w+\s*\{\s*([^,\s]+)", entry)
    if match and match[1] not in keys:
        current += "\n" + entry.rstrip() + "\n"
        keys.add(match[1])
# The original template used Biber, which accepted comment lines inside
# entries. Plain BibTeX needs those comment-only lines removed.
current = "\n".join(line for line in current.splitlines()
                    if not line.lstrip().startswith("%")) + "\n"
current = re.sub(r"@online(?=\s*\{)", "@misc", current, flags=re.I)
bib.write_text(current, encoding="utf-8", newline="\n")

picture = ROOT / "figures/original_submission/figure_nsclc_targeted_therapy_arms.png"
picture.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT.parent / "JASA-template" / picture.name, picture)
print(f"Wrote original-based manuscript: {len(result.splitlines())} lines.")

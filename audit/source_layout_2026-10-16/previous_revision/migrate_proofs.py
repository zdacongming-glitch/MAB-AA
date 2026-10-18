"""Reorganize frozen proofs without editing their historical source files."""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "revision_2026-10-16"
BASE = REV / "baseline"
THEORY = ROOT / "theory"


def sections(path):
    text = path.read_text(encoding="utf-8-sig")
    starts = list(re.finditer(r"^\\section\{", text, re.M))
    return [text[m.start(): starts[j + 1].start() if j + 1 < len(starts) else len(text)]
            for j, m in enumerate(starts)]


sp = sections(BASE / "theory/supplementary_proofs.tex")
ex = sections(BASE / "theory/extensions.tex")
iv = sections(BASE / "theory/information_and_variants.tex")
assert len(sp) == 8 and len(ex) == 2 and len(iv) == 2

# A1 retains the already used likelihood/KL tools once. The redundant TV
# inequalities used only by the retired pure-regret lower bounds stay archived.
a1 = sp[0].replace("in the\noriginal physical-time notation", "in physical-time notation")
a1 = a1.replace(
    "D(P\\Vert Q)\\ge\\operatorname{kl}(P(F),Q(F)).",
    "D(P\\Vert Q)\\ge\\operatorname{kl}(P(F),Q(F))\n"
    " \\ge P(F)\\log\\frac1{Q(F)}-\\log2.")
a1 = a1.replace(
    "We repeatedly use\n", 
    "The second inequality uses the binary entropy bound $h(p)\\le\\log2$. "
    "We repeatedly use\n")

reuse = sp[4]
reward_start = reuse.index("\\paragraph{A reward bound")
completion_start = reuse.index("\\paragraph{Arbitrary-arrival completion bound.}")
separated_start = reuse.index("\\paragraph{Separated windows and reuse.}")
reward = reuse[:completion_start]
reward = reward.replace(
    "\\section{History-retaining checkpoint UCB and evidence reuse}\n\\label{app:reuse}",
    "\\section{Joint guarantee of Checkpoint-UCB}\n\\label{app:joint}")
reward = reward.replace("CP-UCB-AA", "Checkpoint-UCB")
reward = reward.replace(
    "Every observation\nserves both the lifetime checkpoint and the empirical reward estimate.",
    "Every observation\nserves both the lifetime checkpoint and the empirical reward estimate.\n"
    "The fixed-checkpoint argument in Section~\\ref{app:tools} gives\n"
    "$P(E_{\\rm lab})\\ge1-\\delta/2$. If $\\mathcal I_T$ denotes designated\n"
    "service rounds, then $|\\mathcal I_T|\\le\\sum_{i\\le K_T}q_i$, because each\n"
    "such observation is charged to an arm below its single lifetime quota.\n"
    "The following reward argument does not assume separated arrival windows.\n")

completion_original = reuse[completion_start:separated_start]
completion_proof = completion_original[completion_original.index("At any fixed reporting precision"):]
growth_start = completion_proof.index("At fixed $\\eta,\\delta$")
growth = completion_proof[growth_start:]
completion_proof = completion_proof[:growth_start]
completion_proof = completion_proof.replace(
    "At any fixed reporting precision $\\rho=\\eta/4$, if all current checkpoints\nare complete,",
    "If all current checkpoints are complete,")
completion_proof = completion_proof.replace(
    "Thus on simultaneous coverage,\n\\[\n \\mathcal U_T(\\eta)\\le\n"
    " \\sum_{t\\le T}K_t1\\{\\overline Q_t>0\\}\n"
    " \\le\\min\\{K_TT,2K_T\\sum_{i\\le K_T}q_i\\}.\n\\]",
    "Thus on simultaneous coverage the unresolved area is bounded by the\n"
    "queue-weighted sum in the statement, which is at most $K_TT$ and at most\n"
    "$2K_T\\sum_{i\\le K_T}q_i$.")
completion = r"""
\begin{lemma}[Completion under arbitrary arrivals]
\label{app:completion_general}
Fix $\eta>0$ and use Checkpoint-UCB with the predetermined precision
$\rho=\eta/4$. Let $\overline Q_t$ be the post-service workload of the
virtual FIFO queue that inserts $q_i$ units at arm $i$'s arrival and serves
one unit at every even physical round when nonempty. On the simultaneous
checkpoint-coverage event, for each fixed deterministic endpoint $T$,
\[
 \mathcal U_T(\eta)\le
 \sum_{t\le T}K_t1\{\overline Q_t>0\}
 \le\min\{K_TT,2K_T\sum_{i\le K_T}q_i\}.
\]
\end{lemma}
\begin{proof}
""" + completion_proof + "\\end{proof}\n"
a2 = reward + completion

a3 = sp[1].replace("The broadcast obstruction and its queue consequence", "Broadcast uncertainty and queue area")
a4 = sp[2].replace("The partial simultaneous-recovery lemma", "Partial simultaneous recovery")

a5 = sp[7].replace("Worst-schedule area and a sparse but bursty schedule", "Worst-schedule area and growth consequences")
a5 = a5.replace("The arbitrary-arrival queue bound proves, on coverage,", "Lemma~\\ref{app:completion_general} proves, on coverage,")
a5 = a5.replace("The UCB reward bound and", "The unconditional reward bound in Section~\\ref{app:joint} and")
a5 = a5.replace("\\paragraph{A fixed sparse schedule", "\\paragraph{Growth on a fixed schedule.}\n" + growth + "\n\\paragraph{A fixed sparse schedule")
a5 = a5.replace("Combined with the broadcast consequence", "Combined with the broadcast consequence in Section~\\ref{app:broadcast}")

a6 = sp[3].replace("Area-constrained multiple updates", "Area-constrained temporary tasks")
a6 = a6.replace(
    " \\sup_\\sigma E_\\sigma R_T\\ge\n",
    " \\sup_\\sigma E_\\sigma R_T\\ge\n")
# The full allocation relaxation has left the main article; give its moved
# display the former label so the migration remains explicit.
old = """\\[
 \\sup_\\sigma E_\\sigma R_T\\ge
 \\inf_{\\substack{0\\le p_e\\le1\\\\
       \\sum_ew_ep_e\\ge(1-\\delta)V-2a}}
 \\sum_e\\frac{(\\varepsilon-d_e)M_e}{\\kappa_e}
                  g_{M_e,\\delta}(p_e).
\\]"""
new = old.replace("\\[", "\\begin{equation}\n\\label{eq:allocation_lower}", 1)
new = new[:-2] + "\\end{equation}"
assert old in a6
a6 = a6.replace(old, new)

separated = reuse[separated_start:]
a7 = "\\section{Shared evidence and rapid/deferred endpoints}\n\\label{app:reuse}\n\n" + separated
a7 = a7.replace("\\paragraph{Separated windows and reuse.}", "\\subsection{Shared evidence across separated windows}")
a7 = a7.replace(
    "Let $\\gamma_i$ be the smallest positive gap arm $i$ ever has and\n$D_i^T$ its largest gap through $T$.",
    "For each arm that has a positive gap by $T$, let\n"
    "$\\gamma_i=\\min_{t\\le T:i\\in\\mathcal A_t,\\,\\Delta_i(t)>0}\\Delta_i(t)$\n"
    "and $D_i^T=\\max_{t\\le T:i\\in\\mathcal A_t}\\Delta_i(t)$.\n"
    "Use the good-round concentration bound from Section~\\ref{app:joint}.")
reuse_regret = """\\[
 ER_T\\le\\sum_{e<J}\\sum_{k=1}^{M_e}(\\varepsilon+d_e)q_{e,k}
 +\\sum_{i:\\gamma_i\\text{ exists}}D_i^T
 \\left[\\left\\lceil\\frac{12\\log(2T)}{\\gamma_i^2}\\right\\rceil-q_i+1\\right]_+
 +1.
\\]"""
assert reuse_regret in a7
new = reuse_regret.replace("\\[", "\\begin{equation}\n\\label{eq:app_reuse_regret}", 1)
new = new[:-2] + "\\end{equation}"
a7 = a7.replace(reuse_regret, new)
a7 = a7.replace("Since counts do not\nrepeat,", "Since lifetime counts do not\nrepeat,")
a7 += sp[5].replace("\\section{The rapid and deferred endpoints on one family}", "\\subsection{Rapid and deferred endpoints on one family}")
a7 = a7.replace("the preceding reward bound", "\\eqref{eq:app_reuse_regret}")

a8 = ex[0].replace("A quantile lower bound under the same maintenance protocol", "Regret quantiles under the same maintenance protocol")
a9 = ex[1].replace("A horizon-truncated lower bound across compatible task windows", "Compatible-window truncated area")
a10 = sp[6]
a10 = a10.replace(
    "Let epochs be", 
    "This extension uses a separate, revisable multiresolution policy, rather\n"
    "than the fixed-checkpoint policy. Let epochs be", 1)
a10 = a10.replace("Apply the unconditional UCB counting bound", "Apply the unconditional UCB counting bound in Section~\\ref{app:joint}")
a11 = iv[0].replace("A general information-allocation lower relaxation", "General information-allocation relaxation")
a12 = iv[1].replace("Intermediate configurations and known-reference diagnostics", "Intermediate service configurations and disclosed-reference diagnostic")

pieces = [a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12]
names = ["probability_tools", "joint_guarantee", "broadcast", "partial_recovery",
         "worst_area", "temporary_tasks", "shared_endpoints", "regret_quantiles",
         "compatible_windows", "eventual_classification", "information_relaxation",
         "service_variants"]
files = []
for n, (name, content) in enumerate(zip(names, pieces), 1):
    path = THEORY / f"maintenance_a{n:02d}_{name}.tex"
    path.write_text("% Reorganized from the frozen October 15, 2026 supplement.\n" + content.rstrip() + "\n", encoding="utf-8")
    files.append(path)

supp = r"""\documentclass[11pt]{article}
\input{preamble}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thepage}{S-\arabic{page}}
\title{Supplement to ``The Cost of Reliable Near-Optimal Set Maintenance with Arriving Arms''}
\author{}
\date{October 15, 2026}
\begin{document}
\maketitle
\section*{Notation and scope}
The observation model has independent arm streams, each consisting of
independent, identically distributed rewards in $[0,1]$, deterministic
permanent arrivals $\mathcal A_t$, and one observation per physical time step.
Each finite $\mathcal A_t$ is nonempty, and arbitrarily large finite batches
are allowed. Arrivals occur before the action, and reports follow its
observation. Let $r^*(t)=\max_{i\in\mathcal A_t}r_i$,
$\Delta_i(t)=r^*(t)-r_i$, and
$\mathcal G_t^\varepsilon=\{i\in\mathcal A_t:\Delta_i(t)\le\varepsilon\}$.
Reports partition $\mathcal A_t$ as
$(\mathcal P_t,\mathcal N_t,\mathcal V_t)$. Write
\[
 E_{\rm lab}=\{\forall t:\mathcal P_t\subseteq\mathcal G_t^\varepsilon
                      \subseteq\mathcal A_t\setminus\mathcal N_t\},\qquad
 \mathcal U_T(\eta)=\sum_{t\le T}\sum_{i\in\mathcal A_t}
 \ind\{i\in\mathcal V_t,|\Delta_i(t)-\varepsilon|>\eta\},
\]
and $R_T=\sum_{t\le T}\Delta_{I_t}(t)$. Reliability means
$P(E_{\rm lab})\ge1-\delta$ for every allowed environment.
$\mathfrak R_\Theta(a)$ minimizes worst-case $ER_T$ over full-model reliable
policies with $P_\theta(E_{\rm lab},\mathcal U_T\le a)\ge1-\delta$ for all
$\theta\in\Theta$. A bar denotes averaging under the independent uniform
prior on all candidate signs. These priors are proof devices and impose no
Bayesian requirement on the policy.

The probability and sample-budget arguments are given below. Classical
change of measure and multiple-recovery scales are credited to the existing
literature \citep{kaufmann2016,malloy2014,jamieson2018,mason2020}.

"""
for path in files:
    supp += "\\input{" + path.relative_to(ROOT).with_suffix("").as_posix() + "}\n"
supp += "\n\\input{revision_2026-10-16/computational_details.tex}\n\n"
supp += "\\FloatBarrier\n\\bibliographystyle{plainnat}\n\\bibliography{references}\n\\end{document}\n"
(ROOT / "supplement.tex").write_text(supp, encoding="utf-8")

new_all = "\n".join(p.read_text(encoding="utf-8") for p in files)
labels = {x: p.relative_to(ROOT).as_posix() for p in files
          for x in re.findall(r"\\label\{([^}]+)\}", p.read_text(encoding="utf-8"))}
rows = []
fields = ["source_file", "source_section_or_label", "source_statement_name", "action", "new_file", "new_label", "proof_dependencies", "assumption_changes", "status"]
for rel in ["theory/ucbaa_repaired_analysis.tex", "theory/retained_regret_lower_bounds.tex",
            "theory/supplementary_proofs.tex", "theory/extensions.tex",
            "theory/information_and_variants.tex", "supplement.tex"]:
    content = (BASE / rel).read_text(encoding="utf-8-sig")
    for lab in re.findall(r"\\label\{([^}]+)\}", content):
        if lab in labels:
            action, newfile, newlab = "move", labels[lab], lab
            deps = "app:tools;app:joint;app:partial (as used in proof)"
        elif rel.endswith("retained_regret_lower_bounds.tex") and lab in {
                "lem:retained_information", "eq:retained_binary_information",
                "eq:retained_bernoulli_upper", "eq:retained_adaptive_kl"}:
            action, newfile, newlab = "merge", labels["app:tools"], "app:tools"
            deps = "Existing entropy, binary KL and adaptive history KL only; unused TV tool archived"
        elif lab == "app:computation":
            action, newfile, newlab = "rewrite", "revision_2026-10-16/computational_details.tex", lab
            deps = "existing reporting experiment records;experiment_migration agent"
        else:
            action, newfile, newlab = "remove", "", ""
            deps = "archived only; excluded from submission dependency graph"
        rows.append(dict(zip(fields, [rel, lab, lab, action, newfile, newlab, deps, "none", "migrated" if action != "remove" else "archived"])))
rows.append(dict(zip(fields, ["theory/supplementary_proofs.tex", "S7 arbitrary-arrival completion paragraph",
          "Completion under arbitrary arrivals", "move", labels["app:completion_general"], "app:completion_general",
          "app:tools;existing FIFO queue argument", "none", "existing result given independent lemma label"])))
rows.append(dict(zip(fields, ["manuscript.tex", "eq:allocation_lower", "Area-to-regret information relaxation", "move",
          labels["eq:allocation_lower"], "eq:allocation_lower", "app:partial", "none", "full original proof retained in A6"])))
with (REV / "theorem-map-supp.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

manifest = {}
for path in files:
    manifest[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
(REV / "proof_reorganization_manifest.json").write_text(json.dumps({
    "new_files": manifest,
    "preserved_labels": sorted(labels),
    "source_files_unchanged": all((BASE / rel).read_bytes() == (ROOT / rel).read_bytes()
        for rel in ["theory/ucbaa_repaired_analysis.tex", "theory/retained_regret_lower_bounds.tex", "theory/supplementary_proofs.tex", "theory/extensions.tex", "theory/information_and_variants.tex"]),
    "numbered_appendix_sections": 12,
    "final_section_external_input": "revision_2026-10-16/computational_details.tex",
}, indent=2), encoding="utf-8")
print(json.dumps({"created_proof_files": len(files), "mapping_rows": len(rows), "preserved_labels": len(labels)}))

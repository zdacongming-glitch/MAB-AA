#!/usr/bin/env python3
"""Summarize every frozen run and draw reproducible vector/raster figures."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
RES=ROOT/"experiments/results"
SCENARIO_LABELS={"stable_benchmark":"Stable benchmark", "successive_improvements":"Successive improvements", "burst":"Burst", "arrivals_stop":"Arrivals stop"}
METHOD_LABELS={"CP-FIFO-fine":"CP, precision 0.04", "CP-FIFO":"CP, precision 0.12", "CP-confidence":"CP, confidence service", "CP-period8":"CP, period 8", "UCB-checkpoint":"UCB + checkpoint", "UCB-prefix":"UCB + prefix", "Growing-MOSS":"Growing MOSS", "ALL-epsilon-adapt":"ALL-epsilon adaptation", "Batch100-UCB":"Batch-100 UCB"}
COLORS={"CP-FIFO-fine":"#CC79A7", "CP-FIFO":"#D55E00", "CP-confidence":"#E69F00", "CP-period8":"#8C6D31", "UCB-checkpoint":"#56B4E9", "UCB-prefix":"#0072B2", "Growing-MOSS":"#000000", "ALL-epsilon-adapt":"#009E73", "Batch100-UCB":"#7A7A7A"}
MARKERS=dict(zip(METHOD_LABELS,["P","o","v","s","D","^","x","*","h"]))
LINESTYLES=dict(zip(METHOD_LABELS,["-","-","--",":","--","-",":","--","-."]))


def tex_name(name):
    return {"CP-FIFO-fine":r"CP-FIFO ($\rho=.04$)","CP-FIFO":r"CP-FIFO ($\rho=.12$)","CP-confidence":"CP-confidence","CP-period8":"CP-period8","UCB-checkpoint":"UCB-checkpoint","UCB-prefix":"UCB-prefix","Growing-MOSS":"Growing-MOSS","ALL-epsilon-adapt":r"ALL-$\varepsilon$ adapt.","Batch100-UCB":"Batch100-UCB"}[name]


def main(*, figures_only=False):
    data=pd.read_csv(RES/"runs.csv")
    config=json.loads((RES/"config.json").read_text())
    scenario_names=[s["name"] for s in config["scenarios"]]
    methods=[m["name"] for m in config["methods"]]
    metrics=["regret","area_eta","area_all","service_pulls","service_regret","final_u_eta","final_u_all","quota_completed","admission_delay_regret","elimination_deficit_regret","within_active_regret"]
    summary=[]
    for scenario in scenario_names:
        for method in methods:
            sample=data[(data.scenario==scenario)&(data.method==method)]
            n=len(sample)
            row={"scenario":scenario,"method":method,"n":n}
            for metric in metrics:
                row[metric+"_mean"]=sample[metric].mean()
                row[metric+"_se"]=sample[metric].std(ddof=1)/math.sqrt(n)
            errors=int(sample.error_ever.sum())
            row.update(error_runs=errors,error_rate=errors/n,
                error_rate_upper95=1. if errors==n else beta.ppf(.95,errors+1,n-errors),
                fully_eta_resolved_rate=(sample.final_u_eta==0).mean(),
                end_coverage_rate=sample.coverage_at_end.mean())
            summary.append(row)
    summary=pd.DataFrame(summary)
    if not figures_only:
        summary.to_csv(RES/"summary.csv",index=False,float_format="%.12g")
    paired=[]
    for scenario in scenario_names:
        sample=data[data.scenario==scenario]
        for target in ["CP-FIFO","CP-FIFO-fine","CP-confidence","CP-period8"]:
            ref=sample[sample.method==target].set_index("seed")
            for baseline in methods:
                if baseline==target:
                    continue
                other=sample[sample.method==baseline].set_index("seed")
                for metric in ["regret","area_eta"]:
                    diff=ref[metric]-other[metric]
                    paired.append(dict(scenario=scenario,target=target,baseline=baseline,metric=metric,
                        mean_difference=diff.mean(),paired_se=diff.std(ddof=1)/math.sqrt(len(diff)),n=len(diff)))
    if not figures_only:
        pd.DataFrame(paired).to_csv(RES/"paired_differences.csv",index=False,float_format="%.12g")
    # The exact pathwise comparator decomposition is a useful audit of the
    # reviewer's concern about conflating admission and historical deletion.
    decomp_error=(data.regret-data.admission_delay_regret-data.elimination_deficit_regret-data.within_active_regret).abs().max()
    assert decomp_error<1e-7
    assert len(data)==len(scenario_names)*config["replications"]*len(methods)
    checks={"all_rows_present":True,"maximum_regret_decomposition_error":float(decomp_error),
        "total_runs":len(data),"error_runs":int(data.error_ever.sum()),
        "replications_per_environment":config["replications"],
        "zero_error_one_sided95_upper_per_environment_method":1-.05**(1/config["replications"]),
        "fixed_checkpoint_quotas":{str(rho):[math.ceil(2/rho**2*math.log(4*i*(i+1)/config["delta"])) for i in range(1,9)] for rho in [.04,.12]},
        "joint_label_reliability_claim":"Not empirically established; finite scenarios and Monte Carlo sampling cannot verify uniform time-uniform reliability."}
    if not figures_only:
        (RES/"verification.json").write_text(json.dumps(checks,indent=2),encoding="utf-8")
    # Compact tables use mean (Monte Carlo standard error).
    main_methods=["CP-FIFO-fine","CP-FIFO","UCB-prefix","Growing-MOSS","ALL-epsilon-adapt","Batch100-UCB"]
    lines=[r"\begin{table}[t]",r"\centering",r"\caption{Final cumulative dynamic regret and cumulative $\eta$-unresolved arm-time at $T=20{,}000$. Entries are means (Monte Carlo standard errors), from 160 paired replications. Area is in units of $10^3$. The two checkpoint precisions have different completeness guarantees.}",r"\label{tab:simulation}",r"\small",r"\begin{tabular}{llrr}",r"\toprule",r"Scenario & Method & Regret & Area / $10^3$ \\",r"\midrule"]
    for scenario in scenario_names:
        for j,method in enumerate(main_methods):
            row=summary[(summary.scenario==scenario)&(summary.method==method)].iloc[0]
            label=SCENARIO_LABELS[scenario] if j==0 else ""
            lines.append(f"{label} & {tex_name(method)} & {row.regret_mean:.1f} ({row.regret_se:.1f}) & {row.area_eta_mean/1000:.2f} ({row.area_eta_se/1000:.2f}) \\\\")
        lines.append(r"\midrule")
    lines[-1]=r"\bottomrule"
    lines += [r"\end{tabular}",r"\end{table}"]
    if not figures_only:
        (RES/"table_main.tex").write_text("\n".join(lines)+"\n",encoding="utf-8")
    # All policies, including allocation ablations, remain visible in one table.
    lines=[r"\begin{table}[t]",r"\centering",r"\caption{Allocation diagnostics. Each cell gives mean forced service pulls and mean final $\eta$-unresolved arms. UCB and MOSS have zero forced service.}",r"\label{tab:allocation}",r"\small",r"\begin{tabular}{lrrrr}",r"\toprule",r"Method & Stable & Improvements & Burst & Stop \\",r"\midrule"]
    for method in methods:
        cells=[]
        for scenario in scenario_names:
            row=summary[(summary.scenario==scenario)&(summary.method==method)].iloc[0]
            cells.append(f"{row.service_pulls_mean:.0f}, {row.final_u_eta_mean:.2f}")
        lines.append(tex_name(method)+" & "+" & ".join(cells)+r" \\")
    lines += [r"\bottomrule",r"\end{tabular}",r"\end{table}"]
    if not figures_only:
        (RES/"table_allocation.tex").write_text("\n".join(lines)+"\n",encoding="utf-8")
    # Plot all policies on cost/latency axes; no result-based removal of methods.
    plt.rcParams.update({"font.family":"serif","font.serif":["Times New Roman","DejaVu Serif"],
        "font.size":9,"axes.titlesize":10,"axes.labelsize":9,"legend.fontsize":8,
        "legend.frameon":False,"axes.spines.top":False,"axes.spines.right":False,
        "axes.grid":True,"grid.alpha":.16,"lines.linewidth":1.45,"pdf.fonttype":42,"ps.fonttype":42,
        "savefig.bbox":"tight"})
    fig,axes=plt.subplots(2,2,figsize=(7.1,5.0))
    for ax,scenario in zip(axes.flat,scenario_names):
        for method in methods:
            row=summary[(summary.scenario==scenario)&(summary.method==method)].iloc[0]
            ax.errorbar(row.regret_mean,row.area_eta_mean/1000,
                xerr=1.96*row.regret_se,yerr=1.96*row.area_eta_se/1000,
                fmt=MARKERS[method],ms=5,color=COLORS[method],capsize=1.7,elinewidth=.9,
                label=METHOD_LABELS[method])
        ax.set_title(SCENARIO_LABELS[scenario])
        ax.set_xlabel("Regret")
        ax.set_ylabel(r"Unresolved area ($10^3$)")
    handles,labels=axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,-.04),ncol=3)
    fig.tight_layout(rect=(0,.11,1,1))
    for ext in ["pdf","png"]:
        fig.savefig(HERE/f"fig_cost_area.{ext}",dpi=300)
    plt.close(fig)
    arrays=np.load(RES/"paths.npz")
    paths,times=arrays["paths"],arrays["times"]
    fig,axes=plt.subplots(2,4,figsize=(10.2,4.4),sharex="col")
    for s,scenario in enumerate(scenario_names):
        for method in main_methods:
            m=methods.index(method)
            for row,metric in [(0,0),(1,1)]:
                arr=paths[s,:,m,:,metric]
                mean=arr.mean(axis=0)
                se=arr.std(axis=0,ddof=1)/math.sqrt(arr.shape[0])
                ax=axes[row,s]
                ax.plot(times/1000,mean,color=COLORS[method],ls=LINESTYLES[method],label=METHOD_LABELS[method])
                ax.fill_between(times/1000,mean-1.96*se,mean+1.96*se,color=COLORS[method],alpha=.10,linewidth=0)
        for t,_ in config["scenarios"][s]["arrivals"][1:]:
            for ax in axes[:,s]:
                ax.axvline(t/1000,color="#B0B0B0",lw=.6,ls=":",zorder=0)
        axes[0,s].set_title(SCENARIO_LABELS[scenario])
        axes[1,s].set_xlabel(r"Physical pulls ($10^3$)")
        axes[1,s].set_ylim(bottom=-.05)
    axes[0,0].set_ylabel("Regret")
    axes[1,0].set_ylabel(r"$\eta$-unresolved arms")
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,-.02),ncol=3)
    fig.tight_layout(rect=(0,.12,1,1))
    for ext in ["pdf","png"]:
        fig.savefig(HERE/f"fig_paths.{ext}",dpi=300)
    plt.close(fig)
    # Two-column versions keep the path labels legible at manuscript width.
    for pair, selected in enumerate([[0,1],[2,3]], 1):
        fig,axes=plt.subplots(2,2,figsize=(7.0,5.4),sharex="col")
        for col,s in enumerate(selected):
            scenario=scenario_names[s]
            for method in main_methods:
                m=methods.index(method)
                for row,metric in [(0,0),(1,1)]:
                    arr=paths[s,:,m,:,metric]
                    mean=arr.mean(axis=0)
                    se=arr.std(axis=0,ddof=1)/math.sqrt(arr.shape[0])
                    ax=axes[row,col]
                    ax.plot(times/1000,mean,color=COLORS[method],ls=LINESTYLES[method],label=METHOD_LABELS[method])
                    ax.fill_between(times/1000,mean-1.96*se,mean+1.96*se,color=COLORS[method],alpha=.10,linewidth=0)
            for t,_ in config["scenarios"][s]["arrivals"][1:]:
                for ax in axes[:,col]:
                    ax.axvline(t/1000,color="#B0B0B0",lw=.6,ls=":",zorder=0)
            axes[0,col].set_title(SCENARIO_LABELS[scenario])
            axes[1,col].set_xlabel(r"Physical pulls ($10^3$)")
            axes[1,col].set_ylim(bottom=-.05)
        axes[0,0].set_ylabel("Regret")
        axes[1,0].set_ylabel(r"$\eta$-unresolved arms")
        handles,labels=axes[0,0].get_legend_handles_labels()
        fig.legend(handles,labels,loc="lower center",bbox_to_anchor=(.5,-.015),ncol=2)
        fig.tight_layout(rect=(0,.13,1,1))
        for ext in ["pdf","png"]:
            fig.savefig(HERE/f"fig_paths_pair{pair}.{ext}",dpi=300)
        plt.close(fig)
    print(summary[["scenario","method","regret_mean","regret_se","area_eta_mean","area_eta_se","final_u_eta_mean","service_pulls_mean","error_runs"]].to_string(index=False))
    print(json.dumps(checks,indent=2))


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--figures-only",action="store_true",
        help="Redraw labels and figures without rewriting numerical results or tables.")
    main(figures_only=parser.parse_args().figures_only)

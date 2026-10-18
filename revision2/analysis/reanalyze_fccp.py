"""Read frozen research results, make manuscript tables/figures, and copy release inputs.

No policy simulation is called by this script. Original research directories are read only.
Generated LaTeX is a JSON string for insertion in manuscript.tex/supplement.tex.
"""
from __future__ import annotations
import csv, hashlib, json, re, shutil, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT = Path(__file__).resolve().parents[2]
REPO = PROJECT.parent
REV = PROJECT / 'revision2'
OUT = REV / 'analysis'
GEN = REV / 'generated'
F = REPO / 'F-CCP_2026-10-17'
if '--release-only' in sys.argv or not F.is_dir(): F = PROJECT / 'experiments/fccp_frozen'
BASES = ['UCB1','Growing-MOSS','MC-MOSS','Thompson','KL-UCB']
PREFERENCE = ['F-R','F-auto-0.1','F-auto-0.3','F-auto-0.6','F-auto-0.9','F-all-service-budgeted']
PREF_VALUE = [0,.1,.3,.6,.9,1]
CORE_NAMES = {0:'UCB conservative',1:'Growing-MOSS',2:'MC-MOSS',3:'Beta score',4:'KL-UCB',7:'clipped MC-MOSS',10:'UCB1',11:'warm Beta score'}
SC_LABELS = {'two_close':'Two close arms','few_arrivals':'Few arrivals','stable':'Stable benchmark',
 'successive_improvements':'Successive improvements','burst':'Burst','membership_boundary':'Membership boundary',
 'many_close_means':'Many close means','late_improvement':'Late improvement','rare_rewards':'Rare rewards',
 'ceiling':'Ceiling','larger_pool':'Larger pool','bounded_low_variance':'Bounded low variance'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(name, obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def esc(s): return str(s).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
def fmt(v,d=2): return f'{v:.{d}f}'
def ms(row,key,scale=1,d=2): return f"{row[key+'_mean']/scale:.{d}f} ({row[key+'_se']/scale:.{d}f})"
def table(caption,label,spec,headers,rows,small=r'\small',placement='t'):
    return '\n'.join([rf'\begin{{table}}[{placement}]',r'\centering',rf'\caption{{{caption}}}',rf'\label{{{label}}}',small,
      rf'\begin{{tabular}}{{{spec}}}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule',
      *[' & '.join(row)+r' \\' for row in rows],r'\bottomrule',r'\end{tabular}',r'\end{table}'])+'\n'
def longtable(caption,label,spec,headers,rows,fontsize=8):
    return '\n'.join([r'\begingroup',rf'\fontsize{{{fontsize}}}{{{fontsize+2}}}\selectfont',r'\setlength{\tabcolsep}{4pt}',
      rf'\begin{{longtable}}{{{spec}}}',rf'\caption{{{caption}}}\label{{{label}}}\\',r'\toprule',
      ' & '.join(headers)+r' \\',r'\midrule',r'\endfirsthead',r'\toprule',' & '.join(headers)+r' \\',r'\midrule',r'\endhead',
      r'\midrule',rf'\multicolumn{{{len(headers)}}}{{r}}{{Continued on next page}}\\',r'\endfoot',r'\bottomrule',r'\endlastfoot',
      *[' & '.join(row)+r' \\' for row in rows],r'\end{longtable}',r'\endgroup'])+'\n'

def main():
    OUT.mkdir(parents=True,exist_ok=True); GEN.mkdir(parents=True,exist_ok=True)
    all_before={str(p.relative_to(F)).replace('\\','/'):sha(p) for p in F.rglob('*') if p.is_file()}
    original_manifest=json.loads((F/'MANIFEST.json').read_text(encoding='utf-8'))
    source_is_release=F.resolve()==(PROJECT/'experiments/fccp_frozen').resolve()
    original_zip=PROJECT/'experiments/fccp_frozen/original-archives/F-CCP_可调算法_理论与实验_2026-10-17.zip'
    for rel,meta in original_manifest.items():
        if (F/rel).is_file(): actual=sha(F/rel)
        else:
            assert source_is_release and original_zip.is_file(), f'Missing frozen input: {rel}'
            with zipfile.ZipFile(original_zip) as z:
                matches=[n for n in z.namelist() if n.endswith('/'+rel)]
                assert len(matches)==1
                actual=hashlib.sha256(z.read(matches[0])).hexdigest()
        assert actual==meta['sha256'], f'Frozen manifest mismatch: {rel}'
    freeze=json.loads((F/'protocols/holdout-freeze.json').read_text(encoding='utf-8'))
    correction=json.loads((F/'protocols/matched-all-freeze.json').read_text(encoding='utf-8'))
    scenarios=freeze['scenarios']; names=[x['name'] for x in scenarios]
    policies={p['name']:p for p in freeze['policies']+correction['policies']}
    methods=list(policies); codes={m:f'M{i+1:02d}' for i,m in enumerate(methods)}
    main_data=pd.read_csv(F/'results/holdout-all.csv'); corrected=pd.read_csv(F/'results/matched-all-all.csv')
    data=pd.concat([main_data,corrected],ignore_index=True)
    assert len(main_data)==27648 and len(corrected)==1152 and len(data)==28800
    assert not data.duplicated(['scenario','rep','method']).any()
    assert data.method.nunique()==25 and (data.groupby(['scenario','method']).size()==96).all()
    primary=data[data.method!='ALL-auto-0.6']; assert len(primary)==27648 and primary.method.nunique()==24
    metrics=['regret','area','service_pulls','service_regret','service_denials','reward_projections','service_mass','service_attempts',
             'active_service_rounds','final_unresolved','final_all_unresolved','reward_tax','service_tax']
    records=[]
    for sc in names:
        for method in methods:
            g=data[(data.scenario==sc)&(data.method==method)]; row={'scenario':sc,'method':method,'n':len(g)}
            for key in metrics:
                v=g[key].to_numpy(); row.update({key+'_mean':float(v.mean()),key+'_se':float(v.std(ddof=1)/np.sqrt(len(v))),
                    key+'_q95':float(np.quantile(v,.95)),key+'_max':float(v.max())})
            for key in ['label_error','coverage_error','empty_intersection']: row[key+'_count']=int(g[key].sum())
            row['proposed_busy_rate']=float(g.service_mass.sum()/g.active_service_rounds.sum()) if g.active_service_rounds.sum() else 0.
            records.append(row)
    summary=pd.DataFrame(records); summary.to_csv(OUT/'full-results-recomputed.csv',index=False)
    si=summary.set_index(['scenario','method']); suite=summary.groupby('method').mean(numeric_only=True)
    source_summary=pd.read_csv(F/'results/holdout-summary.csv').set_index(['scenario','method'])
    errors={key:float(np.max(np.abs(si[key+'_mean']-source_summary[key+'_mean']))) for key in metrics if key+'_mean' in source_summary}
    assert max(errors.values())<1e-7
    pure=[]
    for sc in names:
        p=data[data.scenario==sc].pivot(index='rep',columns='method',values='regret'); f=p['F-R'].to_numpy()
        for b in BASES:
            v=p[b].to_numpy(); delta=f-v; se=delta.std(ddof=1)/np.sqrt(96); relaxed=f-1.05*v-2
            pure.append(dict(scenario=sc,baseline=b,n=96,F_mean=float(f.mean()),baseline_mean=float(v.mean()),delta_mean=float(delta.mean()),
              delta_se=float(se),delta_l95=float(delta.mean()-student_t.ppf(.975,95)*se),delta_u95=float(delta.mean()+student_t.ppf(.975,95)*se),
              delta_upper95_family60=float(delta.mean()+student_t.ppf(1-.05/60,95)*se),
              relaxed_upper95_family60=float(relaxed.mean()+student_t.ppf(1-.05/60,95)*relaxed.std(ddof=1)/np.sqrt(96))))
    paired=pd.DataFrame(pure); paired.to_csv(OUT/'pure-reward-paired-recomputed.csv',index=False)
    joint=[]
    for a,b in [('F-auto-0.6','ALL-auto-costmatched'),('F-area','ALL-area'),('F-auto-0.6','CCP-original'),
                 ('F-R','Cold-TS-unprotected'),('F-auto-0.6','F-fixed-0.6'),('F-auto-0.6','F-auto-0.6-no-service-cap'),('F-auto-0.6','F-auto-0.6-TS')]:
        for sc in names:
            for key in ['regret','area','service_pulls']:
                p=data[data.scenario==sc].pivot(index='rep',columns='method',values=key)
                v=(p[a]-p[b]).to_numpy(); se=v.std(ddof=1)/np.sqrt(96)
                joint.append(dict(candidate=a,baseline=b,scenario=sc,metric=key,delta_mean=float(v.mean()),se=float(se),
                    lower95=float(v.mean()-student_t.ppf(.975,95)*se),upper95=float(v.mean()+student_t.ppf(.975,95)*se)))
    pd.DataFrame(joint).to_csv(OUT/'joint-paired-recomputed.csv',index=False)
    suite[['regret_mean','area_mean','service_pulls_mean','service_denials_mean','final_unresolved_mean']].to_csv(OUT/'equal-scenario-means.csv')
    winmean=int((paired.delta_mean<0).sum()); strict=int((paired.delta_upper95_family60<0).sum()); relaxed=int((paired.relaxed_upper95_family60<0).sum())
    all5=int((paired.groupby('scenario').delta_mean.max()<0).sum())
    reduction=float(100*(1-suite.loc['F-R','regret_mean']/suite.loc['Thompson','regret_mean']))
    assert (winmean,strict,relaxed,all5)==(59,52,54,11)
    failures=data.groupby('method')[['label_error','coverage_error','empty_intersection']].sum().astype(int)
    assert failures.loc['F-auto-0.6'].tolist()==[1,7,1]
    failure_examples=data[(data.label_error>0)|(data.coverage_error>0)|(data.empty_intersection>0)]
    failure_examples.to_csv(OUT/'all-failure-records.csv',index=False)

    # Figures use only 96 paired terminal outcomes, never reconstructed paths.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'ps.fonttype':42,'savefig.bbox':'tight'})
    p=paired[paired.baseline=='Thompson'].set_index('scenario').loc[names]
    fig,ax=plt.subplots(figsize=(7.0,4.8)); yy=np.arange(12)
    ax.errorbar(p.delta_mean,yy,xerr=np.vstack((p.delta_mean-p.delta_l95,p.delta_u95-p.delta_mean)),fmt='o',color='#24638a',ecolor='#658ca3',capsize=3,markersize=4)
    ax.axvline(0,color='.4',lw=.8);ax.set_yticks(yy,[SC_LABELS[s] for s in names]);ax.invert_yaxis()
    ax.set_xlabel('F-R minus Thompson: cumulative dynamic regret');ax.grid(axis='x',alpha=.2)
    fig.tight_layout();fig.savefig(GEN/'reward-paired.pdf');fig.savefig(GEN/'reward-paired.png',dpi=210);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.7,4.6)); xs=[suite.loc[m,'regret_mean'] for m in PREFERENCE]; ys=[suite.loc[m,'area_mean']/1000 for m in PREFERENCE]
    ax.plot(xs,ys,'o-',color='#24638a',lw=1.1,markersize=5,label=r'F-CCP, $\beta_C=1$ (inactive at $\lambda=0$)')
    offsets=[(6,5),(5,6),(5,5),(-40,12),(7,-4),(-28,-17)]
    for x,y,lam,of in zip(xs,ys,PREF_VALUE,offsets):ax.annotate(r'$\lambda='+str(lam)+'$',(x,y),xytext=of,textcoords='offset points',fontsize=8)
    for m,marker,col,label in [('F-area','*','#bc6b23',r'F-area, $\beta_C=\infty$'),('ALL-auto-costmatched','s','#8c4662','ALL-auto-costmatched'),('CCP-original','D','#7c7c39','CCP-original'),('ALL-area','^','#777777','ALL-area')]:
        ax.scatter([suite.loc[m,'regret_mean']],[suite.loc[m,'area_mean']/1000],marker=marker,color=col,s=68 if marker=='*' else 38,label=label,zorder=3)
    ax.set_xlabel('Cumulative dynamic regret');ax.set_ylabel(r'Cumulative unresolved arm-time / $10^3$');ax.grid(alpha=.17)
    ax.legend(fontsize=8,loc='upper right',frameon=False);fig.tight_layout();fig.savefig(GEN/'preference-tradeoff.pdf');fig.savefig(GEN/'preference-tradeoff.png',dpi=210);plt.close(fig)

    # Inline table strings, preserving the user's two-file authoring structure.
    reward_rows=[[SC_LABELS[s]]+[fmt(si.loc[(s,m),'regret_mean']) for m in BASES+['F-R']] for s in names]
    reward_main=table('Mean cumulative dynamic regret in the frozen test suite. Each entry uses 96 paired replications; Monte Carlo standard errors are in Supplementary Table~\\ref{tab:reward-se}. All six methods devote no pulls to certification.','tab:reward-baselines','lrrrrrr',['Scenario','UCB1','G-MOSS','MC-MOSS','TS','KL-UCB','F-R'],reward_rows,r'\footnotesize')
    pref_rows=[]
    for m,lam in zip(PREFERENCE,PREF_VALUE):pref_rows.append([r'F-R' if m=='F-R' else rf'F, $\lambda={lam:g}$','$1$ (inactive)' if m=='F-R' else '$1$',fmt(suite.loc[m,'regret_mean']),fmt(suite.loc[m,'area_mean']/1000)])
    for m in ['F-area','CCP-original','ALL-auto-costmatched','ALL-area']:
        pref_rows.append([esc(m),'$\\infty$' if policies[m]['beta_s'] is None else fmt(policies[m]['beta_s'],0),fmt(suite.loc[m,'regret_mean']),fmt(suite.loc[m,'area_mean']/1000)])
    pref_main=table('Descriptive equal-weight averages of the 12 scenario means. The first six rows keep $\\beta_C=1$ wherever certification is active; F-area uses no certification cap. Area is in $10^3$ arm-time units. These operating points are not an optimal frontier.','tab:preference-costs','llrr',['Method / preference',r'$\beta_C$','Regret',r'Area / $10^3$'],pref_rows)
    tail_rows=[[SC_LABELS[s],fmt(si.loc[(s,'F-R'),'regret_q95'],3),fmt(si.loc[(s,'Thompson'),'regret_q95'],3)] for s in ['burst','ceiling','larger_pool']]
    tail_main=table('Empirical 95th percentiles of cumulative dynamic regret from 96 replications per method and scenario. These are finite-sample tail summaries, not high-probability regret bounds.','tab:tail-and-failure','lrr',['Scenario','F-R','Thompson'],tail_rows)
    rdiff=p.loc['two_close']
    main_section=r'''\section{Numerical studies}\label{sec:experiments}
\subsection{Protocol and comparisons}
We study reward performance and the cost of reliable reporting separately. The frozen main suite contains 12 scenarios, 24 configurations and 96 paired replications per scenario and configuration, giving 27,648 records. A subsequent correction of one ALL comparator contributes 1,152 additional records. The original and corrected comparator records are both retained. The primary analysis replaces the original adaptive ALL configuration by its corrected version, leaving 24 configurations and 27,648 records.

The scenarios have 2--20 arms and horizons of 12,000--16,000. Eleven use Bernoulli rewards; one uses bounded two-point rewards. The reporting parameters $\varepsilon$ and $\eta$ vary by scenario, while $\delta=.05$ throughout. Supplementary Section~\ref{sec:main-numerical-protocol} gives every arrival time, mean and configuration. Within a replication, all methods share the same potential reward stream for each arm, and the mean labels of arms arriving together are jointly permuted. The action routines receive only revealed arms, past observations and their own randomization; they do not receive the means, future arrivals or evaluation horizon. All failed-report paths remain in every reported mean, area and quantile.

The five reward comparators are UCB1, Growing-MOSS, MC-MOSS, Thompson sampling and KL-UCB. They make no designated certification pulls and carry the same valid reporter as F-CCP. Thompson sampling uses Beta$(1,1)$ updates for Bernoulli rewards; its fractional updates for the bounded two-point scenario are an action heuristic, not a correctly specified Bernoulli posterior. F-R uses temperature $.5$ and reward protection $\beta_R=16$ with service disabled. The compatibility configuration F-R-TS-exact instead uses temperature one and no reward guard; it reproduces the specified Thompson rule rather than serving as a second independent comparator.

For joint performance we compare the prespecified F configurations with CCP-original, ALL-area and ALL-auto-costmatched. CCP-original is the earlier CCP configuration in this test suite, not the checkpoint method in Supplementary Section~\ref{sec:legacy-checkpoint-study}. The ALL methods are natural retained-history adaptations, rather than implementations of the original FAREAST or $(ST)^2$ procedures. The corrected adaptive ALL method uses the same projected-mean sampling price as F-CCP, the same reward kernel and the same two budgets. Its initial implementation returned zero as that price; the correction changes that comparator input alone, with the scenarios, seeds and all F-CCP parameters fixed. The superseded output remains a diagnostic in Supplementary Section~\ref{sec:development-audit}.

Development and testing use separate environments and seeds. The reward configuration was selected by the prespecified equal-weight development mean regret, and the moderate-service configuration was fixed before the main test. No preference, temperature or confidence parameter is selected from the test results. The parameter values in these experiments are not generally in the narrower regime of the minimax lower bound; these comparisons do not validate its asymptotic rate.

\subsection{Reward performance with service disabled}
'''+reward_main+r'''
F-R has a lower mean regret than all five reward comparators in 11 of the 12 scenarios, and a strictly lower mean in 59 of the 60 scenario--comparator comparisons. Its mean is '''+fmt(reduction,1)+r'''\% below Thompson sampling when the 12 scenario means are averaged with equal weights. This ratio compares two descriptive suite averages; it is not an average of scenario-specific percentage reductions or a risk under one common environment distribution. The gain in this experiment concerns the reward-score configuration and its protection, since the certificate scheduler is disabled.

The two-close-arms scenario is an exception. F-R minus Thompson has mean '''+fmt(rdiff.delta_mean,2)+r''' and a paired, two-sided 95\% approximate $t$ interval $['''+fmt(rdiff.delta_l95,2)+','+fmt(rdiff.delta_u95,2)+r''']$. Across the full family of 60 prespecified comparisons, 52 one-sided Bonferroni-adjusted upper endpoints are below zero. Under the separate, more permissive margin of 5\% of the comparator mean plus two regret units, 54 are below the corresponding threshold. The latter criterion is not zero-margin noninferiority. Neither the low means nor a failure to detect a difference proves uniform dominance over the baselines.

\begin{figure}[t]
\centering
\includegraphics[width=.94\linewidth]{revision2/generated/reward-paired.pdf}
\caption{F-R minus Thompson cumulative dynamic regret in each frozen scenario. Points are means of 96 within-replication differences; error bars are individual two-sided 95\% approximate $t$ intervals. Negative differences favor F-R. These 12 intervals do not by themselves control the 60-comparison family; the adjusted counts are reported in the text.}
\label{fig:reward-paired}
\end{figure}

\subsection{Preference and certification cost}
'''+pref_main+r'''
Increasing service preference reduces unresolved arm-time over much of the tested range, at a substantial reward cost. The points at $\lambda=.9$ and $1$ under the fixed certification budget are not monotone: the latter has slightly lower regret and slightly larger area. We retain that reversal. F-area removes the certification cap; it is a different budget configuration and is not a continuation of the same-budget curve.

Relative to ALL-auto-costmatched, F-auto-0.6 has lower equal-weight mean regret ('''+fmt(suite.loc['F-auto-0.6','regret_mean'],2)+' versus '+fmt(suite.loc['ALL-auto-costmatched','regret_mean'],2)+r''') and area ('''+fmt(suite.loc['F-auto-0.6','area_mean']/1000,2)+' versus '+fmt(suite.loc['ALL-auto-costmatched','area_mean']/1000,2)+r''' thousand arm-time units). The comparison with CCP-original is a trade-off: F-auto-0.6 has lower mean regret but higher mean area. F-area has lower suite mean regret and area than ALL-area. These are finite-suite averages, rather than per-scenario or pathwise Pareto guarantees. Supplementary Tables~\ref{tab:all-methods} and~\ref{tab:joint-paired} give the scenario decomposition and paired uncertainty.

\begin{figure}[t]
\centering
\includegraphics[width=.94\linewidth]{revision2/generated/preference-tradeoff.pdf}
\caption{Descriptive averages of terminal costs over the 12 frozen scenarios. Connected circles follow the prespecified order $\lambda=0,.1,.3,.6,.9,1$, with $\beta_R=16$, temperature $.5$, and $\beta_C=1$ whenever service is active. The star is F-area with $\beta_C=\infty$; the other markers are named comparators. The connecting segments identify configurations and do not estimate a continuous or optimal frontier. Area is divided by $10^3$.}
\label{fig:preference-tradeoff}
\end{figure}

The controller's proposed rate differs from the realized service fraction because the phase must accumulate and the certification guard can reject a proposal. Supplementary Table~\ref{tab:service-diagnostics} reports proposed busy-round rates, successful pulls, denials and the final unresolved count. Fixed-rate, uncapped-service, temperature-one and unprotected-reward variants are retained as prespecified ablations. We use those comparisons only for the mechanisms they actually change.

\subsection{Tail behavior and report failures}
'''+tail_main+r'''
The lower mean regret of F-R does not extend to all tail summaries. Its empirical 95th percentile exceeds Thompson's in the burst, ceiling and larger-pool scenarios in Table~\ref{tab:tail-and-failure}. Each percentile uses only 96 replications; it should not be read as a precise population tail estimate.

F-auto-0.6 produces an incorrect determined label on one of its 1,152 runs; F-R and F-area produce none. Coverage failures and empty intersections also occur: the respective counts are $(6,1)$ for F-R, $(7,1)$ for F-auto-0.6, and $(8,0)$ for F-area. An empty intersection triggers persistent all-unresolved reporting, not successful completion. All these runs enter the cost calculations. Since methods share potential streams, their failures are dependent and cannot be pooled as independent reliability trials. These empirical counts neither replace the reliability theorem nor justify an all-times claim from 96 repetitions. Full failure counts, empirical maxima and implementation qualifications appear in Supplementary Sections~\ref{sec:main-numerical-protocol}--\ref{sec:development-audit}.
'''

    # S15 complete frozen protocol, full tables and uncertainty.
    scenario_rows=[[esc(s['name']),str(len(s['means'])),f"{s['T']:,}",str(s['epsilon']),str(s['eta']),'Bernoulli' if s['kind']=='bernoulli' else 'Two-point'] for s in scenarios]
    sc_table=table('Frozen main-test scenarios; $\\delta=.05$ in every row. The arrays below specify arrivals and arm means before within-batch random permutation.','tab:main-scenarios','lrrrrl',['Scenario',r'$K_T$',r'$T$',r'$\varepsilon$',r'$\eta$','Reward'],scenario_rows,r'\footnotesize')
    map_rows=[]; mapping=[]
    for m in methods:
        pol=policies[m]; status='superseded controller diagnostic' if m=='ALL-auto-0.6' else 'corrected comparator' if m=='ALL-auto-costmatched' else 'original frozen main configuration'
        mapping.append(dict(code=codes[m],method_id=m,display_name=m,analysis_status=status,**{k:v for k,v in pol.items() if k!='name'}))
        br=r'$\infty$' if pol['beta_r'] is None else f"{pol['beta_r']:g}"
        bs='inactive' if pol['priority']==0 else (r'$\infty$' if pol['beta_s'] is None else f"{pol['beta_s']:g}")
        map_rows.append([codes[m],r'\texttt{'+esc(m)+'}',f"{pol['priority']:g}",f"{pol['temperature']:g}",br,bs,'auto' if pol['adaptive'] else 'fixed'])
    pd.DataFrame(mapping).to_csv(OUT/'method-mapping.csv',index=False)
    map_table=longtable('Method identifiers and frozen controls. M22 is retained solely as a superseded controller diagnostic; M25 is its corrected primary comparator. An inactive service budget is never tested because service is disabled.','tab:frozen-method-map','llrrrrl',['Code','Frozen method ID',r'$\lambda$',r'$\theta$',r'$\beta_R$',r'$\beta_C$','Rate'],map_rows,8)
    arrays=[]
    for s in scenarios:
        arrays.append(r'\paragraph{'+SC_LABELS[s['name']]+r'.} '+r'Arrivals and corresponding means, grouped by physical arrival time, are')
        groups=[]
        for at in sorted(set(s['arrivals'])):
            values=[str(mu) for a,mu in zip(s['arrivals'],s['means']) if a==at]
            groups.append(rf'$t={at}$: $('+', '.join(values)+')$')
        arrays.append('; '.join(groups)+'.')
    se_rows=[[SC_LABELS[s]]+[ms(si.loc[(s,m)],'regret') for m in BASES+['F-R']] for s in names]
    se_table=longtable('Cumulative dynamic regret, mean (Monte Carlo standard error), from 96 paired replications per cell. G-MOSS denotes Growing-MOSS and TS denotes Thompson sampling.','tab:reward-se','lrrrrrr',['Scenario','UCB1','G-MOSS','MC-MOSS','TS','KL-UCB','F-R'],se_rows,7.5)
    full_rows=[]
    for j,s in enumerate(names):
        full_rows.append([rf'\multicolumn{{7}}{{l}}{{\textit{{{SC_LABELS[s]}}}}}','','','','','',''])
        # Marker handled below to avoid invalid extra cells after multicolumn.
        for m in methods:
            r=si.loc[(s,m)];full_rows.append([codes[m],ms(r,'regret'),ms(r,'area',1000),fmt(r.regret_q95),fmt(r.regret_max),ms(r,'service_pulls',1,1),ms(r,'final_unresolved',1,2)])
    full_table=longtable('All 25 stored method IDs in every scenario, including the superseded M22 diagnostic. Each row uses all 96 replications. Regret, area, service pulls and final boundary-separated unresolved counts are means (Monte Carlo standard errors); area is divided by $10^3$. The two regret tail columns give the empirical 95th percentile and observed maximum. Method codes are in Table~\\ref{tab:frozen-method-map}.','tab:all-methods','lrrrrrr',['Code','Regret (SE)',r'Area/$10^3$ (SE)',r'$q_{.95}(R)$',r'$\max R$','Service (SE)',r'$V_{\rm sep}(T)$ (SE)'],full_rows,8)
    full_table=re.sub(r'(\\multicolumn\{7\}\{l\}\{\\textit\{[^\n]+?\}\}) &  &  &  &  &  & ',r'\1',full_table)
    paired_rows=[[esc(r.scenario),r.baseline,fmt(r.delta_mean),fmt(r.delta_se),f'[{r.delta_l95:.2f}, {r.delta_u95:.2f}]',fmt(r.delta_upper95_family60),fmt(r.relaxed_upper95_family60)] for r in paired.itertuples()]
    paired_table=longtable('All 60 prespecified reward comparisons. Differences are F-R minus the named baseline. The interval is an individual two-sided approximate $t$ interval; $U_{60}$ is the one-sided Bonferroni upper endpoint at family level $.05$. The last column instead tests F-R minus $1.05$ times the comparator minus 2. These margins are different.','tab:reward-paired-full','llrrrrr',['Scenario','Baseline','Difference','SE','Individual 95\% CI',r'$U_{60}$',r'$U_{60}^{\rm relaxed}$'],paired_rows,7.5)
    joint_rows=[]
    for r in joint:
        if (r['candidate'],r['baseline']) not in [('F-auto-0.6','ALL-auto-costmatched'),('F-area','ALL-area'),('F-auto-0.6','CCP-original')]:continue
        if r['metric']=='service_pulls':continue
        scale=1000 if r['metric']=='area' else 1
        joint_rows.append([codes[r['candidate']]+'--'+codes[r['baseline']],esc(r['scenario']),'Area/$10^3$' if scale==1000 else 'Regret',fmt(r['delta_mean']/scale),fmt(r['se']/scale),f"[{r['lower95']/scale:.2f}, {r['upper95']/scale:.2f}]"])
    joint_table=longtable('Prespecified joint-cost differences by scenario, candidate minus comparator. Codes identify M15=F-auto-0.6, M17=F-area, M12=CCP-original, M23=ALL-area and M25=ALL-auto-costmatched. Individual two-sided approximate $t$ intervals use 96 paired differences and have no family adjustment.','tab:joint-paired','llrrrr',['Pair','Scenario','Metric','Difference','SE','Individual 95\% CI'],joint_rows,8)
    fail_rows=[[codes[m],str(int(failures.loc[m,'label_error'])),str(int(failures.loc[m,'coverage_error'])),str(int(failures.loc[m,'empty_intersection']))] for m in methods]
    fail_table=table('Runs with at least one label error, coverage failure or empty intersection, out of 1,152 per method. Failures across methods can share the same latent reward stream and are dependent. Superseded M22 is retained as a diagnostic.','tab:failure-counts','lrrr',['Method code','Label error','Coverage failure','Empty intersection'],fail_rows,r'\footnotesize')
    diag_rows=[]
    for m in PREFERENCE+['F-area','CCP-original','ALL-auto-costmatched','ALL-area']:
        g=data[data.method==m];rate=float(g.service_mass.sum()/g.active_service_rounds.sum()) if g.active_service_rounds.sum() else 0
        diag_rows.append([codes[m],fmt(rate,4),fmt(suite.loc[m,'service_pulls_mean'],1),fmt(suite.loc[m,'service_denials_mean'],1),fmt(suite.loc[m,'final_unresolved_mean'],2)])
    diag_table=table('Service diagnostics: proposed rate pooled over busy rounds, and equal-weight scenario means of actual successful service pulls, denied proposals and final boundary-separated unresolved counts. The proposed rate is not the realized service fraction.','tab:service-diagnostics','lrrrr',['Code','Proposed busy rate','Service pulls','Denials',r'$V_{\rm sep}(T)$'],diag_rows,r'\footnotesize')
    supplement15=r'''\section{Main numerical protocol and full results}\label{sec:main-numerical-protocol}
\subsection{Frozen scenarios and randomization}
The original test has 27,648 records ($12\times24\times96$); the corrected ALL comparator adds 1,152. All 28,800 records are retained. Replacing, rather than pooling, the superseded adaptive ALL method yields the 24-method primary roster. A replication is a shared-stream paired experiment, not 24 independent environments. The reward-stream seed is 117110100 and the policy seed is 117120100, with the recorded scenario and replication offsets. Within-batch permutations use a separate generator with offset 50,000,000. Complete settings and exact offsets are stored in the two frozen JSON protocols.
'''+sc_table+'\n'+'\n\n'.join(arrays)+r'''

For Bernoulli arms, each latent observation is an indicator with the listed mean. In the two-point scenario an arm with mean $r_i$ takes values $r_i\pm h_i$ with equal probability, where $h_i=\min\{.045,r_i,1-r_i\}$. All observations lie in $[0,1]$. Arm labels within a simultaneous batch are permuted jointly for all methods in a replication. An evaluator holds the future streams and true means; the selection routines do not receive them. Every stored run has total actual pulls equal to its stated horizon.

\subsection{Method identity and recorded metrics}
'''+map_table+r'''
All methods use prior parameter one for Beta action scores and the same report evidence. The default reward guard coefficient is 16 where enabled; the adaptive controller uses price $.1$, floor $.02$ and backlog scale four. The scheduler is the new certificate-cost planner for the F configurations, the retained earlier scheduler for CCP-original, and the ALL adaptation for the ALL configurations. Pure reward controls have no designated certification. Frozen null service caps in F-R and F-R-TS-exact are inactive because $\lambda=0$; the interactive presets express the same behavior with service cap zero.

The CSV field \texttt{regret} stores the sum of current mean gaps, called cumulative dynamic regret in the manuscript. \texttt{area} is unresolved arm-time outside the scenario's $\eta$ boundary band. \texttt{final\_unresolved} counts only these boundary-separated unresolved arms, whereas \texttt{final\_all\_unresolved} includes unresolved arms inside the band. The latter is not substituted for the former. \texttt{service\_pulls} counts actual certification observations; \texttt{service\_attempts} also includes rejected proposals. \texttt{service\_mass} sums proposed rates over busy rounds. The two \texttt{tax} fields accumulate virtual optimism gaps for actual reward and service choices; they are distinct from \texttt{service\_regret}, which the evaluator computes from true means. \texttt{label\_error}, \texttt{coverage\_error} and \texttt{empty\_intersection} are separate run-level indicators.

\subsection{Complete costs and Monte Carlo uncertainty}
'''+se_table+'\n'+full_table+r'''
Every cost summary includes report-failure and fallback paths. Standard errors describe independent repetitions within one fixed scenario; sharing streams across methods is used in the paired differences below. Equal weighting of scenario means is descriptive because horizons, arm counts and reporting tolerances differ. Empirical quantiles and maxima are finite-suite summaries, not distribution-wide probability bounds.

\subsection{Paired reward and joint-cost comparisons}
'''+paired_table+'\n'+joint_table+r'''
The family of 60 reward comparisons was specified before testing. Of these, 59 mean differences are strictly negative, 52 one-sided family-adjusted zero-margin upper endpoints are negative, and 54 pass the separate relaxed criterion. These statements concern different targets. The individual intervals are approximate Student $t$ intervals; no exact finite-sample Monte Carlo coverage is asserted. In particular, the positive F-R minus Thompson point estimate for two close arms remains in all tables and figures.

\subsection{Service diagnostics and all failures}
'''+diag_table+'\n'+fail_table+r'''
F-auto-0.6 has one erroneous-label trajectory in the ceiling scenario, associated with replication index 75. The full stored trajectory is retained. A persistent empty-intersection failure changes all later reports to all unresolved, so an observed zero label-error count alone does not show successful maintenance. The raw failure records, including their scenario, replication and method keys, accompany the release. Methods sharing latent streams are not independent reliability trials.
'''

    # S16 preserve generations, ablations and implementation scope.
    ablate=['F-R','Cold-TS-unprotected','Warm-TS-guard','F-auto-0.6','F-fixed-0.6','F-auto-0.6-no-service-cap','F-auto-0.6-TS','F-area','ALL-auto-0.6','ALL-auto-costmatched']
    ab_rows=[[codes[m],esc(m),fmt(suite.loc[m,'regret_mean'],2),fmt(suite.loc[m,'area_mean']/1000,2)] for m in ablate]
    ab_table=table('Prespecified implementation variants, averaged equally over the 12 scenario means. M22 is superseded and is shown only to document its controller input; it is not evidence for an allocation advantage. Scenario-specific results and uncertainty for every row are in Table~\\ref{tab:all-methods}.','tab:implementation-ablations','llrr',['Code','Configuration','Regret',r'Area / $10^3$'],ab_rows,r'\footnotesize')
    inv=[]
    inputs=[('Earlier checkpoint',PROJECT/'experiments/results','5760',4,9,160),('CCP development study',REPO/'CCP_research_2026-10-16/test-results.csv','13440',10,21,64),('Frontier/Shared study',REPO/'frontier_research_2026-10-16/holdout-all.csv','12672',12,22,48)]
    for lab,path,expect,nsc,nm,reps in inputs:
        if path.is_dir():
            candidates=list(path.glob('*.csv')); chosen=[]
            for pp in candidates:
                try:
                    dg=pd.read_csv(pp); count=len(dg)
                    if count==int(expect):chosen.append((pp,dg))
                except Exception:pass
            assert chosen, f'Cannot locate {expect} row legacy data'
            path,dg=chosen[0]
        elif path.is_file():dg=pd.read_csv(path)
        else:
            archive_name='CCP_算法探索_研究包_2026-10-16.zip' if nsc==10 else 'Regret_未决量前沿_理论与算法研究包_2026-10-16.zip'
            archive=PROJECT/'experiments/fccp_frozen/original-archives'/archive_name
            with zipfile.ZipFile(archive) as z:
                matches=[n for n in z.namelist() if n.endswith('/'+path.name) and '/prior/' not in n]
                assert len(matches)==1
                with z.open(matches[0]) as stream:dg=pd.read_csv(stream)
        assert len(dg)==int(expect)
        assert dg.scenario.nunique()==nsc and dg.method.nunique()==nm
        assert (dg.groupby(['scenario','method']).size()==reps).all()
        if path.is_file(): original_path=str(path.relative_to(REPO)).replace('\\','/'); original_hash=sha(path)
        else:
            original_path=str(archive.relative_to(PROJECT)).replace('\\','/')+'!/'+matches[0]
            with zipfile.ZipFile(archive) as z:original_hash=hashlib.sha256(z.read(matches[0])).hexdigest()
        inv.append(dict(generation=lab,path=original_path,rows=len(dg),scenarios=nsc,methods=nm,repetitions=reps,sha256=original_hash,role='historical; not pooled with F17'))
    inv.extend([dict(generation='F17 original test',path='F-CCP_2026-10-17/results/holdout-all.csv',rows=27648,scenarios=12,methods=24,repetitions=96,sha256=sha(F/'results/holdout-all.csv'),role='original; superseded ALL retained'),dict(generation='F17 corrected comparator',path='F-CCP_2026-10-17/results/matched-all-all.csv',rows=1152,scenarios=12,methods=1,repetitions=96,sha256=sha(F/'results/matched-all-all.csv'),role='replaces old ALL in primary analysis')])
    write_json('dataset-inventory.json',inv)
    inv_table=table('Distinct numerical generations. Similar scenario or method names do not imply identical environments, reporting tolerances, implementations or replication counts. Development trajectories are not pooled with any frozen test.','tab:data-generations','lrrrr',['Generation','Scenarios','Methods','Repetitions','Records'],[[r['generation'],str(r['scenarios']),str(r['methods']),str(r['repetitions']),f"{r['rows']:,}"] for r in inv],r'\footnotesize')
    dev_counts={}
    for stem in ['development-all','development2-all','development3-all']:
        dev_counts[stem]=len(pd.read_csv(F/'results'/f'{stem}.csv'))
    assert list(dev_counts.values())==[2640,5616,5760]
    residual=data.service_mass-data.service_attempts
    phase_count=int((data.service_attempts != np.floor(data.service_mass+1e-8)).sum())
    assert phase_count==1035
    audit=json.loads((F/'results/implementation-audit.json').read_text(encoding='utf-8'))
    supplement16=r'''\section{Development, ablations, and implementation audit}\label{sec:development-audit}
\subsection{Distinct studies and prespecified controls}
'''+inv_table+r'''
The first CCP study and the subsequent frontier/Shared study are development predecessors with their own frozen protocols. Their tests contain 13,440 and 12,672 records, respectively. They preserve unsuccessful candidates and negative comparisons; they are not added to the F-CCP win counts. The earlier checkpoint comparison is retained in Supplementary Section~\ref{sec:legacy-checkpoint-study}. Its 5,760 observations, four environments and resource measurements remain separate.

Within the F-CCP study, the three valid development rounds contain 2,640, 5,616 and 5,760 trajectories (14,016 in total). The initial development compilation failure generated no valid trajectory; its protocol and failure logs remain in the source archive. The final temperature and reward guard were selected using the recorded development rule, before the test. Development and test seeds and numerical environments differ, although their task types overlap. These archives document selection rather than provide independent repetitions of the main test.

'''+ab_table+r'''
Cold-TS-unprotected removes the reward guard while retaining temperature $.5$; Warm-TS-guard changes the temperature schedule. The fixed-rate variant, the uncapped certification variant and the temperature-one variant each preserve the settings stated in the frozen method map. Their full scenario results include unfavorable comparisons. These are configuration comparisons, not evidence that an untested mechanism caused the observed gain. No configuration was retuned during this manuscript reanalysis.

\subsection{Comparator correction and numerical qualifications}
The original adaptive ALL planner returned the proposed arm together with zero as its estimated sampling cost. That second return value is irrelevant when the service rate is fixed or equals one, but changes the interior adaptive controller. The corrected planner returns the gap between the largest projected mean and the proposed arm's projected mean, exactly as in F-CCP. The comparator correction was separately frozen after the audit and rerun on the same 12 scenarios and 96 seeds. No F-CCP or reward-baseline parameter changed. Both versions remain in the archive; the corrected version replaces the original in primary comparisons and is not averaged with it.

The mathematical phase rule uses exact arithmetic. The frozen implementation has 1,035 runs in which floating-point accumulation delays a service attempt by one slot at an integer boundary. Across the stored main and corrected records, the phase residual $\sum p_t-\mathrm{attempts}$ ranges from '''+fmt(residual.min(),12)+' to '+fmt(residual.max(),12)+r'''. These records were not changed retrospectively. The guard comparisons allow $10^{-12}$, planning uses the frozen regularization, and confidence inversion uses outward numerical roots. Such diagnostics do not establish exact arithmetic guarantees for all machine inputs. Changing those tolerances would define a new implementation version and require new experiments.

The interactive interface owns a NumPy Generator, whereas the frozen batch engine uses Numba randomization. Same-backend compatibility requires the same state, draw order and random stream; equal seeds across these backends do not imply identical paths. The batch production entry is \texttt{flexible\_v2.choose\_dual}; the corrected ALL driver uses \texttt{flexible\_matched.choose\_dual}. The earlier single-ledger development routine is retained for provenance and is not the production entry.

The interactive entry \texttt{FlexibleCCP} accepts newly arriving labels and one observed reward per physical round. It accepts no future arrival schedule, true means or evaluation horizon. Priority may change only after the pending observation, and changing it retains counts, intervals, phase and both ledgers. \texttt{None} disables a guard; zero is a zero budget. Thus changing priority to one does not remove a pre-existing finite certification cap. The classification preset instead uses no cap from initialization.

The direct implementation examines pairs of arms for comparison, planning and reporting, giving quadratic per-round pair work, together with spectral-bin loops and numerical confidence inversion. Its machine-integer checkpoints and fixed 64-bin spectrum representation are implementation limits; they do not impose corresponding finite-horizon assumptions on the mathematical model. No linear-complexity claim for the older checkpoint method is transferred to F-CCP.

\subsection{Resources and scope of reproducibility}
The original F-CCP implementation audit records Python 3.13.5 on Linux x86-64, NumPy 2.3.5 and Numba 0.65.1. The environment file records pandas 2.2.3, SciPy 1.17.0 and matplotlib 3.10.8. The archive does not identify a benchmark CPU, so we report none. Per-run timing fields and worker logs are retained, but their compilation, concurrency and timing boundaries do not define one comparable total wall-clock runtime. The Windows configuration and 13.5-second measurement in the earlier checkpoint study are not F-CCP measurements.

The source archive reports internal diagnostics for 50,000 same-backend compatibility actions, 800 future-padding checks, 126 interval inversions, 10,000 service-rate formula checks and 4,000 rounds with preference changes. Those are historical diagnostics, not independently rerun probability proofs. The manuscript revision separately performs read-only endpoint reanalysis and short API checks in a copied workspace, with their actual commands and environment saved in the release. Neither form of checking constitutes independent peer review or formal verification.

All results use simulated data. The accompanying local release includes the frozen code dependency closure, both protocols, all test records, development and failure archives, summaries, limited saved paths, source hashes and the read-only table/figure generator. A public repository or permanent accession has not been established. Each main-test scenario saves only its first four diagnostic paths on a 200-round grid; no figure presents them as a 96-replication learning curve. The two main figures are computed entirely from terminal records.
'''

    (REV/'numerical_sections.json').write_text(json.dumps({'main_section':main_section,'supplement_s15':supplement15,'supplement_s16':supplement16},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_json('inline-table-record.json',dict(reward_rows=reward_rows,preference_rows=pref_rows,tail_rows=tail_rows))
    # Release copies preserve every byte and keep source research directories untouched.
    release=PROJECT/'experiments/fccp_frozen'; release.mkdir(parents=True,exist_ok=True)
    copied=json.loads((OUT/'release-manifest.json').read_text(encoding='utf-8'))['files'] if source_is_release else []
    for p in ([] if source_is_release else F.rglob('*')):
        if not p.is_file() or '__pycache__' in p.parts:continue
        rel=p.relative_to(F)
        if p.suffix=='.md' or p.name.startswith('assessment'):continue
        dest=release/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists():assert sha(dest)==sha(p), f'Existing release differs: {rel}'
        else:shutil.copyfile(p,dest)
        copied.append(dict(source=str(p.relative_to(REPO)).replace('\\','/'),destination=str(dest.relative_to(PROJECT)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size))
    archives=release/'original-archives';archives.mkdir(exist_ok=True)
    zip_sources=['F-CCP_可调算法_理论与实验_2026-10-17.zip','CCP_算法探索_研究包_2026-10-16.zip','Regret_未决量前沿_理论与算法研究包_2026-10-16.zip']
    for z in ([] if source_is_release else zip_sources):
        p=REPO/z;dest=archives/z
        if dest.exists():assert sha(dest)==sha(p)
        else:shutil.copyfile(p,dest)
        copied.append(dict(source=z,destination=str(dest.relative_to(PROJECT)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size))
    write_json('release-manifest.json',dict(files=copied,source_research_directories_read_only=True,copy_policy='Exact computational files and complete original ZIP archives; no source modified.'))
    mapping_notes=[dict(module='flexible_v2.py::choose_dual',role='main production action rule',status='frozen',note='two independent ledgers'),
       dict(module='flexible_ccp.py::FlexibleCCP',role='interactive production API',status='frozen',note='owns NumPy Generator; no future truth inputs'),
       dict(module='flexible_matched.py::choose_dual',role='corrected ALL action rule',status='frozen',note='only ALL planner cost return corrected'),
       dict(module='matched_all.py::service_plan_matched',role='CCP and corrected ALL planning dispatch',status='frozen',note='corrected price interface'),
       dict(module='flexible_engine.py::choose_flexible',role='historical single-ledger development',status='archive only',note='not main production entry')]
    pd.DataFrame(mapping_notes).to_csv(OUT/'production-branch-map.csv',index=False)
    all_after={str(p.relative_to(F)).replace('\\','/'):sha(p) for p in F.rglob('*') if p.is_file()}
    assert all_before==all_after, 'Frozen source tree changed'
    write_json('numerical-validation.json',dict(status='passed',scope='read-only reanalysis, figures and exact copies; no new comparative simulation',
        frozen_source_files=len(all_before),original_manifest_entries_checked=len(original_manifest),frozen_source_unchanged=True,stored_records=len(data),corrected_primary_records=len(primary),
        stored_methods=25,primary_methods=24,summary_mean_max_abs_error=errors,mean_wins=winmean,all_five_mean_wins_scenarios=all5,
        strict_family60= strict,relaxed_family60=relaxed,equal_scenario_mean_reduction_vs_thompson_percent=reduction,
        phase_integer_boundary_cases=phase_count,phase_residual_range=[float(residual.min()),float(residual.max())],
        failure_paths_retained=len(failure_examples),development_rows=dev_counts,figures=['reward-paired.pdf','preference-tradeoff.pdf'],
        generated_tex_files=0,release_copies=len(copied)))
    print(json.dumps(dict(status='passed',stored=len(data),primary=len(primary),mean_wins=winmean,strict=strict,relaxed=relaxed,
                         reduction_percent=reduction,json=str(REV/'numerical_sections.json'),copied_files=len(copied)),indent=2))

if __name__=='__main__':main()

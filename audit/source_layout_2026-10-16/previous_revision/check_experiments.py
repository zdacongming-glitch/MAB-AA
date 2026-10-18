#!/usr/bin/env python3
"""Read-only data audit and short semantic diagnostics; no comparison reruns."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXP = ROOT / "experiments"
RES = EXP / "results"
sys.dont_write_bytecode = True
os.environ["NUMBA_CACHE_DIR"] = str(HERE / "semantic_check_cache")
import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes():
    roots = [EXP, ROOT / "figures"]
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
            for base in roots for p in base.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts}


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def semantic_checks():
    ref = load_module("checkpoint_reference_revision_oct16", EXP / "reference_cp_ucb_aa.py")
    runner = load_module("checkpoint_runner_revision_oct16", EXP / "run_experiments.py")
    cases = [
        dict(name="initial_single_zero", horizon=35, arrivals={1:[0.]}, eps=.05),
        dict(name="initial_multiple_zero_one", horizon=350, arrivals={1:[0.,0.,1.]}, eps=.05),
        dict(name="rear_checkpoint_and_skip", horizon=120, arrivals={1:[0.,0.,0.,1.]}, eps=.05, rho=.99),
        dict(name="odd_even_arrivals", horizon=120, arrivals={1:[0.],3:[1.],4:[0.]}, eps=.05),
        dict(name="batch_exceeds_remaining_budget", horizon=6, arrivals={1:[1.],5:[0.,1.]*8}, eps=.05),
        dict(name="mixed_deterministic_streams", horizon=90, arrivals={1:[.5,.75],31:[.25,1.]}, eps=.3),
    ]
    all_case_results = []
    global_witness = dict(behind_front_checkpoint=None, completed_rear_skipped=None, frozen_qplus1=None,
                          negative_then_ucb_selected=None)
    for case in cases:
        horizon = case["horizon"]
        births=[]; means=[]
        for t, values in sorted(case["arrivals"].items()):
            means.extend(values); births.extend([t]*len(values))
        means=np.asarray(means); births=np.asarray(births,dtype=np.int64)
        rewards = np.zeros((len(means),horizon),dtype=np.uint8)
        for i,mean in enumerate(means):
            # Fixed binary periodic streams; inputs diagnose semantics, not power.
            rewards[i] = (np.arange(horizon)%4 < round(4*mean)).astype(np.uint8)
        eps=case["eps"]; rho=case.get("rho",.9); delta=.49
        metrics, _, _, _, _, trace = runner.simulate(rewards,means,births,horizon,
            eps,.1,delta,1,rho,2,False,1,np.asarray([horizon],np.int64),True)
        alg=ref.CheckpointUCBAA(eps,delta,rho)
        steps=[]; freezes={}; old_negative=set(); arrived=0
        behind=[]; frozen_steps=[]; negative_ucb=[]
        for t in range(1,horizon+1):
            new=[]
            while arrived<len(means) and births[arrived]==t:
                arrived+=1; new.append(arrived)
            queue_before=list(alg.pending)
            completed_before={i for i in queue_before if alg.arms[i].count>=alg.arms[i].quota}
            label,service=alg.choose(new)
            popped_completed=completed_before-set(alg.pending)
            if global_witness["behind_front_checkpoint"] and global_witness["completed_rear_skipped"] is None:
                witness=global_witness["behind_front_checkpoint"]
                if witness["case"]==case["name"] and witness["arm"] in popped_completed:
                    global_witness["completed_rear_skipped"]={"case":case["name"],"t":t,"arm":witness["arm"],
                        "queue_before":queue_before,"queue_after":list(alg.pending)}
            assert label==int(trace[t-1,0]),(case["name"],t,"action")
            assert service==bool(trace[t-1,1]),(case["name"],t,"service")
            assert 1<=label<=arrived
            if service:
                assert t%2==0 and alg.pending and alg.pending[0]==label
            else:
                # All arrived arms, including negative reports, enter this index.
                indices={i:math.inf if a.count==0 else a.reward_sum/a.count+
                         math.sqrt(3*math.log(2*t)/a.count) for i,a in alg.arms.items()}
                assert label==max(indices,key=lambda i:(indices[i],-i))
                if label in old_negative:
                    negative_ucb.append(t)
            a=alg.arms[label]
            before=a.count
            was=(a.lower,a.upper)
            reward=int(rewards[label-1,before])
            alg.observe(reward)
            positive,negative,unresolved=alg.report()
            assert not(positive&negative or positive&unresolved or negative&unresolved)
            assert positive|negative|unresolved==set(range(1,arrived+1))
            assert sum(a.count for a in alg.arms.values())==t
            if a.count==a.quota:
                freezes[label]=(a.lower,a.upper)
                if alg.pending and alg.pending[0]!=label:
                    behind.append(t)
                    if global_witness["behind_front_checkpoint"] is None:
                        global_witness["behind_front_checkpoint"]={"case":case["name"],"t":t,"arm":label,
                            "queue_front":alg.pending[0],"service":bool(service)}
            if a.count>a.quota:
                assert (a.lower,a.upper)==was==freezes[label]
                if a.count==a.quota+1:
                    frozen_steps.append(t)
                    if global_witness["frozen_qplus1"] is None:
                        global_witness["frozen_qplus1"]={"case":case["name"],"t":t,"arm":label,
                            "count":a.count,"quota":a.quota,"interval":[a.lower,a.upper]}
            if not service and label in old_negative and global_witness["negative_then_ucb_selected"] is None:
                global_witness["negative_then_ucb_selected"]={"case":case["name"],"t":t,"arm":label}
            old_negative=set(negative)
            # Re-evaluate the unchanged compiled simulator at this endpoint to
            # compare frozen intervals and counts at every physical time.
            prefix=runner.simulate(rewards,means,births,t,eps,.1,delta,1,rho,2,False,1,
                                   np.asarray([t],np.int64),False)
            for i,arm in alg.arms.items():
                assert arm.count==int(trace[t-1,2+i-1])==int(prefix[2][i-1])
                assert arm.reward_sum==float(rewards[i-1,:arm.count].sum())
                assert abs(arm.lower-prefix[3][i-1])<1e-14
                assert abs(arm.upper-prefix[4][i-1])<1e-14
                code=1 if i in positive else -1 if i in negative else 0
                assert code==int(trace[t-1,2+len(means)+i-1])
                if i in freezes:
                    assert (arm.lower,arm.upper)==freezes[i]
            steps.append(dict(t=t,arrivals=new,action=label,service=bool(service),reward=reward,
                pending=list(alg.pending),counts={str(i):a.count for i,a in alg.arms.items()},
                sums={str(i):a.reward_sum for i,a in alg.arms.items()},
                quotas={str(i):a.quota for i,a in alg.arms.items()},
                intervals={str(i):[a.lower,a.upper] for i,a in alg.arms.items()},
                positive=sorted(positive),negative=sorted(negative),unresolved=sorted(unresolved)))
        all_case_results.append(dict(name=case["name"],horizon=horizon,epsilon=eps,delta=delta,rho=rho,
            arrivals={str(k):v for k,v in case["arrivals"].items()},input="deterministic periodic binary reward streams",
            all_checks_passed=True,behind_front_checkpoint_rounds=behind,
            first_postcheckpoint_pull_rounds=frozen_steps,negative_arm_ucb_rounds=negative_ucb,steps=steps))
    assert all(global_witness.values()),global_witness
    return dict(performed_this_revision=True,comparison_experiments_rerun=False,
                historical_20000_round_check_rerun=False,renaming="display only; no API or policy changes",
                compared_fields=["actions","service flags","all counts","reward sums derived from identical streams",
                                 "frozen intervals","positive/negative/unresolved reports"],
                cases=all_case_results,witnesses=global_witness)


def data_checks():
    config=json.loads((RES/"config.json").read_text(encoding="utf-8"))
    data=pd.read_csv(RES/"runs.csv")
    summary=pd.read_csv(RES/"summary.csv")
    methods=[m["name"] for m in config["methods"]]
    scenarios=[s["name"] for s in config["scenarios"]]
    n=config["replications"]
    assert len(data)==4*9*160 and not data.duplicated(["scenario","method","seed"]).any()
    assert data.groupby(["scenario","method"]).size().eq(160).all()
    assert config["horizon"]==20000 and config["epsilon"]==.3 and config["eta"]==.1 and config["delta"]==.05
    assert len(methods)==9 and len(scenarios)==4
    metric_names=["regret","area_eta","area_all","service_pulls","service_regret",
                  "final_u_eta","final_u_all","quota_completed","admission_delay_regret",
                  "elimination_deficit_regret","within_active_regret"]
    summary_discrepancies=[]
    for _,row in summary.iterrows():
        sample=data[(data.scenario==row.scenario)&(data.method==row.method)]
        for metric in metric_names:
            for stat,value in [("mean",sample[metric].mean()),("se",sample[metric].std(ddof=1)/math.sqrt(n))]:
                saved=float(row[metric+"_"+stat])
                err=abs(saved-value)
                assert math.isclose(saved,value,rel_tol=2e-11,abs_tol=1e-10),(row.scenario,row.method,metric,stat,saved,value)
                summary_discrepancies.append(err)
    main_methods=["CP-FIFO-fine","CP-FIFO","UCB-prefix","Growing-MOSS","ALL-epsilon-adapt","Batch100-UCB"]
    lines=[line for line in (RES/"table_main.tex").read_text(encoding="utf-8").splitlines()
           if re.search(r"&\s*[0-9]+\.[0-9]+\s*\(",line)]
    assert len(lines)==24
    main_rows=[]
    for line,(scenario,method) in zip(lines,[(s,m) for s in scenarios for m in main_methods]):
        sample=data[(data.scenario==scenario)&(data.method==method)]
        regret=f"{sample.regret.mean():.1f} ({sample.regret.std(ddof=1)/math.sqrt(n):.1f})"
        area=f"{sample.area_eta.mean()/1000:.2f} ({sample.area_eta.std(ddof=1)/math.sqrt(n)/1000:.2f})"
        assert regret in line and area in line,(scenario,method,line,regret,area)
        main_rows.append(dict(scenario=scenario,method=method,regret=regret,area_in_1000=area))
    alloc_lines=[line for line in (RES/"table_allocation.tex").read_text(encoding="utf-8").splitlines()
                 if re.search(r"&\s*[0-9]+,\s*[0-9]+\.[0-9]+",line)]
    assert len(alloc_lines)==9
    for line,method in zip(alloc_lines,methods):
        for scenario in scenarios:
            sample=data[(data.scenario==scenario)&(data.method==method)]
            assert f"{sample.service_pulls.mean():.0f}, {sample.final_u_eta.mean():.2f}" in line
    fine=data[data.method=="CP-FIFO-fine"]
    exposure={s["name"]:sum(len(mus)*(config["horizon"]-t+1) for t,mus in s["arrivals"]) for s in config["scenarios"]}
    assert len(fine)==640
    assert fine.apply(lambda row:row.area_all==exposure[row.scenario],axis=1).all()
    assert fine.final_u_all.eq(8).all()
    # A nonnegative unresolved count can equal total exposure only if every
    # available arm was unresolved after every observation, not just at saved times.
    quota_totals={str(rho):sum(math.ceil(2/rho**2*math.log(4*i*(i+1)/.05)) for i in range(1,9)) for rho in [.04,.12]}
    assert quota_totals=={"0.04":73083,"0.12":8123}
    assert data.error_ever.sum()==0 and data.error_rounds.sum()==0
    decomposition=(data.regret-data.admission_delay_regret-data.elimination_deficit_regret-data.within_active_regret).abs()
    assert decomposition.max()<3.1e-12
    batch=data[data.method=="Batch100-UCB"]
    batch_admission={s:batch[batch.scenario==s].admission_delay_regret.mean() for s in scenarios}
    assert all(abs(a-b)<1e-10 for a,b in zip(batch_admission.values(),[0,33.92,16.,22.4]))
    assert batch.elimination_deficit_regret.eq(0).all()
    npz=np.load(RES/"paths.npz")
    assert npz["paths"].shape[:3]==(4,160,9)
    assert list(npz["methods"])==methods and list(npz["scenarios"])==scenarios
    for s in config["scenarios"]:
        assert all(t in npz["times"] for t,_ in s["arrivals"])
    paired=pd.read_csv(RES/"paired_differences.csv")
    for _,row in paired.iterrows():
        sample=data[data.scenario==row.scenario]
        target=sample[sample.method==row.target].set_index("seed")[row.metric]
        other=sample[sample.method==row.baseline].set_index("seed")[row.metric]
        diff=target-other
        assert math.isclose(row.mean_difference,diff.mean(),rel_tol=1e-9,abs_tol=1e-8)
        assert math.isclose(row.paired_se,diff.std(ddof=1)/math.sqrt(n),rel_tol=1e-9,abs_tol=1e-8)
    manifest=json.loads((RES/"manifest.json").read_text(encoding="utf-8"))
    hash_map={"source_sha256":EXP/"reference_cp_ucb_aa.py","runner_sha256":EXP/"run_experiments.py",
              "config_sha256":RES/"config.json","runs_sha256":RES/"runs.csv","paths_sha256":RES/"paths.npz"}
    hash_checks={k:sha(path)==manifest[k] for k,path in hash_map.items()}
    assert all(hash_checks.values()),hash_checks
    return dict(total_runs=len(data),groups=36,replications_per_group=160,main_table_rows=main_rows,
                allocation_rows=9,summary_max_absolute_rounding_discrepancy=max(summary_discrepancies),
                fine_runs=640,fine_all_available_arms_unresolved_every_round=True,
                exposure_by_environment=exposure,final_fine_u_eta=sorted(fine.final_u_eta.unique().tolist()),
                quota_totals=quota_totals,error_runs=0,
                zero_error_upper95_per_fixed_environment_method=1-.05**(1/160),
                maximum_decomposition_error=float(decomposition.max()),batch_admission=batch_admission,
                batch_retirement_deficit=0,paired_records_rechecked=len(paired),manifest_hash_checks=hash_checks,
                paths_shape=list(npz["paths"].shape),saved_times=int(len(npz["times"])),
                publicly_verified_release_url=None,
                availability="Local configuration, reference class, driver, raw runs and saved paths exist; no public release URL independently verified.")


def main():
    before=protected_hashes()
    data=data_checks()
    semantic=semantic_checks()
    after=protected_hashes()
    assert before==after,"Protected experiment/figure file modified"
    details=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),passed=True,
                 new_comparison_experiments=False,new_figures=False,
                 protected_files_byte_identical=True,protected_file_hashes=after,
                 data=data,semantic_checks=semantic)
    (HERE/"experiments_validation.json").write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding="utf-8")
    report="""# 本轮实验迁移与核验

执行对象为当前本地四环境、九方法、每组160次、每次20,000物理轮的既有模拟记录。此次没有开展新比较实验，没有重画图，没有更改任何方法、参数、seed、代码接口或原始结果。

## 数据核对

- 实际读取 `experiments/results/config.json`、`runs.csv`、`paths.npz`、`summary.csv`、`paired_differences.csv` 与两份表格源码。
- 5,760条记录、36组、每组160条均完整且无重复环境/方法/seed；配置为 $T=20,000$、$\\varepsilon=.30$、$\\eta=.10$、$\\delta=.05$。
- 从真实运行记录重算主表24行的均值、Monte Carlo标准误和面积单位 $10^3$，与原表显示精度全部一致；九方法分配表与256条成对差异亦核对一致。
- 640次细精度运行的 `area_all` 都等于该环境全部已到达臂的总曝光量，终点全部八臂未决。这证明每个报告时刻所有可用臂始终未决，而非只在稀疏保存网格未决。边界外终点数量为5、6或8，不能解释为其余臂已分类。
- 两个八臂配额和分别为73,083与8,123；零误报只描述既有有限实验。固定方法和环境160次零失败的单侧95%上界约0.018549。
- 三项regret记账的最大绝对误差小于 $3.1\\times10^{-12}$。Batch100的接纳项依次为0、33.92、16.00、22.40，历史退休项均为0。
- manifest列出的reference、driver、配置、runs及paths五个SHA256全部匹配。完整文件hash、逐项主表数值与差异记录见JSON。

## 本轮执行的代码语义诊断

实际导入现有reference类和Numba编译的 `simulate`，在相同确定性潜在流上逐轮核对动作、服务标记、计数、可重构奖励和、冻结区间及三分类集合。使用合法但不同于比较实验的诊断参数 $\\rho=.9$ 或 $.99$、$\\delta=.49$ 缩短配额；这些输入只验证程序语义，不估计方法性能或可靠性概率。

覆盖初始单臂、初始多臂、0/1奖励、奇数/偶数到达、批次大于剩余物理预算、UCB提前完成队列后方配额、$q_i-1\\to q_i\\to q_i+1$区间冻结，以及已判负臂仍进入UCB并再次被其选中。每步单个合法动作、计数总和等于物理时间、报告集合不交且覆盖全部已到达臂均通过。每个输入与逐轮动作/计数/奖励和/区间/队列/报告均存于JSON；未改类名、API或策略，无需另造改名包装。

历史 `results/source_parity.json` 的20,000轮检查没有在本轮重跑；不把历史记录计为新执行。本轮短诊断与既有5,760次比较明确区分。

## 可用性与范围

本地完整配置、逐次终点记录、共同网格路径、代码及绘图入口存在；路径文件不含完整逐轮动作日志，不能冒称其记录全部轮次。当前未独立核实公开仓库/永久发布URL，稿件只陈述本地复现材料状态。该公开发布事项应在正式投稿前由作者完成，不影响此次基于本地真数据的核对。

旧60,000轮实验与图片保持历史归档，新正文及新投稿补充材料不调用它们。本轮所有实验、结果、图文件均在核验前后逐字节一致。精细配置全未决、粗配置在稳定/突发环境双指标劣势、连续改善中的服务量混杂和MOSS低regret大面积等负面事实仍在正文。

未发现数据或代码语义阻塞；公开发布地址尚未核实。新的机制实验、同任务前沿比较和理论扩展均未执行。
"""
    (HERE/"experiments_validation.md").write_text(report,encoding="utf-8")
    print(json.dumps({"passed":True,"total_runs":data["total_runs"],"main_table_rows":len(data["main_table_rows"]),
        "fine_all_unresolved_runs":640,"diagnostic_cases":len(semantic["cases"]),
        "diagnostic_rounds":sum(c["horizon"] for c in semantic["cases"]),
        "semantic_witnesses":semantic["witnesses"],"protected_files_byte_identical":True},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()

"""Independent aggregate reconstruction and eight primary paired contrasts.

This verifier does not import the producer's analysis or simulation functions.
It accepts only a completed full 384-cell/20-repeat dataset. Run after analyze.
"""
from pathlib import Path
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from collections import defaultdict

import numpy as np
from scipy.stats import t


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(root):
    root=Path(root)
    config=json.loads((root/"config.json").read_text(encoding="utf-8"))
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"]=="PASS" and not manifest["errors"]
    recoveries=[]
    incident_path=root/"validation/execution_incidents.json"
    if incident_path.exists():
        for incident in json.loads(incident_path.read_text(encoding="utf-8")):
            archived=[name for name in incident["evidence_files"] if name.endswith("_manifest.json")]
            assert len(archived)==1
            previous=json.loads((root/"validation"/archived[0]).read_text(encoding="utf-8"))
            assert previous["status"] in {"FAILED","INTERRUPTED"}
            assert previous["fingerprint"]==manifest["fingerprint"]
            assert previous["config_sha256"]==manifest["config_sha256"]
            assert all(manifest["shards"].get(task)==sha for task,sha in previous["shards"].items())
            assert all(error["task_id"] in manifest["shards"] for error in previous["errors"])
            recoveries.append(dict(evidence_manifest=archived[0],
                retained_byte_identical_shards=len(previous["shards"]),
                source_config_seed_fingerprint_unchanged=True,
                failed_task_worlds_present_in_complete_dataset=True))
    assert (len(config["layouts"]),len(config["tasks"]),config["replications"],config["expected_runs"])==(24,7680,20,38400)
    assert config["protocol"]["primary_family_size"]==8
    layout_map={l["id"]:l for l in config["layouts"]}
    sources={name:digest(root/"source_snapshot"/name)==sha for name,sha in config["source_files"].items()}
    assert all(sources.values())
    canonical=json.loads((root/"source_snapshot/configs/layouts.json").read_text(encoding="utf-8"))
    assert config["layouts"]==[l for l in canonical if l["group"] in {"f17","adaptive"}]
    aggregate={}
    hashers={table:hashlib.sha256() for table in ("runs","counts","trajectories")}
    fields={}
    row_counts=defaultdict(int)
    observations=defaultdict(lambda:defaultdict(dict))
    worlds=set()
    feedbacks=0
    for task in config["tasks"]:
        path=root/"shards"/(task["task_id"]+".json.gz")
        assert digest(path)==manifest["shards"][task["task_id"]]
        with gzip.open(path,"rt",encoding="utf-8") as f:
            value=json.load(f)
        assert value["task_id"]==task["task_id"] and value["execution_errors"]==[]
        assert value["numba_cache"]["source_fingerprint"]==config["cache"]["source_fingerprint"]
        world=(task["layout_id"],task["law"],task["rep"])
        assert world not in worlds
        worlds.add(world)
        assert len(value["runs"])==5 and {r["method"] for r in value["runs"]}==set(config["methods"])
        for row in value["runs"]:
            assert (row["layout_id"],row["law"],row["rep"])==world
            assert row["seed_base"]==config["protocol"]["seed_base"]==2026111401
            layout=layout_map[row["layout_id"]]
            assert row["T"]==layout["T"] and row["K"]==len(layout["arms"])
            assert row["reports_evaluated"] is False
            assert math.isfinite(row["regret"]) and 0<=row["regret"]<=row["T"]
            observations[(row["group"],row["method"])][world[:2]][row["rep"]]=row["regret"]
            counts=[r for r in value["counts"] if r["method"]==row["method"]]
            assert sum(r["n"] for r in counts)==row["T"]
            assert {r["arm"] for r in counts}==set(range(row["K"]))
            feedbacks+=sum(r["n"] for r in counts)
        for table,hasher in hashers.items():
            rows=value[table]
            buffer=io.StringIO(newline="")
            if table not in fields:
                fields[table]=list(rows[0])
                writer=csv.DictWriter(buffer,fieldnames=fields[table])
                writer.writeheader()
            else:
                writer=csv.DictWriter(buffer,fieldnames=fields[table])
            writer.writerows(rows)
            hasher.update(buffer.getvalue().encode("utf-8"))
            row_counts[table]+=len(rows)
    assert feedbacks==483200000
    for table,hasher in hashers.items():
        with gzip.open(root/(table+".csv.gz"),"rb") as f:
            actual=hashlib.sha256(f.read()).hexdigest()
        assert hasher.hexdigest()==actual
        assert row_counts[table]==manifest["files"][table+".csv.gz"]["rows"]
        aggregate[table]=dict(rows=row_counts[table],uncompressed_sha256=actual)
    with (root/"analysis/primary_comparisons.csv").open(encoding="utf-8",newline="") as f:
        reported=list(csv.DictReader(f))
    assert len(reported)==8
    recomputed=[]
    def mean(x):
        return math.fsum(x)/len(x)
    def variance(x):
        center=mean(x)
        return math.fsum((z-center)**2 for z in x)/(len(x)-1)
    for report in reported:
        group,baseline=report["group"],report["comparator"]
        a=observations[(group,"FULL-R")]
        b=observations[(group,baseline)]
        assert len(a)==len(b)==192 and set(a)==set(b)
        pairs=[]
        for cell in sorted(a):
            assert set(a[cell])==set(b[cell])==set(range(20))
            pairs.append(([a[cell][r] for r in range(20)],[b[cell][r] for r in range(20)]))
        A=mean([mean(x) for x,y in pairs]); B=mean([mean(y) for x,y in pairs])
        diffs=[[x-y for x,y in zip(xs,ys)] for xs,ys in pairs]
        D=mean([mean(d) for d in diffs]); relative=D/B
        expected=dict(candidate_regret=A,comparator_regret=B,regret_difference=D,percent_change=100*relative)
        for stem,values,center in [("difference",diffs,D),("percent",[[100/B*(d-relative*y) for d,y in zip(ds,ys)] for ds,(xs,ys) in zip(diffs,pairs)],100*relative)]:
            parts=[variance(x)/(20*192**2) for x in values]
            V=math.fsum(parts); se=math.sqrt(V)
            df=V*V/math.fsum(x*x/19 for x in parts) if V else math.inf
            critical=t.ppf(1-.05/16,df)
            expected.update({stem+"_mcse":se,stem+"_df":df,
                stem+"_adjusted_ci_low":center-critical*se,stem+"_adjusted_ci_high":center+critical*se})
        for key,value in expected.items():
            assert math.isclose(float(report[key]),value,rel_tol=2e-10,abs_tol=1e-9),(group,baseline,key,report[key],value)
        recomputed.append(dict(group=group,comparator=baseline,**expected))
    result=dict(status="PASS",scope="deterministic data and statistic checks, not universal scientific validity",
        worlds=len(worlds),runs=row_counts["runs"],feedbacks=feedbacks,
        feedback_scope="Unique included trajectories; interrupted in-flight computations are not extra samples",
        aggregate_reconstruction=aggregate,source_snapshot_checks=sources,primary_family_size=8,
        primary_recomputed=recomputed,execution_recoveries=recoveries,verifier_sha256=digest(__file__))
    (root/"analysis/independent_verification.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","worlds","runs","feedbacks")},indent=2))
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    verify(parser.parse_args().output)

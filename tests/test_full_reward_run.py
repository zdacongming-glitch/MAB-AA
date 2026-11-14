"""Original-grid contract and paired execution/resume invariance."""
from copy import deepcopy
import gzip
import json

import numpy as np
import pytest

from srcbench import full_reward as fr
from srcbench.design import load_layouts, LAWS_16
from srcbench.full_reward_analysis import comparison


def test_full_grid_retains_every_original_input_and_twenty_pairs():
    c=fr.config_for()
    original=[x for x in load_layouts() if x["group"] in {"f17","adaptive"}]
    assert c["layouts"] == original
    assert len(original)==24 and c["expected_worlds"]==7680 and c["expected_runs"]==38400
    assert c["replications"]==20
    cells={(t["layout_id"],t["law"]) for t in c["tasks"]}
    assert cells=={(l["id"],law) for l in original for law in LAWS_16}
    assert {m for m in c["methods"]}=={"FULL-R","SRC-R","SRC-KL-R","IMED","Empirical-KL-UCB"}
    assert c["methods"]["SRC-KL-R"]["params"].get("cap_multiplier",1)==1


def tiny_config():
    c=fr.config_for()
    layout=deepcopy(c["layouts"][0])
    layout.update(T=45,id="tiny-test",arms=[dict(arrival=1,mean=.5),dict(arrival=1,mean=.4),dict(arrival=17,mean=.7)])
    c["layouts"]=[layout]
    c["tasks"]=[dict(task_id="tiny-"+str(rep),layout_id=layout["id"],law="beta02",rep=rep,seed_base=81019) for rep in range(2)]
    c.update(expected_worlds=2,expected_runs=10,replications=2)
    return c


def test_workers_order_resume_and_fingerprints(tmp_path,monkeypatch):
    config=tiny_config()
    monkeypatch.setattr(fr,"config_for",lambda pilot=False:deepcopy(config))
    one,two=tmp_path/"one",tmp_path/"two"
    fr.run(one,workers=1)
    fr.run(two,workers=2)
    assert fr.verify(one,True)["runs"]==10
    def normalized(path):
        raw=fr._read(path)
        for row in raw["runs"]:
            row.pop("runtime_seconds")
        return raw
    for task in config["tasks"]:
        assert normalized(one/"shards"/(task["task_id"]+".json.gz"))==normalized(two/"shards"/(task["task_id"]+".json.gz"))
    saved={n:(one/n).read_bytes() for n in ("runs.csv.gz","counts.csv.gz","trajectories.csv.gz")}
    fr.run(one,workers=2,resume=True)
    for name,value in saved.items():
        assert (one/name).read_bytes()==value
    task=config["tasks"][0]
    reversed_methods=dict(reversed(list(config["methods"].items())))
    rev=fr.simulate_world(task,config["layouts"][0],reversed_methods,config["protocol"]["trajectory_fractions"])
    a={r["method"]:(r["regret"],r["action_hash"]) for r in rev["runs"]}
    b={r["method"]:(r["regret"],r["action_hash"]) for r in fr._read(one/"shards"/(task["task_id"]+".json.gz"))["runs"]}
    assert a==b
    config["tasks"][0]["seed_base"]+=1
    with pytest.raises(ValueError,match="cannot resume"):
        fr.run(one,resume=True)


def test_paired_statistics_stable_and_family_adjusted():
    import pandas as pd
    rows=[]
    for cell,offset in enumerate((1.,1e6)):
        for rep,change in enumerate((-3.,-1.,1.,3.)):
            for method,value in [("FULL-R",offset+10+change),("IMED",offset+12)]:
                rows.append(dict(layout_id=str(cell),law="test",rep=rep,group="f17",method=method,regret=value))
    r=comparison(pd.DataFrame(rows),"FULL-R","IMED",8)
    assert r["regret_difference"]==pytest.approx(-2.)
    assert r["difference_mcse"]==pytest.approx(np.sqrt((20/3)/8))
    assert r["difference_adjusted_ci_low"] < r["difference_ci_low"]
    assert r["difference_adjusted_ci_high"] > r["difference_ci_high"]

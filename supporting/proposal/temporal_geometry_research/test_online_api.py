"""Small interface and clipping checks, distinct from the simulation totals."""
from __future__ import annotations
import json
from pathlib import Path
from mc_moss import MCMOSS

steps = 0
results = {}
for clip in (False, True):
    policy = MCMOSS(clip=clip)
    regret = 0
    for t in range(1, 1001):
        arm = policy.select([t])
        reward = 1.0 if arm == 1 else 0.0
        policy.update(reward)
        regret += 1-reward
        steps += 1
    assert regret == (0 if clip else 999)
    assert sum(policy.lifetime_counts.values()) == 1000
    assert policy.statistical_counts == policy.lifetime_counts
    results['clipped' if clip else 'unclipped'] = regret

p = MCMOSS()
try:
    p.select()
    raise AssertionError('Empty initial set was accepted')
except ValueError:
    pass
assert p.select(['a', 'b']) == 'a'
try:
    p.select()
    raise AssertionError('A second select was accepted before update')
except RuntimeError:
    pass
try:
    p.update(2.0)
    raise AssertionError('An invalid reward was accepted')
except ValueError:
    pass
p.update(0.5)
steps += 1
try:
    p.select(['b'])
    raise AssertionError('Duplicate label was accepted')
except ValueError:
    pass
results.update(additional_completed_policy_steps=steps, status='all API checks passed')
Path(__file__).with_name('api_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))

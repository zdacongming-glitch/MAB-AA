"""Combine actual isolated-agent records; never generate scores."""
from pathlib import Path
import argparse, json, importlib.util

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument('phase', choices=['initial', 'final'])
ap.add_argument('--planned', type=int, default=5)
args = ap.parse_args()
folder = ROOT/'assessments'
manifest = json.loads((folder/f'{args.phase}_manifest.json').read_text(encoding='utf-8'))
round_paths = sorted(folder.glob(f'{args.phase}_round_*.json'))
rounds=[]
for p in round_paths:
    r=json.loads(p.read_text(encoding='utf-8-sig'))
    assert r['context_id'].startswith('/root/'), (p, 'actual collaboration context required')
    assert r['packet_id']==manifest['packet_id'], p
    assert r['protocol_id']==manifest['protocol_id'], p
    rounds.append(r)
labels={'c1':'Broadcast uncertainty and arrival feasibility',
        'c2':'Temporary tasks and regret-service tradeoff',
        'c3':'Executable lifetime-evidence method',
        'c4':'Worst-schedule service complexity and bursts',
        'c5':'New risk-mode and truncated-window extensions',
        'overall':'Overall innovation'}
batch={'schema_version':1,'batch_id':f'{args.phase}-20261015',
       'packet_id':manifest['packet_id'],'protocol_id':manifest['protocol_id'],
       'protocol':{'rubric_version':'local-rubric-and-repeated-assessment-read-20261015',
                   'model_id':manifest['model_id'],'model_snapshot':None,
                   'settings':manifest['settings'],'execution_method':'isolated_agents'},
       'planned_rounds':args.planned,
       'objects':[{'id':i,'label':labels[i], 'kind':'overall' if i=='overall' else 'contribution',
                   'basis':'current','dimensions':['innovation']} for i in manifest['objects']],
       'rounds':rounds}
batch_path=folder/f'{args.phase}_batch.json'
batch_path.write_text(json.dumps(batch,ensure_ascii=False,indent=2),encoding='utf-8')
script=Path(r'C:\Users\12701\.codex\skills\statistical-innovation-assessment\scripts\summarize_assessments.py')
spec=importlib.util.spec_from_file_location('summary',script)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
result=mod.summarize_batch(batch)
(folder/f'{args.phase}_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
# Skill-generated dashes are changed only in prose, without touching mathematics.
markdown=mod.markdown_summary(result).replace('\u2014','-').replace('\u2013',' to ')
(folder/f'{args.phase}_summary.md').write_text(markdown,encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))

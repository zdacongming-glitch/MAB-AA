"""Record actual agent contexts and summarize their unaltered assessments."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
SKILL = Path('C:/Users/12701/.codex/skills/statistical-innovation-assessment')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--register', action='append', default=[])
parser.add_argument('--planned', type=int, default=5)
parser.add_argument('--summarize', action='store_true')
args = parser.parse_args()
manifest = read(HERE/'evidence-manifest.json')
protocol = read(HERE/'protocol.json')
execution_path = HERE/'execution-log.json'
executions = read(execution_path) if execution_path.exists() else {'execution_method':'isolated_agents','contexts':[]}
known = {x['canonical_task_name'] for x in executions['contexts']}
for name in args.register:
    if name in known:
        raise ValueError('Context already recorded: '+name)
    executions['contexts'].append({'canonical_task_name':name,
        'registration_time_utc':datetime.now(timezone.utc).isoformat(),
        'execution_id_source':'actual canonical task name returned by collaboration.spawn_agent',
        'fork_turns':'none','model_override':None,'reasoning_override':None,
        'invocation_sha256':sha(HERE/'agent-invocation.txt')})
    known.add(name)
if args.register:
    write(execution_path,executions)

errors=[]
for item in manifest['files']:
    frozen = HERE/item['snapshot']
    if sha(frozen)!=item['sha256']:
        errors.append('Frozen source changed: '+item['snapshot'])
    if sha(PROJECT/item['source'])!=item['sha256']:
        errors.append('Live source changed: '+item['source'])
for item in manifest['rules']:
    if sha(HERE/item['snapshot'])!=item['sha256']:
        errors.append('Frozen rule changed: '+item['snapshot'])
for rel,key in [('evidence-packet.md','packet_sha256'),('manuscript-excerpts.txt','excerpts_sha256')]:
    if sha(HERE/rel)!=manifest[key]:
        errors.append('Packet component changed: '+rel)
for rel,key in [('evaluation-task.txt','task_sha256'),('agent-invocation.txt','invocation_sha256')]:
    if sha(HERE/rel)!=protocol['settings'][key]:
        errors.append('Task changed: '+rel)
if errors:
    raise ValueError('\n'.join(errors))

if args.summarize:
    rounds=[]
    for file in sorted((HERE/'rounds').glob('*.json')):
        item=read(file)
        name=item['canonical_task_name']
        if name not in known:
            raise ValueError('Assessment has no actual registered context: '+name)
        if file.stem!=name.rsplit('/',1)[-1]:
            raise ValueError('Filename differs from actual context: '+str(file))
        for key in ['packet_id','protocol_id']:
            if item[key]!=manifest[key]:
                raise ValueError('Mixed '+key+' in '+str(file))
        rounds.append({'round_id':file.stem,'context_id':name,
            'packet_id':manifest['packet_id'],'protocol_id':manifest['protocol_id'],
            'scores':item['scores'],
            'source_file':file.relative_to(HERE).as_posix(),'source_sha256':sha(file),
            'verification_scope':item.get('verification_scope'),
            'confidence':item.get('confidence'),
            'priority_validation':item.get('priority_validation')})
    batch={'schema_version':1,'batch_id':'ucbaa-current-innovation-2026-10-18',
        'packet_id':manifest['packet_id'],'protocol_id':manifest['protocol_id'],
        'protocol':protocol,'planned_rounds':args.planned,
        'objects':protocol['objects'],'rounds':rounds}
    write(HERE/'assessment-batch.json',batch)
    script=HERE/'rules/summarize_assessments.py'
    subprocess.run([sys.executable,str(script),str(HERE/'assessment-batch.json'),
        '--output',str(HERE/'assessment-summary.json'),
        '--markdown',str(HERE/'assessment-summary.md')],check=True)
    write(HERE/'integrity-check.json',{'checked_at_utc':datetime.now(timezone.utc).isoformat(),
        'frozen_and_live_sources_unchanged':True,'source_count':len(manifest['files']),
        'rules_and_task_unchanged':True,'executed_rounds':len(rounds),
        'summarizer_source':str(script),'summarizer_sha256':sha(script),
        'round_files':{x['source_file']:x['source_sha256'] for x in rounds}})
    summary=read(HERE/'assessment-summary.json')
    compact=[{k:x[k] for k in ['object_id','mean','sample_variance',
        'standard_deviation','minimum','maximum','tier_counts','scored_rounds',
        'consensus_status']} for x in summary['results']]
    print(json.dumps({'executed_rounds':len(rounds),'planned_rounds':args.planned,
        'results':compact,'recommendation':summary['recommendation']},ensure_ascii=False))
else:
    print(json.dumps({'registered_contexts':len(known),'integrity':'passed'},ensure_ascii=False))

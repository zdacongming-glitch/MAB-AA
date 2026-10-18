from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
source = ROOT.parent/'proposal'/'ucbaa_continuous_maintenance_2026-10-14'/'持续集合维护_理论与完整证明.md'
note = source.read_text(encoding='utf-8').split('## 18.')[0]
(ROOT/'assessments'/'initial_theory.txt').write_text(note, encoding='utf-8')
paths = [ROOT/'assessments'/'initial_evidence.md', ROOT/'assessments'/'initial_theory.txt']
hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
packet = 'initial-'+hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
manifest = {'packet_id':packet,'protocol_id':'innovation-only-fixed-rubric-isolated-v1',
 'files':hashes,'objects':['c1','c2','c3','c4','overall'],
 'model_id':'inherited parent model; exact serving snapshot not exposed',
 'model_snapshot':None,'settings':{'fork_turns':'none','model_override':False},
 'verification':'Hashes identify material, not mathematical truth.'}
(ROOT/'assessments'/'initial_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(packet)

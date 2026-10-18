from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'manuscript.tex',*sorted((ROOT/'sections').glob('*.tex')),
       ROOT/'supplement.tex',*sorted((ROOT/'theory').glob('*.tex')),
       ROOT/'references.bib',ROOT/'experiments'/'results'/'summary.csv',
       ROOT/'experiments'/'results'/'verification.json',
       ROOT/'experiments'/'results'/'source_parity.json']
packet='\n\n'.join('FILE: '+p.relative_to(ROOT).as_posix()+'\n'+p.read_text(encoding='utf-8') for p in files)
out=ROOT/'assessments'/'final_packet.txt';out.write_text(packet,encoding='utf-8')
paths=[ROOT/'assessments'/'final_evidence.md',out]
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
packet_id='final-'+hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
manifest={'packet_id':packet_id,'protocol_id':'innovation-only-fixed-rubric-isolated-v1',
 'files':hashes,'source_files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
 'objects':['c1','c2','c3','c4','c5','overall'],
 'model_id':'inherited parent model; exact serving snapshot not exposed',
 'model_snapshot':None,'settings':{'fork_turns':'none','model_override':False},
 'verification':'Hashes identify frozen evidence; they do not prove truth or novelty.'}
(ROOT/'assessments'/'final_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(packet_id)

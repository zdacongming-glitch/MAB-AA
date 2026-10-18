from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
wrapper=Path(r'C:\Users\12701\.codex\skills\watermarks-remover\scripts\watermarks.py')
source=ROOT/'assessments'/'final_packet.txt'
dest=ROOT/'audit'/'final_packet.cleaned.txt'
reports={}
for operation,extra in [('inspect',[]),('clean',['--mode','unicode','-o',str(dest)])]:
    run=subprocess.run([sys.executable,'-X','utf8',str(wrapper),operation,str(source),*extra],capture_output=True)
    output=run.stdout.decode('utf-8-sig',errors='replace')
    reports[operation]={'exit_code':run.returncode,'result':json.loads(output),
                        'stderr':run.stderr.decode('utf-8',errors='replace')}
    if run.returncode not in [0,1,3]: raise RuntimeError(output)
reports['byte_identical']=source.read_bytes()==dest.read_bytes()
reports['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
reports['cleaned_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
reports['scope']='Invisible Unicode cleanup only; prose was edited separately. Statistical token watermarks are not tested. Authors, citations, mathematics and required attribution retained.'
(ROOT/'audit'/'watermark_report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'byte_identical':reports['byte_identical'],'source_sha256':reports['source_sha256'],'scope':reports['scope']},ensure_ascii=False))

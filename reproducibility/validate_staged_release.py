"""Export exactly the Git index and test the package without neighboring research."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime as dt,hashlib,json,os,subprocess,sys,time,uuid

PAPER=Path(__file__).resolve().parent.parent
REPO=PAPER.parent
OUT=PAPER/'reproducibility'
raw=subprocess.run(['git','ls-files','--stage','-z'],cwd=REPO,capture_output=True,check=True).stdout
entries=[]
for item in raw.split(b'\0'):
    if not item:
        continue
    metadata,name=item.split(b'\t',1)
    mode,object_id,stage=metadata.decode('ascii').split()
    assert stage=='0'
    entries.append((name.decode('utf-8'),object_id))
roots=sorted({Path(name).parts[0] for name,_ in entries if len(Path(name).parts)>1})
assert roots==['JASA-template',PAPER.name],roots
mismatches=[]
checked=0
for name,object_id in entries:
    if not name.startswith(PAPER.name+'/'):
        continue
    data=(REPO/name).read_bytes()
    calculated=hashlib.sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()
    if calculated!=object_id:
        mismatches.append(name)
    checked+=1
assert not mismatches,mismatches
stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
target=REPO/('.resubmission_release_check_'+stamp+'_'+uuid.uuid4().hex[:6])
assert target.resolve().parent==REPO.resolve() and not target.exists()
target.mkdir()
prefix=target.as_posix()+'/'
subprocess.run(['git','checkout-index','--all','--prefix='+prefix],cwd=REPO,check=True)
project=target/PAPER.name
assert not (target/'proposal').exists()
assert not (target/'F-CCP_2026-10-17').exists()
assert not (target/'CCP_research_2026-10-16').exists()
env=os.environ.copy()
env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
def execute(action):
    command=[sys.executable,'-B','-X','utf8','reproduce.py','--'+action]
    started=time.monotonic()
    result=subprocess.run(command,cwd=project,env=env,capture_output=True,
                          text=True,encoding='utf-8',errors='replace')
    record={'action':action,'command':command,'cwd':str(project),
            'exit_code':result.returncode,'seconds':round(time.monotonic()-started,3),
            'stdout':result.stdout,'stderr':result.stderr}
    (OUT/f'release-{action}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'action':action,'exit_code':result.returncode},ensure_ascii=False),flush=True)
    return record
with ThreadPoolExecutor(max_workers=2) as pool:
    records=list(pool.map(execute,['verify','figures','smoke','build']))
report={'status':'passed' if all(r['exit_code']==0 for r in records) else 'failed',
        'date':'2026-10-17','export':'exact Git index via checkout-index',
        'tracked_files':len(entries),'root_directories':roots,
        'byte_exact_staged_resubmission_files':checked,
        'staged_blob_mismatches':mismatches,'standalone_copy':str(target),
        'external_research_directories_present':False,
        'actions':[{'action':r['action'],'exit_code':r['exit_code'],'seconds':r['seconds']} for r in records],
        'scope':'full packaged data reanalysis, figures, short API checks and manuscript build; complete stochastic performance batches were not rerun'}
(OUT/'release-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='passed' else 1)

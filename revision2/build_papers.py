"""Build the current complete entry with pdfLaTeX/BibTeX/latexmk."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,time

REV=Path(__file__).resolve().parent
ROOT=REV.parent
parser=argparse.ArgumentParser()
parser.add_argument('--baseline',action='store_true')
args=parser.parse_args()
if args.baseline:
    for stem in ['manuscript','supplement']:
        current=(ROOT/f'{stem}.tex').read_bytes()
        frozen=(REV/'baseline'/f'{stem}.tex').read_bytes()
        if hashlib.sha256(current).digest()!=hashlib.sha256(frozen).digest():
            raise SystemExit('The root sources have changed since baseline compilation. '
                             'The actual baseline build is preserved in revision2/baseline-compiled/; '
                             'refusing to label a revised build as baseline.')
outdir=Path('revision2/baseline-build') if args.baseline else Path('build')
(ROOT/outdir).mkdir(parents=True,exist_ok=True)
logs=REV/'build-logs';logs.mkdir(exist_ok=True)
combined='BEGIN MERGED SUPPLEMENTARY MATERIAL' in (ROOT/'manuscript.tex').read_text(encoding='utf-8')
prefix='baseline' if args.baseline else ('combined' if combined else 'revised')
records=[]
entries=['manuscript'] if combined else ['supplement','manuscript']
if not args.baseline and not combined:entries+=['supplement','manuscript']
with (logs/f'{prefix}-console.log').open('w',encoding='utf-8') as log:
    for i,stem in enumerate(entries):
        commands=[['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error',f'-outdir={outdir.as_posix()}',f'{stem}.tex'],
                  ['bibtex',f'{outdir.as_posix()}/{stem}'],
                  ['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error',f'-outdir={outdir.as_posix()}',f'{stem}.tex']]
        for command in commands:
            log.write('\nCOMMAND '+repr(command)+'\n');log.flush();start=time.monotonic()
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            records.append({'command':command,'cwd':str(ROOT),'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3)})
            if result.returncode:
                (logs/f'{prefix}-commands.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
                raise SystemExit(result.returncode)
    for stem in (['manuscript'] if combined else ['manuscript','supplement']):
        destination=REV/'baseline-compiled'/f'{stem}.pdf' if args.baseline else ROOT/f'{stem}.pdf'
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT/outdir/f'{stem}.pdf',destination)
(logs/f'{prefix}-commands.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'mode':prefix,'commands':len(records),'all_exit_zero':True}))

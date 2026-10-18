"""Render every final PDF page and create labeled contact sheets."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
import subprocess,json,re

REV=Path(__file__).resolve().parent
ROOT=REV.parent
OUT=REV/'page-review'
OUT.mkdir(exist_ok=True)

def render(stem):
    folder=OUT/stem
    folder.mkdir(exist_ok=True)
    for old in [*folder.glob(f'{stem}-*.png'),*OUT.glob(f'{stem}-sheet-*.png')]:
        if not old.resolve().is_relative_to(ROOT):
            raise RuntimeError('Render output outside the project')
        old.unlink()
    # Relative paths avoid a Windows Poppler problem with non-ASCII outputs.
    prefix=(folder/stem).relative_to(ROOT).as_posix()
    command=['pdftoppm','-png','-scale-to','1400',f'{stem}.pdf',prefix]
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode:
        raise RuntimeError(result.stderr)
    subprocess.run(['pdftotext','-bbox',f'{stem}.pdf',
                    (folder/'text-bbox.html').relative_to(ROOT).as_posix()],cwd=ROOT,check=True)
    pages=sorted(folder.glob(f'{stem}-*.png'))
    sheets=[]
    for offset in range(0,len(pages),6):
        canvas=Image.new('RGB',(1260,1240),'#c9cdd2')
        draw=ImageDraw.Draw(canvas)
        for local,page in enumerate(pages[offset:offset+6]):
            img=Image.open(page).convert('RGB')
            img.thumbnail((400,580))
            x=10+(local%3)*420
            y=25+(local//3)*620
            draw.text((x,y-18),f'{stem} / page {offset+local+1}',fill='black')
            canvas.paste(img,(x,y))
        target=OUT/f'{stem}-sheet-{offset//6+1:02}.png'
        canvas.save(target)
        sheets.append(str(target.relative_to(ROOT)))
    return {'document':stem,'pages':len(pages),'sheets':sheets,'command':command}

with ThreadPoolExecutor(max_workers=2) as pool:
    records=list(pool.map(render,['manuscript','supplement']))
(OUT/'render-manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))

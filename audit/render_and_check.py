"""Read final PDFs, check extraction/bounds and render review sheets."""
from pathlib import Path
import json, re, subprocess, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'audit'/'pdf_review'
DEST.mkdir(exist_ok=True)
report={}
for name in ['manuscript','supplement']:
    pdf=ROOT/f'{name}.pdf'
    info=subprocess.run(['pdfinfo',pdf.name],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8',errors='replace')
    page_count=int(re.search(r'Pages:\s+(\d+)',info).group(1))
    bbox=DEST/f'{name}_bbox.html'
    subprocess.run(['pdftotext','-bbox',pdf.name,str(bbox.relative_to(ROOT))],cwd=ROOT,check=True,capture_output=True)
    subprocess.run(['pdftotext','-layout',pdf.name,str((DEST/f'{name}_extracted.txt').relative_to(ROOT))],cwd=ROOT,check=True,capture_output=True)
    subprocess.run(['pdftoppm','-scale-to','1200','-png',pdf.name,str((DEST/name).relative_to(ROOT))],cwd=ROOT,check=True,capture_output=True)
    ns={'x':'http://www.w3.org/1999/xhtml'}
    # Some legacy math font maps yield XML-illegal control glyphs in Poppler's
    # extraction. Sanitize this inspection copy only; never alter PDF content.
    bbox_text=bbox.read_text(encoding='utf-8')
    bbox_text=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',bbox_text)
    pdf_pages=ET.fromstring(bbox_text).findall('.//x:page',ns)
    pages=[]; out_of_bounds=[]; empty=[]
    texts=[]
    for i,page in enumerate(pdf_pages):
        words=page.findall('.//x:word',ns)
        texts.append(' '.join(w.text or '' for w in words))
        if len(texts[-1].strip())<30: empty.append(i+1)
        for w in words:
            x0,y0,x1,y1=[float(w.get(k)) for k in ['xMin','yMin','xMax','yMax']]
            if x0<0 or y0<0 or x1>float(page.get('width'))+1 or y1>float(page.get('height'))+1:
                out_of_bounds.append({'page':i+1,'text':w.text,'bbox':[x0,y0,x1,y1]})
        img=Image.open(DEST/f'{name}-{i+1:0{len(str(page_count))}d}.png').convert('RGB')
        thumb=img.copy();thumb.thumbnail((400,550))
        cell=Image.new('RGB',(420,585),'#e7e7e7')
        cell.paste(thumb,((420-thumb.width)//2,25))
        ImageDraw.Draw(cell).text((12,8),f'{name} {i+1}',fill='black')
        pages.append(cell)
    for j in range(0,len(pages),6):
        sheet=Image.new('RGB',(1260,1170),'white')
        for k,img in enumerate(pages[j:j+6]): sheet.paste(img,((k%3)*420,(k//3)*585))
        sheet.save(DEST/f'{name}_sheet_{j//6+1}.png')
    text='\n'.join(texts)
    log=(ROOT/f'{name}.log').read_text(encoding='utf-8',errors='replace')
    report[name]={'pages':page_count,'empty_pages':empty,'page_boundary_violations':out_of_bounds,
                  'unresolved_reference_markers':len(re.findall(r'\?\?',text)),
                  'overfull_boxes':len(re.findall('Overfull',log)),
                  'undefined_warnings':len(re.findall(r'(?:Reference|Citation).*undefined',log)),
                  'pdf_sha256':__import__('hashlib').sha256((ROOT/f'{name}.pdf').read_bytes()).hexdigest()}
(DEST/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))

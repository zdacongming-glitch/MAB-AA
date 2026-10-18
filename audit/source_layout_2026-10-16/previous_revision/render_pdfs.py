"""Render every revised page and check PDF text bounds before visual review."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

REV = Path(__file__).resolve().parent
ROOT = REV.parent
DEST = REV / "pdf_review"
DEST.mkdir(exist_ok=True)
report = {}
for name in ["manuscript", "supplement"]:
    pdf = ROOT / f"{name}.pdf"
    info = subprocess.run(["pdfinfo", pdf.name], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8", errors="replace")
    count = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    bbox = DEST / f"{name}_bbox.html"
    subprocess.run(["pdftotext", "-bbox", pdf.name, str(bbox.relative_to(ROOT))], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["pdftotext", "-layout", pdf.name, str((DEST/f"{name}_extracted.txt").relative_to(ROOT))], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["pdftoppm", "-scale-to", "1400", "-png", pdf.name, str((DEST/name).relative_to(ROOT))], cwd=ROOT, check=True, capture_output=True)
    ns = {"x": "http://www.w3.org/1999/xhtml"}
    xml = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", bbox.read_text(encoding="utf-8"))
    pages = ET.fromstring(xml).findall(".//x:page", ns)
    thumbs = []
    empty = []
    bounds = []
    for index, page in enumerate(pages, 1):
        words = page.findall(".//x:word", ns)
        if len(" ".join(w.text or "" for w in words).strip()) < 30:
            empty.append(index)
        for word in words:
            x0,y0,x1,y1 = [float(word.get(k)) for k in ["xMin", "yMin", "xMax", "yMax"]]
            if x0<0 or y0<0 or x1>float(page.get("width"))+1 or y1>float(page.get("height"))+1:
                bounds.append({"page": index, "text": word.text, "bounds": [x0,y0,x1,y1]})
        image = Image.open(DEST/f"{name}-{index:0{len(str(count))}d}.png").convert("RGB")
        image.thumbnail((400,550))
        cell = Image.new("RGB", (420,585), "#e7e7e7")
        cell.paste(image, ((420-image.width)//2,25))
        ImageDraw.Draw(cell).text((12,8), f"{name} {index}", fill="black")
        thumbs.append(cell)
    for j in range(0,len(thumbs),6):
        sheet = Image.new("RGB", (1260,1170), "white")
        for k,img in enumerate(thumbs[j:j+6]):
            sheet.paste(img, ((k%3)*420,(k//3)*585))
        sheet.save(DEST/f"{name}_sheet_{j//6+1}.png")
    report[name] = {"pages": count, "empty_pages": empty, "page_boundary_violations": bounds,
                    "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
(DEST/"render_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))

"""Small notation-only adjustments applied after source review."""
from pathlib import Path
import hashlib
import json
REV = Path(__file__).resolve().parent
path = REV / "main_theory_blocks.tex"
text = path.read_text(encoding="utf-8")
start = text.index(r"\begin{algorithm}[p]")
end = text.index(r"\end{algorithm}", start) + len(r"\end{algorithm}")
block = text[start:end]
if r"\mathcal A^{\rm cur}" not in block:
    block = block.replace(r"\mathcal A", r"\mathcal A^{\rm cur}")
    text = text[:start] + block + text[end:]
    path.write_text(text, encoding="utf-8")

manifest_path = REV / "proof_reorganization_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["new_files"] = {name: hashlib.sha256((REV.parent/name).read_bytes()).hexdigest() for name in manifest["new_files"]}
manifest["post_review_edit"] = "Completion lemma explicitly uses the model's existing eta in (0,1); no new task restriction."
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

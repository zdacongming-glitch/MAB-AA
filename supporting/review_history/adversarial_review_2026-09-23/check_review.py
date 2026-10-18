"""Check Markdown math, local references, and preservation of audited inputs."""
import hashlib
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
for name, expected in evidence["source_hashes"].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name

links = 0
files = sorted(root.glob("*.md"))
for path in files:
    text = path.read_text(encoding="utf-8")
    assert not any(marker in text for marker in (r"\(", r"\)", r"\[", r"\]")), path
    display = False
    fence = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("~~~"):
            fence = not fence
            continue
        if fence:
            continue
        if "$$" in line:
            assert line.strip() == "$$", (path, number)
            display = not display
        elif not display:
            assert line.count("$") % 2 == 0, (path, number)
    assert not display and not fence, path
    for target in re.findall(r"\]\((<?[CD]:/[^)\n]+)\)", text):
        target = target.strip("<>")
        match = re.match(r"^(.*):(\d+)$", target)
        if match:
            target, line = match.group(1), int(match.group(2))
            destination = Path(target)
            assert line <= len(destination.read_text(encoding="utf-8").splitlines()), target
        else:
            destination = Path(target)
        assert destination.exists(), (path, target)
        links += 1

result = dict(markdown_files=len(files), local_links_checked=links,
              preserved_input_hashes=len(evidence["source_hashes"]),
              math_delimiters="passed", sources_unchanged=True)
(root / "review_checks.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))

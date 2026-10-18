"""Record the one-time editorial assembly; edit manuscript.tex directly after it."""
from pathlib import Path

REV = Path(__file__).resolve().parent
parts = ["main_front.tex", "main_theory_blocks.tex", "experiments_block.tex", "main_end.tex"]
text = "\n\n".join((REV / name).read_text(encoding="utf-8").rstrip() for name in parts) + "\n"
if text.count(r"\documentclass") != 1 or text.count(r"\end{document}") != 1:
    raise SystemExit("Invalid editorial assembly")
(REV.parent / "manuscript.tex").write_text(text, encoding="utf-8")
print("Assembled manuscript.tex with every body section inline.")

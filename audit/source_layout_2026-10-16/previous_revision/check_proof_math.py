"""Check migration of existing displayed mathematics, not proof correctness."""
from pathlib import Path
from collections import Counter
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REV = ROOT / "revision_2026-10-16"
BASE = REV / "baseline/theory"


def displays(text):
    pattern = r"\\\[(.*?)\\\]|\\begin\{equation\}(.*?)\\end\{equation\}"
    out = []
    for match in re.finditer(pattern, text, re.S):
        body = next(x for x in match.groups() if x is not None)
        body = re.sub(r"\\label\{[^}]+\}", "", body)
        out.append(re.sub(r"\s+", "", body))
    return Counter(out)


old = displays("\n".join((BASE / name).read_text(encoding="utf-8-sig") for name in
    ["supplementary_proofs.tex", "extensions.tex", "information_and_variants.tex"]))
new_files = sorted((ROOT / "theory").glob("maintenance_a*.tex"))
new = displays("\n".join(p.read_text(encoding="utf-8") for p in new_files))
missing = list((old-new).elements())
added = list((new-old).elements())
expected_removed = [r"D(P\VertQ)\ge\operatorname{kl}(P(F),Q(F))."]
expected_added = [r"D(P\VertQ)\ge\operatorname{kl}(P(F),Q(F))\geP(F)\log\frac1{Q(F)}-\log2."]
out = dict(
    scope="Display migration only; not independent proof verification",
    baseline_display_count=sum(old.values()),
    revised_display_count=sum(new.values()),
    removed_displays=missing,
    added_displays=added,
    expected_information_tools_merge_only=(missing==expected_removed and added==expected_added),
    legacy_theory_sources_unchanged=all((BASE/name).read_bytes()==(ROOT/"theory"/name).read_bytes()
        for name in ["ucbaa_repaired_analysis.tex", "retained_regret_lower_bounds.tex", "supplementary_proofs.tex", "extensions.tex", "information_and_variants.tex"]),
)
(REV / "proof_math_preservation.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))

#!/usr/bin/env python3
"""Check or explicitly synchronize the seven audited manuscript assets.

The JSON baseline is the last common SHA-256 state, not an immutable research
archive. This script never merges conflicts, compiles papers, commits, or pushes.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


PAPER_FILES = (
    "manuscript.tex",
    "references.bib",
    "revision2/generated/reward-paired.pdf",
    "revision2/generated/preference-tradeoff.pdf",
    "figures/fig_cost_area.pdf",
    "figures/fig_paths_pair1.pdf",
    "figures/fig_paths_pair2.pdf",
)
BASE_FILE = "reproducibility/paper-sync-base.json"
OVERLEAF_FOLDER = "ucbaa_jasa_resubmission_2026-10-15"
FIGURES = set(PAPER_FILES[2:])


class SyncError(RuntimeError):
    """A failed precondition; no automatic conflict resolution is attempted."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scoped_path(root: Path, relative: str) -> Path:
    candidate = root / relative
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise SyncError(f"Path escapes the selected root: {relative}") from exc
    # Replacing a symbolic link is surprising even when it points inside root.
    current = candidate
    while current != root:
        if current.is_symlink():
            raise SyncError(f"Symbolic links are not synchronized: {relative}")
        current = current.parent
    return candidate


def read_assets(root: Path) -> dict[str, bytes]:
    data = {}
    for relative in PAPER_FILES:
        path = scoped_path(root, relative)
        if not path.is_file():
            raise SyncError(f"Missing audited asset: {path}")
        data[relative] = path.read_bytes()
    validate_dependencies(data["manuscript.tex"], root)
    return data


def without_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        for index, char in enumerate(line):
            if char != "%":
                continue
            slash_count = 0
            previous = index - 1
            while previous >= 0 and line[previous] == "\\":
                slash_count += 1
                previous -= 1
            if slash_count % 2 == 0:
                line = line[:index]
                break
        lines.append(line)
    return "\n".join(lines)


def validate_dependencies(content: bytes, root: Path) -> None:
    try:
        text = without_comments(content.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise SyncError(f"manuscript.tex must be UTF-8: {root}") from exc
    graphics = re.findall(
        r"\\includegraphics\*?\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}", text
    )
    graphic_commands = re.findall(r"\\includegraphics\b", text)
    bibliography = re.findall(r"\\bibliography\s*\{([^{}]+)\}", text)
    bib_names = [name.strip() for group in bibliography for name in group.split(",")]
    styles = re.findall(r"\\bibliographystyle\s*\{([^{}]+)\}", text)
    forbidden = re.findall(
        r"\\(?:input|include|addbibresource|graphicspath|includepdf|"
        r"lstinputlisting|verbatiminput)\b", text
    )
    if (
        set(graphics) != FIGURES
        or len(graphics) != len(graphic_commands)
        or bib_names != ["references"]
        or styles != ["plainnat"]
        or forbidden
    ):
        details = {
            "unregistered_figures": sorted(set(graphics) - FIGURES),
            "missing_audited_figures": sorted(FIGURES - set(graphics)),
            "bibliographies": bib_names,
            "bibliography_styles": styles,
            "external_input_commands": sorted(set(forbidden)),
        }
        raise SyncError(
            f"The audited dependency closure changed in {root}. "
            "Audit the new dependencies manually and update the allowlist and "
            "baseline together before synchronization. "
            + json.dumps(details, ensure_ascii=False)
        )


def load_baseline(root: Path) -> tuple[Path, bytes, dict]:
    path = scoped_path(root, BASE_FILE)
    if not path.is_file():
        raise SyncError(
            f"Missing baseline: {path}. Re-establish it only after a manual "
            "comparison; this script does not initialize different copies."
        )
    raw = path.read_bytes()
    try:
        manifest = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SyncError(f"Invalid baseline JSON: {path}") from exc
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or not isinstance(files, dict)
        or set(files) != set(PAPER_FILES)
        or any(
            not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
            for value in files.values()
        )
    ):
        raise SyncError(f"Baseline must contain exactly seven SHA-256 entries: {path}")
    return path, raw, manifest


def atomic_write(path: Path, data: bytes) -> None:
    # The parent already exists: missing directories or assets fail preflight.
    descriptor, temporary = tempfile.mkstemp(prefix=".paper-sync-", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def synchronize(research: Path, overleaf: Path, direction: str | None, apply: bool) -> int:
    research = research.expanduser().resolve()
    overleaf = overleaf.expanduser().resolve()
    if research == overleaf or research in overleaf.parents or overleaf in research.parents:
        raise SyncError("The two selected roots must be separate, nonnested directories.")
    if not research.is_dir() or not overleaf.is_dir():
        raise SyncError("Both selected repository directories must already exist.")
    base_path, baseline_raw, manifest = load_baseline(research)
    observed = {"research": read_assets(research), "overleaf": read_assets(overleaf)}
    hashes = {
        side: {relative: sha256(data) for relative, data in files.items()}
        for side, files in observed.items()
    }
    source = "overleaf" if direction != "to-overleaf" else "research"
    destination = "research" if source == "overleaf" else "overleaf"
    roots = {"research": research, "overleaf": overleaf}
    changed = []
    conflicts = []
    for relative in PAPER_FILES:
        source_hash = hashes[source][relative]
        destination_hash = hashes[destination][relative]
        baseline_hash = manifest["files"][relative]
        if source_hash == destination_hash:
            continue
        changed.append(relative)
        if source_hash == baseline_hash:
            status = f"{destination} changed; use the opposite direction"
            conflicts.append(relative)
        elif destination_hash == baseline_hash:
            status = f"{source} changed; safe for the selected direction"
        else:
            status = "both copies changed differently; resolve manually"
            conflicts.append(relative)
        print(f"DIFFERENT {relative}: {status}")
    if not apply:
        if changed:
            print("Check only: no files were written.")
            return 1
        print("Synchronized: all seven manuscript assets are byte-identical.")
        if any(hashes[source][name] != manifest["files"][name] for name in PAPER_FILES):
            print("The common copies are newer than the baseline; explicit --apply can record them.")
        return 0
    if conflicts:
        raise SyncError("The complete synchronization was refused; no files were written.")
    # Recheck all inputs immediately before writes, including the mutable baseline.
    if base_path.read_bytes() != baseline_raw:
        raise SyncError("The baseline changed during preflight; retry after reviewing it.")
    for side, root in roots.items():
        for relative in PAPER_FILES:
            if scoped_path(root, relative).read_bytes() != observed[side][relative]:
                raise SyncError(f"Input changed during preflight: {side}/{relative}")
    updated = dict(manifest)
    updated["files"] = hashes[source]
    updated["last_sync"] = {
        "direction": direction,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    updated_raw = (json.dumps(updated, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    written = []
    try:
        for relative in changed:
            path = scoped_path(roots[destination], relative)
            atomic_write(path, observed[source][relative])
            written.append(relative)
        for relative in PAPER_FILES:
            if sha256(scoped_path(roots[destination], relative).read_bytes()) != hashes[source][relative]:
                raise SyncError(f"Destination verification failed: {relative}")
        atomic_write(base_path, updated_raw)
    except Exception as exc:
        rollback_errors = []
        for relative in reversed(written):
            try:
                atomic_write(scoped_path(roots[destination], relative), observed[destination][relative])
            except Exception as rollback_exc:
                rollback_errors.append(f"{relative}: {rollback_exc}")
        if rollback_errors:
            raise SyncError("Synchronization failed; rollback also failed: " + "; ".join(rollback_errors)) from exc
        raise SyncError(f"Synchronization failed; replaced assets were restored: {exc}") from exc
    print(f"Synchronized {len(changed)} changed asset(s) {direction}; all seven hashes verified.")
    print("Updated the common baseline. No Git commits or pushes were performed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    research = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overleaf-dir", type=Path,
        default=research.parent / OVERLEAF_FOLDER,
        help="Local Overleaf manuscript directory (default: the sibling resubmission folder).",
    )
    directions = parser.add_mutually_exclusive_group()
    directions.add_argument("--from-overleaf", action="store_const", const="from-overleaf", dest="direction")
    directions.add_argument("--to-overleaf", action="store_const", const="to-overleaf", dest="direction")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true", help="Compare only; this is the default action.")
    actions.add_argument("--apply", action="store_true", help="Copy only safe changes and update the common baseline.")
    args = parser.parse_args(argv)
    if args.apply and not args.direction:
        parser.error("--apply requires --from-overleaf or --to-overleaf")
    try:
        return synchronize(research, args.overleaf_dir, args.direction, args.apply)
    except (SyncError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

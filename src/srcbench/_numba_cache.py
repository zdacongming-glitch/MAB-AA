"""Keep compiled cross-module dependencies inside a source-specific cache."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile


_ROOT_ENV = "SRCBENCH_NUMBA_CACHE_ROOT"
_INFO = {}


def _absolute_cache_path(path):
    path = str(Path(path).expanduser().resolve())
    # Numba appends a module directory and long temporary filenames. Windows
    # extended paths also support explicitly chosen, deeply nested cache roots.
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        path = "\\\\?\\UNC\\" + path[2:] if path.startswith("\\\\") else "\\\\?\\" + path
    return path


def configure_cache():
    """Run before kernel imports; preserve the same root in spawned workers."""
    global _INFO
    try:
        numba_version = importlib.metadata.version("numba")
    except importlib.metadata.PackageNotFoundError:
        numba_version = None
    package = Path(__file__).resolve().parent
    payload = {
        "numba_version": numba_version,
        "python_cache_tag": sys.implementation.cache_tag,
        "sources": [(path.relative_to(package).as_posix(),
                     hashlib.sha256(path.read_bytes()).hexdigest())
                    for path in sorted(package.rglob("*.py"))],
    }
    fingerprint = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    # NUMBA_CACHE_DIR is an input base only on first import. The separate root
    # survives spawn, where NUMBA_CACHE_DIR already contains the namespace.
    root = _absolute_cache_path(os.environ.get(_ROOT_ENV) or
        os.environ.get("NUMBA_CACHE_DIR") or Path(tempfile.gettempdir()) / "srcbench-numba")
    directory = str(Path(root) / ("srcbench-" + fingerprint))
    os.environ[_ROOT_ENV] = root
    os.environ["NUMBA_CACHE_DIR"] = directory
    config = sys.modules.get("numba.core.config")
    if config is None:
        config = getattr(sys.modules.get("numba"), "config", None)
    if config is not None:
        config.CACHE_DIR = directory
    _INFO = dict(source_fingerprint=fingerprint, effective_cache_dir=directory,
                 cache_root=root, numba_version=numba_version,
                 python_cache_tag=sys.implementation.cache_tag)
    return cache_info()


def cache_info():
    """Return provenance without importing Numba or exposing cache contents."""
    return dict(_INFO)

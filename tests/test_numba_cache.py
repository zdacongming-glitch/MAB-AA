"""Exercise cache provenance in fresh interpreters, including stale imports."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _probe(tmp_path, code, source=None, cache_base=None):
    script = tmp_path / "probe.py"
    script.write_text(code, encoding="utf-8")
    environment = os.environ.copy()
    for name in ("NUMBA_CACHE_DIR", "SRCBENCH_NUMBA_CACHE_ROOT", "NUMBA_DEBUG_CACHE"):
        environment.pop(name, None)
    if cache_base is not None:
        environment["NUMBA_CACHE_DIR"] = str(cache_base)
    environment["PYTHONPATH"] = str(source or ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
        environment[name] = "1"
    completed = subprocess.run([sys.executable, "-B", str(script)], env=environment,
                               capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout.splitlines()[-1])


@pytest.fixture
def package_copy(tmp_path):
    checkout = tmp_path / "copy"
    package = checkout / "src" / "srcbench"
    shutil.copytree(ROOT / "src" / "srcbench", package,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.nbc", "*.nbi"))
    (checkout / "configs").mkdir()
    shutil.copy2(ROOT / "configs" / "methods.json", checkout / "configs" / "methods.json")
    return package


def test_default_cache_is_outside_source_and_same_in_new_processes(tmp_path):
    code = "from srcbench import numba_cache_info; import json; print(json.dumps(numba_cache_info()))"
    first = _probe(tmp_path, code)
    second = _probe(tmp_path, code)
    assert first == second
    directory = Path(first["effective_cache_dir"])
    assert directory.is_absolute()
    assert directory.parent == Path(first["cache_root"])
    assert first["source_fingerprint"] in directory.name
    assert len(first["source_fingerprint"]) == 64
    assert not directory.is_relative_to(ROOT / "src")


def test_explicit_cache_root_is_preserved_across_two_spawned_workers(tmp_path):
    result = _probe(tmp_path, '''
import json, multiprocessing, os
from srcbench import numba_cache_info
def worker(queue):
    queue.put(dict(pid=os.getpid(), cache=numba_cache_info()))
if __name__ == '__main__':
    context = multiprocessing.get_context('spawn')
    queue = context.Queue()
    workers = [context.Process(target=worker, args=(queue,)) for _ in range(2)]
    for process in workers: process.start()
    children = [queue.get(timeout=60) for _ in workers]
    for process in workers:
        process.join(timeout=60)
        assert process.exitcode == 0
    print(json.dumps(dict(parent=numba_cache_info(), children=children)))
''', cache_base=tmp_path / "cache")
    assert len({child["pid"] for child in result["children"]}) == 2
    assert all(child["cache"] == result["parent"] for child in result["children"])
    root = Path(result["parent"]["cache_root"])
    assert root.name == "cache"
    assert Path(result["parent"]["effective_cache_dir"]).parent == root


def test_already_imported_numba_configuration_is_updated(tmp_path):
    pytest.importorskip("numba")
    result = _probe(tmp_path, '''
import json, numba
from srcbench import numba_cache_info
print(json.dumps(dict(cache=numba_cache_info(), configured=numba.config.CACHE_DIR)))
''', cache_base=tmp_path / "cache")
    assert result["configured"] == result["cache"]["effective_cache_dir"]
    assert Path(result["configured"]).parent == Path(result["cache"]["cache_root"])


def test_missing_numba_retains_python_fallback(tmp_path):
    result = _probe(tmp_path, '''
import importlib.metadata, json, math, sys
original = importlib.metadata.version
def version(name):
    if name == 'numba': raise importlib.metadata.PackageNotFoundError(name)
    return original(name)
importlib.metadata.version = version
sys.modules['numba'] = None
from srcbench import numba_cache_info
from srcbench.mathcore import NUMBA_AVAILABLE, dinf
import numpy as np
assert not NUMBA_AVAILABLE
assert abs(dinf(np.array([.3]), np.array([2]), .7) - math.log(.7/.3)) < 1e-14
print(json.dumps(numba_cache_info()))
''', cache_base=tmp_path / "cache")
    assert result["numba_version"] is None


def test_read_only_source_files_use_external_cache(tmp_path, package_copy):
    pytest.importorskip("numba")
    sources = list(package_copy.rglob("*.py"))
    try:
        for path in sources:
            path.chmod(stat.S_IREAD)
        result = _probe(tmp_path, '''
import json, numpy as np
from srcbench import numba_cache_info
from srcbench.mathcore import dinf
assert dinf(np.array([.3]), np.array([2]), .7) > 0
print(json.dumps(numba_cache_info()))
''', source=package_copy.parent, cache_base=tmp_path / "external")
        assert not Path(result["effective_cache_dir"]).is_relative_to(package_copy)
        assert list(Path(result["effective_cache_dir"]).rglob("*.nbc"))
        assert not list(package_copy.rglob("*.nbc"))
        assert not list(package_copy.rglob("*.nbi"))
    finally:
        for path in sources:
            path.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_changed_dependency_cannot_hit_old_imed_cache(tmp_path, package_copy):
    pytest.importorskip("numba")
    dependency = package_copy / "mathcore.py"
    correct_source = dependency.read_text(encoding="utf-8")
    assert "if shifted <= 0:" in correct_source
    # Recreate the prior numerical defect only in an isolated source copy.
    dependency.write_text(correct_source.replace("if shifted <= 0:",
                          "if shifted <= 1e-15 * total:"), encoding="utf-8")
    consumer = package_copy / "baselines.py"
    unchanged_consumer = consumer.read_bytes()
    code = '''
import json, numpy as np
from srcbench import numba_cache_info
from srcbench.baselines import BaselineSelector
n = np.array([8, 2, 2, 1], dtype=np.int64)
S = np.array([7.816000000000001, 1.8, 1.908, .79])
atoms = [.977, .9, .954, .79]
supports = [(np.array([value]), np.array([count])) for value,count in zip(atoms,n)]
selector = BaselineSelector('IMED')
chosen = selector.choose(n, S, n*np.array(atoms)**2, np.ones(4,dtype=np.int64), 14, 3, 1, supports)
print(json.dumps(dict(chosen=chosen, cache=numba_cache_info())))
'''
    old = _probe(tmp_path, code, source=package_copy.parent, cache_base=tmp_path / "cache")
    assert old["chosen"] == 0
    old_files = list(Path(old["cache"]["effective_cache_dir"]).rglob("baselines._imed_scores*.nbc"))
    assert old_files
    old_bytes = {path: path.read_bytes() for path in old_files}
    dependency.write_text(correct_source, encoding="utf-8")
    new = _probe(tmp_path, code, source=package_copy.parent, cache_base=tmp_path / "cache")
    assert consumer.read_bytes() == unchanged_consumer
    assert new["chosen"] == 2
    assert new["cache"]["source_fingerprint"] != old["cache"]["source_fingerprint"]
    assert new["cache"]["effective_cache_dir"] != old["cache"]["effective_cache_dir"]
    assert Path(new["cache"]["effective_cache_dir"]).parent == Path(old["cache"]["effective_cache_dir"]).parent
    assert all(path.read_bytes() == content for path, content in old_bytes.items())

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def pytest_configure(config):
    # Native Windows sandbox temporary folders can deny atomic rename. Keep
    # generated test work inside this checkout, also when pytest starts above it.
    if config.option.basetemp is None:
        work = Path(__file__).resolve().parents[1] / "_work"
        work.mkdir(exist_ok=True)
        config.option.basetemp = str(work / "pytest")

"""Final, horizon-free SRC and SRC-KL experiment implementation."""

from ._numba_cache import configure_cache as _configure_numba_cache
from ._numba_cache import cache_info as numba_cache_info

_configure_numba_cache()

__version__ = "1.0.0"


def __getattr__(name):
    if name == "Policy":
        from .policy import Policy
        return Policy
    raise AttributeError(name)

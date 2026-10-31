"""Final, horizon-free SRC and SRC-KL experiment implementation."""

__version__ = "1.0.0"


def __getattr__(name):
    if name == "Policy":
        from .policy import Policy
        return Policy
    raise AttributeError(name)

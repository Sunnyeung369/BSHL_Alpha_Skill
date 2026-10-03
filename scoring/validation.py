"""Input contracts shared by the deterministic research scorers."""

import math
from numbers import Real


def number(name, value, minimum=0, maximum=None):
    """Reject coercion, booleans, nonfinite values and out-of-range inputs."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, not {type(value).__name__}")
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError):
        finite = False
    if not finite:
        raise ValueError(f"{name} must be finite")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return float(value)


def optional_bool(name, value):
    """None represents unknown; a truthy string is never a passed check."""
    if value is not None and type(value) is not bool:
        raise TypeError(f"{name} must be bool or None")
    return value


def score_values(values, weights):
    for name, maximum in weights.items():
        number(name, values[name], 0, maximum)

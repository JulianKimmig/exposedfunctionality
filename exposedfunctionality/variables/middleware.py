from .core import (
    ExposedValueData,
)


def min_max_clamp(value, valuedata: ExposedValueData, min=None, max=None):
    if min is None:
        min = getattr(valuedata, "min", None)
    if max is None:
        max = getattr(valuedata, "max", None)

    if max is not None and min is not None and max < min:
        raise ValueError("max must be greater than or equal to min")
    if min is not None and value < min:
        return min
    if max is not None and value > max:
        return max
    return value

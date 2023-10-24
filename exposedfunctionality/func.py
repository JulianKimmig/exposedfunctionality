from functools import wraps
import asyncio
from .function_parser import (
    function_method_parser,
    SerializedFunction,
    FunctionOutputParam,
    FunctionInputParam,
)
from .function_parser.types import Any, Dict, Callable, Tuple, Optional, List


def exposed_method(
    name: Optional[str] = None,
    inputs: Optional[List[FunctionInputParam]] = None,
    outputs: Optional[List[FunctionOutputParam]] = None,
):
    """ """

    def decorator(func):
        serfunc = function_method_parser(func)
        if outputs is not None:
            for i, o in enumerate(outputs):
                if i >= len(serfunc["output_params"]):
                    serfunc["output_params"].append(o)
                else:
                    serfunc["output_params"][i].update(o)

        if inputs is not None:
            for i, o in enumerate(inputs):
                if i >= len(serfunc["input_params"]):
                    serfunc["input_params"].append(o)
                else:
                    serfunc["input_params"][i].update(o)

        if name is not None:
            serfunc["name"] = name

        func._exposed_method = True
        func._funcmeta: SerializedFunction = serfunc
        return func

    return decorator


def get_exposed_methods(obj: Any) -> Dict[str, Tuple[Callable, SerializedFunction]]:
    """
    Get all exposed methods from an object (either instance or class).

    Args:
        obj (Union[Any, Type]): Object (instance or class) from which exposed methods are fetched.

    Returns:
        Dict[str, Tuple[Callable, SerializedFunction]]: Dictionary of exposed methods, where the
        key is the method name and the value is a tuple of the method itself and its SerializedFunction data.
    """

    methods = [
        (func, getattr(obj, func)) for func in dir(obj) if callable(getattr(obj, func))
    ]
    return {
        attr_name: (attr_value, attr_value._funcmeta)
        for attr_name, attr_value in methods
        if hasattr(attr_value, "_exposed_method")
    }


def assure_exposed_method(obj: Callable, **kwargs):
    if hasattr(obj, "_funcmeta"):
        return obj

    return exposed_method(**kwargs)(obj)

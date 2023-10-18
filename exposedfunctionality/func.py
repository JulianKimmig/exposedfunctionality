from typing import Any, Dict, Callable, Tuple, Optional, List
from functools import wraps
import asyncio
from .function_parser import (
    function_method_parser,
    SerializedFunction,
    FunctionOutputParam,
)


def exposed_method(out: Optional[List[FunctionOutputParam]] = None):
    """ """

    def decorator(func):
        serfunc = function_method_parser(func)
        if out is not None:
            for i, o in enumerate(out):
                if i >= len(serfunc["output_params"]):
                    serfunc["output_params"].append(o)
                else:
                    serfunc["output_params"][i].update(o)
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(*args, **kwargs):
                crout = func(*args, **kwargs)
                return await crout

        else:

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

        wrapper._exposed_method = True
        wrapper._funcmeta: SerializedFunction = serfunc
        return wrapper

    return decorator


def get_exposed_methods(obj: Any) -> Dict[str, Tuple[Callable, SerializedFunction]]:
    """
    Get all exposed methods from an object (either instance or class).

    Args:
        obj (Union[Any, Type]): Object (instance or class) from which exposed methods are fetched.

    Returns:
        Dict[str, Any]: Dictionary of method names to their method instances.
    """

    methods = [
        (func, getattr(obj, func)) for func in dir(obj) if callable(getattr(obj, func))
    ]
    return {
        attr_name: (attr_value, attr_value._funcmeta)
        for attr_name, attr_value in methods
        if hasattr(attr_value, "_exposed_method")
    }

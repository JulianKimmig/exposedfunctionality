"""
This module contains the exposed_method decorator and related functions
for exposing methods to the frontend.
"""

from __future__ import annotations
from functools import wraps
from .function_parser import (
    function_method_parser,
    SerializedFunction,
    FunctionOutputParam,
    FunctionInputParam,
)
from typing import (
    ParamSpec,
    Union,
    Any,
    Callable,
    Dict,
    Tuple,
    List,
    Optional,
    Literal,
    TypedDict,
)
from .function_parser import (
    ExposedFunction,
    ReturnType,
)

try:
    from typing import Unpack
except ImportError:
    from typing_extensions import Unpack


class ExposedMethodKwargs(TypedDict, total=False):
    name: Optional[str]
    inputs: Optional[List[FunctionInputParam]]
    outputs: Optional[List[FunctionOutputParam]]


ExposedMethodKwargsKeysValues = Literal["name", "inputs", "outputs"]
ExposedMethodKwargsKeys: List[ExposedMethodKwargsKeysValues] = [
    "name",
    "inputs",
    "outputs",
]

P = ParamSpec("P")


def expose_method(
    func: Callable[P, ReturnType],
    name: Optional[str] = None,
    inputs: Optional[List[FunctionInputParam]] = None,
    outputs: Optional[List[FunctionOutputParam]] = None,
) -> ExposedFunction[ReturnType]:
    """
    Expose a method by adding the necessary metadata to the function.

    Args:
        func (Callable[P, ReturnType]): Method to be exposed.
        name (Optional[str], optional): Name of the method. Defaults to None.
        inputs (Optional[List[FunctionInputParam]], optional): List of input parameters. Defaults to None.
        outputs (Optional[List[FunctionOutputParam]], optional): List of output parameters. Defaults to None.

    Returns:
        ExposedFunction[ReturnType]: Exposed method, which is the original function with added information, not a copy.
    """

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
    func: ExposedFunction[ReturnType] = func
    try:
        setattr(func, "_is_exposed_method", True)
    except AttributeError:
        # some objects are read-only, so we can't set the attribute
        # as a workaround, we wrap the function in a new function
        of = func

        @wraps(of)
        def new_func(*args, **kwargs):
            return of(*args, **kwargs)

        func = new_func

    func._is_exposed_method = True  # pylint: disable=W0212
    func.ef_funcmeta: SerializedFunction = serfunc
    return func


def exposed_method(
    name: Optional[str] = None,
    inputs: Optional[List[FunctionInputParam]] = None,
    outputs: Optional[List[FunctionOutputParam]] = None,
) -> Callable[[Callable[P, ReturnType]], ExposedFunction[ReturnType]]:  # type: ignore # ignore a random pylance error
    """
    Decorator for exposing a method to the frontend.

    Args:
        name (Optional[str], optional): Name of the method. Defaults to None.
        inputs (Optional[List[FunctionInputParam]], optional): List of input parameters. Defaults to None.
        outputs (Optional[List[FunctionOutputParam]], optional): List of output parameters. Defaults to None.

    Returns:
        Callable[[Callable[P, ReturnType]], ExposedFunction[ReturnType]]: Decorator function.

    Example:
        >>> from exposedfunctionality import exposed_method
        >>> @exposed_method(name="new_name")
        ... def example_func():
        ...     pass
        >>> example_func.ef_funcmeta["name"]
        'new_name'
    """

    def decorator(func: Callable[P, ReturnType]) -> ExposedFunction[ReturnType]:
        return expose_method(func, name=name, inputs=inputs, outputs=outputs)

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
        attr_name: (attr_value, attr_value.ef_funcmeta)
        for attr_name, attr_value in methods
        if is_exposed_method(attr_value)
    }


def is_exposed_method(
    obj: Union[Callable[P, ReturnType], ExposedFunction[ReturnType]],
) -> bool:
    return (
        hasattr(obj, "_is_exposed_method")
        and obj._is_exposed_method  # pylint: disable=W0212
    )


def assure_exposed_method(
    obj: Union[Callable[P, ReturnType], ExposedFunction[ReturnType]],
    **kwargs: Unpack[ExposedMethodKwargs],
) -> ExposedFunction[ReturnType]:
    """
    Assure that a method is exposed. If it is already exposed, it is returned as is.
    If it is not exposed, it is exposed with the given kwargs.

    Args:
        obj (Union[Callable[P, ReturnType], ExposedFunction[ReturnType]]): Method to be exposed.
        **kwargs: Keyword arguments passed to expose_method.

    Returns:
        ExposedFunction[ReturnType]: Exposed method.
    """

    if is_exposed_method(obj):
        return obj

    return expose_method(obj, **kwargs)

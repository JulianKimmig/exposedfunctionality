from __future__ import annotations


import warnings
import inspect
from functools import partial
import json
from .docstring_parser import parse_docstring
from typing import get_type_hints, Callable
from .types import (
    type_to_string,
    Optional,
    Any,
    List,
    Tuple,
    NoneType,
    Dict,
)

from .ser_types import (
    FunctionInputParam,
    SerializedFunction,
    ReturnType,
    DocstringParserResult,
)


def get_base_function(func: Callable) -> Callable:
    """
    Get the base function of a callable. If the callable is a functools.partial
    instance, it returns the base function.

    Parameters:
    - func: A callable whose base function needs to be obtained.

    Returns:
    - Callable: The base function of the callable.

    Examples:
    ```python
    from functools import partial

    def example(a, b, c=3, d=4):
        pass

    p = partial(example, 1, d=5)
    print(get_base_function(p))  # Returns: example
    ```
    """
    base_func = func
    preset_args = []
    preset_kwargs: Dict[str, Any] = {}
    if isinstance(base_func, partial):
        while isinstance(base_func, partial):
            preset_kwargs = {**base_func.keywords, **preset_kwargs}
            preset_args = list(base_func.args) + preset_args
            base_func = base_func.func
    return base_func, preset_args, preset_kwargs


def get_resolved_signature(
    func: Callable[..., ReturnType], class_member_attributes: Optional[List[str]] = None
) -> Tuple[inspect.Signature, Callable[..., ReturnType]]:
    """
    Get the resolved signature of a callable. If the callable is a functools.partial
    instance, it resolves the signature by excluding parameters that have already
    been set in the partial. Nested partials are also supported.

    Parameters:
    - func: A callable whose signature needs to be resolved.
    - class_member_attributes: A list of attributes that are considered class members
      and should be ignored when resolving the signature and occur as the first
      parameter in the signature. Defaults to ["self", "cls"].

    Returns:
    - Signature: The resolved signature of the callable.

    Examples:
    ```python
    from functools import partial

    def example(a, b, c=3, d=4):
        pass

    p = partial(example, 1, d=5)
    print(get_resolved_signature(p)[0])  # Returns: (b, c=3)
    ```

    """
    base_func, preset_args, preset_kwargs = get_base_function(func)
    if class_member_attributes is None:
        class_member_attributes = ["self", "cls"]

    # Resolve the base function and collect preset arguments
    # from any nested partials.

    # Obtain the original signature
    sig = inspect.signature(base_func, follow_wrapped=False)

    params = list(sig.parameters.values())

    # Remove the preset positional arguments from the front
    if preset_args:
        params = params[len(preset_args) :]

    # Remove the preset keyword arguments
    params = [p for p in params if p.name not in preset_kwargs]

    # Create a new signature
    new_sig = sig.replace(parameters=params)

    # in case its a class method, remove the first argument
    if inspect.ismethod(func) or inspect.isfunction(func):
        if len(list(new_sig.parameters.values())) > 0:
            if list(new_sig.parameters.values())[0].name in class_member_attributes:
                params = list(new_sig.parameters.values())[1:]
                new_sig = new_sig.replace(parameters=params)

    return new_sig, base_func


def function_method_parser(
    func: Callable,
) -> SerializedFunction:
    """
    Parses a given function or method and serializes its signature, type annotations,
    and docstring into a structured dictionary.

    Parameters:
    - func (Callable): The function or method to parse. If the callable is an instance of `functools.partial`,
                       the parser will resolve the signature excluding parameters that have
                       already been set in the partial.

    Returns:
    - SerializedFunction: A dictionary containing:
      * name (str): The name of the function or method.
      * input_params (list[FunctionInputParam]): A list of dictionaries, each representing an input parameter with:
        - name (str): Name of the parameter.
        - default (Any, optional): Default value of the parameter if specified. Omitted if no default is provided.
        - type (type): Type hint of the parameter. Defaults to `Any` if no type hint is provided.
        - positional (bool): True if the parameter is positional or can be passed as a keyword argument,
          otherwise False.
        - optional (bool, optional): True if the parameter is optional, otherwise False.
        - description (str, optional): Description of the parameter extracted from the function's
          docstring (if present).
      * output_params (list[FunctionOutputParam]): A list of dictionaries, each representing an
        output parameter (or return type) with:
        - name (str): Name of the output. It can be "out" or "outX" (where X is an index) depending on the return type.
        - type (type): Type hint of the output.
        - description (str, optional): Description of the output extracted from the function's docstring (if present).
      * docstring (str): The docstring of the function or method.

    Raises:
    - FunctionParamError: If an input parameter has an unserializable default value.

    Notes:
    - The function uses the `get_resolved_signature` to handle callables that are instances of `functools.partial`.
    - The parser assumes that the function or method follows standard Python conventions for naming and annotations.

    Examples:
    ```python
    def example_function(a: int, b: str = "default") -> Tuple[int, str]:
        '''This is an example function.'''
        return a, b

    result = function_method_parser(example_function)
    # The result would be a dictionary with the serialized structure of example_function.
    ```
    """
    input_params = []
    base_func, preset_args, preset_kwargs = get_base_function(func)
    docs = inspect.getdoc(base_func)
    parsed_ds: Optional[DocstringParserResult] = None
    if docs is not None:
        parsed_ds = parse_docstring(docs)

    try:
        th = get_type_hints(base_func)
    except TypeError as exe:
        th = {}
    try:
        sig, base_func = get_resolved_signature(func)

        for i, p in sig.parameters.items():
            n = i
            if p.kind == p.VAR_POSITIONAL:
                n = "*" + n
            if p.kind == p.VAR_KEYWORD:
                n = "**" + n

            param_dict: FunctionInputParam = {
                "name": n,
                "default": p.default,
                "type": th[i] if i in th else p.empty,
                "positional": (
                    p.kind == p.POSITIONAL_ONLY
                    or p.kind == p.POSITIONAL_OR_KEYWORD
                    or p.kind == p.VAR_POSITIONAL
                )
                and (p.default == p.empty),
            }

            if param_dict["type"] is p.empty:
                warnings.warn(
                    f"input {i} of {base_func.__name__} has no type type, using Any as type",
                )
                param_dict["type"] = Any

            if param_dict["default"] is not p.empty:
                try:
                    json.dumps(param_dict["default"])
                except TypeError as exe:
                    try:
                        param_dict["default"] = param_dict["default"].__name__
                    except AttributeError:
                        param_dict["default"] = str(param_dict["default"])
                        # raise FunctionParamError(
                        #     f"input {i} has unserializable default value '{param_dict['default']}'"
                        # ) from exe
            else:
                del param_dict["default"]

            param_dict["type"] = type_to_string(param_dict["type"])

            input_params.append(param_dict)
    except ValueError as exe:
        if parsed_ds is not None:
            input_params = parsed_ds["input_params"]

    output_params = []
    if "return" in th:
        # chek if return type is None Type
        if th["return"] == NoneType:
            output_params = []
        elif getattr(th["return"], "__origin__", None) is tuple:
            output_params = [
                {"name": f"out{i}", "type": type_to_string(t)}
                for i, t in enumerate(th["return"].__args__)
            ]

        else:
            output_params = [{"name": "out", "type": type_to_string(th["return"])}]

    if parsed_ds is not None:
        # update input params
        for p in input_params:
            for parsed_ip in parsed_ds["input_params"]:
                if p["name"] != parsed_ip["name"]:
                    continue

                if ("description" not in p) and "description" in parsed_ip:
                    p["description"] = parsed_ip["description"]
                # optinoanl should be set by the parser
                # if ("optional" not in p) and "optional" in parsed_ip:
                #     p["optional"] = parsed_ip["optional"]

                if (
                    ("default" not in p)
                    and "default" in parsed_ip
                    and p.get("optional", False)
                ):
                    p["default"] = parsed_ip["default"]

                if (
                    "type" not in p
                    or p["type"] is None
                    or p["type"] == "Any"
                    or p["type"] is Any
                ) and "type" in parsed_ip:
                    p["type"] = parsed_ip["type"]

                # a default value makes the parameter optional by default and the parameter non-positional
                if "default" in p:
                    p["optional"] = True
                    p["positional"] = False
                else:
                    p["optional"] = False
                    p["positional"] = True
                # possitional is always set
                # if (
                #    "positional" not in p or p["positional"] is None
                # ) and "positional" in parsed_ip:
                #    p["positional"] = parsed_ip["positional"]

                break

        # update output params
        if len(output_params) == 0:
            output_params.extend(parsed_ds["output_params"])
        if len(output_params) == 1 and len(parsed_ds["output_params"]) >= 1:
            output_params[0] = {**parsed_ds["output_params"][0], **output_params[0]}
        if len(output_params) > 1:
            for i, p in enumerate(output_params):
                for _dp in parsed_ds["output_params"]:
                    if p["name"] == _dp["name"] or (
                        p["name"] == "out0" and _dp["name"] == "out"
                    ):
                        output_params[i] = {**_dp, **output_params[i]}

    ser: SerializedFunction = {
        "name": base_func.__name__,
        "input_params": input_params,
        "output_params": output_params,
        "docstring": parsed_ds,
    }
    return ser

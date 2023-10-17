from __future__ import annotations
import importlib
from typing import Dict
from typing import (
    Optional,
    Any,
    TypedDict,
    Required,
    List,
    Type,
)


class FunctionInputParam(TypedDict, total=False):
    """Type definition for a function parameter"""

    name: Required[str]
    default: Any
    type: Required[Type[Any]]
    positional: Required[bool]
    optional: bool
    description: Optional[str]


class FunctionOutputParam(TypedDict):
    """Type definition for an output parameter"""

    name: str
    type: type
    description: Optional[str]


class SerializedFunction(TypedDict):
    """Type definition for a serialized function"""

    name: str
    input_params: List[FunctionInputParam]
    output_params: List[FunctionOutputParam]
    docstring: Optional[DocstringParserResult]


class FunctionParamError(Exception):
    """Base class for function parameter errors"""


class DocstringParserResult(TypedDict, total=False):
    """Type definition for a standardized parsed docstring"""

    oroginal: str
    input_params: list[FunctionInputParam]
    output_params: list[FunctionOutputParam]
    summary: str
    exceptions: dict[str, str]


class UnknownSectionError(Exception):
    """Exception raised when an unknown section is encountered."""


class TypeNotFoundError(Exception):
    """Exception raised when a type cannot be found."""

    def __init__(self, type_name: str):
        self.type_name = type_name
        super().__init__(f"Type '{type_name}' not found.")


ALLOWED_BUILTINS = {
    "int",
    "float",
    "str",
    "list",
    "dict",
    "tuple",
    "set",
    "bool",
    "bytes",
    "bytearray",
    "complex",
    "frozenset",
    "memoryview",
    "range",
    "slice",
    "type",
    "None",
}


TYPE_GETTER: Dict[str, type] = {}


def string_to_type(string: str):
    """
    Convert a string to a class object.

    Parameters:
    - string: The full name of the class, including its module path, if any.

    Returns:
    - The class object.

    Raises:
    - TypeNotFoundError if the class is not found.
    - ImportError if there's a problem importing the module.
    """
    if string in ALLOWED_BUILTINS:
        if isinstance(__builtins__, dict):
            return __builtins__[string]
        else:
            return getattr(__builtins__, string)

    exc = None
    if "." in string:
        # Split the module path from the class name
        module_name, class_name = string.rsplit(".", 1)

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                return getattr(module, class_name)
        except ImportError as _exc:
            exc = _exc

    if string in TYPE_GETTER:
        return TYPE_GETTER[string]

    if exc:
        raise TypeNotFoundError(string) from exc
    else:
        raise TypeNotFoundError(string)

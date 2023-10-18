from __future__ import annotations
import importlib
from typing import Dict
from typing import (
    Optional,
    Any,
    TypedDict,
    Required,
    List,
    Union,
    Type,
)


class FunctionInputParam(TypedDict, total=False):
    """Type definition for a function parameter"""

    name: Required[str]
    default: Any
    type: Required[str]
    positional: Required[bool]
    optional: bool
    description: Optional[str]


class FunctionOutputParam(TypedDict):
    """Type definition for an output parameter"""

    name: str
    type: str
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
    "int": int,
    "float": float,
    "str": str,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "bool": bool,
    "bytes": bytes,
    "bytearray": bytearray,
    "complex": complex,
    "frozenset": frozenset,
    "memoryview": memoryview,
    "range": range,
    "slice": slice,
    "type": type,
    "None": None,
    "Any": Any,
    "Optional": Optional,
    "Union": Union,
    "Type": Type,
    "List": list,
    "Dict": dict,
    "Tuple": tuple,
    "Set": set,
}


TYPE_GETTER: Dict[str, type] = {**ALLOWED_BUILTINS}
STRING_GETTER: Dict[type, str] = {}
for k, v in TYPE_GETTER.items():
    if v not in STRING_GETTER:
        STRING_GETTER[v] = k


def add_type(type_: type, name: str):
    """
    Add a type to the list of allowed types.

    Parameters:
    - type_: The type to add.
    - name: The name of the type.

    Raises:
    - ValueError if the type is already in the list.
    """
    if "name" in TYPE_GETTER:
        raise ValueError(f"Type '{name}' already exists.")

    TYPE_GETTER[name] = type_
    if type_ not in STRING_GETTER:
        STRING_GETTER[type_] = name


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

    if isinstance(string, type):
        return string

    if string in TYPE_GETTER:
        return TYPE_GETTER[string]

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
                cls = getattr(module, class_name)
                add_type(cls, string)
                return cls
        except ImportError as _exc:
            exc = _exc

    if exc:
        raise TypeNotFoundError(string) from exc
    else:
        raise TypeNotFoundError(string)


def type_to_string(t: Union[type, str]):
    """
    Convert a class object to a string.

    Parameters:
    - t: The class object.

    Returns:
    - The full name of the class, including its module path, if any.
    """
    if isinstance(t, str):
        return t
    if t in STRING_GETTER:
        return STRING_GETTER[t]

    raise TypeNotFoundError(t)

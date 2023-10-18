from __future__ import annotations
import importlib
from typing import Dict
from typing import Optional, Any, TypedDict, Required, List, Union, Type, Tuple, Set
import re


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
    "None": type(None),
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
    if name in TYPE_GETTER:
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

    if not isinstance(string, str):
        raise TypeError(f"Expected str, got {type(string)}")

    string = string.strip()

    # Helper function to handle parameterized types

    def handle_param_type(main_type, content):
        if main_type == "List":
            return List[string_to_type(content)]
        elif main_type == "Dict":
            key, value = map(str.strip, content.split(","))
            return Dict[string_to_type(key), string_to_type(value)]
        elif main_type == "Tuple":
            return Tuple[tuple(map(string_to_type, content.split(",")))]
        elif main_type == "Union":
            return Union[tuple(map(string_to_type, content.split(",")))]
        elif main_type == "Optional":
            return Optional[string_to_type(content)]
        elif main_type == "Type":
            return Type[string_to_type(content)]
        else:
            raise TypeNotFoundError(string)

    # Check if the string is a parameterized type (like List[int] or Dict[str, int])
    match = re.match(r"(\w+)\[(.*)\]$", string)
    if match:
        main_type, content = match.groups()
        return handle_param_type(main_type, content)

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

        # Handle common typing types
    origin = getattr(t, "__origin__", None)
    if origin:
        if origin is Optional:
            return f"Optional[{type_to_string(t.__args__[0])}]"
        if origin in [list, List]:
            return f"List[{type_to_string(t.__args__[0])}]"
        elif origin in [dict, Dict]:
            key_type = type_to_string(t.__args__[0])
            value_type = type_to_string(t.__args__[1])
            return f"Dict[{key_type}, {value_type}]"
        elif origin in [tuple, Tuple]:
            return (
                f"Tuple[{', '.join(type_to_string(subtype) for subtype in t.__args__)}]"
            )
        elif origin is Union:
            return (
                f"Union[{', '.join(type_to_string(subtype) for subtype in t.__args__)}]"
            )
        elif origin in [Type, type]:
            if hasattr(t, "__args__"):
                return f"Type[{type_to_string(t.__args__[0])}]"
            else:
                return "Type"
        elif origin is Any:
            return "Any"
        elif origin in [set, Set]:
            return f"Set[{type_to_string(t.__args__[0])}]"

    if t in STRING_GETTER:
        return STRING_GETTER[t]

    raise TypeNotFoundError(t)

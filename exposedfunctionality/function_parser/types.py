from __future__ import annotations
import importlib
import sys
import re
from typing import (
    Union,
    Type,
    Tuple,
    Set,
    get_type_hints,
    Optional,
    Callable,
    Dict,
    Any,
    List,
)

if sys.version_info >= (3, 8):
    from typing import TypedDict

    USE_TYPED_DICT = True
else:
    USE_TYPED_DICT = False

    class TypedDict(dict):
        pass


try:
    from typing import Required
except ImportError:
    Required = Union

try:
    from typing import NoneType
except ImportError:
    NoneType = type(None)


if USE_TYPED_DICT:

    class Endpoint(TypedDict, total=False):
        """Type definition for an endpoint"""

        middleware: Optional[List[Callable[[Any], Any]]]

    class FunctionInputParam(TypedDict, total=False):
        """Type definition for a function parameter

        Parameters:
        - name: The name of the parameter
        - default: The default value of the parameter
        - type: The type of the parameter
        - positional: Whether the parameter is positional
        - optional: Whether the parameter is optional
        - description: The description of the parameter
        - middleware: A list of functions that can be used to transform the parameter value
        - endpoints:  A dictionary of endpoints that can be used to represent the parameter value in different contexts
        """

        name: Required[str]
        default: Any
        type: Required[str]
        positional: Required[bool]
        optional: bool
        description: Optional[str]
        middleware: Optional[List[Callable[[Any], Any]]]
        endpoints: Optional[Dict[str, Endpoint]]

    class FunctionOutputParam(TypedDict):
        """Type definition for an output parameter

        Parameters:
        - name: The name of the parameter
        - type: The type of the parameter
        - description: The description of the parameter
        - endpoints:  A dictionary of endpoints that can be used to represent the parameter value in different contexts
        """

        name: str
        type: str
        description: Optional[str]
        endpoints: Optional[Dict[str, Endpoint]]

    class SerializedFunction(TypedDict):
        """Type definition for a serialized function"""

        name: str
        input_params: List[FunctionInputParam]
        output_params: List[FunctionOutputParam]
        docstring: Optional[DocstringParserResult]

    class DocstringParserResult(TypedDict, total=False):
        """Type definition for a standardized parsed docstring"""

        original: str
        input_params: list[FunctionInputParam]
        output_params: list[FunctionOutputParam]
        summary: Optional[str]
        exceptions: dict[str, str]

else:

    class Endpoint(dict):
        pass

    class FunctionInputParam(dict):
        pass

    class FunctionOutputParam(dict):
        pass

    class SerializedFunction(dict):
        pass

    class DocstringParserResult(dict):
        pass


class FunctionParamError(Exception):
    """Base class for function parameter errors"""


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


_TYPE_GETTER: Dict[str, type] = {**ALLOWED_BUILTINS}
_STRING_GETTER: Dict[type, str] = {}
for k, v in _TYPE_GETTER.items():
    if v not in _STRING_GETTER:
        _STRING_GETTER[v] = k


def add_type(type_: type, name: str):
    """
    Add a type to the list of allowed types.

    Parameters:
    - type_: The type to add.
    - name: The name of the type.

    Raises:
    - ValueError if the type is already in the list.
    """
    if name in _TYPE_GETTER:
        raise ValueError(f"Type '{name}' already exists.")

    _TYPE_GETTER[name] = type_
    if type_ not in _STRING_GETTER:
        _STRING_GETTER[type_] = name


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

    if string in _TYPE_GETTER:
        return _TYPE_GETTER[string]

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
        elif main_type == "Set":
            return Set[string_to_type(content)]
        else:
            raise TypeNotFoundError(string)

    # Check if the string is a parameterized type (like List[int] or Dict[str, int])
    match = re.match(r"(\w+)\[(.*)\]$", string)
    if match:
        main_type, content = match.groups()
        _type = handle_param_type(main_type, content)
        backstring = type_to_string(_type)
        try:
            add_type(
                _type, backstring
            )  # since the backstring should be prioritized add it first
        except ValueError:
            pass
        try:
            add_type(_type, string)
        except ValueError:
            pass
        return _type

    exc = None
    if "." in string:
        # Split the module path from the class name
        module_name, class_name = string.rsplit(".", 1)

        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                try:
                    add_type(cls, string)
                except ValueError:
                    pass
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

    if t in _STRING_GETTER:
        return _STRING_GETTER[t]
        # Handle common typing types

    def get_by_typing(t):
        origin = getattr(t, "__origin__", None)
        if origin:
            # Optional[T] ist just Tuple[T,None] in disguise
            # if origin is Optional:
            #    return f"Optional[{type_to_string(t.__args__[0])}]"
            if origin in [list, List]:
                return f"List[{type_to_string(t.__args__[0])}]"
            elif origin in [dict, Dict]:
                key_type = type_to_string(t.__args__[0])
                value_type = type_to_string(t.__args__[1])
                return f"Dict[{key_type}, {value_type}]"
            elif origin in [tuple, Tuple]:
                return f"Tuple[{', '.join(type_to_string(subtype) for subtype in t.__args__)}]"
            elif origin is Union:
                return f"Union[{', '.join(type_to_string(subtype) for subtype in t.__args__)}]"
            elif origin in [Type, type]:
                if hasattr(t, "__args__"):
                    return f"Type[{type_to_string(t.__args__[0])}]"
                # else: already handeld by the simple "Type" entry
                #    return "Type"
            elif origin in [set, Set]:
                return f"Set[{type_to_string(t.__args__[0])}]"

    ans = get_by_typing(t)
    if ans is not None:
        try:
            add_type(t, ans)
        except ValueError:
            pass
        return ans

    if hasattr(t, "__name__") and hasattr(t, "__module__"):
        name = t.__name__
        module = t.__module__
        # check if name can be imported from module
        try:
            module_obj = importlib.import_module(module)
            if hasattr(module_obj, name):
                ans = f"{module}.{name}"
                try:
                    add_type(t, ans)
                except ValueError:
                    pass
                return ans
        except ImportError:
            pass

    raise TypeNotFoundError(t)

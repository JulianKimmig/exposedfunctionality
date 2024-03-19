from __future__ import annotations
import importlib
import sys
import re
import ast
from typing import (
    Union,
    Type,
    Tuple,
    Set,
    Optional,
    Callable,
    Dict,
    Any,
    List,
    Literal,
    Protocol,
    TypeVar,
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
    from typing import NoneType  # type: ignore # pylint: disable=unused-import
except ImportError:
    NoneType = type(None)


if USE_TYPED_DICT:

    class Endpoint(TypedDict, total=False):
        """Type definition for an endpoint"""

        middleware: Optional[List[Callable[[Any], Any]]]

    class FunctionInputParam(TypedDict, total=False):
        """Type definition for a function parameter"""

        name: Required[str]
        """The name of the parameter, required"""
        default: Any
        """The default value of the parameter, optional"""
        type: Required[str]
        """The type of the parameter, required"""
        positional: Required[bool]
        """Whether the parameter is positional, required"""
        optional: bool
        """Whether the parameter is optional, optional"""
        description: str
        """The description of the parameter, optional"""
        middleware: List[Callable[[Any], Any]]
        """A list of functions that can be used to transform the parameter value, optional"""
        endpoints: Dict[str, Endpoint]
        """A dictionary of endpoints that can be used to represent the parameter value in different contexts, optional"""

    class FunctionOutputParam(TypedDict):
        """Type definition for an output parameter"""

        name: str
        """The name of the parameter, required"""
        type: str
        """The type of the parameter, required"""
        description: Optional[str]
        """The description of the parameter, optional"""
        endpoints: Optional[Dict[str, Endpoint]]
        """A dictionary of endpoints that can be used to represent the parameter value in different contexts, optional"""

    class SerializedFunction(TypedDict):
        """Type definition for a serialized function"""

        name: str
        """The name of the function"""
        input_params: List[FunctionInputParam]
        """The input parameters of the function"""
        output_params: List[FunctionOutputParam]
        """The output parameters of the function"""
        docstring: Optional[DocstringParserResult]
        """The parsed docstring of the function"""

    class DocstringParserResult(TypedDict, total=False):
        """Type definition for a standardized parsed docstring"""

        original: str
        """The original docstring"""
        input_params: list[FunctionInputParam]
        """The input parameters of the function as parsed from the docstring"""
        output_params: list[FunctionOutputParam]
        """The output parameters of the function as parsed from the docstring"""
        summary: Optional[str]
        """The summary of the function as parsed from the docstring"""
        exceptions: dict[str, str]
        """The exceptions of the function as parsed from the docstring"""

else:

    class Endpoint(dict):
        """Type definition for an endpoint"""

    class FunctionInputParam(dict):
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

    class FunctionOutputParam(dict):
        """Type definition for an output parameter

        Parameters:
        - name: The name of the parameter
        - type: The type of the parameter
        - description: The description of the parameter
        - endpoints:  A dictionary of endpoints that can be used to represent the parameter value in different contexts
        """

    class SerializedFunction(dict):
        """Type definition for a serialized function"""

    class DocstringParserResult(dict):
        """Type definition for a standardized parsed docstring"""


ReturnType = TypeVar("ReturnType")


class ExposedFunction(Protocol[ReturnType]):
    ef_funcmeta: SerializedFunction
    _is_exposed_method: bool

    # Define the __call__ method to make this protocol a callable
    def __call__(self, *args: Any, **kwargs: Any) -> ReturnType: ...


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
    "Any": Any,
    "Optional": Optional,
    "Union": Union,
    "Type": Type,
    "List": list,
    "Dict": dict,
    "Tuple": tuple,
    "Literal": Literal,
    "Set": set,
    "None": type(None),
}


_TYPE_GETTER: Dict[str, type] = {**ALLOWED_BUILTINS}
_STRING_GETTER: Dict[type, str] = {}
for k, v in _TYPE_GETTER.items():
    if v not in _STRING_GETTER:
        _STRING_GETTER[v] = k
_TYPE_GETTER.update(
    {
        "integer": int,
        "floating": float,
        "string": str,
        "boolean": bool,
        "number": Union[int, float],
    }
)


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

    if isinstance(string, type) or (
        hasattr(string, "__origin__") and not isinstance(string, str)
    ):
        return string

    if not isinstance(string, str):
        raise TypeError(f"Expected str, got {type(string)}")

    string = string.strip().strip(".,").strip()

    if string in _TYPE_GETTER:
        return _TYPE_GETTER[string]

    # Helper function to handle parameterized types

    def handle_param_type(main_type: str, content: str):
        if main_type == "List":
            return List[string_to_type(content)]
        elif main_type == "Dict":
            key, value = map(str.strip, content.split(","))
            return Dict[string_to_type(key), string_to_type(value)]
        elif main_type == "Tuple":
            items = tuple(map(string_to_type, content.split(",")))
            return Tuple[items]
        elif main_type == "Union":
            subtypes = tuple(map(string_to_type, content.split(",")))
            if len(subtypes) >= 2:
                return Union[subtypes]  # type: ignore # mypy doesn't like the splat operator
            else:
                return subtypes[0]
        elif main_type == "Optional":
            return Optional[string_to_type(content)]
        elif main_type == "Type":
            return Type[string_to_type(content)]
        elif main_type == "Set":
            return Set[string_to_type(content)]
        elif main_type == "Literal":
            items = [item.strip() for item in content.split(",")]
            items = [item for item in items if item]
            items = tuple([ast.literal_eval(item.strip()) for item in items])
            return Literal[items]  # type: ignore # mypy doesn't like the splat operator
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

    if "optional" in string.lower():
        string = string.replace("optional", "")
        string = string.replace("Optional", "")
        return Optional[string_to_type(string.strip())]

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
            elif origin is Literal:
                return f"Literal[{str(tuple(t.__args__))[1:-1]}]"

    #                return f"Literal[{', '.join(str(lit) for lit in t.__args__)}]"

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


def cast_to_type(value: Any, type_):
    try:
        return type_(value)
    except Exception as e:
        pass

    origin = getattr(type_, "__origin__", None)
    ex = []
    if origin:
        if origin is Union:
            for subtype in type_.__args__:
                try:
                    return cast_to_type(value, subtype)
                except Exception as e:
                    ex.append(e)
        if origin is Optional:
            if value in (None, "", "None", "none"):
                return None
            else:
                return cast_to_type(value, type_.__args__[0])

    ex.append(ValueError(f"Could not cast {value} to type {type_}"))

    # raise all ex from each other
    e = ex[-1]
    for _e in reversed(ex[:-1]):
        try:
            raise e from _e
        except Exception as ne:
            e = ne
    raise e

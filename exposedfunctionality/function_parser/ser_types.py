from dataclasses import Field, dataclass, field, fields, is_dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)
from warnings import warn
from collections.abc import KeysView, ItemsView, ValuesView


def dictmethod_deprecated(method: Callable) -> Callable:
    """
    Decorator to mark dictionary-like methods as deprecated.

    This decorator will raise a `DeprecationWarning` the first time
    a dictionary-like method is accessed. The warning indicates that
    such access will be removed in future versions.

    Args:
        method (Callable): The method to be deprecated.

    Returns:
        Callable: The wrapped method with deprecation warning.
    """

    def wrapper(self, *args, **kwargs):
        _cls = self if isinstance(self, type) else type(self)
        if not getattr(_cls, "__warned_dictusage", False):
            warn(
                f"Dictionary-like access to {_cls.__name__} "
                "objects is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=3,
            )
            _cls.__warned_dictusage = True
        return method(self, *args, **kwargs)

    return wrapper


@runtime_checkable
@dataclass
class DataclassProtocol(Protocol):
    """A protocol to enforce that an object is a dataclass."""

    pass


# Generic dataclass type
T = TypeVar("T", bound=DataclassProtocol)


def dataclass_to_dict(instance: T) -> Dict[str, Any]:
    """
    Converts a dataclass instance to a dictionary, recursively converting nested dataclasses.

    Args:
        instance (T): A dataclass instance to be converted.

    Returns:
        Dict[str, Any]: A dictionary representing the dataclass instance.

    Raises:
        TypeError: If the provided instance is not a dataclass.
    """
    if not is_dataclass(instance):
        raise TypeError(f"Expected dataclass instance, got {type(instance).__name__}")

    result = {}
    for field in fields(instance):
        value = getattr(instance, field.name)
        if is_dataclass(value):
            result[field.name] = dataclass_to_dict(value)
        else:
            result[field.name] = value
    return result


def dict_to_dataclass(data: Dict[str, Any], dataclass_type: Type[T]) -> T:
    """
    Converts a dictionary to a dataclass instance, recursively converting nested dictionaries.

    Args:
        data (Dict[str, Any]): The dictionary to be converted.
        dataclass_type (Type[T]): The type of the dataclass to create.

    Returns:
        T: An instance of the specified dataclass type.

    Raises:
        TypeError: If the provided type is not a dataclass.
    """
    if not is_dataclass(dataclass_type):
        raise TypeError(f"Expected dataclass type, got {dataclass_type.__name__}")

    field_values = {}
    for field in fields(dataclass_type):
        if field.name in data:
            value = data[field.name]
            if is_dataclass(field.type):
                field_values[field.name] = dict_to_dataclass(value, field.type)
            else:
                field_values[field.name] = value
        else:
            if isinstance(field.default_factory, Field.default_factory):
                field_values[field.name] = field.default_factory()
            else:
                field_values[field.name] = field.default

    return dataclass_type(**field_values)


class DictMixin:
    """
    A mixin class that allows dataclasses to behave like dictionaries.

    This mixin provides dictionary-like access and modification capabilities
    for dataclass instances, with methods like `__getitem__`, `__setitem__`,
    `keys`, `values`, and `items`. All dictionary-like methods are marked
    as deprecated.
    """

    def __init_subclass__(cls) -> None:
        """Initialize subclass and set the warning flag for dictionary usage."""
        cls.__warned_dictusage = False

    @dictmethod_deprecated
    def __getitem__(self, key: str) -> Any:
        """
        Get the value of a dataclass field by key.

        Args:
            key (str): The field name.

        Returns:
            Any: The value of the field.

        Raises:
            KeyError: If the field does not exist.
        """
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"{self.__class__.__name__} object has no attribute '{key}'")

    @dictmethod_deprecated
    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set the value of a dataclass field by key.

        Args:
            key (str): The field name.
            value (Any): The value to set.

        Raises:
            KeyError: If the field does not exist.
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"{self.__class__.__name__} object has no attribute '{key}'")

    @dictmethod_deprecated
    def __delitem__(self, key: str) -> None:
        """
        Prevent deletion of a dataclass field by key.

        Args:
            key (str): The field name.

        Raises:
            TypeError: Always, as deletion is not allowed.
            KeyError: If the field does not exist.
        """
        if hasattr(self, key):
            raise TypeError(
                f"Cannot delete attribute '{key}' from {self.__class__.__name__}"
            )
        raise KeyError(f"{self.__class__.__name__} object has no attribute '{key}'")

    @dictmethod_deprecated
    def __contains__(self, key: str) -> bool:
        """
        Check if a dataclass field exists by key.

        Args:
            key (str): The field name.

        Returns:
            bool: True if the field exists, False otherwise.
        """
        return hasattr(self, key)

    @dictmethod_deprecated
    def keys(self) -> KeysView[str]:
        """
        Get a view of the dataclass fields' names.

        Returns:
            KeysView[str]: A view of the field names.
        """
        return self.as_dict().keys()

    @dictmethod_deprecated
    def values(self) -> ValuesView[Any]:
        """
        Get a view of the dataclass fields' values.

        Returns:
            ValuesView[Any]: A view of the field values.
        """
        return self.as_dict().values()

    @dictmethod_deprecated
    def items(self) -> ItemsView[str, Any]:
        """
        Get a view of the dataclass fields' items (name-value pairs).

        Returns:
            ItemsView[str, Any]: A view of the field items.
        """
        return self.as_dict().items()

    @dictmethod_deprecated
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get the value of a dataclass field by key, with a default if the field does not exist.

        Args:
            key (str): The field name.
            default (Any): The default value to return if the field does not exist.

        Returns:
            Any: The value of the field, or the default value if the field does not exist.
        """
        return getattr(self, key, default)

    @dictmethod_deprecated
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update multiple dataclass fields with values from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary of field names and values to update.

        Raises:
            KeyError: If any field in the dictionary does not exist.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise KeyError(
                    f"{self.__class__.__name__} object has no attribute '{key}'"
                )

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert the dataclass instance to a dictionary.

        Returns:
            Dict[str, Any]: A dictionary representation of the dataclass instance.
        """
        return dataclass_to_dict(self)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a dataclass instance from a dictionary.

        Args:
            data (Dict[str, Any]): A dictionary of field names and values.

        Returns:
            T: An instance of the dataclass.
        """
        return dict_to_dataclass(data, cls)


@dataclass
class Endpoint(DictMixin):
    """
    Type definition for an endpoint.

    Attributes:
        middleware (Optional[List[Callable[[Any], Any]]]): A list of middleware functions for the endpoint.
    """

    middleware: Optional[List[Callable[[Any], Any]]] = None


@dataclass
class FunctionInputParam(DictMixin):
    """
    Type definition for a function parameter.

    Attributes:
        name (str): The name of the parameter, required.
        type (str): The type of the parameter, required.
        positional (bool): Whether the parameter is positional, required.
        default (Any): The default value of the parameter, optional.
        optional (bool): Whether the parameter is optional, optional.
        description (str): The description of the parameter, optional.
        middleware (List[Callable[[Any], Any]]): A list of functions that can be
            used to transform the parameter value, optional.
        endpoints (Dict[str, Endpoint]): A dictionary of endpoints that can be
            used to represent the parameter value in different contexts, optional.
    """

    name: str
    type: str
    positional: bool
    default: Any = None
    optional: bool = False
    description: str = ""
    middleware: List[Callable[[Any], Any]] = field(default_factory=list)
    endpoints: Dict[str, Endpoint] = field(default_factory=dict)


@dataclass
class FunctionOutputParam(DictMixin):
    """
    Type definition for an output parameter.

    Attributes:
        name (str): The name of the parameter, required.
        type (str): The type of the parameter, required.
        description (Optional[str]): The description of the parameter, optional.
        endpoints (Optional[Dict[str, Endpoint]]): A dictionary of endpoints that can be used to represent the parameter value in different contexts, optional.
    """

    name: str
    type: str
    description: Optional[str] = None
    endpoints: Optional[Dict[str, Endpoint]] = None


@dataclass
class DocstringParserResult(DictMixin):
    """
    Type definition for a standardized parsed docstring.

    Attributes:
        original (Optional[str]): The original docstring.
        input_params (List[FunctionInputParam]): The input parameters of the function as parsed from the docstring.
        output_params (List[FunctionOutputParam]): The output parameters of the function as parsed from the docstring.
        summary (Optional[str]): The summary of the function as parsed from the docstring.
        exceptions (Dict[str, str]): The exceptions of the function as parsed from the docstring.
    """

    original: Optional[str] = None
    input_params: List[FunctionInputParam] = field(default_factory=list)
    output_params: List[FunctionOutputParam] = field(default_factory=list)
    summary: Optional[str] = None
    exceptions: Dict[str, str] = field(default_factory=dict)


@dataclass
class SerializedFunction(DictMixin):
    """
    Type definition for a serialized function.

    Attributes:
        name (str): The name of the function.
        input_params (List[FunctionInputParam]): The input parameters of the function.
        output_params (List[FunctionOutputParam]): The output parameters of the function.
        docstring (Optional[DocstringParserResult]): The parsed docstring of the function.
    """

    name: str
    input_params: List[FunctionInputParam]
    output_params: List[FunctionOutputParam]
    docstring: Optional[DocstringParserResult] = None


ReturnType = TypeVar("ReturnType")


class ExposedFunction(Protocol[ReturnType]):
    """
    Protocol for exposed functions.

    Attributes:
        ef_funcmeta (SerializedFunction): Metadata about the exposed function.
        _is_exposed_method (bool): Indicates if the function is exposed.

    Methods:
        __call__(*args: Any, **kwargs: Any) -> ReturnType: The method signature for the function call.
    """

    ef_funcmeta: SerializedFunction
    _is_exposed_method: bool

    def __call__(self, *args: Any, **kwargs: Any) -> ReturnType: ...


class FunctionParamError(Exception):
    """Base class for function parameter errors."""

    pass


class UnknownSectionError(Exception):
    """Exception raised when an unknown section is encountered in parsing."""

    pass


class TypeNotFoundError(Exception):
    """
    Exception raised when a type cannot be found.

    Attributes:
        type_name (str): The name of the type that was not found.
    """

    def __init__(self, type_name: str):
        self.type_name = type_name
        super().__init__(f"Type '{type_name}' not found.")

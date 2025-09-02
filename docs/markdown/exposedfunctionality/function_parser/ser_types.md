# function_parser/ser_types.py

Defines the typed, serializable schemas used across the package.

## Schemas

- `Endpoint`: Optional endpoint metadata, including `middleware: Optional[List[Callable[[Any], Any]]]`.
- `FunctionInputParam` (TypedDict):
  - `name: str`, `type: str`, `positional: bool`.
  - Optional: `default: Any`, `optional: bool`, `description: str`, `middleware: List[Callable]`, `endpoints: Dict[str, Endpoint]`.
- `FunctionOutputParam` (TypedDict):
  - `name: str`, `type: str`.
  - Optional: `description: Optional[str]`, `endpoints: Optional[Dict[str, Endpoint]]`.
- `DocstringParserResult` (TypedDict):
  - `original: Optional[str]`, `input_params: List[FunctionInputParam]`, `output_params: List[FunctionOutputParam]`, `summary: Optional[str]`, `exceptions: Dict[str, str]`.
- `SerializedFunction` (TypedDict):
  - `name: str`, `input_params: [...]`, `output_params: [...]`, `docstring: Optional[DocstringParserResult]`.
- `ExposedFunction[ReturnType]` (Protocol): Callable with `ef_funcmeta` and `_is_exposed_method`.

## Exceptions

- `FunctionParamError`: Base for parameter issues.
- `UnknownSectionError`: Raised on unknown docstring sections (from parsing helpers).
- `TypeNotFoundError`: Thrown when a type string/object cannot be resolved or stringified.


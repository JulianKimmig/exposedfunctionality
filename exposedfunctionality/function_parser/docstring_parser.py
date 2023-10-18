from __future__ import annotations
from typing import Callable, TypedDict, Optional
import re

from .types import (
    string_to_type,
    type_to_string,
    DocstringParserResult,
)


def _unify_parser_results(
    result: DocstringParserResult, docstring=str
) -> DocstringParserResult:
    # default empty lists

    result["original"] = docstring
    if "input_params" not in result:
        result["input_params"] = []
    if "output_params" not in result:
        result["output_params"] = []
    if "exceptions" not in result:
        result["exceptions"] = {}

    if "summary" in result:
        result["summary"] = result["summary"].strip()

    # strip and remove empty descriptions
    for param in result["input_params"]:
        param["description"] = param["description"].strip()

        if "defaults to" in param["description"]:
            pattern = r"defaults to (`[^`]+`|'[^']+'|\"[^\"]+\"|[^\s.,]+)"
            match = re.search(pattern, param["description"])
            if match:
                description = param["description"]
                description = description[: match.start()] + description[match.end() :]
                default_val = match.group(1)

                # If it's surrounded by backticks, single, or double quotes, strip them.
                if default_val.startswith(("`", "'", '"')):
                    default_val = default_val[1:-1]
                if "default" not in param:
                    param["default"] = default_val

                param["description"] = description.strip()
        if "default" in param and isinstance(param["default"], str):
            if param["default"].startswith(("`", "'", '"')):
                param["default"] = param["default"][1:-1]
        if "default" in param and "type" in param:
            param["default"] = string_to_type(param["type"])(param["default"])

        if "type" in param:
            param["type"] = type_to_string(param["type"])

        param["description"] = (
            param["description"]
            .replace("  ", " ")
            .replace(" .", ".")
            .replace(" ,", ",")
            .replace(" :", ":")
            .replace(",.", ".")
        ).strip()
        # add dot if missing

        if param["description"] and not param["description"].endswith("."):
            param["description"] += "."

        if "positional" not in param:
            if "default" in param or ("optional" in param and param["optional"]):
                param["positional"] = False
            else:
                param["positional"] = True

        if "optional" not in param:
            if "default" in param or not param["positional"]:
                param["optional"] = True
            else:
                param["optional"] = False

        if not param["description"]:
            del param["description"]

    for i, param in enumerate(result["output_params"]):
        if "name" not in param:
            param["name"] = f"out{i}" if len(result["output_params"]) > 1 else "out"

        if "type" in param:
            print(param["type"], type_to_string(param["type"]))
            param["type"] = type_to_string(param["type"])

    # strip and remove empty errors

    for error in list(result["exceptions"].keys()):
        result["exceptions"][error] = result["exceptions"][error].strip()

    # strip  and remove empty return
    for op in result["output_params"]:
        op["description"] = op["description"].strip()
        if not op["description"]:
            del op["description"]

    # strip summary
    if "summary" in result:
        result["summary"] = result["summary"].strip()

    from pprint import pprint

    pprint(result)
    return result


def parse_restructured_docstring(docstring: str) -> DocstringParserResult:
    """Extracts the parameter descriptions from a reStructuredText docstring.

    Args:
        docstring (str): The docstring from which the parameter descriptions are extracted.

    Returns:
        dict: A dictionary of parameter names to their descriptions.


    Format:
        ```[Summary]

        :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
        :type [ParamName]: [ParamType](, optional)
        ...
        :raises [ErrorType]: [ErrorDescription]
        ...
        :return: [ReturnDescription]
        :rtype: [ReturnType]
        ```

    Examples:
    ```python
    docstring = '''
    This is a docstring.

    :param a: The first parameter.
    :param b: The second parameter.
    '''
    print(extract_param_descriptions_reStructuredText(docstring))
    # Returns: {'a': 'The first parameter.', 'b': 'The second parameter.'}
    ```
    """

    # prepend :summary: to the docstring
    original_ = docstring
    docstring = ":summary:\n" + docstring
    lines = docstring.strip().split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    sections = []
    current_section = []
    for line in lines:
        if line.startswith(":") and current_section:
            sections.append(current_section)
            current_section = []
        current_section.append(line)

    if current_section:
        sections.append(current_section)

    sections = [" ".join(section) for section in sections]

    result: DocstringParserResult = {
        "input_params": [],
        "output_params": [],
        "exceptions": {},
    }

    for section in sections:
        if section.startswith(":summary:"):
            s = section.replace(":summary:", "").strip()
            if s:
                result["summary"] = s
        elif section.startswith(":param"):
            psection = section.replace(":param", "").strip()
            param_match = re.match(r"([\w_]+):(.+)", psection)
            if not param_match:
                # maybe only a name is given
                param_match = re.match(r"([\w_]+)", psection)
                if not param_match:
                    raise ValueError(f"Could not parse line '{line}' as parameter")
            param = {"name": param_match.group(1)}
            if param_match.group(2):
                param["description"] = param_match.group(2).strip()

            # default optional
            param["optional"] = False
            if "defaults to" in param["description"]:
                desc, default = param["description"].split("defaults to")
                param["description"] = desc.strip(" ,")
                param["default"] = default.strip()

            result["input_params"].append(param)
        elif section.startswith(":type"):
            if len(result["input_params"]) == 0:
                raise ValueError("Type section without parameter")
            psection = section.replace(":type", "").strip()

            # get param name or last param
            param = None
            if ":" in psection:
                param_name, psection = psection.split(":", 1)
                param_name = param_name.strip()

                for _param in result["input_params"]:
                    if _param["name"] == param_name:
                        param = _param
                        break
            else:
                param = result["input_params"][-1]
            if param is None:
                raise ValueError(f"Could not find parameter for type section '{line}'")

            param["type"] = psection.strip()
            if "optional" in param["type"]:
                ann, opt = param["type"].split(", optional")
                param["optional"] = True
                param["type"] = ann.strip()
            else:
                param["optional"] = False

            param["type"] = string_to_type(param["type"])
        elif section.startswith(":raises"):
            rsection = section.replace(":raises", "").strip()
            raise_match = re.match(r"([\w_]+):(.+)", rsection)
            if not raise_match:
                raise ValueError(f"Could not parse line '{line}' as raise")
            result["exceptions"][raise_match.group(1)] = raise_match.group(2).strip()
        elif section.startswith(":return"):
            rsection = section.replace(":return:", "").strip()
            return_desc = {"description": rsection}
            result["output_params"].append(return_desc)
        elif section.startswith(":rtype"):
            if len(result["output_params"]) == 0:
                raise ValueError("Type section without return")
            rsection = section.replace(":rtype:", "").strip()
            result["output_params"][0]["type"] = string_to_type(rsection)

    return _unify_parser_results(result, docstring=original_)


def parse_google_docstring(docstring: str) -> DocstringParserResult:
    """Extracts the parameter descriptions from a Google-style docstring.

    Args:
        docstring (str): The docstring from which the parameter descriptions are extracted.

    Returns:
        dict: A dictionary of parameter names to their descriptions.

    Examples:
    ```python
    docstring = '''
    This is a docstring.

    Args:
        a (int): The first parameter.
            This continues.
        b (int): The second parameter.
    '''
    print(extract_param_descriptions_google(docstring))
    # Returns: {'a': 'The first parameter. This continues.', 'b': 'The second parameter.'}
    ```

    Format:
        ```[Summary]

        Args:
            [ParamName] ([ParamType]): [ParamDescription]
            ...
        Raises:
            [ErrorType]: [ErrorDescription]
            ...
        Returns:
            [ReturnDescription]
        ```
    """

    # Split the docstring by lines
    lines = [line.strip() for line in docstring.strip().split("\n")]

    # Prepare the result object
    result: DocstringParserResult = {
        "input_params": [],
        "output_params": [],
        "exceptions": {},
    }

    # Define a variable to track the current section being parsed
    section = "Sum"
    last_param: Optional[dict] = None  # to append multi-line descriptions

    for line in lines:
        if line.startswith("Args:"):
            section = "Args"
        elif line.startswith("Returns:"):
            section = "Returns"
        elif line.startswith("Raises:"):
            section = "Raises"
        else:
            if section == "Sum":
                if "summary" in result:
                    result["summary"] += " " + line
                else:
                    result["summary"] = line
            if section == "Args":
                param_match_full = re.match(r"(\w+) \(([\w\[\], ]+)\): (.+)", line)
                param_match_desc = re.match(r"(\w+): (.+)", line)
                param_match_type = re.match(r"(\w+) \(([\w\[\], ]+)\)", line)

                if param_match_full:
                    param_match = param_match_full
                    name = param_match.group(1)
                    type_opt = param_match.group(2)
                    description = param_match.group(3)
                elif param_match_type:
                    param_match = param_match_type
                    name = param_match.group(1)
                    type_opt = param_match.group(2)
                    description = ""
                elif param_match_desc:
                    param_match = param_match_desc
                    name = param_match.group(1)
                    type_opt = None
                    description = param_match.group(2)
                else:
                    last_param["description"] += " " + line
                    continue

                optional = False
                if type_opt and "optional" in type_opt:
                    optional = True
                    type_opt = type_opt.split(",")
                    if len(type_opt) > 1:
                        type = type_opt[0]
                    else:
                        type = None
                else:
                    type = type_opt

                param = {
                    "name": name,
                    "description": description,
                    "optional": optional,
                }
                if type:
                    param["type"] = string_to_type(type)
                del type
                result["input_params"].append(param)
                last_param = param
            elif section == "Returns":
                return_match = re.match(r"([\w\[\], ]+): (.+)", line)
                if return_match:
                    return_param = {
                        "type": string_to_type(return_match.group(1)),
                        "description": return_match.group(2),
                    }
                    result["output_params"].append(return_param)
                    last_param = return_param
                elif last_param:
                    last_param["description"] += " " + line
            elif section == "Raises":
                raise_match = re.match(r"(\w+): (.+)", line)
                if raise_match:
                    result["exceptions"][raise_match.group(1)] = (
                        raise_match.group(2)
                    ).strip()
                    last_exception = raise_match.group(1)
                elif last_exception in result["exceptions"]:
                    result["exceptions"][last_exception] += " " + line

    return _unify_parser_results(result, docstring)


def select_extraction_function(docstring: str) -> Callable:
    """
    Determines the appropriate extraction function for a given docstring.

    Args:
        docstring (str): The docstring for which an extraction function is needed.

    Returns:
        Callable: The selected extraction function.
    """
    # Check for reStructuredText indicators
    if ":param" in docstring:
        return parse_restructured_docstring

    if ":raises" in docstring:
        return parse_restructured_docstring

    if ":return" in docstring:
        return parse_restructured_docstring

    # Check for Google style indicators
    # (Note: Google style is more general and may overlap with other styles,
    # so we check it last)
    param_pattern_google_with_types = (
        r"^\s*([a-zA-Z_]\w*)\s?\(.*\):"  # match "param_name (param_type):"
    )
    param_pattern_google_no_types = r"^\s*([a-zA-Z_]\w*):"  # match "param_name:"
    if re.search(param_pattern_google_with_types, docstring, re.MULTILINE):
        return parse_google_docstring
    if re.search(param_pattern_google_no_types, docstring, re.MULTILINE):
        return parse_google_docstring

    # If none match, return None or you could return a default function
    return None


def parse_docstring(docstring: str) -> DocstringParserResult:
    """
    Extracts the parameter descriptions from a docstring.

    Args:
        docstring (str): The docstring from which the parameter descriptions are extracted.

    Returns:
        dict: A dictionary of parameter names to their descriptions.
    """
    extraction_function = select_extraction_function(docstring)
    if extraction_function is None:
        return _unify_parser_results({"summary": docstring}, docstring=docstring)
    return _unify_parser_results(extraction_function(docstring), docstring=docstring)

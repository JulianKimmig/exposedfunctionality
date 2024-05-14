"""
Test module for the types module.
"""

import unittest
from unittest.mock import patch, Mock
from time import time
from typing import Set, Literal


class CustomTypeA:
    pass


class CustomTypeB:
    pass


class TestStringToType(unittest.TestCase):
    # Test for built-in types
    def test_builtin_types(self):
        from exposedfunctionality.function_parser.types import string_to_type

        self.assertEqual(string_to_type("int"), int)
        self.assertEqual(string_to_type("str"), str)
        self.assertEqual(string_to_type("list"), list)
        # ... you can continue for other built-ins

    # Test for valid module imports
    def test_module_imports(self):
        from exposedfunctionality.function_parser.types import string_to_type

        datetime_type = string_to_type("datetime.datetime")
        self.assertEqual(datetime_type.__name__, "datetime")

    # Test for invalid type names
    def test_invalid_type_name(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TypeNotFoundError,
        )

        with self.assertRaises(TypeNotFoundError):
            string_to_type("NoSuchType")

    # Test for non-existent modules
    def test_non_existent_module(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TypeNotFoundError,
        )

        with self.assertRaises(TypeNotFoundError):
            string_to_type("no_such_module.NoClass")

    def test_type_getter(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            add_type,
        )

        class CustomTypeA:
            pass

        add_type(CustomTypeA, "CustomTypeA")

        self.assertEqual(string_to_type("CustomTypeA"), CustomTypeA)

    @patch("exposedfunctionality.function_parser.types.importlib.import_module")
    def test_module_import_without_class(self, mock_import_module):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TypeNotFoundError,
        )
        import exposedfunctionality

        # Mocking a module object
        mock_module = Mock(spec=exposedfunctionality.function_parser.types)
        mock_import_module.return_value = mock_module

        # Assuming the class_name we're looking for is 'MissingClass'
        with self.assertRaises(TypeNotFoundError):
            string_to_type("mock_module.MissingClass")

        # Asserting that the module was imported
        mock_import_module.assert_called_once_with("mock_module")

    def test_typing_strings(self):
        # Test for typing types
        from exposedfunctionality.function_parser.types import string_to_type
        from typing import Optional, Union, List, Dict, Tuple, Any, Type

        self.assertEqual(string_to_type("Optional[int]"), Optional[int])
        self.assertEqual(string_to_type("Union[int, None]"), Union[int, None])
        self.assertEqual(string_to_type("Union[int, str]"), Union[int, str])
        self.assertEqual(string_to_type("List[int]"), List[int])
        self.assertEqual(string_to_type("Dict[int, str]"), Dict[int, str])
        self.assertEqual(string_to_type("Tuple[int, str]"), Tuple[int, str])
        self.assertEqual(string_to_type("Any"), Any)
        self.assertEqual(string_to_type("Type"), Type)
        self.assertEqual(string_to_type("Type[int]"), Type[int])
        self.assertEqual(string_to_type("List[Union[int, str]]"), List[Union[int, str]])
        self.assertEqual(string_to_type("List[List[int]]"), List[List[int]])
        self.assertEqual(string_to_type("Tuple[int,int]"), Tuple[int, int])
        self.assertEqual(string_to_type("Set[float]"), Set[float])
        self.assertEqual(string_to_type("Literal[1,2,'hello']"), Literal[1, 2, "hello"])

    def test_wrongtypes(self):
        from exposedfunctionality.function_parser.types import string_to_type

        with self.assertRaises(TypeError):
            string_to_type(10)

    def test_unknown_type(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TypeNotFoundError,
        )

        with self.assertRaises(TypeNotFoundError):
            string_to_type("Dummy[int]")


class TestAddType(unittest.TestCase):
    def setUp(self):
        from exposedfunctionality.function_parser.types import (
            _TYPE_GETTER,
            _STRING_GETTER,
        )

        self.initial_types = _TYPE_GETTER.copy()
        self.initial_string_types = _STRING_GETTER.copy()

    def tearDown(self):
        from exposedfunctionality.function_parser import types

        types._TYPE_GETTER = self.initial_types
        types._STRING_GETTER = self.initial_string_types

    def test_add_new_type(self):
        from exposedfunctionality.function_parser.types import add_type, _TYPE_GETTER

        class NewType:
            pass

        add_type(NewType, "NewType")
        self.assertIn("NewType", _TYPE_GETTER)
        self.assertEqual(_TYPE_GETTER["NewType"], NewType)

    def test_adding_duplicate_type_does_not_override(self):
        from exposedfunctionality.function_parser.types import add_type, _TYPE_GETTER

        class DuplicateType:
            pass

        add_type(int, "DuplicateType")

        self.assertEqual(_TYPE_GETTER["int"], _TYPE_GETTER["DuplicateType"])
        self.assertEqual(_TYPE_GETTER["DuplicateType"], int)


class TestGeneral(unittest.TestCase):
    def test_STRING_GETTER_populated_correctly(self):
        from exposedfunctionality.function_parser.types import (
            _STRING_GETTER,
            _TYPE_GETTER,
        )

        for k, v in _TYPE_GETTER.items():
            self.assertIn(v, _STRING_GETTER)


class TestTypeToString(unittest.TestCase):
    """
    Test class for the type_to_string function.
    """

    def test_string_input(self):
        """
        Test that the function returns the input unchanged if it's a string.
        """
        from exposedfunctionality.function_parser.types import type_to_string

        self.assertEqual(type_to_string("str"), "str")

    def test_builtin_types(self):
        """
        Test conversion of built-in types to string representation.
        """
        from exposedfunctionality.function_parser.types import type_to_string

        self.assertEqual(type_to_string(int), "int")
        self.assertEqual(type_to_string(str), "str")
        # ... add other builtin types as needed

    def test_custom_types_to_string(self):
        from exposedfunctionality.function_parser.types import type_to_string, add_type

        class CustomType_T:
            pass

        t = str(time())  # since custom tyoe might be added in another test
        add_type(CustomType_T, "CustomType" + t)
        self.assertEqual(type_to_string(CustomType_T), "CustomType" + t)

    def test_unknown_type_raises_error(self):
        from exposedfunctionality.function_parser.types import (
            type_to_string,
            TypeNotFoundError,
        )

        # Create an object instance without __name__ and __module__ attributes
        UnknownType = type("UnknownType", (), {})()
        with self.assertRaises(TypeNotFoundError):
            type_to_string(UnknownType)

        class UnknownType:
            pass

        with self.assertRaises(TypeNotFoundError):
            _ = type_to_string(UnknownType)

    def test_typing_types(self):
        from exposedfunctionality.function_parser.types import (
            type_to_string,
            _STRING_GETTER,
        )
        from typing import Optional, Union, List, Dict, Tuple, Any, Type

        import pprint

        pprint.pprint(_STRING_GETTER)

        for i in range(2):
            self.assertIn(
                type_to_string(Optional[int]), ["Union[int, None]", "Optional[int]"]
            )
            self.assertEqual(
                type_to_string(Union[int, str]), "Union[int, str]", _STRING_GETTER
            )
            self.assertEqual(type_to_string(List[int]), "List[int]")
            self.assertEqual(type_to_string(Dict[int, str]), "Dict[int, str]")
            self.assertEqual(type_to_string(Tuple[int, str]), "Tuple[int, str]")
            self.assertEqual(type_to_string(Any), "Any")
            self.assertEqual(type_to_string(Type), "Type")
            self.assertEqual(type_to_string(Set[float]), "Set[float]")
            self.assertEqual(type_to_string(Type[Any]), "Type[Any]")
            self.assertEqual(type_to_string(Type[int]), "Type[int]")
            self.assertEqual(
                type_to_string(List[Union[int, str]]), "List[Union[int, str]]"
            )
            self.assertEqual(type_to_string(List[List[int]]), "List[List[int]]")
            self.assertEqual(
                type_to_string(Literal[1, 2, "hello world"]),
                "Literal[1, 2, 'hello world']",
            )

    def test_custom_type(self):
        """
        Test conversion of a custom type to string representation.
        """
        from exposedfunctionality.function_parser.types import type_to_string

        self.assertEqual(type_to_string(CustomTypeB), "test_types.CustomTypeB")

    def test_unknown_type(self):
        """
        Test conversion of an unknown type raises the appropriate exception.
        """
        from exposedfunctionality.function_parser.types import (
            type_to_string,
            TypeNotFoundError,
        )

        # Create a custom type without __name__ and __module__ attributes
        UnknownType = type("UnknownType", (), {})

        with self.assertRaises(TypeNotFoundError):
            type_to_string(UnknownType)

    def test_ser_types(self):
        from exposedfunctionality import serialize_type
        from typing import Optional, Union, List, Dict, Tuple, Any, Type

        self.assertEqual(serialize_type(int), "int")
        self.assertEqual(serialize_type(str), "str")
        self.assertEqual(serialize_type(CustomTypeA), "test_types.CustomTypeA")
        self.assertEqual(serialize_type(CustomTypeB), "test_types.CustomTypeB")
        self.assertEqual(serialize_type(Optional[int]), {"anyOf": ["int", "None"]})
        self.assertEqual(serialize_type(Union[int, str]), {"anyOf": ["int", "str"]})
        self.assertEqual(
            serialize_type(List[int]),
            {"type": "array", "items": "int", "uniqueItems": False},
        )
        self.assertEqual(
            serialize_type(Dict[int, str]),
            {"keys": "int", "type": "object", "values": "str"},
        )
        self.assertEqual(serialize_type(Tuple[int, str]), {"allOf": ["int", "str"]})
        self.assertEqual(serialize_type(Any), "Any")
        self.assertEqual(serialize_type(Type), {"type": "type", "value": "Any"})
        self.assertEqual(
            serialize_type(Set[float]),
            {"items": "float", "type": "array", "uniqueItems": True},
        )
        self.assertEqual(serialize_type(Type[Any]), {"type": "type", "value": "Any"})
        self.assertEqual(serialize_type(Type[int]), {"type": "type", "value": "int"})
        self.assertEqual(
            serialize_type(List[Union[int, str]]),
            {"items": {"anyOf": ["int", "str"]}, "type": "array", "uniqueItems": False},
        )
        self.assertEqual(
            serialize_type(List[List[int]]),
            {
                "items": {"items": "int", "type": "array", "uniqueItems": False},
                "type": "array",
                "uniqueItems": False,
            },
        )
        self.assertEqual(
            serialize_type(Literal[1, 2, "hello world"]),
            {
                "type": "enum",
                "values": [1, 2, "hello world"],
                "nullable": False,
                "keys": ["1", "2", "hello world"],
            },
        )
        self.assertEqual(
            serialize_type(Literal[1, 2, "hello world", None]),
            {
                "type": "enum",
                "values": [1, 2, "hello world"],
                "nullable": True,
                "keys": ["1", "2", "hello world"],
            },
        )

        self.assertEqual(
            serialize_type(Optional[Literal[1, 2, "hello world"]]),
            {
                "type": "enum",
                "values": [1, 2, "hello world"],
                "nullable": True,
                "keys": ["1", "2", "hello world"],
            },
        )
        self.assertEqual(
            serialize_type(Optional[Union[int, Literal[1, 2, "hello world"]]]),
            {
                "anyOf": [
                    "int",
                    {
                        "type": "enum",
                        "values": [1, 2, "hello world"],
                        "nullable": True,
                        "keys": ["1", "2", "hello world"],
                    },
                    "None",
                ]
            },
        )
        import numpy as np

        self.assertEqual(
            serialize_type(Union[int, np.ndarray]),
            {"anyOf": ["int", "numpy.ndarray"]},
        )

        self.assertEqual(
            serialize_type(Union[Union[Union[int, str], float], np.ndarray]),
            {
                "anyOf": [
                    "int",
                    "str",
                    "float",
                    "numpy.ndarray",
                ]
            },
        )

        self.assertEqual(
            serialize_type(Union[Union[Union[int]]]),
            "int",
        )
        self.assertEqual(
            serialize_type(Union[Union[Tuple[Union[int, str], int]]]),
            {"allOf": [{"anyOf": ["int", "str"]}, "int"]},
        )
        self.assertEqual(
            serialize_type(Union[int, Union[Tuple[Union[int, str], int]]]),
            {"anyOf": ["int", {"allOf": [{"anyOf": ["int", "str"]}, "int"]}]},
        )

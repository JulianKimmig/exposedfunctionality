import unittest
from typing import Tuple
from functools import partial


class TestFunctionSerialization(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()

    def test_get_resolved_signature(self):
        from exposedfunctionality.function_parser import get_resolved_signature

        # Test basic function
        def func(a, b=1, c=2):
            pass

        sig, _ = get_resolved_signature(func)
        self.assertEqual(str(sig), "(a, b=1, c=2)")

        # Test functools.partial
        partial_func = partial(func, 5)
        sig, _ = get_resolved_signature(partial_func)
        self.assertEqual(str(sig), "(b=1, c=2)")

    def test_get_resolved_signature_method(self):
        from exposedfunctionality.function_parser import get_resolved_signature

        # Test class methods
        class TestClass:
            def method(self, x, y=0):
                pass

            @classmethod
            def class_method(cls, x, y=0):
                pass

        sig, _ = get_resolved_signature(TestClass().method)
        self.assertEqual(str(sig), "(x, y=0)")

        sig, _ = get_resolved_signature(TestClass.class_method)
        self.assertEqual(str(sig), "(x, y=0)")

    def test_function_method_parser_simple(self):
        from exposedfunctionality.function_parser import function_method_parser

        # Test basic function serialization
        def example_function(a: int, b: str = "default") -> Tuple[int, str]:
            """This is an example function."""
            return a, b

        result = function_method_parser(example_function)
        expected = {
            "name": "example_function",
            "input_params": [
                {"name": "a", "type": "int", "positional": True},
                {
                    "name": "b",
                    "type": "str",
                    "positional": False,
                    "default": "default",
                },
            ],
            "output_params": [
                {"name": "out0", "type": "int"},
                {"name": "out1", "type": "str"},
            ],
            "docstring": {
                "exceptions": {},
                "input_params": [],
                "summary": "This is an example function.",
                "output_params": [],
                "original": "This is an example function.",
            },
        }
        self.assertEqual(result, expected)

    def test_function_method_parser_typed(self):
        from exposedfunctionality.function_parser import function_method_parser
        from typing import Union, Dict, Optional

        # Test basic function serialization
        def example_function(
            a: Union[int, float], b: Optional[str] = None
        ) -> Dict[str, Tuple[int, str]]:
            return {"a": (a, str(b))}

        result = function_method_parser(example_function)
        expected = {
            "name": "example_function",
            "input_params": [
                {"name": "a", "type": "Union[int, float]", "positional": True},
                {
                    "name": "b",
                    "type": "Union[str, None]",
                    "positional": False,
                    "default": None,
                },
            ],
            "output_params": [
                {
                    "name": "out",
                    "type": "Dict[str, Tuple[int, str]]",
                }
            ],
            "docstring": None,
        }
        self.assertEqual(result, expected)

    def test_function_method_parser_custom_return_type(self):
        from exposedfunctionality.function_parser import (
            SerializedFunction,
            function_method_parser,
        )

        def exp_func(a: int) -> SerializedFunction:
            pass

        result = function_method_parser(exp_func)
        expected = {
            "name": "exp_func",
            "input_params": [{"name": "a", "type": "int", "positional": True}],
            "output_params": [
                {
                    "name": "out",
                    "type": "exposedfunctionality.function_parser.types.SerializedFunction",
                }
            ],
            "docstring": None,
        }
        self.assertEqual(result, expected)

    def test_function_method_parser_no_hint(self):
        from exposedfunctionality.function_parser import function_method_parser

        # Test function with no type hints
        def no_hints(a, b):
            pass

        result = function_method_parser(no_hints)
        expected = {
            "name": "no_hints",
            "input_params": [
                {"name": "a", "type": "Any", "positional": True},
                {"name": "b", "type": "Any", "positional": True},
            ],
            "output_params": [],
            "docstring": None,
        }
        self.assertEqual(result, expected)

    def test_function_method_parser_return_None(self):
        from exposedfunctionality.function_parser import function_method_parser

        # Test function with return type of None
        def returns_none() -> None:
            pass

        result = function_method_parser(returns_none)
        expected = {
            "name": "returns_none",
            "input_params": [],
            "output_params": [],
            "docstring": None,
        }
        self.assertEqual(result, expected)

    def test_function_method_parser_unserializable_default(self):
        from exposedfunctionality.function_parser import (
            function_method_parser,
            FunctionParamError,
        )

        # Test unserializable default
        def unserializable_default(a={"unserializable": set()}):
            pass

        with self.assertRaises(FunctionParamError):
            function_method_parser(unserializable_default)

    def test_function_method_parser_param_from_docstring(self):
        from exposedfunctionality.function_parser import function_method_parser

        # Test function with type hint from docstring
        def docstring_type(a, b=1) -> int:
            """Args:
            a (int): This is an integer.
            b (int, optional): This is an optional integer. Defaults to 1

            Returns:
                int: the result.

            """
            pass

        result = function_method_parser(docstring_type)

        expected = {
            "name": "docstring_type",
            "input_params": [
                {
                    "name": "a",
                    "type": "int",
                    "positional": True,
                    "optional": False,
                    "description": "This is an integer.",
                },
                {
                    "default": 1,
                    "name": "b",
                    "type": "int",
                    "positional": False,
                    "optional": True,
                    "description": "This is an optional integer.",
                },
            ],
            "output_params": [
                {"description": "the result.", "name": "out", "type": "int"}
            ],
            "docstring": {
                "exceptions": {},
                "input_params": [
                    {
                        "name": "a",
                        "description": "This is an integer.",
                        "optional": False,
                        "type": "int",
                        "positional": True,
                    },
                    {
                        "default": 1,
                        "name": "b",
                        "description": "This is an optional integer.",
                        "optional": True,
                        "type": "int",
                        "positional": False,
                    },
                ],
                "output_params": [
                    {"description": "the result.", "name": "out", "type": "int"}
                ],
                "original": "Args:\na (int): This is an integer.\nb (int, optional): This is an optional integer. Defaults to 1\n\nReturns:\n    int: the result.",
            },
        }

        self.assertEqual(result, expected)

    def test_function_method_parser_param_from_docstring_with_diff(self):
        from exposedfunctionality.function_parser import function_method_parser

        # Test function with type hint from docstring
        def docstring_type(a: int, b=None):
            """Args:
            a (float): This is an integer.
            b (int, optional): This is an optional integer. Defaults to 1

            Returns:
                int: the result.
                float: the second result.

            """
            pass

        result = function_method_parser(docstring_type)

        expected = {
            "name": "docstring_type",
            "input_params": [
                {
                    "name": "a",
                    "type": "int",
                    "positional": True,
                    "optional": False,
                    "description": "This is an integer.",
                },
                {
                    "default": 1,
                    "name": "b",
                    "type": "int",
                    "positional": False,
                    "optional": True,
                    "description": "This is an optional integer.",
                },
            ],
            "output_params": [
                {"description": "the result.", "name": "out0", "type": "int"},
                {
                    "description": "the second result.",
                    "name": "out1",
                    "type": "float",
                },
            ],
            "docstring": {
                "exceptions": {},
                "input_params": [
                    {
                        "name": "a",
                        "description": "This is an integer.",
                        "optional": False,
                        "type": "float",
                        "positional": True,
                    },
                    {
                        "default": 1,
                        "name": "b",
                        "description": "This is an optional integer.",
                        "optional": True,
                        "type": "int",
                        "positional": False,
                    },
                ],
                "output_params": [
                    {"description": "the result.", "name": "out0", "type": "int"},
                    {
                        "description": "the second result.",
                        "name": "out1",
                        "type": "float",
                    },
                ],
                "original": "Args:\na (float): This is an integer.\nb (int, optional): This is an optional integer. Defaults to 1\n\nReturns:\n    int: the result.\n    float: the second result.",
            },
        }

        self.assertEqual(result, expected)


class TestGetResolvedSignature(unittest.TestCase):
    """Unit tests for the get_resolved_signature function."""

    def test_simple_function(self):
        """Test the behavior with simple functions with no preset arguments."""
        from exposedfunctionality.function_parser import get_resolved_signature

        def example(a, b=2):
            pass

        sig, base_func = get_resolved_signature(example)
        self.assertEqual(str(sig), "(a, b=2)")

    def test_partial_function(self):
        """Test the behavior with partial functions."""
        from exposedfunctionality.function_parser import get_resolved_signature

        def example(a, b, c=3):
            pass

        p = partial(example, 1)
        sig, base_func = get_resolved_signature(p)
        self.assertEqual(str(sig), "(b, c=3)")

    def test_nested_partial(self):
        """Test the behavior with nested partial functions."""
        from exposedfunctionality.function_parser import get_resolved_signature

        def example(a, b, c=3, d=4):
            pass

        p = partial(example, 1, d=5)
        p2 = partial(p, 2)
        sig, base_func = get_resolved_signature(p2)
        self.assertEqual(str(sig), "(c=3)")

    def test_class_method(self):
        """Test the behavior with class methods."""
        from exposedfunctionality.function_parser import get_resolved_signature

        class TestClass:
            def method(self, a, b):
                pass

        t = TestClass()
        sig, base_func = get_resolved_signature(t.method)
        self.assertEqual(str(sig), "(a, b)")

    def test_class_method_with_partial(self):
        """Test the behavior with class methods and partial preset arguments."""
        from exposedfunctionality.function_parser import get_resolved_signature

        class TestClass:
            def method(self, a, b, c=3):
                pass

        t = TestClass()
        p = partial(t.method, 1)
        sig, base_func = get_resolved_signature(p)
        self.assertEqual(str(sig), "(b, c=3)")

    def test_class_static_method(self):
        """Test the behavior with class static methods."""
        from exposedfunctionality.function_parser import get_resolved_signature

        class TestClass:
            @staticmethod
            def static_method(a, b):
                pass

        sig, base_func = get_resolved_signature(TestClass.static_method)
        self.assertEqual(str(sig), "(a, b)")

    def test_class_method_from_class(self):
        """Test the behavior with class methods not from instance."""
        from exposedfunctionality.function_parser import get_resolved_signature

        class TestClass:
            def method(self, a, b, c=3):
                pass

        sig, base_func = get_resolved_signature(TestClass.method)
        self.assertEqual(str(sig), "(a, b, c=3)")

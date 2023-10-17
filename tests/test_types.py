import unittest
from unittest.mock import patch, Mock


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

    @patch(
        f"exposedfunctionality.function_parser.types.__builtins__", new_callable=Mock
    )
    def test_string_to_type_with_module_builtins(self, mock_builtins):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
        )

        # Set __builtins__ to be a module mock
        mock_builtins.__class__ = Mock()
        # Mock the return value for getattr on the builtins module
        mock_int_type = int
        setattr(mock_builtins, "int", mock_int_type)

        # Test the function
        result = string_to_type("int")

        # Assert that the correct type was returned
        self.assertEqual(result, mock_int_type)

    # Test for non-existent modules
    def test_non_existent_module(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TypeNotFoundError,
        )

        with self.assertRaises(TypeNotFoundError):
            string_to_type("no_such_module.NoClass")

    # Test using the TYPE_GETTER mechanism
    def test_type_getter(self):
        from exposedfunctionality.function_parser.types import (
            string_to_type,
            TYPE_GETTER,
        )

        class CustomType:
            pass

        TYPE_GETTER["CustomType"] = CustomType

        self.assertEqual(string_to_type("CustomType"), CustomType)

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

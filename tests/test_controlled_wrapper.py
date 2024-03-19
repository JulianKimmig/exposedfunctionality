import unittest
from exposedfunctionality import controlled_wrapper, update_wrapper


class TestWrapperFunctions(unittest.TestCase):
    def setUp(self):
        # Sample functions to be used in tests
        def sample_function():
            """Sample function docstring."""
            pass

        def wrapper_function():
            pass

        self.sample_function = sample_function
        self.wrapper_function = wrapper_function

    def test_docstring_update(self):
        """Test if the wrapper function docstring is updated from the wrapped function."""
        wrapped = update_wrapper(self.wrapper_function, self.sample_function)
        self.assertEqual(wrapped.__doc__, self.sample_function.__doc__)

    def test_docstring_no_update_if_not_empty(self):
        """Test that the wrapper's docstring is not overwritten if it is not empty."""
        # Changing the wrapper function's docstring to non-empty
        self.wrapper_function.__doc__ = "Non-empty docstring"
        wrapped = update_wrapper(
            self.wrapper_function, self.sample_function, update_if_empty=()
        )
        self.assertEqual(wrapped.__doc__, "Non-empty docstring")

    def test_update_if_missing(self):
        """Test attribute update if missing in wrapper."""
        self.sample_function.custom_attribute = "Custom Value"
        wrapped = update_wrapper(self.wrapper_function, self.sample_function)
        self.assertTrue(hasattr(wrapped, "custom_attribute"))
        self.assertEqual(wrapped.custom_attribute, "Custom Value")

    def test_never_update(self):
        """Test that attributes listed in never_update are not updated."""
        self.sample_function.custom_attribute = "Custom Value"
        self.wrapper_function.custom_attribute = ""
        wrapped = update_wrapper(
            self.wrapper_function,
            self.sample_function,
            never_update=("custom_attribute",),
        )
        self.assertEqual(wrapped.custom_attribute, "")

    def test_update_always_with_dicts(self):
        """Test that dictionary attributes are updated, not replaced, when update_dicts is True."""
        self.sample_function.__dict__.update({"a": 1, "b": 2})
        self.wrapper_function.__dict__.update({"b": 3, "c": 4})
        wrapped = update_wrapper(self.wrapper_function, self.sample_function)
        self.assertEqual(
            {"a": wrapped.a, "b": wrapped.b, "c": wrapped.c}, {"a": 1, "b": 2, "c": 4}
        )

    def test_controlled_wrapper_usage(self):
        """Test using controlled_wrapper to create a decorator that updates wrapper functions."""

        @controlled_wrapper(self.sample_function)
        def new_wrapper_function():
            pass

        self.assertEqual(new_wrapper_function.__doc__, self.sample_function.__doc__)

# Tests for the exposed_var module
import unittest


class TestExposedValue(unittest.TestCase):
    """Tests for the ExposedValue descriptor."""

    def test_init_default_type(self):
        """Test the initialization with default type inference."""

        from exposedfunctionality import ExposedValue

        ev = ExposedValue("name", 10)
        self.assertEqual(ev.name, "name")
        self.assertEqual(ev.default, 10)
        self.assertEqual(ev.type, int)

    def test_init_explicit_type(self):
        """Test the initialization with default type inference."""

        from exposedfunctionality import ExposedValue

        ev = ExposedValue("name", 10, type_=float)
        self.assertEqual(ev.type, float)

        # Test conversions that are okay
        ExposedValue("name", 10.0, type_=int)
        ExposedValue("name", "10", type_=int)

        # Test conversions that should raise errors
        with self.assertRaises(TypeError):
            ExposedValue("name", "10.1", type_=int)

    def test_get(self):
        """Test getting the value using the descriptor."""
        from exposedfunctionality import ExposedValue

        class TestClass:
            attr = ExposedValue("attr", 10)

        tc = TestClass()
        self.assertEqual(tc.attr, 10)
        tc.attr = 20
        self.assertEqual(tc.attr, 20)

    def test_set(self):
        """Test getting the value using the descriptor."""
        from exposedfunctionality import ExposedValue

        class TestClass:
            attr = ExposedValue("attr", 10)

        tc = TestClass()

        # Try setting to an invalid value
        with self.assertRaises(TypeError):
            tc.attr = "invalid"

    def test_delete(self):
        """Test that deletion of the attribute is prevented."""

        from exposedfunctionality import ExposedValue

        class TestClass:
            attr = ExposedValue("attr", 10)

        tc = TestClass()
        with self.assertRaises(AttributeError):
            del tc.attr

    def test_repr(self):
        """Test that deletion of the attribute is prevented."""

        from exposedfunctionality import ExposedValue

        ev = ExposedValue("attr", 10)
        self.assertEqual(repr(ev), "ExposedValue(attr)")


class TestExposedValueFunctions(unittest.TestCase):
    """Test that deletion of the attribute is prevented."""

    def test_add_exposed_value_instance(self):
        """Test dynamically adding an ExposedValue to an instance."""

        from exposedfunctionality import add_exposed_value

        class TestClass:
            pass

        tc = TestClass()
        add_exposed_value(tc, "new_attr", 20, int)
        self.assertEqual(tc.new_attr, 20)
        tc.new_attr = 25
        self.assertEqual(tc.new_attr, 25)

        # Test if adding an already existing attribute raises error
        with self.assertRaises(AttributeError):
            add_exposed_value(tc, "new_attr", 30, int)

        # Try setting to an invalid value
        with self.assertRaises(TypeError):
            tc.new_attr = "invalid"

        self.assertEqual(tc.__class__.__name__, "_TestClass")

    def test_add_exposed_value_class(self):
        """Test dynamically adding an ExposedValue to a class."""
        from exposedfunctionality import add_exposed_value, get_exposed_values

        class TestClass:
            pass

        add_exposed_value(TestClass, "new_attr", 20, int)
        instance = TestClass()
        self.assertEqual(instance.new_attr, 20)

        # Test if adding an already existing attribute raises error
        with self.assertRaises(AttributeError):
            add_exposed_value(TestClass, "new_attr", 30, int)

    def test_get_exposed_values(self):
        # Test if adding an already existing attribute raises error
        from exposedfunctionality import (
            get_exposed_values,
            add_exposed_value,
            ExposedValue,
        )

        class TestClass:
            attr = ExposedValue("attr", 10)

        tc = TestClass()
        # Checking for existing attributes
        self.assertEqual(
            str(get_exposed_values(tc)), str({"attr": ExposedValue("attr", 10)})
        )
        self.assertEqual(
            str(get_exposed_values(TestClass)), str({"attr": ExposedValue("attr", 10)})
        )

        # Adding a new attribute and testing again
        add_exposed_value(tc, "new_attr", 20, int)
        self.assertEqual(
            str(get_exposed_values(tc)),
            str(
                {
                    "attr": ExposedValue("attr", 10),
                    "new_attr": ExposedValue("new_attr", 20),
                }
            ),
        )

    def test_disable_type_checking(self):
        """Test disabling type checking."""

        from exposedfunctionality import ExposedValue

        class TestClass:
            a = ExposedValue("a", 10, type_=None)

        tc = TestClass()
        self.assertEqual(tc.a, 10)
        tc.a = "string"
        self.assertEqual(tc.a, "string")

    def test_new_ins_from_inst_with_added_exposed(self):
        """Test creating a new instance from an instance with added ExposedValues."""

        from exposedfunctionality import (
            get_exposed_values,
            add_exposed_value,
            ExposedValue,
        )

        class TestClass:
            attr = ExposedValue("attr", 10)

        tc = TestClass()
        add_exposed_value(tc, "new_attr", 20, int)
        self.assertEqual(tc.__class__.__name__, "_TestClass")
        tc2 = tc.__class__()
        self.assertEqual(tc2.__class__.__name__, "_TestClass")

        def get_exposed_values_dict(obj):
            return {k: getattr(obj, k) for k, v in get_exposed_values(obj).items()}

        self.assertEqual(
            get_exposed_values_dict(tc2),
            {
                "attr": 10,
                "new_attr": 20,
            },
        )

        tc = TestClass()
        add_exposed_value(tc, "attr2", 10, int)
        tc.attr = 0
        tc2 = TestClass()
        tc.attr = 40
        self.assertEqual(tc2.attr, 10)
        tc2.attr = 20
        self.assertEqual(tc2.attr, 20)
        self.assertEqual(tc.attr, 40)

        tc3 = tc.__class__()
        self.assertEqual(tc3.attr2, 10)
        add_exposed_value(tc3, "attr3", 20, int)

        self.assertEqual(tc3.attr3, 20)
        self.assertEqual(tc3.__class__.__name__, "__TestClass")
        tc3.attr2 = 30

        self.assertEqual(get_exposed_values_dict(tc), {"attr2": 10, "attr": 40})
        self.assertEqual(get_exposed_values_dict(tc2), {"attr": 20})

        # Exposed values are added to the class dict on first access
        with self.assertRaises(KeyError):
            self.assertEqual(tc3.__dict__["attr"], 10)
        self.assertEqual(
            get_exposed_values_dict(tc3), {"attr": 10, "attr2": 30, "attr3": 20}
        )
        self.assertEqual(tc3.attr, 10)
        self.assertEqual(tc3.__dict__["attr"], 10)
        self.assertEqual(
            get_exposed_values_dict(tc3), {"attr": 10, "attr2": 30, "attr3": 20}
        )

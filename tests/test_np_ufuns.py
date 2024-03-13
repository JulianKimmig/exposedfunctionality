import unittest
from exposedfunctionality import (
    exposed_method,
    get_exposed_methods,
    assure_exposed_method,
    is_exposed_method,
)
import numpy as np

from exposedfunctionality.function_parser.docstring_parser import (
    select_extraction_function,
    parse_numpy_docstring,
)
from pprint import pprint


class TestExposedMethodDecorator(unittest.TestCase):
    def test_ufuncs_docstring(self):
        """Test that exposed_method adds the necessary metadata to a function."""
        f, summarycheck, ipsum, ipnamecheck, opsum, opnamecheck = (
            np.sin,
            "Trigonometric sine, element-wise.",
            3,
            ["x"],
            1,
            ["y"],
        )
        self.assertTrue(f.__doc__ is not None)
        prser = select_extraction_function(f.__doc__)
        self.assertTrue(prser is parse_numpy_docstring)
        parseddocs = parse_numpy_docstring(f.__doc__)
        self.assertTrue(
            summarycheck in parseddocs["summary"],
            parseddocs["summary"],
        )
        self.assertEqual(parseddocs["original"], f.__doc__)
        inputs = parseddocs["input_params"]
        self.assertEqual(len(inputs), ipsum)
        for i, n in enumerate(ipnamecheck):
            self.assertEqual(inputs[i]["name"], n)
        self.assertEqual(len(parseddocs["output_params"]), opsum)
        for i, n in enumerate(opnamecheck):
            self.assertEqual(parseddocs["output_params"][i]["name"], n)

    def test_ufunfs(self):
        """Test that exposed_method adds the necessary metadata to a function."""
        f = np.sin
        func = assure_exposed_method(f)
        self.assertTrue(is_exposed_method(func))
        self.assertTrue(func.ef_funcmeta["docstring"] is not None)
        print(func.ef_funcmeta["docstring"])

    def test_arange(self):
        """Test that exposed_method adds the necessary metadata to a function."""
        f = np.arange
        func = assure_exposed_method(f)
        self.assertTrue(is_exposed_method(func))
        self.assertTrue(func.ef_funcmeta["docstring"] is not None)

    def test_arange_docstring(self):
        """Test that exposed_method adds the necessary metadata to a function."""
        f, summarycheck, ipsum, ipnamecheck, opsum, opnamecheck = (
            np.arange,
            "Return evenly spaced values within a given interval.",
            5,
            ["start", "stop", "step"],
            1,
            ["arange"],
        )
        self.assertTrue(f.__doc__ is not None)
        prser = select_extraction_function(f.__doc__)

        self.assertTrue(prser is parse_numpy_docstring, prser)
        parseddocs = parse_numpy_docstring(f.__doc__)

        self.assertTrue(
            summarycheck in parseddocs["summary"],
            parseddocs["summary"],
        )
        self.assertEqual(parseddocs["original"], f.__doc__)
        inputs = parseddocs["input_params"]
        self.assertEqual(len(inputs), ipsum)
        for i, n in enumerate(ipnamecheck):
            self.assertEqual(inputs[i]["name"], n)
        self.assertEqual(len(parseddocs["output_params"]), opsum)
        for i, n in enumerate(opnamecheck):
            self.assertEqual(parseddocs["output_params"][i]["name"], n)

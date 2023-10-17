import unittest


class DoctringExtractionTests:
    BASIC_DOCSTRING: str
    JUST_SUMMARY: str = """
        Just a summary.
        """
    ONLY_PARAM: str
    ONLY_RETURN: str
    ONLY_EXCEPT: str
    P_WO_TYPE: str
    MULTI_EXCEPT: str
    NO_SUM: str
    MILTILINE_DESC: str

    def setUp(self) -> None:
        self.maxDiff = None
        return super().setUp()

    def get_parser(self):
        raise NotImplementedError()

    def test_basic_docstring(self):
        result = self.get_parser()(self.BASIC_DOCSTRING)
        expected = {
            "summary": "A basic function.",
            "input_params": [
                {
                    "name": "a",
                    "description": "The first parameter.",
                    "type": int,
                    "positional": False,
                    "optional": True,
                    "default": 1,
                },
                {
                    "name": "b",
                    "description": "The second parameter.",
                    "type": str,
                    "positional": True,
                    "optional": False,
                },
            ],
            "exceptions": {"ValueError": "When something is wrong."},
            "output_params": [
                {"description": "A string representation.", "type": str, "name": "out"}
            ],
            "original": self.BASIC_DOCSTRING,
        }

        self.assertEqual(result, expected)

    def test_only_summary(self):
        result = self.get_parser()(self.JUST_SUMMARY)
        expected = {
            "summary": "Just a summary.",
            "input_params": [],
            "output_params": [],
            "exceptions": {},
            "original": self.JUST_SUMMARY,
        }

        self.assertEqual(result, expected)

    def test_only_params(self):
        result = self.get_parser()(self.ONLY_PARAM)
        expected = {
            "summary": "Summary here.",
            "input_params": [
                {
                    "name": "a",
                    "description": "Description for a.",
                    "type": int,
                    "positional": True,
                    "optional": False,
                },
                {
                    "name": "b",
                    "description": "b is an optional integer.",
                    "type": int,
                    "positional": False,
                    "optional": True,
                },
            ],
            "output_params": [],
            "exceptions": {},
            "original": self.ONLY_PARAM,
        }
        self.assertEqual(result, expected)

    def test_only_return(self):
        result = self.get_parser()(self.ONLY_RETURN)
        expected = {
            "summary": "Summary for this one.",
            "input_params": [],
            "output_params": [
                {"description": "Some output.", "type": int, "name": "out"}
            ],
            "exceptions": {},
            "original": self.ONLY_RETURN,
        }
        self.assertEqual(result, expected)

    def test_only_exceptions(self):
        result = self.get_parser()(self.ONLY_EXCEPT)
        expected = {
            "summary": "Exception function.",
            "input_params": [],
            "output_params": [],
            "exceptions": {"ValueError": "If value is wrong."},
            "original": self.ONLY_EXCEPT,
        }
        self.assertEqual(result, expected)

    def test_params_without_type(self):
        result = self.get_parser()(self.P_WO_TYPE)
        expected = {
            "summary": "Function without types.",
            "input_params": [
                {
                    "name": "a",
                    "description": "Description for a.",
                    "positional": True,
                    "optional": False,
                },
                {
                    "name": "b",
                    "description": "Description for b.",
                    "positional": True,
                    "optional": False,
                },
            ],
            "output_params": [],
            "exceptions": {},
            "original": self.P_WO_TYPE,
        }
        self.assertEqual(result, expected)

    def test_multiple_exceptions(self):
        result = self.get_parser()(self.MULTI_EXCEPT)
        expected = {
            "summary": "Function with multiple exceptions.",
            "input_params": [],
            "output_params": [],
            "exceptions": {
                "ValueError": "If value is wrong.",
                "TypeError": "If type is wrong.",
            },
            "original": self.MULTI_EXCEPT,
        }
        self.assertEqual(result, expected)

    def test_no_summary(self):
        result = self.get_parser()(self.NO_SUM)
        expected = {
            "input_params": [
                {
                    "name": "a",
                    "description": "Description for a.",
                    "positional": True,
                    "optional": False,
                },
                {
                    "name": "b",
                    "description": "Description for b.",
                    "positional": True,
                    "optional": False,
                },
            ],
            "output_params": [],
            "exceptions": {},
            "original": self.NO_SUM,
        }
        self.assertEqual(result, expected)

    def test_multiline_descriptions(self):
        result = self.get_parser()(self.MILTILINE_DESC)

        expected = {
            "summary": "Function with multiline descriptions. Even the summary is multiline.",
            "input_params": [
                {
                    "name": "a",
                    "description": "Description for a. This continues.",
                    "positional": True,
                    "optional": False,
                },
                {
                    "name": "b",
                    "description": "Description for b.",
                    "positional": True,
                    "optional": False,
                },
            ],
            "output_params": [
                {
                    "description": "Some output. This continues.",
                    "type": int,
                    "name": "out",
                }
            ],
            "exceptions": {
                "ValueError": "If value is wrong. This explains why.",
                "TypeError": "If type is wrong.",
            },
            "original": self.MILTILINE_DESC,
        }

        self.assertEqual(result, expected)


class TestParseRestructuredDocstring(DoctringExtractionTests, unittest.TestCase):
    BASIC_DOCSTRING = """
        A basic function.
        
        :param a: The first parameter, defaults to '1'
        :type a: int, optional
        :param b: The second parameter
        :type b: str
        :raises ValueError: When something is wrong.
        :return: A string representation.
        :rtype: str
        """

    ONLY_PARAM = """
        Summary here.
        
        :param a: Description for a.
        :type a: int

        :param b: b is an optional integer.
        :type b: int, optional
        """

    ONLY_RETURN = """
        Summary for this one.
        
        :return: Some output.
        :rtype: int
        """

    ONLY_EXCEPT = """
        Exception function.
        
        :raises ValueError: If value is wrong.
        """

    P_WO_TYPE = """
        Function without types.
        
        :param a: Description for a.
        :param b: Description for b.
        """

    MULTI_EXCEPT = """
        Function with multiple exceptions.
        
        :raises ValueError: If value is wrong.
        :raises TypeError: If type is wrong.
        """

    NO_SUM = """
        :param a: Description for a.
        :param b: Description for b.
        """
    MILTILINE_DESC = """
        Function with multiline descriptions.
        Even the summary is multiline.

        :param a: Description for a.
            This continues.
        :param b: Description for b.
        
        :return: Some output.
            This continues.
        :rtype: int

        :raises ValueError: If value is wrong.
            This explains why.
        
        :raises TypeError: If type is wrong.
        """

    def get_parser(self):
        from exposedfunctionality.function_parser.docstring_parser import (
            parse_restructured_docstring,
        )

        return parse_restructured_docstring


class TestParseGoogleStyledDocstring(DoctringExtractionTests, unittest.TestCase):
    BASIC_DOCSTRING = """
        A basic function.
        
        Args:
            a (int, optional): The first parameter, defaults to "1".
            b (str): The second parameter.

        Raises:
            ValueError: When something is wrong.

        Returns:
            str: A string representation.
        """

    ONLY_PARAM = """
        Summary here.
        
        Args:
            a (int): Description for a.
            b (int, optional): b is an optional integer.
        """

    ONLY_RETURN = """
        Summary for this one.
        
        Returns:
            int: Some output.
        """

    ONLY_EXCEPT = """
        Exception function.
        
        Raises:
            ValueError: If value is wrong.
        """

    P_WO_TYPE = """
        Function without types.
        
        Args:
            a: Description for a.
            b: Description for b.
        """

    MULTI_EXCEPT = """
        Function with multiple exceptions.
        
        Raises:
            ValueError: If value is wrong.
            TypeError: If type is wrong.
        """

    NO_SUM = """
        Args:
            a: Description for a.
            b: Description for b.
        """

    MILTILINE_DESC = """
        Function with multiline descriptions.
        Even the summary is multiline.

        Args:
            a: Description for a.
                This continues.
            b: Description for b.

        Returns:
            int: Some output.
                This continues.

        Raises:
            ValueError: If value is wrong.
                This explains why.
            TypeError: If type is wrong.
        """

    def get_parser(self):
        from exposedfunctionality.function_parser.docstring_parser import (
            parse_google_docstring,
        )

        return parse_google_docstring


class TestAutoDetectRetring(DoctringExtractionTests, unittest.TestCase):
    BASIC_DOCSTRING = TestParseRestructuredDocstring.BASIC_DOCSTRING
    JUST_SUMMARY = TestParseRestructuredDocstring.JUST_SUMMARY
    ONLY_PARAM = TestParseRestructuredDocstring.ONLY_PARAM
    ONLY_RETURN = TestParseRestructuredDocstring.ONLY_RETURN
    ONLY_EXCEPT = TestParseRestructuredDocstring.ONLY_EXCEPT
    P_WO_TYPE = TestParseRestructuredDocstring.P_WO_TYPE
    MULTI_EXCEPT = TestParseRestructuredDocstring.MULTI_EXCEPT
    NO_SUM = TestParseRestructuredDocstring.NO_SUM
    MILTILINE_DESC = TestParseRestructuredDocstring.MILTILINE_DESC

    def get_parser(self):
        from exposedfunctionality.function_parser import (
            parse_docstring,
        )

        return parse_docstring


class TestAutoDetectGoogltring(DoctringExtractionTests, unittest.TestCase):
    BASIC_DOCSTRING = TestParseGoogleStyledDocstring.BASIC_DOCSTRING
    JUST_SUMMARY = TestParseGoogleStyledDocstring.JUST_SUMMARY
    ONLY_PARAM = TestParseGoogleStyledDocstring.ONLY_PARAM
    ONLY_RETURN = TestParseGoogleStyledDocstring.ONLY_RETURN
    ONLY_EXCEPT = TestParseGoogleStyledDocstring.ONLY_EXCEPT
    P_WO_TYPE = TestParseGoogleStyledDocstring.P_WO_TYPE
    MULTI_EXCEPT = TestParseGoogleStyledDocstring.MULTI_EXCEPT
    NO_SUM = TestParseGoogleStyledDocstring.NO_SUM
    MILTILINE_DESC = TestParseGoogleStyledDocstring.MILTILINE_DESC

    def get_parser(self):
        from exposedfunctionality.function_parser import parse_docstring

        return parse_docstring

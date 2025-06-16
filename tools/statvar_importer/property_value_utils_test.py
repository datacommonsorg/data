# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from property_value_utils import is_valid_property, is_valid_value, is_schema_node, has_namespace, add_key_value


class TestIsValidProperty(unittest.TestCase):

    def test_valid_lower_camel_case(self):
        self.assertTrue(is_valid_property("measuredProperty"))

    def test_valid_single_word(self):
        self.assertTrue(is_valid_property("population"))

    def test_schemaless_upper_camel_case(self):
        self.assertTrue(is_valid_property("Observation", schemaless=True))

    def test_schemaless_single_word_capitalized(self):
        self.assertTrue(is_valid_property("Person", schemaless=True))

    def test_invalid_upper_camel_case_without_schemaless(self):
        self.assertFalse(is_valid_property("Observation"))

    def test_invalid_single_word_capitalized_without_schemaless(self):
        self.assertFalse(is_valid_property("Person"))

    def test_invalid_leading_underscore(self):
        self.assertFalse(is_valid_property("_invalid"))

    def test_invalid_leading_number(self):
        self.assertFalse(is_valid_property("123invalid"))

    def test_invalid_none(self):
        self.assertFalse(is_valid_property(None))

    def test_invalid_empty_string(self):
        self.assertFalse(is_valid_property(""))


class TestIsValidValue(unittest.TestCase):

    def test_valid_string(self):
        self.assertTrue(is_valid_value("someValue"))

    def test_valid_integer(self):
        self.assertTrue(is_valid_value(123))

    def test_invalid_none(self):
        self.assertFalse(is_valid_value(None))

    def test_invalid_empty_string(self):
        self.assertFalse(is_valid_value(""))

    def test_invalid_unresolved_curly_braces(self):
        self.assertFalse(is_valid_value('{unresolved}'))

    def test_invalid_unresolved_at_symbol(self):
        self.assertFalse(is_valid_value('@unresolved'))


class TestIsSchemaNode(unittest.TestCase):

    def test_valid_with_schema_prefix(self):
        self.assertTrue(is_schema_node("schema:Person"))

    def test_valid_with_dcid_prefix(self):
        self.assertTrue(is_schema_node("dcid:country/USA"))

    def test_valid_with_brackets(self):
        self.assertTrue(is_schema_node("[1 2 3]"))

    def test_invalid_with_hyphen(self):
        self.assertFalse(is_schema_node("invalid-node"))

    def test_invalid_integer(self):
        self.assertFalse(is_schema_node(123))

    def test_invalid_none(self):
        self.assertFalse(is_schema_node(None))

    def test_invalid_empty_string(self):
        self.assertFalse(is_schema_node(""))


class TestHasNamespace(unittest.TestCase):

    def test_valid_dcid_prefix(self):
        self.assertTrue(has_namespace("dcid:country/USA"))

    def test_valid_schema_prefix(self):
        self.assertTrue(has_namespace("schema:Person"))

    def test_no_prefix(self):
        self.assertFalse(has_namespace("country/USA"))

    def test_prefix_only(self):
        self.assertTrue(has_namespace("dcid:"))

    def test_leading_colon(self):
        self.assertFalse(has_namespace(":no_namespace"))

    def test_none(self):
        self.assertFalse(has_namespace(None))

    def test_empty_string(self):
        self.assertFalse(has_namespace(""))


if __name__ == '__main__':
    unittest.main()

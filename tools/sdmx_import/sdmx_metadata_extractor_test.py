#!/usr/bin/env python3

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Unit tests for SDMX metadata extractor.

Tests the extraction of SDMX metadata from XML files and validation
against expected JSON output format.
"""

import json
import os
import unittest
from typing import Dict, Any

from sdmx_metadata_extractor import extract_dataflow_metadata_from_file


class TestSdmxMetadataExtractor(unittest.TestCase):
    """Test cases for SDMX metadata extraction functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = os.path.dirname(__file__)
        self.testdata_dir = os.path.join(self.test_dir, "testdata")

    def _load_expected_json(self, filename: str) -> Dict[str, Any]:
        """Load expected JSON from testdata directory."""
        filepath = os.path.join(self.testdata_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_testdata_path(self, filename: str) -> str:
        """Get full path to test data file."""
        return os.path.join(self.testdata_dir, filename)

    def assert_json_equal(self,
                          actual: Dict[str, Any],
                          expected: Dict[str, Any],
                          path: str = ""):
        """
        Assert that two JSON structures are equal with helpful error messages.

        Args:
            actual: The actual JSON structure
            expected: The expected JSON structure
            path: Current path in the JSON structure for error reporting
        """
        if isinstance(expected, dict) and isinstance(actual, dict):
            # Check for missing keys
            missing_keys = set(expected.keys()) - set(actual.keys())
            if missing_keys:
                self.fail(f"Missing keys at {path}: {missing_keys}")

            # Check for extra keys
            extra_keys = set(actual.keys()) - set(expected.keys())
            if extra_keys:
                self.fail(f"Extra keys at {path}: {extra_keys}")

            # Recursively check each key
            for key in expected.keys():
                new_path = f"{path}.{key}" if path else key
                self.assert_json_equal(actual[key], expected[key], new_path)

        elif isinstance(expected, list) and isinstance(actual, list):
            if len(actual) != len(expected):
                self.fail(
                    f"List length mismatch at {path}: expected {len(expected)}, got {len(actual)}"
                )

            for i, (actual_item,
                    expected_item) in enumerate(zip(actual, expected)):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                self.assert_json_equal(actual_item, expected_item, new_path)

        else:
            if actual != expected:
                self.fail(
                    f"Value mismatch at {path}: expected {expected!r}, got {actual!r}"
                )

    def test_basic_dataflow_extraction(self):
        """Test extraction of a generic dataflow structure."""
        # Extract metadata from generic XML file (renamed from ECB but content is generic)
        xml_path = self._get_testdata_path("generic_full_structure.xml")
        actual_result = extract_dataflow_metadata_from_file(xml_path, "EXR")

        # Check basic structure
        self.assertIn("dataflow", actual_result)
        dataflow = actual_result["dataflow"]

        # Check dataflow properties
        self.assertEqual(dataflow["id"], "EXR")
        self.assertIn("data_structure_definition", dataflow)

        # Check that we have dimensions
        dsd = dataflow["data_structure_definition"]
        self.assertIsInstance(dsd["dimensions"], list)
        self.assertGreater(len(dsd["dimensions"]), 0)

        # Check that we have concept schemes
        self.assertIsInstance(dataflow["referenced_concept_schemes"], list)
        self.assertGreater(len(dataflow["referenced_concept_schemes"]), 0)

    def test_dataflow_not_found(self):
        """Test error handling when dataflow ID is not found in XML."""
        xml_path = self._get_testdata_path("generic_full_structure.xml")

        with self.assertRaises(ValueError) as context:
            extract_dataflow_metadata_from_file(xml_path, "NONEXISTENT_DF")

        self.assertIn("not found in the structure message",
                      str(context.exception))

    def test_file_not_found(self):
        """Test error handling when XML file does not exist."""
        nonexistent_path = self._get_testdata_path("nonexistent.xml")

        with self.assertRaises(FileNotFoundError):
            extract_dataflow_metadata_from_file(nonexistent_path, "EXR")

    def test_dataclass_serialization(self):
        """Test that dataclasses are properly serialized to dictionaries."""
        xml_path = self._get_testdata_path("generic_full_structure.xml")
        result = extract_dataflow_metadata_from_file(xml_path, "EXR")

        # Check that result is a dictionary (not a dataclass instance)
        self.assertIsInstance(result, dict)

        # Check main structure
        self.assertIn("dataflow", result)
        self.assertIsInstance(result["dataflow"], dict)

        # Check that nested structures are also dictionaries
        dataflow = result["dataflow"]
        if "data_structure_definition" in dataflow and dataflow[
                "data_structure_definition"]:
            dsd = dataflow["data_structure_definition"]
            self.assertIsInstance(dsd, dict)

            # Check dimensions
            if "dimensions" in dsd:
                self.assertIsInstance(dsd["dimensions"], list)
                for dim in dsd["dimensions"]:
                    self.assertIsInstance(dim, dict)

    def test_concept_extraction(self):
        """Test that concepts are correctly extracted from concept schemes."""
        xml_path = self._get_testdata_path("generic_full_structure.xml")
        result = extract_dataflow_metadata_from_file(xml_path, "EXR")

        # Check concept schemes
        dataflow = result["dataflow"]
        concept_schemes = dataflow["referenced_concept_schemes"]

        self.assertGreater(len(concept_schemes), 0)

        # Check that concepts are present in at least one scheme
        found_concepts = False
        for scheme in concept_schemes:
            if scheme["concepts"]:
                found_concepts = True
                concepts = scheme["concepts"]
                # Check that we have some concepts
                self.assertGreater(len(concepts), 0)
                # Check that concepts have required fields
                for concept in concepts[:3]:  # Check first 3
                    self.assertIn("id", concept)
                    self.assertIn("concept_scheme_id", concept)
                break

        self.assertTrue(found_concepts, "No concepts found in any scheme")

    def test_codelist_extraction(self):
        """Test that codelists and codes are correctly extracted."""
        xml_path = self._get_testdata_path("generic_full_structure.xml")
        result = extract_dataflow_metadata_from_file(xml_path, "EXR")

        # Check dimensions with codelists
        dsd = result["dataflow"]["data_structure_definition"]
        dimensions = dsd["dimensions"]

        # Find a dimension with enumerated representation
        enumerated_dim = None
        for dim in dimensions:
            if dim["representation"] and dim["representation"][
                    "type"] == "enumerated":
                enumerated_dim = dim
                break

        self.assertIsNotNone(enumerated_dim, "No enumerated dimension found")

        # Check codelist
        representation = enumerated_dim["representation"]
        self.assertEqual(representation["type"], "enumerated")

        codelist = representation["codelist"]
        self.assertIsNotNone(codelist)
        self.assertIn("id", codelist)

        # Check codes if they exist
        if codelist["codes"]:
            codes = codelist["codes"]
            self.assertGreater(len(codes), 0)
            # Check that codes have required fields
            for code in codes[:3]:  # Check first 3
                self.assertIn("id", code)

    def test_empty_facets_list(self):
        """Test that enumerated representations have empty facets list."""
        xml_path = self._get_testdata_path("generic_full_structure.xml")
        result = extract_dataflow_metadata_from_file(xml_path, "EXR")

        # Check that enumerated representations have empty facets
        dsd = result["dataflow"]["data_structure_definition"]
        for dimension in dsd["dimensions"]:
            if dimension["representation"] and dimension["representation"][
                    "type"] == "enumerated":
                self.assertEqual(dimension["representation"]["facets"], [])


if __name__ == "__main__":
    unittest.main()

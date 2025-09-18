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
Unit tests for SDMX 2.1 metadata extractor.

Tests the extraction of SDMX metadata from XML files and validation
against expected JSON output format using SDMX 2.1 standard.
"""

import json
import os
import unittest
from typing import Dict, Any

from sdmx_metadata_extractor import extract_dataflow_metadata_from_file


class TestSdmxV21MetadataExtractor(unittest.TestCase):
    """Test cases for SDMX 2.1 metadata extraction functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = os.path.dirname(__file__)
        self.testdata_dir = os.path.join(self.test_dir, "testdata", "sdmx_2_1")
        self.sample_xml_file = "sample_dataflow_sdmx2_1.xml"
        self.expected_json_file = "expected_sample_dataflow_output.json"
        self.dataflow_id = "SAMPLE_DATA"

    def _get_testdata_path(self, filename: str) -> str:
        """Get full path to test data file."""
        return os.path.join(self.testdata_dir, filename)

    def _load_expected_json(self) -> Dict[str, Any]:
        """Load expected JSON output from testdata directory."""
        filepath = self._get_testdata_path(self.expected_json_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

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

    def test_complete_metadata_extraction(self):
        """Test complete metadata extraction against expected JSON output."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        actual_result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)
        expected_result = self._load_expected_json()

        # Compare entire structure against expected output
        self.assert_json_equal(actual_result, expected_result)

    def test_basic_dataflow_structure(self):
        """Test basic dataflow structure and properties."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        # Check basic structure
        self.assertIn("dataflow", result)
        dataflow = result["dataflow"]

        # Check dataflow properties
        self.assertEqual(dataflow["id"], self.dataflow_id)
        self.assertIn("data_structure_definition", dataflow)
        self.assertIn("referenced_concept_schemes", dataflow)

        # Check DSD structure
        dsd = dataflow["data_structure_definition"]
        self.assertEqual(dsd["id"], "SAMPLE_DSD")
        self.assertIn("dimensions", dsd)
        self.assertIn("attributes", dsd)
        self.assertIn("measures", dsd)

    def test_dimensions_structure(self):
        """Test that dimensions are correctly extracted."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        dsd = result["dataflow"]["data_structure_definition"]
        dimensions = dsd["dimensions"]

        # Should have 3 dimensions: FREQ, GEO, INDICATOR
        self.assertEqual(len(dimensions), 3)

        # Check dimension IDs
        dimension_ids = [dim["id"] for dim in dimensions]
        expected_ids = ["FREQ", "GEO", "INDICATOR"]
        self.assertEqual(dimension_ids, expected_ids)

        # Check that each dimension has required structure
        for dim in dimensions:
            self.assertIn("id", dim)
            self.assertIn("concept", dim)
            self.assertIn("representation", dim)

            # Should have concept with correct scheme
            concept = dim["concept"]
            self.assertIn("id", concept)
            self.assertEqual(concept["concept_scheme_id"], "SAMPLE_CONCEPTS")

            # Should have enumerated representation
            rep = dim["representation"]
            self.assertEqual(rep["type"], "enumerated")
            self.assertIn("codelist", rep)
            self.assertEqual(rep["facets"], [])

    def test_attributes_structure(self):
        """Test that attributes are correctly extracted."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        dsd = result["dataflow"]["data_structure_definition"]
        attributes = dsd["attributes"]

        # Should have 1 attribute: OBS_STATUS
        self.assertEqual(len(attributes), 1)

        attr = attributes[0]
        self.assertEqual(attr["id"], "OBS_STATUS")
        self.assertIn("concept", attr)
        self.assertIn("representation", attr)

        # Check concept
        concept = attr["concept"]
        self.assertEqual(concept["id"], "OBS_STATUS")
        self.assertEqual(concept["concept_scheme_id"], "SAMPLE_CONCEPTS")

        # Check representation
        rep = attr["representation"]
        self.assertEqual(rep["type"], "enumerated")
        self.assertIn("codelist", rep)

    def test_measures_structure(self):
        """Test that measures are correctly extracted."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        dsd = result["dataflow"]["data_structure_definition"]
        measures = dsd["measures"]

        # Should have 1 measure: OBS_VALUE
        self.assertEqual(len(measures), 1)

        measure = measures[0]
        self.assertEqual(measure["id"], "OBS_VALUE")
        self.assertIn("concept", measure)
        self.assertIn("representation", measure)

        # Check concept
        concept = measure["concept"]
        self.assertEqual(concept["id"], "OBS_VALUE")
        self.assertEqual(concept["concept_scheme_id"], "SAMPLE_CONCEPTS")

        # Check representation (should be non-enumerated for measures)
        rep = measure["representation"]
        self.assertEqual(rep["type"], "non-enumerated")
        self.assertIsNone(rep["codelist"])

    def test_concept_schemes_structure(self):
        """Test that concept schemes are correctly extracted."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        concept_schemes = result["dataflow"]["referenced_concept_schemes"]

        # Should have 1 concept scheme: SAMPLE_CONCEPTS
        self.assertEqual(len(concept_schemes), 1)

        scheme = concept_schemes[0]
        self.assertEqual(scheme["id"], "SAMPLE_CONCEPTS")
        self.assertIn("concepts", scheme)

        # Check concepts in the scheme
        concepts = scheme["concepts"]
        self.assertEqual(len(concepts), 5)  # FREQ, GEO, INDICATOR, OBS_VALUE, OBS_STATUS

        concept_ids = [concept["id"] for concept in concepts]
        expected_concept_ids = ["FREQ", "GEO", "INDICATOR", "OBS_VALUE", "OBS_STATUS"]
        self.assertEqual(set(concept_ids), set(expected_concept_ids))

        # Check that each concept has required fields
        for concept in concepts:
            self.assertIn("id", concept)
            self.assertEqual(concept["concept_scheme_id"], "SAMPLE_CONCEPTS")

    def test_codelist_structure(self):
        """Test that codelists are correctly extracted."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        dsd = result["dataflow"]["data_structure_definition"]

        # Check FREQ dimension codelist
        freq_dim = next(dim for dim in dsd["dimensions"] if dim["id"] == "FREQ")
        freq_codelist = freq_dim["representation"]["codelist"]

        self.assertEqual(freq_codelist["id"], "CL_FREQ")
        self.assertIn("codes", freq_codelist)

        # Should have 3 codes: A, Q, M
        codes = freq_codelist["codes"]
        self.assertEqual(len(codes), 3)

        code_ids = [code["id"] for code in codes]
        expected_code_ids = ["A", "Q", "M"]
        self.assertEqual(code_ids, expected_code_ids)

    def test_dataclass_serialization(self):
        """Test that dataclasses are properly serialized to dictionaries."""
        xml_path = self._get_testdata_path(self.sample_xml_file)
        result = extract_dataflow_metadata_from_file(xml_path, self.dataflow_id)

        # Check that result is a dictionary (not a dataclass instance)
        self.assertIsInstance(result, dict)

        # Check main structure
        self.assertIn("dataflow", result)
        self.assertIsInstance(result["dataflow"], dict)

        # Check that nested structures are also dictionaries
        dataflow = result["dataflow"]
        dsd = dataflow["data_structure_definition"]
        self.assertIsInstance(dsd, dict)

        # Check dimensions
        self.assertIsInstance(dsd["dimensions"], list)
        for dim in dsd["dimensions"]:
            self.assertIsInstance(dim, dict)

    def test_dataflow_not_found(self):
        """Test error handling when dataflow ID is not found in XML."""
        xml_path = self._get_testdata_path(self.sample_xml_file)

        with self.assertRaises(ValueError) as context:
            extract_dataflow_metadata_from_file(xml_path, "NONEXISTENT_DF")

        self.assertIn("not found in the structure message",
                      str(context.exception))

    def test_file_not_found(self):
        """Test error handling when XML file does not exist."""
        nonexistent_path = self._get_testdata_path("nonexistent.xml")

        with self.assertRaises(FileNotFoundError):
            extract_dataflow_metadata_from_file(nonexistent_path, self.dataflow_id)


if __name__ == "__main__":
    unittest.main()
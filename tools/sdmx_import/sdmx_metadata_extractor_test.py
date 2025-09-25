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
import sys
import tempfile
import unittest
from typing import Dict, Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from sdmx_metadata_extractor import extract_dataflow_metadata


class TestSdmxV21MetadataExtractor(unittest.TestCase):
    """Test cases for SDMX 2.1 metadata extraction functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = os.path.dirname(__file__)
        self.testdata_dir = os.path.join(self.test_dir, "testdata", "sdmx_2_1")
        self.sample_xml_file = "sample_dataflow_sdmx2_1.xml"
        self.expected_json_file = "expected_sample_dataflow_output.json"

    def _get_testdata_path(self, filename: str) -> str:
        """Get full path to test data file."""
        return os.path.join(self.testdata_dir, filename)

    def _load_expected_json(self) -> Dict[str, Any]:
        """Load expected JSON output from testdata directory."""
        filepath = self._get_testdata_path(self.expected_json_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_complete_metadata_extraction(self):
        """Test complete metadata extraction against expected JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = os.path.join(tmpdir, "output.json")
            xml_path = self._get_testdata_path(self.sample_xml_file)
            extract_dataflow_metadata(xml_path, temp_output)

            # Load both JSON files and compare
            with open(temp_output, encoding='utf-8') as f:
                actual_result = json.load(f)
            expected_result = self._load_expected_json()
            self.assertEqual(actual_result, expected_result)

    def test_file_not_found(self):
        """Test error handling when XML file does not exist."""
        nonexistent_path = self._get_testdata_path("nonexistent.xml")
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_output = os.path.join(tmpdir, "output.json")
            with self.assertRaises(FileNotFoundError):
                extract_dataflow_metadata(nonexistent_path, temp_output)


if __name__ == "__main__":
    unittest.main()

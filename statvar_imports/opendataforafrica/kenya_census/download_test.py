# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hermetic unit tests for download.py."""

import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from download import (
    ALL_DATASETS,
    GCS_BUCKET_DIR,
    convert_sdmx_xml_to_dataframe,
    process_xml_file,
    pull_from_gcs,
)


class DownloadTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_datasets_completeness(self):
        expected_datasets = [
            'dlrrjxg', 'egdxgkd', 'emxkej', 'fwjfdnc', 'gxbucsd', 'ixdvqrf',
            'rsfzlbg', 'srricmg', 'tdxdksf', 'vdbvyfd', 'welrttb', 'xszlbb'
        ]
        self.assertEqual(sorted(ALL_DATASETS), sorted(expected_datasets))
        self.assertEqual(len(ALL_DATASETS), 12)

    def test_convert_sdmx_xml_to_dataframe_success(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <Series SEX="M" AGE_GROUP="Y15-24" FREQ="A">
    <Obs TIME_PERIOD="2019" OBS_VALUE="12345"/>
    <Obs TIME_PERIOD="2020" OBS_VALUE="12890"/>
  </Series>
  <Series SEX="F" AGE_GROUP="Y15-24" FREQ="A">
    <Obs TIME_PERIOD="2019" OBS_VALUE="11900"/>
  </Series>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "sample.xml")
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("SEX", df.columns)
        self.assertIn("AGE_GROUP", df.columns)
        self.assertIn("TIME_PERIOD", df.columns)
        self.assertIn("OBS_VALUE", df.columns)
        self.assertEqual(df.iloc[0]["SEX"], "M")
        self.assertEqual(df.iloc[0]["OBS_VALUE"], "12345")
        self.assertEqual(df.iloc[2]["SEX"], "F")

    def test_convert_sdmx_xml_to_dataframe_invalid_xml(self):
        xml_file = os.path.join(self.test_dir.name, "invalid.xml")
        with open(xml_file, "w") as f:
            f.write("This is not valid XML <tag>")

        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIn("Failed to parse XML file", str(ctx.exception))

    def test_convert_sdmx_xml_to_dataframe_empty_xml(self):
        empty_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <message:Header>
    <message:ID>Empty</message:ID>
  </message:Header>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "empty.xml")
        with open(xml_file, "w") as f:
            f.write(empty_xml)

        with self.assertRaises(ValueError) as ctx:
            convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIn("No <Series> or <Obs> records found", str(ctx.exception))

    def test_process_xml_file_atomic_write(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
  <Series INDICATOR="IND1" FREQ="A">
    <Obs TIME_PERIOD="2022" OBS_VALUE="500"/>
  </Series>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "test_table.xml")
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        out_csv = os.path.join(self.test_dir.name, "output_subdir", "test_table.csv")
        df = process_xml_file(xml_file, out_csv)

        self.assertTrue(os.path.exists(out_csv))
        self.assertTrue(os.path.getsize(out_csv) > 0)
        read_df = pd.read_csv(out_csv)
        self.assertEqual(len(read_df), 1)
        self.assertEqual(read_df.iloc[0]["OBS_VALUE"], 500)

    @patch("subprocess.check_call")
    def test_pull_from_gcs_success(self, mock_check_call):
        out_dir = os.path.join(self.test_dir.name, "gcs_inputs")
        pull_from_gcs(out_dir)

        mock_check_call.assert_called_once_with(
            ["gcloud", "storage", "cp", "--recursive", f"{GCS_BUCKET_DIR}/*", out_dir]
        )
        self.assertTrue(os.path.exists(out_dir))

    @patch("subprocess.check_call")
    def test_pull_from_gcs_failure_propagates(self, mock_check_call):
        mock_check_call.side_effect = subprocess.CalledProcessError(1, ["gcloud"])
        out_dir = os.path.join(self.test_dir.name, "gcs_inputs_fail")

        with self.assertRaises(subprocess.CalledProcessError):
            pull_from_gcs(out_dir)


if __name__ == "__main__":
    unittest.main()

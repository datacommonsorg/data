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
"""Hermetic unit tests for convert_sdmx_xml_to_csv.py."""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from convert_sdmx_xml_to_csv import (
    convert_sdmx_xml_to_dataframe,
    convert_sdmx_xml_to_csv,
    main,
)


class ConvertSdmxXmlToCsvTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_convert_sdmx_xml_to_dataframe_sdmx_primary(self):
        """Tests parsing standard SDMX-ML XML via sdmx1."""
        sample_sdmx_xml = """<?xml version="1.0" encoding="utf-8"?>
<message:StructureSpecificData
  xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
  xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Header>
    <message:ID>TEST</message:ID>
    <message:Test>false</message:Test>
    <message:Prepared>2026-10-09T00:00:00</message:Prepared>
    <message:Sender id="TEST"/>
    <message:Structure structureID="STR1" dimensionAtObservation="TIME_PERIOD">
      <common:Structure>
        <Ref agencyID="KNBS" id="DSD1" version="1.0"/>
      </common:Structure>
    </message:Structure>
  </message:Header>
  <message:DataSet structureRef="STR1">
    <Series SEX="M" AGE_GROUP="Y15-24" FREQ="A">
      <Obs TIME_PERIOD="2019" OBS_VALUE="12345"/>
      <Obs TIME_PERIOD="2020" OBS_VALUE="12890"/>
    </Series>
    <Series SEX="F" AGE_GROUP="Y15-24" FREQ="A">
      <Obs TIME_PERIOD="2019" OBS_VALUE="11900"/>
    </Series>
  </message:DataSet>
</message:StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "sample_sdmx.xml")
        with open(xml_file, "w") as f:
            f.write(sample_sdmx_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("SEX", df.columns)
        self.assertIn("AGE_GROUP", df.columns)
        self.assertIn("TIME_PERIOD", df.columns)
        self.assertIn("OBS_VALUE", df.columns)

    def test_convert_sdmx_xml_to_dataframe_fallback(self):
        """Tests fallback to ElementTree when XML lacks SDMX structure headers."""
        sample_fallback_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series REGION="KEN" FREQ="A">
      <Obs TIME_PERIOD="2020" OBS_VALUE="47564296"/>
      <Obs TIME_PERIOD="2021" OBS_VALUE="48500000"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "sample_fallback.xml")
        with open(xml_file, "w") as f:
            f.write(sample_fallback_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn("REGION", df.columns)
        self.assertIn("OBS_VALUE", df.columns)
        self.assertEqual(df.iloc[0]["OBS_VALUE"], "47564296")

    def test_convert_sdmx_xml_to_dataframe_lowercase_columns(self):
        """Tests that column names with lowercase or @ prefix are normalized."""
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series region="KEN" freq="A">
      <Obs time_period="2021" value="1234"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "sample_lowercase.xml")
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        df = convert_sdmx_xml_to_dataframe(xml_file)
        self.assertIn("REGION", df.columns)
        self.assertIn("FREQ", df.columns)
        self.assertIn("TIME_PERIOD", df.columns)
        self.assertIn("OBS_VALUE", df.columns)

    def test_convert_sdmx_xml_to_dataframe_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            convert_sdmx_xml_to_dataframe(
                os.path.join(self.test_dir.name, "nonexistent.xml"))

    def test_convert_sdmx_xml_to_csv(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series INDICATOR="TEST" FREQ="A">
      <Obs TIME_PERIOD="2022" OBS_VALUE="999"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "test_table.xml")
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        out_csv = os.path.join(self.test_dir.name, "output_subdir",
                               "test_table.csv")
        convert_sdmx_xml_to_csv(xml_file, out_csv)
        self.assertTrue(os.path.isfile(out_csv))
        df = pd.read_csv(out_csv)
        self.assertEqual(len(df), 1)
        self.assertIn("OBS_VALUE", df.columns)
        self.assertEqual(int(df.iloc[0]["OBS_VALUE"]), 999)

    def test_main_input_file_success(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series REGION="KEN" FREQ="A">
      <Obs TIME_PERIOD="2022" OBS_VALUE="5000"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_file = os.path.join(self.test_dir.name, "egdxgkd.xml")
        with open(xml_file, "w") as f:
            f.write(sample_xml)

        out_dir = os.path.join(self.test_dir.name, "cli_output")
        with patch.object(
                sys,
                "argv",
            [
                "convert_sdmx_xml_to_csv.py",
                "--input_file",
                xml_file,
                "--output_dir",
                out_dir,
            ],
        ):
            main()

        expected_csv = os.path.join(out_dir, "egdxgkd.csv")
        self.assertTrue(os.path.isfile(expected_csv))
        df = pd.read_csv(expected_csv)
        self.assertEqual(len(df), 1)

    def test_main_input_file_not_found(self):
        nonexistent = os.path.join(self.test_dir.name, "nonexistent.xml")
        with patch.object(
                sys, "argv",
            ["convert_sdmx_xml_to_csv.py", "--input_file", nonexistent]):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 1)

    def test_main_xml_dir_success(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<StructureSpecificData>
  <DataSet>
    <Series REGION="KEN" FREQ="A">
      <Obs TIME_PERIOD="2022" OBS_VALUE="100"/>
    </Series>
  </DataSet>
</StructureSpecificData>
"""
        xml_dir = os.path.join(self.test_dir.name, "xml_inputs")
        os.makedirs(xml_dir, exist_ok=True)
        with open(os.path.join(xml_dir, "test1.xml"), "w") as f:
            f.write(sample_xml)

        out_dir = os.path.join(self.test_dir.name, "batch_output")
        with patch.object(
                sys,
                "argv",
            [
                "convert_sdmx_xml_to_csv.py", "--xml_dir", xml_dir,
                "--output_dir", out_dir
            ],
        ):
            main()

        expected_csv = os.path.join(out_dir, "test1.csv")
        self.assertTrue(os.path.isfile(expected_csv))
        df = pd.read_csv(expected_csv)
        self.assertEqual(len(df), 1)

    def test_main_no_args_exits_with_error(self):
        with patch.object(sys, "argv", ["convert_sdmx_xml_to_csv.py"]):
            with self.assertRaises(SystemExit) as ctx:
                main()
            self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

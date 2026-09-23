# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Script to automate testing for CDC PRAMS Excel processing pipeline.
"""
import io
import os
import sys
import tempfile
import unittest
import pandas as pd

MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, MODULE_DIR)

from process import USPrams

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    Unit test class verifying that the Excel processing pipeline produces
    exact CSV, MCF, and TMCF files matching the expected test fixtures.
    """

    @classmethod
    def setUpClass(cls):
        test_data_files = [
            'PRAMS-MCH-Indicators-Test.xlsx'
        ]
        ip_data = [
            os.path.join(TEST_DATASET_DIR, file_name)
            for file_name in test_data_files
        ]
        cls.tmp_dir = tempfile.TemporaryDirectory()

        base = USPrams(ip_data, output_location=cls.tmp_dir.name)
        base.process()

        csv_path = os.path.join(cls.tmp_dir.name, "PRAMS.csv")
        mcf_path = os.path.join(cls.tmp_dir.name, "PRAMS.mcf")
        tmcf_path = os.path.join(cls.tmp_dir.name, "PRAMS.tmcf")

        with open(mcf_path, encoding="utf-8") as mcf_file:
            cls.actual_mcf_data = mcf_file.read()

        with open(tmcf_path, encoding="utf-8") as tmcf_file:
            cls.actual_tmcf_data = tmcf_file.read()

        with open(csv_path, encoding="utf-8-sig") as csv_file:
            cls.actual_csv_data = csv_file.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def test_mcf_tmcf_files(self):
        """
        Tests whether generated MCF and TMCF match expected files.
        """
        expected_mcf_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.mcf")
        expected_tmcf_file_path = os.path.join(EXPECTED_FILES_DIR,
                                               "PRAMS.tmcf")

        with open(expected_mcf_file_path,
                  encoding="utf-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="utf-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()

        self.assertEqual(expected_mcf_data.strip(),
                         self.actual_mcf_data.strip())
        self.assertEqual(expected_tmcf_data.strip(),
                         self.actual_tmcf_data.strip())

    def test_create_csv(self):
        """
        Tests whether generated CSV matches expected file.
        """
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.csv")

        with open(expected_csv_file_path,
                  encoding="utf-8") as expected_csv_file:
            expected_csv_data = expected_csv_file.read()

        self.assertEqual(expected_csv_data.strip(),
                         self.actual_csv_data.strip())

    def test_scaling_factor_on_ci_bounds(self):
        """
        Verifies that confidence interval lower and upper limits have ScalingFactor=100.
        """
        df = pd.read_csv(io.StringIO(self.actual_csv_data))
        ci_lower = df[df['SV'].str.contains('ConfidenceIntervalLowerLimit')]
        ci_upper = df[df['SV'].str.contains('ConfidenceIntervalUpperLimit')]
        self.assertFalse(ci_lower.empty)
        self.assertFalse(ci_upper.empty)
        self.assertTrue((ci_lower['ScalingFactor'] == 100.0).all())
        self.assertTrue((ci_upper['ScalingFactor'] == 100.0).all())

    def test_year_range_extended_to_2022(self):
        """
        Verifies that observation years extend through 2022 without regression.
        """
        df = pd.read_csv(io.StringIO(self.actual_csv_data))
        years = set(df['Year'].unique())
        expected_years = {2016, 2017, 2018, 2019, 2020, 2021, 2022}
        self.assertEqual(years, expected_years)

    def test_discrete_sample_sizes_no_decimals(self):
        """
        Verifies that sample count values are integers and do not contain decimal parts.
        """
        df = pd.read_csv(io.StringIO(self.actual_csv_data), dtype=str)
        ss_df = df[df['SV'].str.startswith('SampleSize_Count')]
        self.assertFalse(ss_df.empty)
        for val in ss_df['Observation']:
            self.assertTrue(val.isdigit(), f"Sample size '{val}' contains non-digit chars")


if __name__ == '__main__':
    unittest.main()

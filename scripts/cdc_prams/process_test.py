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
Script to automate the testing for CDC PRAMS process script.
"""

import os
import unittest
import sys
import tempfile
import pandas as pd
import numpy as np

# MODULE_DIR is the absolute path to where this test is running from.
MODULE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, MODULE_DIR)

from process import USPrams, _split_statvar_value, _splitting_ci_columns

TEST_DATASET_DIR = os.path.join(MODULE_DIR, "test_data", "datasets")
EXPECTED_FILES_DIR = os.path.join(MODULE_DIR, "test_data", "expected_files")


class TestProcess(unittest.TestCase):
    """
    TestProcess is inheriting unittest class properties for unit testing.
    Generates CSV, MCF and TMCF files based on sample input and compares
    them with the expected golden files.
    """

    @classmethod
    def setUpClass(cls):
        test_data_files = [
            'Alabama-PRAMS-MCH-Indicators-508.pdf',
            'All-Sites-PRAMS-MCH-Indicators-508.pdf'
        ]
        ip_data = [
            os.path.join(TEST_DATASET_DIR, file_name)
            for file_name in test_data_files
        ]
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cleaned_csv_path = os.path.join(cls.tmp_dir.name, "data.csv")
        mcf_path = os.path.join(cls.tmp_dir.name, "test_census.mcf")
        tmcf_path = os.path.join(cls.tmp_dir.name, "test_census.tmcf")

        base = USPrams(ip_data, cleaned_csv_path, mcf_path, tmcf_path)
        base.process()

        with open(mcf_path, encoding="UTF-8") as mcf_file:
            cls.actual_mcf_data = mcf_file.read()

        with open(tmcf_path, encoding="UTF-8") as tmcf_file:
            cls.actual_tmcf_data = tmcf_file.read()

        with open(cleaned_csv_path, encoding="utf-8-sig") as csv_file:
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
                  encoding="UTF-8") as expected_mcf_file:
            expected_mcf_data = expected_mcf_file.read()

        with open(expected_tmcf_file_path,
                  encoding="UTF-8") as expected_tmcf_file:
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
        expected_csv_file_path = os.path.join(EXPECTED_FILES_DIR, "PRAMS.csv")
        df = pd.read_csv(expected_csv_file_path)
        ci_lower = df[df['SV'].str.contains('ConfidenceIntervalLowerLimit')]
        ci_upper = df[df['SV'].str.contains('ConfidenceIntervalUpperLimit')]
        self.assertFalse(ci_lower.empty)
        self.assertFalse(ci_upper.empty)
        self.assertTrue((ci_lower['ScalingFactor'] == 100.0).all())
        self.assertTrue((ci_upper['ScalingFactor'] == 100.0).all())

    def test_split_statvar_value_multi_digit_regex(self):
        """
        Tests that _split_statvar_value correctly matches multi-digit percentages (>=10.0%)
        and does not truncate parenthesis.
        """
        df = pd.DataFrame([{
            'statVar': '12.5 (10.2-14.8) Indicator description',
            'Overall_2020_CI': '',
            '2016_sampleSize': ''
        }])
        res = _split_statvar_value(df, 'National')
        self.assertEqual(res.loc[0, 'Overall_2020_CI'], '12.5 (10.2-14.8)')
        self.assertEqual(res.loc[0, 'statVar'], 'Indicator description')

    def test_suppressed_data_not_converted_to_zero(self):
        """
        Tests that suppressed data indicated by '.' or '(.-.)' does not become '0.0'.
        """
        state_cols = [
            'Geo', 'newStatVar', '2016_CI', '2017_CI', '2018_CI', '2019_CI',
            '2020_CI', 'Overall_2020_CI', '2016_sampleSize', '2017_sampleSize',
            '2018_sampleSize', '2019_sampleSize', '2020_sampleSize', 'SV',
            'ScalingFactor'
        ]
        df = pd.DataFrame([{col: '' for col in state_cols}])
        df.loc[0, '2018_CI'] = '0.0 (.-.)'
        res = _splitting_ci_columns(df, 'State')
        self.assertEqual(res.loc[0, '2018_CI_PERCENT'], '0.0')
        self.assertTrue(
            pd.isna(res.loc[0, '2018_CI_LOWER'])
            or res.loc[0, '2018_CI_LOWER'] == '')
        self.assertTrue(
            pd.isna(res.loc[0, '2018_CI_UPPER'])
            or res.loc[0, '2018_CI_UPPER'] == '')
        self.assertNotEqual(res.loc[0, '2018_CI_LOWER'], '0.0')
        self.assertNotEqual(res.loc[0, '2018_CI_UPPER'], '0.0')


if __name__ == '__main__':
    unittest.main()

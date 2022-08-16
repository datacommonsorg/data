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
Script to automate the testing for USA Census Population Estimate's (by SRH)
process, generate_mcf and generate_tmcf scripts.
"""

import os
import unittest
from mcf_generator import generate_mcf
from tmcf_generator import generate_tmcf

from process import process
from constants import OUTPUT_DIR

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


class ProcessTest(unittest.TestCase):
    """
    This class defines unit test cases for automated testing of generation of
    MCF, tMCF and DC import CSV files for US Census Estimates by SRH data.
    """

    def testMcf(self):
        """
        This method runs generate_mcf method, which generates MCF files for
        as-is and aggregate import and compares expected mcf files with actual
        (generated) files
        """
        generate_mcf()
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.mcf',
                  'r',
                  encoding='utf-8') as expected_mcf_file:
            expected_mcf = expected_mcf_file.read()

        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.mcf',
                  'r',
                  encoding='utf-8') as actual_mcf_file:
            actual_mcf = actual_mcf_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.mcf',
                'r',
                encoding='utf-8') as expected_agg_mcf_file:
            expected_agg_mcf = expected_agg_mcf_file.read()

        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh_agg.mcf',
                  'r',
                  encoding='utf-8') as actual_agg_mcf_file:
            actual_agg_mcf = actual_agg_mcf_file.read()

        expected_agg_mcf_file.close()
        actual_agg_mcf_file.close()

        self.assertEqual(expected_mcf, actual_mcf)
        self.assertEqual(expected_agg_mcf, actual_agg_mcf)

    def testTmcf(self):
        """
        This method runs generate_tmcf method, which generates tMCF files for
        as-is and aggregate import and compares expected tmcf files with actual
        (generated) files.
        """
        generate_tmcf()
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.tmcf',
                  'r',
                  encoding='utf-8') as expected_tmcf_file:
            expected_tmcf = expected_tmcf_file.read()
        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.tmcf',
                  'r',
                  encoding='utf-8') as actual_tmcf_file:
            actual_tmcf = actual_tmcf_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.tmcf',
                'r',
                encoding='utf-8') as expected_agg_tmcf_file:
            expected_agg_tmcf = expected_agg_tmcf_file.read()
        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh_agg.tmcf',
                  'r',
                  encoding='utf-8') as actual_agg_tmcf_file:
            actual_agg_tmcf = actual_agg_tmcf_file.read()

        self.assertEqual(expected_tmcf, actual_tmcf)
        self.assertEqual(expected_agg_tmcf, actual_agg_tmcf)

    def testCsv(self):
        """
        This method runs process script, which generates csv files for
        as-is and aggregate imports to dc. It compares expected files with 
        actual files.
        """
        process('/testdata/input_files/')
        with open(_CODEDIR +
                  '/testdata/expected_results/population_estimate_by_srh.csv',
                  'r',
                  encoding='utf-8') as expected_csv_file:
            expected_csv = expected_csv_file.read()
        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh.csv',
                  'r',
                  encoding='utf-8') as actual_csv_file:
            actual_csv = actual_csv_file.read()

        with open(
                _CODEDIR +
                '/testdata/expected_results/population_estimate_by_srh_agg.csv',
                'r',
                encoding='utf-8') as expected_agg_csv_file:
            expected_agg_csv = expected_agg_csv_file.read()
        with open(_CODEDIR + OUTPUT_DIR + 'population_estimate_by_srh_agg.csv',
                  'r',
                  encoding='utf-8') as actual_agg_csv_file:
            actual_agg_csv = actual_agg_csv_file.read()

        self.assertEqual(expected_csv, actual_csv)
        self.assertEqual(expected_agg_csv, actual_agg_csv)

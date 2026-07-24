# Copyright 2024 Google LLC
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
# Author: Sanika Prasad
# Date: 05/31/2024
# Name: process_test
# Description: Tests the process script of NCBI Assembly summary reports to make sure all funcationality are working as expected.
# @source data: Sample input curated from assembly_summary_genbank.txt and assembly_summary_refseq.txt from NCBI Assembly FTP Download page
# @file_input: assembly_summary_genbank.txt and assembly_summary_refseq.txt
# @file_output: formatted ncbi_assembly_summary.csv
# @expected_output: Expected output of the input file which is compared against output generated from test.

# Import all functions and classes from the process module
import os
import copy
import filecmp
import unittest
from pathlib import Path
from process import *
from os.path import dirname, abspath, join

_FLAGS = None

# Compute the directory path where this module is located
MODULE_DIR_PATH = dirname(dirname(abspath(__file__)))


def set_flag():
    global _FLAGS
    _FLAGS = flags.FLAGS  # Initialize the _FLAGS with the flags object
    # Define the output directory for generated files
    flags.DEFINE_string('output_dir',
                        os.path.join(MODULE_DIR_PATH, 'test_data/output_file/'),
                        'Output directory for generated files.')

    # Define the input directory for assembly summary GenBank files
    flags.DEFINE_string(
        'input_dir',
        os.path.join(MODULE_DIR_PATH,
                     'test_data/input/assembly_summary_genbank.txt'),
        'Input directory where .txt files downloaded.')

    # Define the input directory for assembly summary RefSeq files
    flags.DEFINE_string(
        'input_dir1',
        os.path.join(MODULE_DIR_PATH,
                     'test_data/input/assembly_summary_refseq.txt'),
        'Output directory for generated files.')

    # Define the input directory for tax ID to DCID mapping files
    flags.DEFINE_string(
        'tax_id_dcid_mapping',
        os.path.join(MODULE_DIR_PATH,
                     'test_data/input/tax_id_dcid_mapping.txt'),
        'Input directory where .txt files downloaded.')
    _FLAGS(sys.argv)


class TestSummaryReport(unittest.TestCase):
    """
    Unit test case to check the correctness of the output generation.
    """

    @classmethod
    def setUpClass(self):
        set_flag()

    def test_csv_check(self):
        """
        Test case to verify if the generated CSV file matches the expected output.
        """

        main(_FLAGS)
        # Compare the generated CSV file with the expected CSV file
        same = filecmp.cmp(
            os.path.join(_FLAGS.output_dir,
                         'ncbi_assembly_summary.csv'), MODULE_DIR_PATH +
            '/test_data/output_file/expected_ncbi_assembly_summary.csv')
        # Assert that the files are identical
        self.assertTrue(same)


if __name__ == '__main__':
    unittest.main()  # Run all test cases
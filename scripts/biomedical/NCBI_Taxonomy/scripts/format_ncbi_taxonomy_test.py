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
"""
Author: Pradeep Kumar Krishnaswamy
Date: 18-Apr-2024
Last Edited: 03-Sep-2024
"""

import os
import copy
import tempfile
import unittest
from deepdiff.diff import DeepDiff
from .format_ncbi_taxonomy import *

MODULE_DIR_PATH = dirname(dirname(abspath(__file__)))
SOURCE_FILE_PATH = dirname(dirname(abspath(__file__))) + '/test_data/input'
OUTPUT_FILE_PATH = dirname(dirname(abspath(__file__))) + '/test_data/output/'


class TestNCBITaxonomy(unittest.TestCase):

    # @classmethod
    # def setUpClass(self):
    #     global SOURCE_FILE_PATH, OUTPUT_FILE_PATH, MODULE_DIR_PATH
    #     SOURCE_FILE_PATH = os.path.join(MODULE_DIR_PATH, SOURCE_FILE_PATH)
    #     OUTPUT_FILE_PATH = os.path.join(MODULE_DIR_PATH, OUTPUT_FILE_PATH)

    def test_check_division_df_columns(self):
        """ Check for the column header for Division dmp file 
        """
        global SOURCE_FILE_PATH
        division_df = DivisionCls().create_dataframe(SOURCE_FILE_PATH)
        division_col_lst = copy.deepcopy(DIVISION_COL)
        division_col_lst.append('division_namePascalCase')
        self.assertListEqual(division_col_lst, division_df.columns.to_list())

    def test_check_names_df_columns(self):
        """ Check for the column header for Names dmp file 
        """
        names_df = NamesCls().create_dataframe(SOURCE_FILE_PATH)
        self.assertListEqual(NAMES_COL, names_df.columns.to_list())

    def test_check_host_df_columns(self):
        """ Check for the column header for Hosts dmp file 
        """
        host_df = HostCls().create_dataframe(SOURCE_FILE_PATH)
        host_col_lst = copy.deepcopy(HOST_COL)
        host_col_lst.append('DC_host_enum')
        self.assertListEqual(host_col_lst, host_df.columns.to_list())

    def test_check_nodes_df_columns(self):
        """ Check for the column header for Nodes dmp file 
        """
        nodes_df = NodesCls().create_dataframe(SOURCE_FILE_PATH)
        nodes_col_lst = NODES_COL
        nodes_col_lst.remove('embl_code')
        self.assertListEqual(nodes_col_lst, nodes_df.columns.to_list())

    def test_check_categories_df_columns(self):
        """ Check for the column header for Categories dmp file 
        """
        categories_df = CategoriesCls().create_dataframe(SOURCE_FILE_PATH)
        categories_col_lst = CATEGORIES_COL
        categories_col_lst.remove('speciesTaxID')
        self.assertListEqual(CATEGORIES_COL, categories_df.columns.to_list())

    def test_check_mcf_entries_division(self):
        """ check the generated enum mcf file for Division dum file
        """
        expected_mcf_list = []
        current_mcf_list = []
        division_df = DivisionCls().create_dataframe(SOURCE_FILE_PATH)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            DivisionCls().append_mcf_data(division_df, result_mcf_file)
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))
            with open(
                    os.path.join(
                        MODULE_DIR_PATH,
                        'test_data/expected_mcf_files/division_enum_expected.mcf'
                    ), 'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))

        assert DeepDiff(expected_mcf_list, current_mcf_list) == {}

    def test_check_mcf_entries_hosts(self):
        """ check the generated enum mcf file for Hosts dum file
        """
        expected_mcf_list = []
        current_mcf_list = []
        host_df = HostCls().create_dataframe(SOURCE_FILE_PATH)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            HostCls().append_mcf_data(host_df, result_mcf_file)
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))
            with open(
                    os.path.join(
                        MODULE_DIR_PATH,
                        'test_data/expected_mcf_files/host_enum_expected.mcf'),
                    'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))

        assert DeepDiff(expected_mcf_list, current_mcf_list) == {}

    def test_check_mcf_entries_nodes(self):
        """ check the generated enum mcf file for Nodes dum file
        """
        expected_mcf_list = []
        current_mcf_list = []
        nodes_df = NodesCls().create_dataframe(SOURCE_FILE_PATH)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            NodesCls().append_mcf_data(nodes_df, result_mcf_file)
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))
            with open(
                    os.path.join(
                        MODULE_DIR_PATH,
                        'test_data/expected_mcf_files/nodes_enum_expected.mcf'),
                    'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))

        assert DeepDiff(expected_mcf_list, current_mcf_list) == {}


if __name__ == '__main__':
    unittest.main()

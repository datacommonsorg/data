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
"""

import os
import copy
import tempfile
import unittest
from format_ncbi_taxonomy import *

MODULE_DIR_PATH = str(Path(os.path.dirname(__file__)).parents[0])


class TestNCBITaxonomy(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        set_flages()

    def test_check_division_df_columns(self):
        division_df = DivisionCls().create_dataframe()
        division_col_lst = copy.deepcopy(DIVISION_COL)
        division_col_lst.append('division_namePascalCase')
        self.assertListEqual(division_col_lst, division_df.columns.to_list())

    def test_check_names_df_columns(self):
        names_df = NamesCls().create_dataframe()
        self.assertListEqual(NAMES_COL, names_df.columns.to_list())

    def test_check_host_df_columns(self):
        host_df = HostCls().create_dataframe()
        host_col_lst = copy.deepcopy(HOST_COL)
        host_col_lst.append('DC_host_enum')
        self.assertListEqual(host_col_lst, host_df.columns.to_list())

    def test_check_nodes_df_columns(self):
        nodes_df = NodesCls().create_dataframe()
        nodes_col_lst = NODES_COL
        nodes_col_lst.remove('embl_code')
        self.assertListEqual(nodes_col_lst, nodes_df.columns.to_list())

    def test_check_categories_df_columns(self):
        categories_df = CategoriesCls().create_dataframe()
        categories_col_lst = CATEGORIES_COL
        categories_col_lst.remove('speciesTaxID')
        self.assertListEqual(CATEGORIES_COL, categories_df.columns.to_list())

    def test_check_mcf_entries_division(self):
        expected_mcf_list = []
        current_mcf_list = []
        division_df = DivisionCls().create_dataframe()
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            DivisionCls().append_mcf_data(division_df, result_mcf_file)
            with open(
                    os.path.join(MODULE_DIR_PATH,
                                 'ncbi_taxonomy/test_data/division_enum_expected.mcf'),
                    'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))

        self.assertTrue(set(expected_mcf_list).issubset(set(current_mcf_list)))

    def test_check_mcf_entries_hosts(self):
        expected_mcf_list = []
        current_mcf_list = []
        host_df = HostCls().create_dataframe()
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            HostCls().append_mcf_data(host_df, result_mcf_file)
            with open(
                    os.path.join(MODULE_DIR_PATH,
                                 'ncbi_taxonomy/test_data/host_enum_expected.mcf'),
                    'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))

        self.assertTrue(set(expected_mcf_list).issubset(set(current_mcf_list)))

    def test_check_mcf_entries_nodes(self):
        expected_mcf_list = []
        current_mcf_list = []
        nodes_df = NodesCls().create_dataframe()
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_mcf_file = os.path.join(tmp_dir, 'test_mcf.mcf')
            NodesCls().append_mcf_data(nodes_df, result_mcf_file)
            with open(
                    os.path.join(MODULE_DIR_PATH,
                                 'ncbi_taxonomy/test_data/nodes_enum_expected.mcf'),
                    'r') as mcf:
                expected_mcf_list.extend(mcf.read().split('\n\n'))
            with open(result_mcf_file, 'r') as mcf:
                current_mcf_list.extend(mcf.read().split('\n\n'))

        self.assertTrue(set(expected_mcf_list).issubset(set(current_mcf_list)))


if __name__ == '__main__':
    unittest.main()

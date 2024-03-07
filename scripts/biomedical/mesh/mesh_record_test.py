# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
Author: Suhana Bedi
Date: 08/29/2022
Name: mesh_record_test.py
Description: runs unit tests for format_mesh_record.py
Run: python3 mesh_record_test.py
'''
import unittest
from pandas.testing import assert_frame_equal 
from format_mesh_record import *

class TestParseMesh(unittest.TestCase): 
    """Test the functions in format_mesh_record.py"""

    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df1_expected = pd.read_csv('unit-tests/mesh_record_test.csv')
        df2_expected = pd.read_csv('unit-tests/mesh_pubchem_mapping_test.csv')
        df_actual = format_mesh_record('unit-tests/mesh_record_test_data.xml')
        
        # Run all the functions in format_mesh_record.py 
        df1_actual = date_modify_record(df_actual)
        df1_actual = format_recordID(df1_actual)
        df2_actual = format_pubchem_mesh_mapping('unit-tests/mesh_pubchem_test_data.csv', df1_actual)

        # Compare expected and actual output files
        assert_frame_equal(df1_expected.reset_index(drop=True), df1_actual.reset_index(drop=True))
        assert_frame_equal(df2_expected.reset_index(drop=True), df2_actual.reset_index(drop=True))

if __name__ == '__main__':
    unittest.main()
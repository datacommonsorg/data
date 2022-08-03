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
'''
Author: Mariam Benazouz
Date: 07/27/2022
Name: test_compile_stitch.py
Description: runs unit tests for test_compile_stitch.py
Run: python3 compile_stitch.py
'''
import unittest
from pandas.util.testing import assert_frame_equal
from compile_stitch import *

class TestStitch(unittest.TestCase):
    """Test the functions in compile_stitch.py"""
    
    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df_expected = pd.read_csv('test-data/expected_output_test.csv')
        PATH_SOURCES= 'test-data/test_file1.tsv'
        PATH_INCHIKEYS = 'test-data/test_file2.tsv'
        PATH_CHEMICALS = 'test-data/test_file3.tsv'
        # Run all the functions in compile_drugs.py 
        merged_df = merge_dfs(PATH_SOURCES, PATH_INCHIKEYS, PATH_CHEMICALS)  
        final_df = find_IDs(merged_df)
        df_actual = format_df(final_df)
        df_actual.to_csv('test-data/actual_output_test.csv')
        df_actual = pd.read_csv('test-data/actual_output_test.csv')
        # Compare expected and actual output files
        assert_frame_equal(df_expected.reset_index(drop=True), df_actual.reset_index(drop=True))
        
if __name__ == '__main__':
    unittest.main() 
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
Date: 07/08/2022
Name: disease_ontology_test.py
Description: runs unit tests for format_disease_ontology.py
Run: python3 disease_ontology_test.py
'''

import unittest
from pandas.testing import assert_frame_equal 
from format_disease_ontology import *

class TestParseMesh(unittest.TestCase): 
    """Test the functions in format_disease_ontology"""

    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df1_expected = pd.read_csv('unit-tests/test-output.csv')
        df_actual = wrapper_fun('unit-tests/test-do.xml')
        # Run all the functions in format_mesh.py 
        # Compare expected and actual output files
        assert_frame_equal(df1_expected.reset_index(drop=True), df_actual.reset_index(drop=True))

if __name__ == '__main__':
    unittest.main()
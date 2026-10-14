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
Author: Suhana Bedi
Date: 10/24/2022
Name: chembl_pubchem_mapping_test.py
Description: runs unit tests for format_chembl_pubchem_mapping.py
Run: python3 chembl_pubchem_mapping_test.py
'''
import unittest
from pandas.testing import assert_frame_equal 
from format_chembl_pubchem_mapping import *

class TestParseMesh(unittest.TestCase): 
    """Test the functions in format_chembl_uniprot"""

    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df_expected = pd.read_csv('test-data/Synonym-mapping-expected.csv')
        df_actual = pd.read_csv('test-data/synonym_mapping_test_data.txt', sep = '\t', header = None)
        # Run all the functions in format_chembl_uniprot.py 
        df_actual = split_synonyms(df_actual)
        df_actual['Name'] = df_actual['Name'].apply(', '.join)
        df_actual['Id'] = df_actual.index
        df_actual['Id'] = "chem/CID" + df_actual['Id'].astype(str)
        # Compare expected and actual output files
        assert_frame_equal(df_expected.reset_index(drop=True), df_actual.reset_index(drop=True))

if __name__ == '__main__':
    unittest.main()
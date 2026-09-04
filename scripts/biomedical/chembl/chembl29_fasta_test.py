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
Date: 07/09/2022
Name: chembl29_fasta_test.py
Description: runs unit tests for format_chembl29_fasta.py
Run: python3 chembl29_fasta_test.py
'''
import unittest
from pandas.testing import assert_frame_equal 
from format_chembl29_fasta import *

class TestParseMesh(unittest.TestCase): 
    """Test the functions in format_chembl29_fasta"""

    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df_expected = pd.read_csv('test-data/chembl_29_fasta_expected.csv')
        df_actual = fasta_to_df('test-data/chembl_29_fasta_test_data.fa')
        # Run all the functions in format_chembl29_fasta.py 
        df_actual = format_identifier(df_actual)
        df_actual = format_cols(df_actual)
        df_actual = multiple_dcid(df_actual)
        # Rearrange the order of columns for comparison
        df_actual = df_actual[['Sequence', 'chembl', 'uniprot', 'name', 'dcid']]
        # Compare expected and actual output files
        assert_frame_equal(df_expected.reset_index(drop=True), df_actual.reset_index(drop=True))

if __name__ == '__main__':
    unittest.main()
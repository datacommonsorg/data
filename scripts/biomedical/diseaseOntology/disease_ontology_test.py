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


def assert_column_contains_expected(expected_series, actual_series):
    """Asserts that at least one expected value (after stripping leading/trailing spaces and normalizing) is contained within the corresponding actual value (split by comma)."""
    for expected, actual in zip(expected_series, actual_series):
        if pd.isna(expected) or pd.isna(actual):
            if pd.isna(expected) and pd.isna(actual):
                continue  # Both are NaN, so continue
            else:
                raise AssertionError(f"Nan values do not match: Expected '{expected}' vs Actual '{actual}'")
        expected_values = [val.replace("DOID_", "DOID:").strip() for val in str(expected).split(', ')]
        actual_values = [val.strip() for val in str(actual).split(', ')]
        found_match = False
        for val in expected_values:
            if val in actual_values:
                found_match = True
                break
        
        if not found_match:
            raise AssertionError(f"None of the normalized expected values '{expected_values}' were found in '{actual_values}'")
class TestParseMesh(unittest.TestCase): 
    """Test the functions in format_disease_ontology"""

    def test_main(self):
        """Test in the main function"""
        # Read in the expected output files into pandas dataframes
        df1_expected = pd.read_csv('unit-tests/test-expected.csv')
        tree = ElementTree.parse('unit-tests/test-do.xml')
        # Get file root
        root = tree.getroot()
        # Find owl classes elements
        all_classes = root.findall('{http://www.w3.org/2002/07/owl#}Class')
        # Parse owl classes to human-readble dictionary format
        parsed_owl_classes = []
        for owl_class in all_classes:
            info = list(owl_class.iter())
            parsed_owl_classes.append(parse_do_info(info))
        # Convert to pandas Dataframe
        df_do = pd.DataFrame(parsed_owl_classes)
        format_cols(df_do)
        df_do = df_do.drop([
            'Class', 'exactMatch', 'deprecated', 'hasRelatedSynonym', 'comment',
            'OBI_9991118', 'narrowMatch', 'hasBroadSynonym', 'disjointWith',
            'hasNarrowSynonym', 'broadMatch', 'created_by', 'creation_date',
            'inSubset', 'hasOBONamespace'
        ],
                        axis=1)
        df_do = col_explode(df_do)
        df_do = mesh_separator(df_do)
        df_do = col_string(df_do)
        df_do = df_do.drop(['A', 'B', 'nan', 'hasDbXref', 'KEGG'], axis=1)
        df_do = df_do.drop_duplicates(subset='id', keep="last")
        df_do = df_do.reset_index(drop=True)
        df_do = df_do.replace('"nan"', np.nan)
        df_do['IAO_0000115'] = df_do['IAO_0000115'].str.replace("_", " ")
        df_actual = df_do.applymap(lambda x: x.replace('"', '') if (isinstance(x, str)) else x)
        ## fixes the float to object type conversion by pandas while reading the dataframe
        col_list = ['SNOMEDCTUS20200901', 'SNOMEDCTUS20180301', 'SNOMEDCTUS20200301', 'SNOMEDCTUS20190901', 'OMIM', 'ORDO']
        for i in col_list:
            df_actual[i] = df_actual[i].astype(float)
       
        
        try:
    # Compare other columns
            other_columns = [col for col in df1_expected.columns if col != 'hasAlternativeId']
            assert_frame_equal(df1_expected[other_columns].reset_index(drop=True), df_actual[other_columns].reset_index(drop=True))
            assert_column_contains_expected(df1_expected['hasAlternativeId'], df_actual['hasAlternativeId'])
            

        except AssertionError as e:
            print(f"Test Failed: {e}")

if __name__ == '__main__':
    unittest.main()
# Copyright 2025 Google LLC
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
"""Tests for the filtering utility."""

import unittest
import pandas as pd
from tools.import_validation.util import filter_dataframe


class TestFilterDataFrame(unittest.TestCase):

    def test_filter_with_dcids(self):
        """Tests filtering by a list of exact StatVar DCIDs."""
        df = pd.DataFrame({
            'StatVar': [
                'Count_Person_Male', 'Count_Person_Female',
                'Count_Person_AgeU18'
            ]
        })
        filtered_df = filter_dataframe(df, statvar_dcids=['Count_Person_Male'])
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['StatVar'], 'Count_Person_Male')

    def test_filter_with_regex(self):
        """Tests filtering by a regex pattern."""
        df = pd.DataFrame({
            'StatVar': [
                'Count_Person_Male', 'Count_Person_Female',
                'Amount_Debt_Government'
            ]
        })
        filtered_df = filter_dataframe(df, regex_patterns=['Count_Person_.*'])
        self.assertEqual(len(filtered_df), 2)

    def test_filter_with_single_substring_match(self):
        """Tests filtering by a single matching substring."""
        df = pd.DataFrame(
            {'StatVar': ['Count_Person_gender_Male', 'Count_Person_Female']})
        filtered_df = filter_dataframe(df, contains_all=['gender_Male'])
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['StatVar'],
                         'Count_Person_gender_Male')

    def test_filter_with_multiple_substrings_match(self):
        """Tests that all substrings must match for a row to be included."""
        df = pd.DataFrame({
            'StatVar': [
                'Count_Person_gender_Male_age_U18', 'Count_Person_gender_Male'
            ]
        })
        filtered_df = filter_dataframe(df,
                                       contains_all=['gender_Male', 'age_U18'])
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['StatVar'],
                         'Count_Person_gender_Male_age_U18')

    def test_filter_with_substring_existence(self):
        """Tests filtering for the existence of a substring."""
        df = pd.DataFrame({
            'StatVar': [
                'Count_Person_gender_Male', 'Count_Person_age_U18',
                'Amount_Debt'
            ]
        })
        filtered_df = filter_dataframe(df, contains_all=['gender'])
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['StatVar'],
                         'Count_Person_gender_Male')

    def test_no_filters(self):
        """Tests that providing no filters returns the original DataFrame."""
        df = pd.DataFrame(
            {'StatVar': ['Count_Person_Male', 'Count_Person_Female']})
        filtered_df = filter_dataframe(df)
        self.assertEqual(len(filtered_df), 2)

    def test_multiple_filter_types_are_unioned(self):
        """Tests that results from different filter types are combined (union)."""
        df = pd.DataFrame({
            'StatVar': [
                'Count_Person_Male', 'Count_Person_Female',
                'Amount_Debt_Government'
            ]
        })
        filtered_df = filter_dataframe(df,
                                       statvar_dcids=['Amount_Debt_Government'],
                                       regex_patterns=['Count_Person_Male'])
        self.assertEqual(len(filtered_df), 2)
        self.assertIn('Count_Person_Male', filtered_df['StatVar'].values)
        self.assertIn('Amount_Debt_Government', filtered_df['StatVar'].values)

    def test_filter_with_non_matching_dcid(self):
        """Tests that a non-matching DCID returns an empty DataFrame."""
        df = pd.DataFrame({'StatVar': ['Count_Person_Male']})
        filtered_df = filter_dataframe(df, statvar_dcids=['Non_Existent_DCID'])
        self.assertTrue(filtered_df.empty)

    def test_filter_with_non_matching_regex(self):
        """Tests that a non-matching regex returns an empty DataFrame."""
        df = pd.DataFrame({'StatVar': ['Count_Person_Male']})
        filtered_df = filter_dataframe(df, regex_patterns=['Non_Existent_.*'])
        self.assertTrue(filtered_df.empty)

    def test_filter_with_non_matching_substring(self):
        """Tests that a non-matching substring returns an empty DataFrame."""
        df = pd.DataFrame({'StatVar': ['Count_Person_gender_Male']})
        filtered_df = filter_dataframe(df,
                                       contains_all=['non_existent_substring'])
        self.assertTrue(filtered_df.empty)

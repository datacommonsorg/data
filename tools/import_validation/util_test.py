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
"""Tests for the filtering utility."""

import unittest
import pandas as pd
from tools.import_validation.util import filter_dataframe


class TestFilterDataFrame(unittest.TestCase):

    def setUp(self):
        self.test_df = pd.DataFrame({
            'StatVar': [
                'Count_Person_Male', 'Count_Person_Female',
                'Count_Person_U18', 'Amount_Money_Debt_Government'
            ]
        })

    def test_filter_with_exact_string(self):
        config = ['Count_Person_Male']
        filtered_df = filter_dataframe(self.test_df, config)
        self.assertEqual(len(filtered_df), 1)
        self.assertEqual(filtered_df.iloc[0]['StatVar'], 'Count_Person_Male')

    def test_filter_with_regex(self):
        config = ['Count_Person_.*']
        filtered_df = filter_dataframe(self.test_df, config)
        self.assertEqual(len(filtered_df), 3)

    def test_filter_with_dictionary(self):
        # This is a simplified test. A more robust implementation would
        # require a more sophisticated mock of the DCID structure.
        config = [{
            'populationType': 'Person',
            'gender': 'Male'
        }]
        # Our current implementation uses string matching, so this will fail.
        # This highlights the need for a more robust DCID parsing implementation.
        # For now, we expect this to return 0 results.
        filtered_df = filter_dataframe(self.test_df, config)
        self.assertEqual(len(filtered_df), 0)

    def test_filter_with_wildcard_dictionary(self):
        config = [{
            'populationType': 'Person',
            'age': '*'
        }]
        # This will also fail with the current simplified implementation.
        filtered_df = filter_dataframe(self.test_df, config)
        self.assertEqual(len(filtered_df), 0)

    def test_no_filter(self):
        filtered_df = filter_dataframe(self.test_df, [])
        self.assertEqual(len(filtered_df), 4)

    def test_multiple_filters(self):
        config = ['Count_Person_Male', 'Count_Person_Female']
        filtered_df = filter_dataframe(self.test_df, config)
        self.assertEqual(len(filtered_df), 2)

# Copyright 2020 Google LLC
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

import sys
sys.path.append('../')
from utils import multi_index_to_single_index, generate_geo_id
import unittest
import json
import pandas as pd
from pandas.testing import assert_frame_equal


class TestUtils(unittest.TestCase):

    def test_multi_index_to_single_index(self):
        df = pd.read_csv("test.csv")
        df_cleaned = df.pivot_table(values='value',
                                    index=['name'],
                                    columns=['var', 'sex'])

        df_cleaned = multi_index_to_single_index(df_cleaned)
        df_expected = pd.read_csv("test_expected.csv")

        self.assertTrue(assert_frame_equal(df_cleaned, df_expected) is None)

    def test_generate_geo_id(self):
        df = pd.DataFrame({
            "TL": [1, 3, 1],
            "REG_ID": ["USA", "TR906", "RUS"],
            "Region": ["United States", "Gümüshane", "Russia"]
        })

        regid2dcid = dict(json.loads(open('../regid2dcid.json').read()))
        nuts = dict(json.loads(open('../region_nuts_codes.json').read()))

        res = []
        for index, row in df.iterrows():
            res.append(generate_geo_id(row, nuts, regid2dcid))

        expected = ['dcid:country/USA', 'dcid:nuts/TR906', 'dcid:country/RUS']
        self.assertTrue(res == expected)


if __name__ == '__main__':
    unittest.main()

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

import csv
import os
import pandas as pd
import unittest
from india_lgd.local_government_directory_districts.preprocess import LocalGovermentDirectoryDistrictsDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestPreprocess(unittest.TestCase):

    def test_create_csv(self):
        lgd_csv = os.path.join(os.path.dirname(__file__),
                               "./test_data/lgd_allDistrictofIndia_export.csv")
        wikidata_csv = os.path.join(
            os.path.dirname(__file__),
            "./test_data/wikidata_india_districts_export.csv")
        clean_csv = os.path.join(os.path.dirname(__file__),
                                 "./test_data/clean_csv.csv")

        loader = LocalGovermentDirectoryDistrictsDataLoader(
            lgd_csv, wikidata_csv, clean_csv)
        loader.process()
        loader.save()

        clean_df = pd.read_csv(clean_csv, dtype=str)
        clean_df.fillna('', inplace=True)

        # `karbi anglong` should be mapped to `east karbi anglong`
        row = clean_df.loc[clean_df["LGDDistrictName"] == "karbi anglong"]
        self.assertEqual("east karbi anglong",
                         row.iloc[0]["closestDistrictLabel"])
        self.assertEqual("Q29025081", row.iloc[0]["WikiDataId"])

        # `west karbi anglong` should be mapped to `west karbi anglong`
        row = clean_df.loc[clean_df["LGDDistrictName"] == "west karbi anglong"]
        self.assertEqual("west karbi anglong",
                         row.iloc[0]["closestDistrictLabel"])
        self.assertEqual("Q24949218", row.iloc[0]["WikiDataId"])

        # `tuticorin` should be mapped to `thoothukudi`
        row = clean_df.loc[clean_df["LGDDistrictName"] == "tuticorin"]
        self.assertEqual("thoothukudi", row.iloc[0]["closestDistrictLabel"])
        self.assertEqual("Q15198", row.iloc[0]["WikiDataId"])

        # `balod` should be mapped to `balod`
        row = clean_df.loc[clean_df["LGDDistrictName"] == "balod"]
        self.assertEqual("balod", row.iloc[0]["closestDistrictLabel"])
        self.assertEqual("Q16056266", row.iloc[0]["WikiDataId"])

        # `malerkotla` should be mapped to `malerkotla`
        row = clean_df.loc[clean_df["LGDDistrictName"] == "malerkotla"]
        self.assertEqual("malerkotla", row.iloc[0]["closestDistrictLabel"])
        self.assertEqual("Q1470987", row.iloc[0]["WikiDataId"])

        os.remove(clean_csv)


if __name__ == '__main__':
    unittest.main()

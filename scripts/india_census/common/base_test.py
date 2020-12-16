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

import filecmp
import os
import json
import unittest
from .base import CensusPrimaryAbstractDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestCensusPrimaryAbstractDataLoaderBase(unittest.TestCase):

    def test_create_csv(self):
        data_file_path = os.path.join(os.path.dirname(__file__),
                                      './test_data/test_input.xlsx')

        metadata_file_path = os.path.join(
            os.path.dirname(__file__), 'primary_abstract_data_variables.csv')

        existing_stat_var = [
            "Count_Household", "Count_Person", "Count_Person_Urban",
            "Count_Person_Rural", "Count_Person_Male", "Count_Person_Female"
        ]

        mcf_file_path = os.path.join(os.path.dirname(__file__),
                                     './test_data/test_Data.mcf')
        tmcf_file_path = os.path.join(os.path.dirname(__file__),
                                      './test_data/test_Data.tmcf')
        csv_file_path = os.path.join(os.path.dirname(__file__),
                                     './test_data/test_Data.csv')

        mcf_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test_Data_Expected.mcf')
        tmcf_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test_Data_Expected.tmcf')
        csv_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test_Data_Expected.csv')

        loader = CensusPrimaryAbstractDataLoaderBase(
            data_file_path=data_file_path,
            metadata_file_path=metadata_file_path,
            mcf_file_path=mcf_file_path,
            tmcf_file_path=tmcf_file_path,
            csv_file_path=csv_file_path,
            existing_stat_var=existing_stat_var,
            census_year=2011,
            dataset_name="TEST")
        loader.process()

        same_mcf = filecmp.cmp(mcf_file_path, mcf_expected_file_path)
        same_tmcf = filecmp.cmp(tmcf_file_path, tmcf_expected_file_path)
        same_csv = filecmp.cmp(csv_file_path, csv_expected_file_path)

        #Remove the created files, after comparison
        if os.path.exists(mcf_file_path):
            os.remove(mcf_file_path)

        if os.path.exists(tmcf_file_path):
            os.remove(tmcf_file_path)

        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        self.assertTrue(same_mcf)
        self.assertTrue(same_tmcf)
        self.assertTrue(same_csv)

    def test_create_csv_workers_data(self):
        data_file_path = os.path.join(os.path.dirname(__file__),
                                      './test_data/test2_input.xlsx')

        metadata_file_path = os.path.join(
            os.path.dirname(__file__), 'primary_abstract_data_variables.csv')

        existing_stat_var = [
            "Count_Household", "Count_Person", "Count_Person_Urban",
            "Count_Person_Rural", "Count_Person_Male", "Count_Person_Female"
        ]

        mcf_file_path = os.path.join(os.path.dirname(__file__),
                                     './test_data/test2_Data.mcf')
        tmcf_file_path = os.path.join(os.path.dirname(__file__),
                                      './test_data/test2_Data.tmcf')
        csv_file_path = os.path.join(os.path.dirname(__file__),
                                     './test_data/test2_Data.csv')

        mcf_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test2_Data_Expected.mcf')
        tmcf_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test2_Data_Expected.tmcf')
        csv_expected_file_path = os.path.join(
            os.path.dirname(__file__), './test_data/test2_Data_Expected.csv')

        loader = CensusPrimaryAbstractDataLoaderBase(
            data_file_path=data_file_path,
            metadata_file_path=metadata_file_path,
            mcf_file_path=mcf_file_path,
            tmcf_file_path=tmcf_file_path,
            csv_file_path=csv_file_path,
            existing_stat_var=existing_stat_var,
            census_year=2011,
            dataset_name="TEST2")
        loader.process()

        same_mcf = filecmp.cmp(mcf_file_path, mcf_expected_file_path)
        same_tmcf = filecmp.cmp(tmcf_file_path, tmcf_expected_file_path)
        same_csv = filecmp.cmp(csv_file_path, csv_expected_file_path)

        #Remove the created files, after comparison
        if os.path.exists(mcf_file_path):
            os.remove(mcf_file_path)

        if os.path.exists(tmcf_file_path):
            os.remove(tmcf_file_path)

        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        self.assertTrue(same_mcf)
        self.assertTrue(same_tmcf)
        self.assertTrue(same_csv)


if __name__ == '__main__':
    unittest.main()

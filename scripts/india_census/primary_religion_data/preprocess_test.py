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
from india_census.common.base import CensusPrimaryAbstractDataLoaderBase
from india_census.primary_religion_data.preprocess import CensusPrimaryReligiousDataLoader

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class TestCensusCensusPrimaryReligiousDataLoader(unittest.TestCase):
    def test_create_cleaned_religion_data_csv(self):
        data_file_path = os.path.join(os.path.dirname(__file__),
                                      './test_data/test_input.xlsx')

        metadata_file_path = os.path.join(
            os.path.dirname(__file__),
            '../common/primary_abstract_data_variables.csv')

        existing_stat_var = [
            "Count_Household", "Count_Person", "Count_Person_Urban",
            "Count_Person_Rural", "Count_Person_Male", "Count_Person_Female"
        ]

        data_categories = [
            "Total", "Hindu", "Muslim", "Christian", "Sikh", "Buddhist",
            "Jain", "Other religions and persuasions", "Religion not stated"
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

        loader = CensusPrimaryReligiousDataLoader(
            data_file_path=data_file_path,
            metadata_file_path=metadata_file_path,
            mcf_file_path=mcf_file_path,
            tmcf_file_path=tmcf_file_path,
            csv_file_path=csv_file_path,
            existing_stat_var=existing_stat_var,
            census_year=2011,
            dataset_name="TEST",
            data_categories=data_categories,
            data_category_column="Religion")
        loader.process()

        result_mcf_file = open(mcf_file_path)
        result_mcf_data = result_mcf_file.read()
        result_mcf_file.close()

        mcf_expected_file = open(mcf_expected_file_path)
        expected_mcf_data = mcf_expected_file.read()
        mcf_expected_file.close()

        result_tmcf_file = open(tmcf_file_path)
        result_tmcf_data = result_tmcf_file.read()
        result_tmcf_file.close()

        tmcf_expected_file = open(tmcf_expected_file_path)
        expected_tmcf_data = tmcf_expected_file.read()
        tmcf_expected_file.close()

        result_csv_file = open(csv_file_path)
        result_csv_data = result_csv_file.read()
        result_csv_file.close()

        csv_expected_file = open(csv_expected_file_path)
        expected_csv_data = csv_expected_file.read()
        csv_expected_file.close()

        if os.path.exists(mcf_file_path):
            os.remove(mcf_file_path)

        if os.path.exists(tmcf_file_path):
            os.remove(tmcf_file_path)

        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)

        self.assertEqual(expected_mcf_data, result_mcf_data)
        self.assertEqual(expected_tmcf_data, result_tmcf_data)
        # self.assertEqual(expected_csv_data, result_csv_data)

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

import os
import unittest
from india_nhm.states.base.data_cleaner import NHMDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
cols_to_nodes = {
    'State': 'State',
    'isoCode': 'isoCode',
    'Date': 'Date',
    'IPD (Number)': 'Count_InPatient',
    'OPD (Number)': 'Count_OutPatient',
    'OPD (Allopathic)': 'Count_OutPatient',
    'Number of Major Operations': 'Count_SurgicalProcedure_Major',
    'Number of Minor Operations': 'Count_SurgicalProcedure_Minor',
    '% Inpatient Deaths to Total IPD':
    'Count_InPatient_Deceased_AsFractionOf_Count_InPatient',
    'Ayush OPD (Number)': 'Count_OutPatient_Ayush',
}


class TestPreprocess(unittest.TestCase):

    maxDiff = None

    def test_create_csv(self):
        expected_file = open(os.path.join(module_dir_, 'test/expected.csv'))
        expected_data = expected_file.read()
        expected_file.close()

        loader = NHMDataLoaderBase(
            data_folder=os.path.join(module_dir_, 'test/'),
            dataset_name='test_gen',
            cols_dict=cols_to_nodes,
            final_csv_path=os.path.join(module_dir_, "test/test_gen.csv"))
        loader.generate_csv()

        result_file = open(os.path.join(module_dir_, "test/test_gen.csv"))
        result_data = result_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir_, "test/test_gen.csv"))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()

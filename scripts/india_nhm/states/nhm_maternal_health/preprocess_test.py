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

os.chdir('../../../')

import unittest
from india_nhm.states.base.data_cleaner import NHMDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
cols_to_nodes = {
    'State':
        'State',
    'isoCode':
        'isoCode',
    'Date':
        'Date',
    'Estimated Number of Annual Pregnancies #':
        'Count_PregnancyEvent',
    'Total number of pregnant women Registered for ANC':
        'Count_PregnantWomen_RegisteredForAntenatalCare',
    'Number of Pregnant women registered within first trimester':
        'Count_PregnantWomen_RegisteredForAntenatalCareWithinFirstTrimester',
    'Total reported deliveries':
        'Count_ChildDeliveryEvent',
    'Institutional deliveries (Public Insts.+Pvt. Insts.)':
        'Count_ChildDeliveryEvent_InAnInstitution',
    'Deliveries Conducted at Public Institutions':
        'Count_ChildDeliveryEvent_InPublicInstitution',
    'Number of Home deliveries':
        'Count_ChildDeliveryEvent_AtHome',
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/Auxillary Nurse Midwife)':
        'Count_ChildDeliveryEvent_AtHome_WithStandbyAssist',
    '% Safe deliveries to Total Reported Deliveries':
        'Count_DeliveryEvent_Safe_AsFractionOf_Count_DeliveryEvent'
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
            clean_names=None,
            final_csv_path=os.path.join(module_dir_, "test/test_gen.csv"),
            module_dir=module_dir_)
        loader.generate_csv()

        result_file = open(os.path.join(module_dir_, "test/test_gen.csv"))
        result_data = result_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir_, "test/test_gen.csv"))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()

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
from india_nhm.districts.base.data_cleaner import NHMDataLoaderBase

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)
cols_to_nodes = {
    'District':
    'District',
    'DistrictCode':
    'lgdCode',
    'Date':
    'Date',
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
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/ANM)':
    'Count_ChildDeliveryEvent_AtHome_WithStandByAssist',
    '% Safe deliveries to Total Reported Deliveries':
    'Count_DeliveryEvent_Safe_AsFractionOf_Count_DeliveryEvent'
}

clean_names = {
    'District':
    'District',
    'DistrictCode':
    'lgdCode',
    'Date':
    'Date',
    'Total number of pregnant women Registered for ANC':
    'Total number of pregnant women registered for Antenatal Care',
    'Number of Pregnant women registered within first trimester':
    'Number of pregnant women registered for Antenatal Care within first trimester',
    'Total reported deliveries':
    'Total reported deliveries',
    'Institutional deliveries (Public Insts.+Pvt. Insts.)':
    'Institutional deliveries (Public Insts.+Pvt. Insts.)',
    'Deliveries Conducted at Public Institutions':
    'Deliveries conducted at public institutions',
    'Number of Home deliveries':
    'Number of home deliveries',
    'Number of home deliveries attended by SBA trained (Doctor/Nurse/ANM)':
    'Number of home deliveries attended by StandBy Assist (Doctor/Nurse/ANM)',
    '% Safe deliveries to Total Reported Deliveries':
    'Percentage of safe deliveries to total reported deliveries'
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
            clean_names=clean_names,
            final_csv_path=os.path.join(module_dir_, "test/test_gen.csv"))
        loader.generate_csv()

        result_file = open(os.path.join(module_dir_, 'test/test_gen.csv'))
        result_data = result_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir_, 'test/test_gen.csv'))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()

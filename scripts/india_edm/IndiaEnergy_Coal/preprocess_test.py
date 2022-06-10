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
import pandas as pd

from india_edm.base import EnergyIndiaBase

DATASET_NAME = "IndiaEnergy_Coal"

NODE = """Node: dcid:{statvar}
typeOf: dcs:StatisticalVariable
populationType: dcs:{pop}
measuredProperty: dcs:{mProp}
measurementQualifier: dcs:{mQual}
statType: dcs:measuredValue
{energy_type}
{consumingSector}

"""
TYPE = "energySource: dcs:{}"
SECTOR = "consumingSector: dcs:{}"

mcf_strings = {'node': NODE, 'type': TYPE, 'sector': SECTOR}

module_dir = os.path.dirname(__file__)
mcf_path = os.path.join(module_dir, "test_data/test.mcf")
tmcf_path = os.path.join(module_dir, "test_data/test.tmcf")


class EnergyIndiaTest(EnergyIndiaBase):

    def _load_data(self):
        data_path = os.path.join(module_dir, 'test_data/')

        data = pd.concat([
            pd.read_csv(data_path + f, skiprows=2)
            for f in os.listdir(data_path)
            if os.path.isfile(os.path.join(module_dir, data_path, f))
        ],
                         join='outer')

        return data


class TestPreprocess(unittest.TestCase):

    def create_test_output(self):
        expected_file = open(
            os.path.join(module_dir, 'test_data/expected_output.csv'))
        expected_data = expected_file.read()
        expected_file.close()

        base_class = EnergyIndiaTest(category='Coal',
                                     json_file='coalTypes.json',
                                     json_key='CoalType',
                                     dataset_name=DATASET_NAME,
                                     mcf_path=mcf_path,
                                     tmcf_path=tmcf_path,
                                     mcf_strings=mcf_strings)

        self.final_csv = base_class.preprocess_data()
        self.final_csv.to_csv(os.path.join(module_dir,
                                           'test_data/test_output.csv'),
                              index=False)

        result_file = open(os.path.join(module_dir,
                                        'test_data/test_output.csv'))
        result_data = expected_file.read()
        result_file.close()

        os.remove(os.path.join(module_dir, 'test_data/test_output.csv'))
        self.assertEqual(u'{}'.format(expected_data), result_data)


if __name__ == '__main__':
    unittest.main()

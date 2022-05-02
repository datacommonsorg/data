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
import json
import pandas as pd
import unittest

DATASET_NAME = 'India_WRIS_Surface'

module_dir = os.path.dirname(__file__)
json_file_path = os.path.join(module_dir, "../util/surfaceWater.json")

with open(json_file_path, 'r') as j:
    properties = json.loads(j.read())

pollutants, chem_props = properties

tmcf_file = os.path.join(module_dir, "{}.tmcf".format(DATASET_NAME))
mcf_file = os.path.join(module_dir, "{}.mcf".format(DATASET_NAME))


class TestPreprocess(unittest.TestCase):

    # Test if all properties are in MCF and TMCF files
    def test_all_nodes_in_mcf_tmcf(self):
        with open(mcf_file, 'r') as mcf, open(tmcf_file, 'r') as tmcf:
            # find() method returns the character number if query string is
            # present in the file, else returns -1
            for pollutant in pollutants['Pollutant']:
                self.assertTrue(mcf.read().find(pollutant['statvar']))
                self.assertTrue(tmcf.read().find(pollutant['statvar']))

            for chem_prop in chem_props['ChemicalProperty']:
                self.assertTrue(mcf.read().find(chem_prop['statvar']))
                self.assertTrue(tmcf.read().find(chem_prop['statvar']))

    # Test if all columns in dataset are represented as nodes in MCF files
    def test_all_columns_in_mcf_tmcf(self):
        data = pd.read_csv(
            os.path.join(module_dir, '{}.csv'.format(DATASET_NAME)))
        with open(mcf_file, 'r') as mcf, open(tmcf_file, 'r') as tmcf:
            for column in data.columns:
                self.assertTrue(mcf.read().find(column))
                self.assertTrue(tmcf.read().find(column))


if __name__ == '__main__':
    unittest.main()

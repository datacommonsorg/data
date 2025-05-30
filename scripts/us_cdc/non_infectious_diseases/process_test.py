# Copyright 2022 Google LLC
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
"""Tests for process.py"""

import os
import unittest
import pandas as pd
from pandas.testing import assert_frame_equal

from process import process_non_infectious_data


class ProcessTest(unittest.TestCase):

    def test_nors(self):
        self.maxDiff = None
        base_path = os.path.dirname(__file__)
        test_path = os.path.join(base_path, './data/testdata')
        inputfile_path = os.path.join(
            test_path, "./sample_input/NationalOutbreakPublicDataTool.xlsx")
        schema_path = os.path.join(test_path, '../col_map_exc_food.json')
        process_non_infectious_data(inputfile_path, 'Outbreak Data',
                                    schema_path, test_path)

        ## validate the csvs
        test_df = pd.read_csv(
            os.path.join(test_path, 'NORS_NonInfectious_Disease.csv'))
        expected_df = pd.read_csv(
            os.path.join(
                test_path,
                'expected_output/NORS_NonInfectious_Disease_expected.csv'))
        assert_frame_equal(test_df, expected_df)

        ## validate the template mcf
        f = open(os.path.join(test_path, 'NORS_NonInfectious_Disease.tmcf'),
                 'r')
        test_tmcf = f.read()
        f.close()

        f = open(
            os.path.join(
                test_path,
                'expected_output/NORS_NonInfectious_Disease_expected.tmcf'),
            'r')
        expected_tmcf = f.read()
        f.close()

        self.assertEqual(test_tmcf, expected_tmcf)

        # clean up
        os.remove(os.path.join(test_path, 'NORS_NonInfectious_Disease.csv'))
        os.remove(os.path.join(test_path, 'NORS_NonInfectious_Disease.tmcf'))
        os.remove(os.path.join(test_path, 'NORS_NonInfectious_Disease.mcf'))


if __name__ == '__main__':
    unittest.main()

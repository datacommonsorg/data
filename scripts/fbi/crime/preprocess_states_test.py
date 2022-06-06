# Copyright 2021 Google LLC
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
import tempfile
import unittest
from .preprocess_states import *

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class CleanCrimeFileTest(unittest.TestCase):

    def test_clean_crime_file(self):
        in_test()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv_file = os.path.join(module_dir_,
                                         'test_data/test_state_data_basic.csv')
            result_csv_file = os.path.join(tmp_dir, 'state_crime.csv')
            expected_csv_file = os.path.join(
                module_dir_, 'test_data/expected_state_crime.csv')
            create_formatted_csv_file([test_csv_file], result_csv_file)

            with open(result_csv_file, "r") as result_f:
                result_str: str = result_f.read()
                with open(expected_csv_file, "r") as expect_f:
                    expect_str: str = expect_f.read()
                    self.assertEqual(result_str, expect_str)

            os.remove(result_csv_file)

    def test_calculate_crimes(self):
        in_test()
        crime = {
            'Year': 2019,
            'State': 'WISCONSIN',
            'Population': '39752.0',
            'Violent': '20.0',
            'ViolentMurderAndNonNegligentManslaughter': '1.0',
            'ViolentRape': '6.0',
            'ViolentRobbery': '3.0',
            'ViolentAggravatedAssault': '10.0',
            'Property': '452.0',
            'PropertyBurglary': '32.0',
            'PropertyLarcenyTheft': '407.0',
            'PropertyMotorVehicleTheft': '13.0',
        }
        calculate_crimes(crime)
        self.assertEqual(
            crime, {
                'Year': 2019,
                'State': 'WISCONSIN',
                'Population': '39752.0',
                'Violent': 20,
                'ViolentMurderAndNonNegligentManslaughter': 1,
                'ViolentRape': 6,
                'ViolentRobbery': 3,
                'ViolentAggravatedAssault': 10,
                'Property': 452,
                'PropertyBurglary': 32,
                'PropertyLarcenyTheft': 407,
                'PropertyMotorVehicleTheft': 13,
                'Total': 472,
            })

    def test_create_tmcf(self):
        in_test()
        with tempfile.TemporaryDirectory() as tmp_dir:
            expected_tmcf_file = os.path.join(
                module_dir_, 'test_data/expected_fbi_state_crime.tmcf')
            result_tmcf_file = os.path.join(tmp_dir, 'FBI_state_crime.tmcf')

            create_tmcf_file(result_tmcf_file)

            with open(result_tmcf_file, "r") as result_f:
                result_str: str = result_f.read()
                with open(expected_tmcf_file, "r") as expect_f:
                    expect_str: str = expect_f.read()
                    self.assertEqual(result_str, expect_str)

            os.remove(result_tmcf_file)


if __name__ == '__main__':
    unittest.main()

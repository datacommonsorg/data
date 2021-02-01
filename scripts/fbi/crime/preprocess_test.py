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
from preprocess import clean_crime_file
from preprocess import calculate_crimes

# module_dir_ is the path to where this test is running from.
module_dir_ = os.path.dirname(__file__)


class CleanCrimeFileTest(unittest.TestCase):

    def test_clean_crime_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # TODO(hanlu): take this CSV as input, run update_and_calculate_crime_csv and validate geocodes e2e2.
            test_csv_file = os.path.join(module_dir_,
                                         'test_data/test_data_basic.csv')
            result_csv_file = os.path.join(tmp_dir, 'cleaned_data_basic.csv')
            expected_csv_file = os.path.join(
                module_dir_, 'test_data/expected_cleaned_data_basic.csv')
            year = '2019'
            with open(test_csv_file, "r") as f_input:
                with open(result_csv_file, "w") as f_output:
                    clean_crime_file(f_input, f_output, year)

                with open(result_csv_file, "r") as result_f:
                    result_str: str = result_f.read()
                    with open(expected_csv_file, "r") as expect_f:
                        expect_str: str = expect_f.read()
                        self.assertEqual(result_str, expect_str)

                os.remove(result_csv_file)

    def test_calculate_crimes(self):
        crime = {
            'Year': 2019,
            'State': 'WISCONSIN',
            'City': 'New Berlin',
            'Population': '39752.0',
            'Violent': '20.0',
            'ViolentMurderAndNonNegligentManslaughter': '1.0',
            'ViolentRape': '6.0',
            'Rape2': '0',
            'ViolentRobbery': '3.0',
            'ViolentAggravatedAssault': '10.0',
            'Property': '452.0',
            'PropertyBurglary': '32.0',
            'PropertyLarcenyTheft': '407.0',
            'PropertyMotorVehicleTheft': '13.0',
            'PropertyArson': '0.0',
            'Geocode': '5556375'
        }
        calculate_crimes(crime)
        self.assertEqual(
            crime, {
                'Year': 2019,
                'State': 'WISCONSIN',
                'City': 'New Berlin',
                'Population': '39752.0',
                'Violent': 20,
                'ViolentMurderAndNonNegligentManslaughter': 1,
                'ViolentRape': 6,
                'Rape2': 0,
                'ViolentRobbery': 3,
                'ViolentAggravatedAssault': 10,
                'Property': 452,
                'PropertyBurglary': 32,
                'PropertyLarcenyTheft': 407,
                'PropertyMotorVehicleTheft': 13,
                'PropertyArson': 0,
                'Total': 472,
                'Geocode': '5556375'
            })


if __name__ == '__main__':
    unittest.main()

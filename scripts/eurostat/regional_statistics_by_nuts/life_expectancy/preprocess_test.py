# Copyright 2020 Google LLC
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

import unittest
import os
import pandas as pd
import tempfile
import shutil
from preprocess import obtain_value, preprocess


class PreprocessTest(unittest.TestCase):

    def test_obtain_value(self):
        self.assertEqual(obtain_value('81.6'), 81.6)
        self.assertEqual(obtain_value('81.6 e'), 81.6)
        self.assertEqual(obtain_value(': '), None)
        self.assertEqual(obtain_value(':'), None)
        self.assertEqual(obtain_value(''), None)

    def test_preprocess(self):
        test_dir = tempfile.mkdtemp()
        try:
            input_file = os.path.join(test_dir, 'input.tsv')
            output_file = os.path.join(test_dir, 'output.csv')

            with open(input_file, 'w') as f:
                f.write("freq,unit,sex,age,geo\\TIME_PERIOD\t2022 \t2021 \n"
                        "A,YR,F,Y1,AT\t81.6 \t82.0 \n"
                        "A,YR,M,Y_GE85,BE\t: \t5.1 \n")

            preprocess(input_file, output_file)

            df = pd.read_csv(output_file)

            # Expected rows:
            # 2022, country/AUT, dcid:LifeExpectancy_Person_1Years_Female, 81.6
            # 2021, country/AUT, dcid:LifeExpectancy_Person_1Years_Female, 82.0
            # 2021, country/BEL, dcid:LifeExpectancy_Person_85OrMoreYears_Male, 5.1

            self.assertEqual(len(df), 3)

            # Check one row
            row = df[(df['year'] == 2022) & (df['place'] == 'country/AUT')]
            self.assertEqual(row['SV'].values[0],
                             'dcid:LifeExpectancy_Person_1Years_Female')
            self.assertEqual(row['value'].values[0], 81.6)

            row2 = df[(df['year'] == 2021) & (df['place'] == 'country/BEL')]
            self.assertEqual(row2['SV'].values[0],
                             'dcid:LifeExpectancy_Person_85OrMoreYears_Male')
            self.assertEqual(row2['value'].values[0], 5.1)

        finally:
            shutil.rmtree(test_dir)


if __name__ == '__main__':
    unittest.main()

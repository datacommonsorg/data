# Copyright 2025 Google LLC
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

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch

import download_script

class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('download_script.download_file')
    def test_download_saipe_data(self, mock_download_file):
        start_year = 2020
        end_year = 2021
        
        download_script.download_saipe_data(start_year, end_year, self.temp_dir)

        expected_calls = [
            unittest.mock.call(
                url='https://www2.census.gov/programs-surveys/saipe/datasets/2020/2020-school-districts/ussd20.xls',
                output_file=os.path.join(self.temp_dir, 'saipe_school_district_2020.xls')
            ),
            unittest.mock.call(
                url='https://www2.census.gov/programs-surveys/saipe/datasets/2021/2021-school-districts/ussd21.xls',
                output_file=os.path.join(self.temp_dir, 'saipe_school_district_2021.xls')
            )
        ]
        
        mock_download_file.assert_has_calls(expected_calls, any_order=True)
        self.assertEqual(mock_download_file.call_count, 2)

if __name__ == '__main__':
    unittest.main()

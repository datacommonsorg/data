# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import shutil
import datetime

# Add the script's directory to the Python path
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_PATH)
import download_script


class DownloadScriptTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_temp_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        download_script._OUTPUT_DIRECTORY = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_year_column_csv(self):
        # Create a dummy CSV
        csv_path = os.path.join(self.test_dir, "test.csv")
        df = pd.DataFrame({'A': [1, 2]})
        df.to_csv(csv_path, index=False)

        # Add year column
        download_script.add_year_column(csv_path, 2023)

        # Check if year column was added
        df_result = pd.read_csv(csv_path)
        self.assertIn('year', df_result.columns)
        self.assertEqual(df_result['year'].iloc[0], 2023)

    def test_add_year_column_xlsx(self):
        # Create a dummy XLSX
        xlsx_path = os.path.join(self.test_dir, "test.xlsx")
        df = pd.DataFrame({'A': [1, 2]})
        df.to_excel(xlsx_path, index=False)

        # Add year column
        download_script.add_year_column(xlsx_path, 2023)

        # Check if year column was added
        df_result = pd.read_excel(xlsx_path)
        self.assertIn('year', df_result.columns)
        self.assertEqual(df_result['year'].iloc[0], 2023)

    def test_preprocess_file(self):
        # Create a dummy CSV
        csv_path = os.path.join(self.test_dir, "test_preprocess.csv")
        df = pd.DataFrame({
            'LEAID': ['12345', '0123456'],
            'SCHID': ['6789', '01234']
        },
                              dtype=str)
        df.to_csv(csv_path, index=False)

        # Preprocess the file
        download_script.preprocess_file(csv_path)

        # Check if NCESSCH column is correct
        df_result = pd.read_csv(csv_path, dtype=str)
        self.assertIn('NCESSCH', df_result.columns)
        self.assertEqual(df_result['NCESSCH'].iloc[0], '001234506789')
        self.assertEqual(df_result['NCESSCH'].iloc[1], '012345601234')

    @patch('download_script.download_file')
    @patch('download_script.datetime')
    def test_main_flow(self, mock_datetime, mock_download):
        # Mock the current year to have a deterministic test
        mock_datetime.now.return_value = datetime.datetime(2021, 1, 1)
        download_script._CURRENT_YEAR = 2021

        # Define the behavior of the mocked download_file function
        def mock_download_side_effect(url, output_folder, unzip):
            if "2017-18" in url:
                # Create dummy files for a successful download
                os.makedirs(os.path.join(output_folder, "data"), exist_ok=True)
                # A file to keep
                df_offenses = pd.DataFrame({
                    'LEAID': ['1234567'],
                    'SCHID': ['12345']
                })
                df_offenses.to_csv(os.path.join(output_folder, "Offenses.csv"),
                                   index=False)
                # Another file to keep
                df_chronic = pd.DataFrame({
                    'LEAID': ['7654321'],
                    'SCHID': ['54321']
                })
                df_chronic.to_excel(os.path.join(output_folder, "data",
                                                 "Chronic.xlsx"),
                                    index=False)
                # A file to be deleted
                with open(os.path.join(output_folder, "extra.txt"), "w") as f:
                    f.write("delete me")
                return True
            # Simulate failure for other years
            return False

        mock_download.side_effect = mock_download_side_effect

        # Run the main function
        download_script.main(None)

        # Assertions
        final_files = os.listdir(self.test_dir)
        self.assertEqual(len(final_files), 2)  # Should only have the 2 kept files

        # Check Offenses file
        offenses_file = [f for f in final_files if 'offenses' in f][0]
        self.assertTrue(offenses_file.startswith('crdc_2017-18_offenses'))
        df_offenses = pd.read_csv(os.path.join(self.test_dir, offenses_file),
                                    dtype=str)
        self.assertIn('year', df_offenses.columns)
        df_offenses['year'] = pd.to_numeric(df_offenses['year'])
        self.assertEqual(df_offenses['year'].iloc[0], 2018)
        self.assertIn('NCESSCH', df_offenses.columns)
        self.assertEqual(df_offenses['NCESSCH'].iloc[0], '123456712345')

        # Check Chronic file
        chronic_file = [f for f in final_files if 'chronic' in f][0]
        self.assertTrue(chronic_file.startswith('crdc_2017-18_chronic'))
        df_chronic = pd.read_excel(os.path.join(self.test_dir, chronic_file),
                                   dtype=str)
        df_chronic['year'] = pd.to_numeric(df_chronic['year'])
        self.assertIn('year', df_chronic.columns)
        self.assertEqual(df_chronic['year'].iloc[0], 2018)
        self.assertIn('NCESSCH', df_chronic.columns)
        self.assertEqual(df_chronic['NCESSCH'].iloc[0], '765432154321')


if __name__ == '__main__':
    unittest.main()

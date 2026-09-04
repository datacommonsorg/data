# Copyright 2026 Google LLC
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

import pathlib
import tempfile
from unittest import mock

from absl.testing import absltest
import pandas as pd

from statvar_imports.database_on_indian_economy.india_rbi_state_statistics import rbi_download


class PreprocessFilesTest(absltest.TestCase):

    def test_preserves_workbook_and_original_error(self):
        with tempfile.TemporaryDirectory() as directory:
            workbook = pathlib.Path(directory) / 'source.xlsx'
            workbook.write_bytes(b'original workbook')
            sheets = {'Sheet1': pd.DataFrame([['State/Union Territory']])}

            with mock.patch.object(
                    rbi_download.pd, 'read_excel', return_value=sheets), \
                 mock.patch.object(
                     pd.DataFrame,
                     'map',
                     side_effect=ValueError('transform failed')), \
                 mock.patch.object(rbi_download.logging, 'fatal') as fatal:
                rbi_download.preprocess_files(directory)

            self.assertEqual(workbook.read_bytes(), b'original workbook')
            fatal.assert_called_once_with(
                'Error processing source.xlsx: transform failed')

    def test_preprocess_files_converts_numeric_headers(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = pathlib.Path(directory) / 'source.xlsx'
            initial_df = pd.DataFrame(
                [['State/Union Territory', '2015*', '2016@', '2017-18'],
                 ['Andhra Pradesh', '10.5', '20.0', '30.5']])
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                initial_df.to_excel(writer,
                                    sheet_name='Sheet1',
                                    index=False,
                                    header=False)

            rbi_download.preprocess_files(directory)

            processed = pd.read_excel(file_path,
                                      sheet_name='Sheet1',
                                      header=None)
            self.assertEqual(processed.iloc[0, 0], 'State/Union Territory')
            self.assertEqual(processed.iloc[0, 1], 2015)
            self.assertEqual(processed.iloc[0, 2], 2016)
            self.assertEqual(processed.iloc[0, 3], '2017-18')
            self.assertEqual(processed.iloc[1, 0], 'Andhra Pradesh')


if __name__ == '__main__':
    absltest.main()

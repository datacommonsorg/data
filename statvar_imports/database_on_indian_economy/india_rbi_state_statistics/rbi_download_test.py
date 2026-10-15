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


if __name__ == '__main__':
    absltest.main()

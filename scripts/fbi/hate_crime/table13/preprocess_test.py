# Copyright 2021 Google LLC
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
"""Tests for Hate Crime Table 13."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd

from . import preprocess

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '..'))  # for utils

import utils

_YEAR_INDEX = 0

_OUTPUT_COLUMNS = ('Year', 'Geo', 'StatVar', 'ObsDate', 'ObsPeriod', 'Quantity')


class HateCrimeTable13Test(unittest.TestCase):

    def test_csv(self):
        # table13/preprocess.py now uses the 2020-2023 column definitions from
        # table_config.json (which include state and agency type columns,
        # unlike the legacy 2004 7-column fixture).
        with open(os.path.join(_SCRIPT_PATH, '..', 'table_config.json'),
                  'r',
                  encoding='utf-8') as f:
            table_config = json.load(f)

        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_file_path = os.path.join(tmp_dir, '2023.csv')
            read_file = pd.DataFrame([
                [
                    'Wyoming', 'Total', None, 2, 1, 0, 0, 0, 0, 1, 0, 1, 1,
                    500000
                ],
                [
                    None, 'Cities', 'Casper1', 1, 0, 0, 0, 0, 0, 1, 0, 0, 0,
                    58000
                ],
                [
                    None, 'Universities and Colleges', 'Univ of Wyoming', 1, 1,
                    0, 0, 0, 0, 0, 0, 1, 1, 12000
                ],
            ])
            with mock.patch.object(preprocess,
                                   '_YEARWISE_CONFIG',
                                   table_config,
                                   create=True):
                read_file = preprocess._clean_dataframe(read_file, '2023', '13')
            read_file.insert(_YEAR_INDEX, 'Year', '2023')
            read_file.to_csv(csv_file_path, header=True, index=False)

            config_path = os.path.join(_SCRIPT_PATH, 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            cleaned_csv_path = os.path.join(tmp_dir, 'cleaned.csv')
            utils.create_csv_mcf([csv_file_path], cleaned_csv_path, config,
                                 _OUTPUT_COLUMNS, preprocess._write_output_csv)

            with open(cleaned_csv_path, 'r', encoding='utf-8') as f_result:
                lines = f_result.read().strip().splitlines()

            self.assertEqual(lines[0],
                             'Year,Geo,StatVar,ObsDate,ObsPeriod,Quantity')
            # State Total row resolves to geoId/56; Casper resolves to
            # geoId/5613150; non-city Universities row is filtered out.
            self.assertIn(
                '2023,geoId/56,Count_CriminalIncidents_BiasMotivationRaceOrEthnicity_IsHateCrime,2023,P1Y,2',
                lines)
            self.assertIn(
                '2023,geoId/56,Count_CriminalIncidents_IsHateCrime,2023-03,P3M,1',
                lines)
            self.assertIn(
                '2023,geoId/5613150,Count_CriminalIncidents_BiasMotivationRaceOrEthnicity_IsHateCrime,2023,P1Y,1',
                lines)
            self.assertIn(
                '2023,geoId/5613150,Count_CriminalIncidents_IsHateCrime,2023-03,P3M,1',
                lines)
            # 2 kept rows (Wyoming Total + Casper) * 10 stat columns (6 bias + 4 quarters).
            self.assertEqual(len(lines), 1 + 2 * 10)

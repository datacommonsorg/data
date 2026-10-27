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
"""
Script to automate the testing for EuroStat BMI (Body Mass Index) process script.
"""
import os
import sys
from absl import flags
import pandas as pd

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from bmi.process import EuroStatBMI
from common.unitest_common_methods import CommonTestClass
# pylint: enable=wrong-import-position
while _COMMON_PATH in sys.path:
    sys.path.remove(_COMMON_PATH)
for _mod in [
        m for m in sys.modules if m == 'common' or m.startswith('common.')
]:
    sys.modules.pop(_mod, None)
if 'input_path' in flags.FLAGS:
    delattr(flags.FLAGS, 'input_path')


class BMITest(CommonTestClass.CommonTestCases):
    """Unit tests for EuroStatBMI data processing."""
    _import_class = EuroStatBMI
    _import_name = "bmi"
    _test_module_directory = os.path.dirname(__file__)

    # pylint: disable=protected-access
    def test_parse_file_filters_excluded_geos(self):
        """Tests that _parse_file filters regional aggregate geos."""
        df = pd.DataFrame({
            'freq,unit,bmi,isced11,sex,age,geo\\TIME_PERIOD': [
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,AT',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EA',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EA18',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EA19',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EA20',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EEA',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,EFTA',
                'A,PC,BMI18P5-24,ED0-2,F,TOTAL,DE',
            ],
            '2014 ': [
                '45.6', '45.7', '45.8', '45.9', '46.0', '46.1', '46.2', '46.3'
            ],
            '2019 ': [
                '40.9', '41.0', '41.1', '41.2', '41.3', '41.4', '41.5', '41.6'
            ]
        })
        self._ob._import_name = "bmi"
        parsed_df = self._ob._parse_file('hlth_ehis_bm1e', df, 'bmi')
        self.assertNotIn('EA', parsed_df['geo'].values)
        self.assertNotIn('EA18', parsed_df['geo'].values)
        self.assertNotIn('EA19', parsed_df['geo'].values)
        self.assertNotIn('EA20', parsed_df['geo'].values)
        self.assertNotIn('EEA', parsed_df['geo'].values)
        self.assertNotIn('EFTA', parsed_df['geo'].values)
        self.assertIn('AT', parsed_df['geo'].values)
        self.assertIn('DE', parsed_df['geo'].values)

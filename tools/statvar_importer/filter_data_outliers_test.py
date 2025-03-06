# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for filter_data_outliers.py."""

import os
import sys
import unittest

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), 'util'))

import filter_data_outliers as filter_data

from config_map import ConfigMap


class FilterDataOutlierTest(unittest.TestCase):

    def test_filter_data_get_series_key(self):
        pvs = {
            'observationDate': '2023-01-01',
            'value': 100,
            'observationAbout': 'country/IND',
            'variableMeasured': 'Count_Person',
            'unit': 'Percent',
            'scalingFactor': 100
        }
        key = filter_data.filter_data_get_series_key(pvs)
        self.assertEqual(
            key,
            'observationAbout=country/IND;scalingFactor=100;unit=Percent;variableMeasured=Count_Person'
        )

        pvs = {
            'observationDate': '2023-01-01',
            'value': 100,
            'observationAbout': 'country/IND',
            'variableMeasured': 'Count_Person',
        }
        key = filter_data.filter_data_get_series_key(pvs)
        self.assertEqual(
            key, 'observationAbout=country/IND;variableMeasured=Count_Person')
        pvs = {
            'observationDate': '2023-01-01',
            'value': 100,
        }
        key = filter_data.filter_data_get_series_key(pvs)
        self.assertEqual(key, '')

    def test_filter_data_get_date_key(self):
        pvs = {
            'observationDate': '2023-01-01',
            'value': 100,
            'prop1': 'a',
            'prop2': 1
        }
        date = filter_data.filter_data_get_date_key(pvs)
        self.assertEqual(date, '2023-01-01')

    def test_filter_data_series_min_value(self):
        data = {
            '2023-01-01': {
                'value': 100,
                'variableMeasured': 'TestVar',
                'observationAbout': 'country/IND',
            },
            '2023-01-02': {
                'value': 90,
                'variableMeasured': 'TestVar',
                'observationAbout': 'country/IND',
            },
            '2023-01-03': {
                'value': 80,
                'variableMeasured': 'TestVar',
                'observationAbout': 'country/IND',
            }
        }
        filtered_data = filter_data.filter_data_series(data, min_value=85)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn('2023-01-03', filtered_data)

    def test_filter_data_series_max_value(self):
        data = {
            '2023-01-01': {
                'value': 100
            },
            '2023-01-02': {
                'value': 110
            },
            '2023-01-03': {
                'value': 120
            }
        }
        filtered_data = filter_data.filter_data_series(data, max_value=110)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn('2023-01-03', filtered_data)

    def test_filter_data_series_max_change_ratio(self):
        data = {
            '2023-01-01': {
                'value': 10
            },
            '2023-01-02': {
                'value': 72
            },
            '2023-01-03': {
                'value': 5
            }
        }
        filtered_data = filter_data.filter_data_series(dict(data),
                                                       max_change_ratio=5)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn('2023-01-02', filtered_data)
        filtered_data = filter_data.filter_data_series(dict(data),
                                                       max_change_ratio=7,
                                                       keep_recent=False)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn('2023-01-03', filtered_data)

    def test_filter_data_series_max_yearly_change_ratio(self):
        data = {
            '2021-01-01': {
                'value': 10
            },
            '2021-10-02': {
                'value': 20,  # filtered as change > 100% per year
            },
            '2022-10-07': {
                'value': 25,
            },
            '2023': {
                'value': 70,  # filtered
            }
        }
        filtered_data = filter_data.filter_data_series(dict(data),
                                                       max_yearly_change=1,
                                                       keep_recent=False)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn('2021-10-02', filtered_data)
        self.assertNotIn('2023', filtered_data)

    def test_filter_data_svobs(self):
        config = {
            'filter_data_max_change_ratio': 5,
            'filter_data_min_value': 2,
            'filter_data_max_value': 100,
        }
        data = {
            1: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRate',
                'observationDate': '2023',
                'value': '10',
            },
            2: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRate',
                'observationDate': '2022',
                'value': 101,  # Filtered by max value
            },
            3: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRate',
                'observationDate': '2021',
                'value': 1,  # Filtered by min value
            },
            4: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRate',
                'observationDate': '2020',
                'value': '20.2',
            },
            5: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRateGDP',
                'observationDate': '2020',
                'value': 52,  # filtered with keep recent
            },
            6: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRateGDP',
                'observationDate': '2021',
                'value': 7.2,  # filtered with keep_recent off
            },
            7: {
                'observationAbout': 'country/IND',
                'variableMeasured': 'GrowthRateGDP',
                'observationDate': '2022',
                'value': '5.3',  # filtered with keep recent off
            },
        }
        svobs = dict(data)
        # filter without any configs doesn't remove any data
        filtered_svobs = filter_data.filter_data_svobs(svobs, config={})
        self.assertEqual(filtered_svobs, svobs)
        filtered_svobs = filter_data.filter_data_svobs(svobs, config=config)
        self.assertEqual({2, 3, 5},
                         set(data.keys()).difference(filtered_svobs.keys()))
        # Verify retained values are not modified
        for key in filtered_svobs.keys():
            self.assertEqual(data[key], filtered_svobs[key])
        config['filter_data_keep_recent'] = False
        svobs = dict(data)
        filtered_svobs = filter_data.filter_data_svobs(svobs, config=config)
        self.assertEqual({2, 3, 6, 7},
                         set(data.keys()).difference(filtered_svobs.keys()))

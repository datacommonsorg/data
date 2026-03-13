# Copyright 2022 Google LLC
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
"""Test for events_processor.py"""

import math
import os
import s2sphere
import shapely
import sys
import tempfile
import unittest
from unittest import mock
import pandas as pd

from absl import logging

# Allows the following module imports to work when running as a script
_MODULE_DIR = os.path.dirname(__file__)
sys.path.append(_MODULE_DIR)
sys.path.append(os.path.dirname(_MODULE_DIR))
sys.path.append(os.path.dirname(os.path.dirname((_MODULE_DIR))))

import utils
import file_util

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')

from process_events import process, GeoEventsProcessor

from util.config_map import ConfigMap


class ProcessEventsTest(unittest.TestCase):

    def setUp(self):
        self._config = ConfigMap(
            filename=os.path.join(_TESTDIR, 'event_config.py'))

    def compare_files(self, expected: str, actual: str):
        '''Compare lines in files after sorting.'''
        logging.info(f'Comparing files: expected:{expected}, actual: {actual}')
        file, ext = os.path.splitext(expected)
        if ext == '.csv':
            self.compare_csv_files(expected, actual)
        with file_util.FileIO(expected, 'r') as exp:
            with file_util.FileIO(actual, 'r') as act:
                exp_lines = sorted(exp.readlines())
                act_lines = sorted(act.readlines())
                self.assertEqual(exp_lines, act_lines)

    def compare_csv_files(self,
                          expected_file: str,
                          actual_file: str,
                          ignore_columns: list = []):
        '''Compare CSV files with statvar observation data.'''
        # Sort files by columns.
        df_expected = pd.read_csv(expected_file)
        df_actual = pd.read_csv(actual_file)
        self.assertEqual(
            df_expected.columns.to_list(), df_actual.columns.to_list(),
            f'Found different columns in CSV files:' +
            f'expected:{expected_file}:{df_expected.columns.to_list()}, ' +
            f'actual:{actual_file}:{df_actual.columns.to_list()}, ')
        if ignore_columns:
            df_expected.drop(
                columns=df_expected.columns.difference(ignore_columns),
                inplace=True)
            df_actual.drop(columns=df_actual.columns.difference(ignore_columns),
                           inplace=True)
        df_expected.sort_values(by=df_expected.columns.to_list(),
                                inplace=True,
                                ignore_index=True)
        df_actual.sort_values(by=df_expected.columns.to_list(),
                              inplace=True,
                              ignore_index=True)
        self.assertTrue(
            df_expected.equals(df_actual), f'Found diffs in CSV rows:' +
            f'"{actual_file}" vs "{expected_file}":')

    def test_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_prefix = os.path.join(tmp_dir, 'events_test_')
            test_prefix = os.path.join(_TESTDIR, 'sample_floods_')
            # Process flood s2 cells into events.
            process(
                csv_files=[os.path.join(_TESTDIR, 'sample_floods_output.csv')],
                output_path=output_prefix,
                config=self._config)
            # Verify generated events.
            self.compare_csv_files(
                os.path.join(tmp_dir, 'events_test_events.csv'),
                os.path.join(_TESTDIR, test_prefix + 'events.csv'))
            self.compare_files(
                os.path.join(tmp_dir, 'events_test_events.tmcf'),
                os.path.join(_TESTDIR, test_prefix + 'events.tmcf'))
            self.compare_csv_files(
                os.path.join(tmp_dir, 'event_svobs', 'events_test_svobs.csv'),
                os.path.join(_TESTDIR, test_prefix + 'svobs.csv'))
            self.compare_files(
                os.path.join(tmp_dir, 'event_svobs', 'events_test_svobs.tmcf'),
                os.path.join(_TESTDIR, test_prefix + 'svobs.tmcf'))
            self.compare_csv_files(
                os.path.join(tmp_dir, 'place_svobs',
                             'events_test_place_svobs.csv'),
                os.path.join(_TESTDIR, test_prefix + 'place_svobs.csv'))
            self.compare_files(
                os.path.join(tmp_dir, 'place_svobs',
                             'events_test_place_svobs.tmcf'),
                os.path.join(_TESTDIR, test_prefix + 'place_svobs.tmcf'))

    def test_process_event_data(self):
        '''Verify events can be added by date.'''
        events_processor = GeoEventsProcessor(self._config)
        event_data = {
            's2CellId': 's2CellId/0x89c2590000000000',
            'area': 0.5,
            'water': 1,
            'date': '2022-10',
        }
        logging.set_verbosity(1)
        self.assertTrue(events_processor.process_event_data(event_data))
        active_events = events_processor.get_active_event_ids('2022-10')
        self.assertEqual(1, len(active_events))
        event_id = active_events[0]
        event = events_processor.get_event_by_id(event_id)
        self.assertTrue('floodEvent/2022-10_s2CellId/0x89c2590000000000',
                        event.event_id())
        event_pvs = events_processor.get_event_output_properties(event_id)
        self.assertTrue(event_data['s2CellId'] in event_pvs['affectedPlace'])
        self.assertEqual(0.5, event_pvs['AreaSqKm'])

        # Add data for neighbouring place that should get aggregated into event.
        event_data2 = dict(event_data)
        event_data2['s2CellId'] = 's2CellId/0x89c2570000000000'
        self.assertTrue(events_processor.process_event_data(event_data2))

        # Verify both cells are in affected place
        updated_event_pvs = events_processor.get_event_output_properties(
            event_id)
        self.assertTrue(
            event_data['s2CellId'] in updated_event_pvs['affectedPlace'])
        self.assertTrue(
            event_data2['s2CellId'] in updated_event_pvs['affectedPlace'])
        self.assertEqual(1.0, updated_event_pvs['AreaSqKm'])

        # Add data for place too far away that is not aggregated.
        event_data3 = dict(event_data)
        event_data3['s2CellId'] = 's2CellId/0x89c3ab0000000000'
        self.assertTrue(events_processor.process_event_data(event_data3))
        active_events = events_processor.get_active_event_ids('2022-10')
        self.assertEqual(2, len(active_events))

        updated_event_pvs = events_processor.get_event_output_properties(
            event_id)
        self.assertFalse(
            event_data3['s2CellId'] in updated_event_pvs['affectedPlace'])
        self.assertEqual(1.0, updated_event_pvs['AreaSqKm'])

        # Add a neighbouring place with more recent date that is added to
        # existing event.
        event_data4 = dict(event_data)
        event_data4['s2CellId'] = 's2CellId/0x89c2f70000000000'
        event_data4['date'] = '2022-11'
        self.assertTrue(events_processor.process_event_data(event_data4))
        active_events = events_processor.get_active_event_ids('2022-11')
        self.assertEqual(2, len(active_events))
        updated_event_pvs = events_processor.get_event_output_properties(
            event_id)
        self.assertTrue(
            event_data4['s2CellId'] in updated_event_pvs['affectedPlace'])
        self.assertEqual(1.5, updated_event_pvs['AreaSqKm'])
        self.assertEqual('P32D', updated_event_pvs['observationPeriod'])

        # Add a neighbouring place with recent date too new
        # that is not added to existing event.
        event_data5 = dict(event_data)
        event_data5['s2CellId'] = 's2CellId/0x89c2f90000000000'
        event_data5['date'] = '2023-01'
        self.assertTrue(events_processor.process_event_data(event_data5))
        # All older events are deactivated and a new event is added for
        # event_data5
        active_events = events_processor.get_active_event_ids('2023-01')
        self.assertEqual(1, len(active_events))
        # Verify older event is not modified.
        old_event_pvs = events_processor.get_event_output_properties(event_id)
        self.assertEqual(old_event_pvs, updated_event_pvs)
        # Verify new event has a single place.
        new_event_pvs = events_processor.get_event_output_properties(
            active_events[0])
        self.assertEqual(1, new_event_pvs['AffectedPlaceCount'])
        self.assertEqual('floodEvent/2023-01_0x89c2f90000000000',
                         new_event_pvs['dcid'])

    @mock.patch('process_events.dc_api_batched_wrapper')
    @mock.patch('process_events.get_datacommons_client')
    def test_prefetch_placeid_property_uses_v2_client(
            self, mock_get_datacommons_client, mock_dc_api_batched_wrapper):
        events_processor = GeoEventsProcessor(self._config)
        mock_client = mock.Mock()
        mock_get_datacommons_client.return_value = mock_client

        def _mock_v2_property_response(**kwargs):
            prop = kwargs['args']['properties']
            if prop == 'latitude':
                return {
                    'geoId/06': {
                        'arcs': {
                            'latitude': {
                                'nodes': [{
                                    'value': '37.148573'
                                }]
                            }
                        }
                    }
                }
            if prop == 'longitude':
                return {
                    'geoId/06': {
                        'arcs': {
                            'longitude': {
                                'nodes': [{
                                    'value': '-119.5406515'
                                }]
                            }
                        }
                    }
                }
            return {}

        mock_dc_api_batched_wrapper.side_effect = _mock_v2_property_response

        events_processor.prefetch_placeid_property('latitude',
                                                   ['dcid:geoId/06'])
        events_processor.prefetch_placeid_property('longitude',
                                                   ['dcid:geoId/06'])

        mock_dc_api_batched_wrapper.assert_any_call(
            function=mock_client.node.fetch_property_values,
            dcids=['geoId/06'],
            args={
                'properties': 'latitude',
            },
            dcid_arg_kw='node_dcids',
            config=self._config)
        mock_dc_api_batched_wrapper.assert_any_call(
            function=mock_client.node.fetch_property_values,
            dcids=['geoId/06'],
            args={
                'properties': 'longitude',
            },
            dcid_arg_kw='node_dcids',
            config=self._config)
        self.assertEqual(['37.148573'],
                         events_processor.get_place_property(
                             'geoId/06', 'latitude'))
        self.assertEqual(['-119.5406515'],
                         events_processor.get_place_property(
                             'geoId/06', 'longitude'))

        lat, lng = events_processor._get_place_lat_lng('geoId/06')
        self.assertAlmostEqual(37.148573, lat, places=6)
        self.assertAlmostEqual(-119.5406515, lng, places=6)

    @mock.patch('process_events.dc_api_batched_wrapper')
    @mock.patch('process_events.get_datacommons_client')
    def test_prefetch_placeid_property_negative_cache(
            self, mock_get_datacommons_client, mock_dc_api_batched_wrapper):
        events_processor = GeoEventsProcessor(self._config)
        mock_client = mock.Mock()
        mock_get_datacommons_client.return_value = mock_client
        mock_dc_api_batched_wrapper.return_value = {}

        events_processor.prefetch_placeid_property('typeOf', ['dcid:geoId/00'])
        events_processor.prefetch_placeid_property('typeOf', ['dcid:geoId/00'])

        mock_dc_api_batched_wrapper.assert_called_once_with(
            function=mock_client.node.fetch_property_values,
            dcids=['geoId/00'],
            args={
                'properties': 'typeOf',
            },
            dcid_arg_kw='node_dcids',
            config=self._config)
        self.assertIn('geoId/00',
                      events_processor._place_property_cache['typeOf'])
        self.assertEqual([],
                         events_processor.get_place_property(
                             'geoId/00', 'typeOf'))

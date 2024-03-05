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
"""Tests for raster_to_csv.py"""

import math
import os
import sys
import tempfile
import unittest

from absl import logging
import s2sphere
import shapely

# Allows the following module imports to work when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(_SCRIPTS_DIR)
sys.path.append(os.path.dirname(_SCRIPTS_DIR))

import utils

_TESTDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                        'test_data')


class DictUtilsTest(unittest.TestCase):
    dict1 = {
        'int_key1': 10,
        'int_key2': 20,
        'int_key3': 30,
        'float_key1': 12.12,
        'float_key2': 20.123,
        'float_key3': 33.33,
        'string_key1': 'String Value',
        'string_key2': 'Value1',
    }

    def setUp(self):
        self.maxDiff = None

    def test_dict_filter_values(self):
        filter_config = {
            'int_key1': {
                'min': 10,
                'max': 100,
            },
            'int_key2': {
                'min': 1000,
            },
            'float_key3': {
                'max': 10000.0,
            },
            'string_key1': {
                'regex': r'^[^ ]*$'
            },
            'string_key2': {
                'regex': r'^[^ ]*$'
            },
            'param1': {
                'ignore': 'drop'
            },
        }
        filter_dict = dict(self.dict1)
        utils.dict_filter_values(filter_dict, filter_config)
        expected_dict = dict(self.dict1)
        expected_dict.pop('int_key2')  # dropped as < min(1000)
        expected_dict.pop('string_key1')
        self.assertEqual(expected_dict, filter_dict)

        # Test ignore
        self.assertFalse(
            utils.dict_filter_values({'param1': ['value1', 'drop this']},
                                     filter_config))
        self.assertTrue(
            utils.dict_filter_values(
                {
                    'param1': 'allowed',
                    'param2': 'do not drop this'
                }, filter_config))


class S2CellUtilsTest(unittest.TestCase):

    def test_is_s2_cell_id(self):
        self.assertFalse(utils.is_s2_cell_id(''))
        self.assertTrue(utils.is_s2_cell_id('dcid:s2CellId/0x54ce1f0000000000'))
        self.assertTrue(utils.is_s2_cell_id('s2CellId/0x0000010000000000'))
        self.assertFalse(utils.is_s2_cell_id('0x0000010000000000'))

    def test_s2_cell_from_latlng(self):
        self.assertEqual(
            s2sphere.CellId(0x11282F0000000000),
            utils.s2_cell_from_latlng(10.1, 20.2, 10),
        )

    def test_s2_cell_to_dcid(self):
        self.assertEqual(
            'dcid:s2CellId/0x0000050000000000',
            utils.s2_cell_to_dcid(s2sphere.CellId(0x0000050000000000)),
        )
        self.assertEqual(
            'dcid:s2CellId/0x0000050000000000',
            utils.s2_cell_to_dcid(0x0000050000000000),
        )

    def test_s2_cell_from_dcid(self):
        self.assertEqual(
            s2sphere.CellId(0x0000050000000000),
            utils.s2_cell_from_dcid('dcid:s2CellId/0x0000050000000000'),
        )
        self.assertEqual(
            s2sphere.CellId(0x0000070000000000),
            utils.s2_cell_from_dcid('s2CellId/0x0000070000000000'),
        )

    def test_s2_cell_distance(self):
        self.assertTrue(
            math.isclose(
                7.84,
                utils.s2_cells_distance(0x0000050000000000, 0x0000070000000000),
                rel_tol=1e-2,
            ))

    def test_s2_cell_area(self):
        self.assertTrue(
            math.isclose(53.23,
                         utils.s2_cell_area(0x0000050000000000),
                         rel_tol=1e-2))
        self.assertTrue(
            math.isclose(
                68.95,
                utils.s2_cell_area(utils.s2_cell_from_latlng(0, 0, 10)),
                rel_tol=1e-2,
            ))
        self.assertTrue(
            math.isclose(
                81.37,
                utils.s2_cell_area(utils.s2_cell_from_latlng(80, 90, 10)),
                rel_tol=1e-2,
            ))

    def test_s2_cell_get_neighbor_ids(self):
        s2_cell = utils.s2_cell_from_latlng(10, 20, 10)
        neighbors = utils.s2_cell_get_neighbor_ids(s2_cell)
        expected_neighbors = [
            'dcid:s2CellId/0x10d7e10000000000',
            'dcid:s2CellId/0x10d7d90000000000',
            'dcid:s2CellId/0x10d7df0000000000',
            'dcid:s2CellId/0x1128230000000000',
            'dcid:s2CellId/0x11281f0000000000',
            'dcid:s2CellId/0x1128270000000000',
            'dcid:s2CellId/0x1128190000000000',
            'dcid:s2CellId/0x1128250000000000',
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            n_cell = utils.s2_cell_from_dcid(n)
            self.assertEqual(n_cell.level(), s2_cell.level())

    def test_latlng_cell_area(self):
        self.assertEqual(12309, int(utils.latlng_cell_area(0, 0, 1, 1)))
        self.assertEqual(21, int(utils.latlng_cell_area(80, -80, 0.1, 0.1)))


class GridCellUtilsTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def test_is_grid_id(self):
        self.assertFalse(utils.is_grid_id(''))
        self.assertFalse(utils.is_grid_id('s2CellId/0x1128250000000000'))
        self.assertTrue(utils.is_grid_id('grid_2/-20.12_30.12'))
        self.assertTrue(utils.is_grid_id('dcid:grid_1/10_20'))
        self.assertFalse(utils.is_grid_id('ipcc_5/10_20'))
        self.assertTrue(utils.is_ipcc_id('ipcc_50/34.25_-85.25_USA'))

    def test_grid_id_from_latlng(self):
        self.assertEqual('dcid:grid_1/20_30',
                         utils.grid_id_from_lat_lng(1, 20, 30))

    def test_grid_ids_distance(self):
        self.assertTrue(
            math.isclose(
                1541.85,
                utils.grid_ids_distance(
                    utils.grid_id_from_lat_lng(1, 10, 20),
                    utils.grid_id_from_lat_lng(1, 20, 30),
                ),
                rel_tol=1e-2,
            ))
        self.assertTrue(
            math.isclose(
                143.84,
                utils.grid_ids_distance('ipcc_50/34.25_-85.25_USA',
                                        'ipcc_50/35.25_-84.25_USA'),
                rel_tol=1e-2,
            ))

    def test_grid_area(self):
        self.assertTrue(
            math.isclose(10248.33,
                         utils.grid_area('dcid:grid_1/34_-85'),
                         rel_tol=1e-2))
        self.assertTrue(
            math.isclose(2554.56,
                         utils.grid_area('ipcc_50/34.25_-85.25_USA'),
                         rel_tol=1e-2))

    def test_grid_get_neighbor_ids(self):
        grid_id = 'dcid:ipcc_50/26.25_81.75_IND'
        neighbors = utils.grid_get_neighbor_ids(grid_id)
        expected_neighbors = [
            'dcid:ipcc_50/25.75_81.25_IND',
            'dcid:ipcc_50/25.75_81.75_IND',
            'dcid:ipcc_50/25.75_82.25_IND',
            'dcid:ipcc_50/26.25_81.25_IND',
            'dcid:ipcc_50/26.25_82.25_IND',
            'dcid:ipcc_50/26.75_81.25_IND',
            'dcid:ipcc_50/26.75_81.75_IND',
            'dcid:ipcc_50/26.75_82.25_IND',
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            place_neighbors = utils.grid_get_neighbor_ids(n)
            self.assertTrue(grid_id in place_neighbors)
        grid_id = 'dcid:grid_1/10_-65'
        neighbors = utils.grid_get_neighbor_ids(grid_id)
        expected_neighbors = [
            'dcid:grid_1/9_-66',
            'dcid:grid_1/9_-65',
            'dcid:grid_1/9_-64',
            'dcid:grid_1/10_-66',
            'dcid:grid_1/10_-64',
            'dcid:grid_1/11_-66',
            'dcid:grid_1/11_-65',
            'dcid:grid_1/11_-64',
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            place_neighbors = utils.grid_get_neighbor_ids(n)
            self.assertTrue(grid_id in place_neighbors)

    def test_grid_to_polygon(self):
        self.assertEqual(
            {
                'coordinates': ((
                    (81.5, 26.0),
                    (81.5, 26.5),
                    (82.0, 26.5),
                    (82.0, 26.0),
                    (81.5, 26.0),
                ),),
                'type': 'Polygon',
            },
            shapely.geometry.mapping(
                utils.grid_to_polygon('dcid:ipcc_50/26.25_81.75_IND')),
        )
        # Polygon at edge doesn't go over max lat/lng.
        self.assertEqual(
            {
                'coordinates': ((
                    (179.5, 89.5),
                    (179.5, 90.0),
                    (180.0, 90.0),
                    (180.0, 89.5),
                    (179.5, 89.5),
                ),),
                'type': 'Polygon',
            },
            shapely.geometry.mapping(utils.place_to_polygon('grid_1/90_180')),
        )

        self.assertEqual(
            {
                'coordinates': ((
                    (20.04496617551588, 10.074733389893098),
                    (20.140259352250975, 10.068731256770613),
                    (20.140259352250975, 10.153784179458425),
                    (20.04496617551588, 10.159834880513182),
                    (20.04496617551588, 10.074733389893098),
                ),),
                'type': 'Polygon',
            },
            shapely.geometry.mapping(
                utils.place_to_polygon('s2CellId/0x1128250000000000')),
        )


class StrUtilsTest(unittest.TestCase):

    def test_strip_namespace(self):
        self.assertEqual('country/IND',
                         utils.strip_namespace('dcid:country/IND'))
        self.assertEqual(
            'ipcc_50/26.25_81.75_IND',
            utils.strip_namespace('dcs:ipcc_50/26.25_81.75_IND'),
        )
        self.assertEqual(
            's2CellId/0x1128250000000000',
            utils.strip_namespace('s2CellId/0x1128250000000000'),
        )

    def test_add_namespace(self):
        self.assertEqual('dcid:country/IND', utils.add_namespace('country/IND'))
        self.assertEqual(
            'dcid:ipcc_50/26.25_81.75_IND',
            utils.add_namespace('dcs:ipcc_50/26.25_81.75_IND'),
        )
        self.assertEqual(
            'dcid:s2CellId/0x1128250000000000',
            utils.add_namespace('s2CellId/0x1128250000000000'),
        )

    def test_str_get_numeric_vlaue(self):
        self.assertEqual(10.1, utils.str_get_numeric_value('10.1'))
        self.assertEqual(-11.23, utils.str_get_numeric_value(' -11.23 '))
        self.assertEqual(1234, utils.str_get_numeric_value(' 1,234 '))
        self.assertEqual(6543210.12,
                         utils.str_get_numeric_value(' 6,543,210.12 '))
        self.assertEqual(0.123, utils.str_get_numeric_value(' .123 '))
        self.assertEqual(2100, utils.str_get_numeric_value('2.1e+3'))
        self.assertEqual(2748, utils.str_get_numeric_value('0xabc'))
        self.assertEqual(1234567, utils.str_get_numeric_value('1.234.567'))
        self.assertEqual(1.23, utils.str_get_numeric_value(['1.23', '4.56']))
        self.assertEqual(2.34, utils.str_get_numeric_value([2.34, 5.67]))
        self.assertEqual(None, utils.str_get_numeric_value('abc'))
        self.assertEqual(None, utils.str_get_numeric_value('123abc'))


class DateUtilsTest(unittest.TestCase):

    def test_date_parse_time_period(self):
        self.assertEqual((1, 'days'), utils.date_parse_time_period('P1D'))
        self.assertEqual((10, 'days'), utils.date_parse_time_period('10D'))
        self.assertEqual((-7, 'days'), utils.date_parse_time_period('-7D'))

        self.assertEqual((1, 'months'), utils.date_parse_time_period('P1M'))
        self.assertEqual((3, 'months'), utils.date_parse_time_period('3M'))

        self.assertEqual((1, 'years'), utils.date_parse_time_period('P1Y'))
        self.assertEqual((5, 'years'), utils.date_parse_time_period('5Y'))

    def test_date_advance_by_time_period(self):
        self.assertEqual(
            utils.date_today(),
            utils.date_advance_by_period(utils.date_yesterday(), 'P1D'),
        )
        self.assertEqual('2023-04-10',
                         utils.date_advance_by_period('2023-04-20', 'P-10D'))
        self.assertEqual(
            '2023-06', utils.date_advance_by_period('2023-04', 'P2M', '%Y-%m'))
        self.assertEqual('2033',
                         utils.date_advance_by_period('2023', '10Y', '%Y'))

    def test_date_format_by_time_period(self):
        self.assertEqual('2023-04-10',
                         utils.date_format_by_time_period('2023-04-10', 'P1D'))
        self.assertEqual('2022-04',
                         utils.date_format_by_time_period('2022-04-10', 'P3M'))
        self.assertEqual('2021',
                         utils.date_format_by_time_period('2021-01-10', '1Y'))

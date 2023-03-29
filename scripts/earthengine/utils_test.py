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
import s2sphere
import shapely
import sys
import tempfile
import unittest

from absl import logging

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
        return

    def test_dict_aggregate_values(self):
        '''Test aggreation of dictionaries with dict_aggregate_test().'''
        dict2 = {
            'int_key1': 11,
            'int_key2': 2,
            'float_key2': 4.56,
            'float_key3': 44.44,
            'string_key1': 'Value2',
            'string_key2': 'Value1,StrValue2',
            'string_key3': 'New String',
        }

        config = {
            'aggregate': 'sum',  # default aggregate
            'int_key2': {
                'aggregate': 'max'
            },
            'float_key2': {
                'aggregate': 'min'
            },
            'float_key3': {
                'aggregate': 'mean'
            },
            'string_key2': {
                'aggregate': 'list'
            },
        }

        merged_dict = dict(dict2)
        utils.dict_aggregate_values(self.dict1, merged_dict, config)
        expected_dict = {
            'int_key1': self.dict1['int_key1'] + dict2['int_key1'],
            'int_key2': max(self.dict1['int_key2'], dict2['int_key2']),
            'int_key3': self.dict1['int_key3'],
            'float_key1': self.dict1['float_key1'],
            'float_key2': min(self.dict1['float_key2'], dict2['float_key2']),
            'float_key3': (self.dict1['float_key3'] + dict2['float_key3']) / 2,
            '#float_key3:count': 2,
            'string_key1': 'Value2String Value',  # sum
            'string_key2': 'StrValue2,Value1',  # list
            'string_key3': 'New String',
        }
        self.assertEqual(expected_dict, merged_dict)

        utils.dict_aggregate_values(dict2, merged_dict, config)
        expected_dict['int_key1'] += dict2['int_key1']
        expected_dict['float_key3'] = (self.dict1['float_key3'] +
                                       2 * dict2['float_key3']) / 3
        expected_dict['#float_key3:count'] = 3
        expected_dict['string_key1'] = 'Value2String ValueValue2'
        expected_dict['string_key2'] = 'StrValue2,Value1'
        expected_dict['string_key3'] = 'New StringNew String'
        self.assertEqual(expected_dict, merged_dict)

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
        }
        filter_dict = dict(self.dict1)
        utils.dict_filter_values(filter_dict, filter_config)
        expected_dict = dict(self.dict1)
        expected_dict.pop('int_key2')  # dropped as < min(1000)
        expected_dict.pop('string_key1')
        self.assertEqual(expected_dict, filter_dict)


class S2CellUtilsTest(unittest.TestCase):

    def test_is_s2_cell_id(self):
        self.assertFalse(utils.is_s2_cell_id(''))
        self.assertTrue(utils.is_s2_cell_id('dcid:s2CellId/0x54ce1f0000000000'))
        self.assertTrue(utils.is_s2_cell_id('s2CellId/0x0000010000000000'))
        self.assertFalse(utils.is_s2_cell_id('0x0000010000000000'))

    def test_s2_cell_from_latlng(self):
        self.assertEqual(s2sphere.CellId(0x11282f0000000000),
                         utils.s2_cell_from_latlng(10.1, 20.2, 10))

    def test_s2_cell_to_dcid(self):
        self.assertEqual(
            'dcid:s2CellId/0x0000050000000000',
            utils.s2_cell_to_dcid(s2sphere.CellId(0x0000050000000000)))
        self.assertEqual('dcid:s2CellId/0x0000050000000000',
                         utils.s2_cell_to_dcid(0x0000050000000000))

    def test_s2_cell_from_dcid(self):
        self.assertEqual(
            s2sphere.CellId(0x0000050000000000),
            utils.s2_cell_from_dcid('dcid:s2CellId/0x0000050000000000'))
        self.assertEqual(s2sphere.CellId(0x0000070000000000),
                         utils.s2_cell_from_dcid('s2CellId/0x0000070000000000'))

    def test_s2_cell_distance(self):
        self.assertTrue(
            math.isclose(7.84,
                         utils.s2_cells_distance(0x0000050000000000,
                                                 0x0000070000000000),
                         rel_tol=1e-2))

    def test_s2_cell_area(self):
        self.assertTrue(
            math.isclose(53.23,
                         utils.s2_cell_area(0x0000050000000000),
                         rel_tol=1e-2))
        self.assertTrue(
            math.isclose(68.95,
                         utils.s2_cell_area(utils.s2_cell_from_latlng(0, 0,
                                                                      10)),
                         rel_tol=1e-2))
        self.assertTrue(
            math.isclose(81.37,
                         utils.s2_cell_area(
                             utils.s2_cell_from_latlng(80, 90, 10)),
                         rel_tol=1e-2))

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
            'dcid:s2CellId/0x1128250000000000'
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            n_cell = utils.s2_cell_from_dcid(n)
            self.assertEqual(n_cell.level(), s2_cell.level())

    def test_latlng_cell_area(self):
        self.assertEqual(12309, int(utils.latlng_cell_area(0, 0, 1, 1)))
        self.assertEqual(21, int(utils.latlng_cell_area(80, -80, .1, .1)))


class GridCellUtilsTest(unittest.TestCase):

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
            math.isclose(1541.85,
                         utils.grid_ids_distance(
                             utils.grid_id_from_lat_lng(1, 10, 20),
                             utils.grid_id_from_lat_lng(1, 20, 30)),
                         rel_tol=1e-2))
        self.assertTrue(
            math.isclose(143.84,
                         utils.grid_ids_distance('ipcc_50/34.25_-85.25_USA',
                                                 'ipcc_50/35.25_-84.25_USA'),
                         rel_tol=1e-2))

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
            'dcid:ipcc_50/25.75_81.25_IND', 'dcid:ipcc_50/25.75_81.75_IND',
            'dcid:ipcc_50/25.75_82.25_IND', 'dcid:ipcc_50/26.25_81.25_IND',
            'dcid:ipcc_50/26.25_82.25_IND', 'dcid:ipcc_50/26.75_81.25_IND',
            'dcid:ipcc_50/26.75_81.75_IND', 'dcid:ipcc_50/26.75_82.25_IND'
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            place_neighbors = utils.grid_get_neighbor_ids(n)
            self.assertTrue(grid_id in place_neighbors)
        grid_id = 'dcid:grid_1/10_-65'
        neighbors = utils.grid_get_neighbor_ids(grid_id)
        expected_neighbors = [
            'dcid:grid_1/9_-66', 'dcid:grid_1/9_-65', 'dcid:grid_1/9_-64',
            'dcid:grid_1/10_-66', 'dcid:grid_1/10_-64', 'dcid:grid_1/11_-66',
            'dcid:grid_1/11_-65', 'dcid:grid_1/11_-64'
        ]
        self.assertEqual(expected_neighbors, neighbors)
        for n in neighbors:
            place_neighbors = utils.grid_get_neighbor_ids(n)
            self.assertTrue(grid_id in place_neighbors)

    def test_grid_to_polygon(self):
        self.assertEqual(
            {
                'coordinates': (((81.5, 26.0), (81.5, 26.5), (82.0, 26.5),
                                 (82.0, 26.0), (81.5, 26.0)),),
                'type': 'Polygon'
            },
            shapely.geometry.mapping(
                utils.grid_to_polygon('dcid:ipcc_50/26.25_81.75_IND')))
        # Polygon at edge doesn't go over max lat/lng.
        self.assertEqual(
            {
                'coordinates': (((179.5, 89.5), (179.5, 90.0), (180.0, 90.0),
                                 (180.0, 89.5), (179.5, 89.5)),),
                'type': 'Polygon'
            },
            shapely.geometry.mapping(utils.place_to_polygon('grid_1/90_180')))

        self.assertEqual(
            {
                'coordinates': (((20.04496617551588, 10.074733389893098),
                                 (20.140259352250975, 10.068731256770613),
                                 (20.140259352250975, 10.153784179458425),
                                 (20.04496617551588, 10.159834880513182),
                                 (20.04496617551588, 10.074733389893098)),),
                'type': 'Polygon'
            },
            shapely.geometry.mapping(
                utils.place_to_polygon('s2CellId/0x1128250000000000')))


class FileUtilsTest(unittest.TestCase):

    def test_file_get_matching(self):
        files = utils.file_get_matching(os.path.join(_TESTDIR, 'sample*.csv'))
        self.assertTrue(len(files) > 2)
        for file in files:
            self.assertTrue(os.path.exists(file))

    def test_file_get_estimate_num_rows(self):
        files = utils.file_get_matching(os.path.join(_TESTDIR, 'sample*.csv'))
        for file in files:
            estimate_rows = utils.file_estimate_num_rows(file)
            with open(file, 'r') as fp:
                num_lines = len(fp.readlines())
                self.assertTrue(
                    math.isclose(num_lines, estimate_rows, rel_tol=1))

    def test_file_load_csv_dict(self):
        csv_dict = utils.file_load_csv_dict(
            os.path.join(_TESTDIR, 'sample_output.csv'), 's2CellId')
        self.assertTrue(len(csv_dict) > 0)
        test_key = 'dcid:s2CellId/0x39925b1c00000000'
        self.assertTrue(test_key in csv_dict)
        self.assertEqual('1', csv_dict[test_key]['water'])
        self.assertEqual('13', csv_dict[test_key]['s2Level'])

    def test_file_write_load_py_dict(self):
        test_dict = {'test_key': 'test_value', 'int_key': 10, 'list': [1, 2, 3]}
        # read/write dict as a py file
        fd, tmp_py_filename = tempfile.mkstemp(suffix='.py')
        utils.file_write_py_dict(test_dict, tmp_py_filename)
        self.assertTrue(os.path.getsize(tmp_py_filename) > 10)
        read_dict = utils.file_load_py_dict(tmp_py_filename)
        self.assertEqual(test_dict, read_dict)
        # Repeat test with pkl file.
        fd, tmp_pkl_filename = tempfile.mkstemp(suffix='.pkl')
        utils.file_write_py_dict(test_dict, tmp_pkl_filename)
        self.assertTrue(os.path.getsize(tmp_pkl_filename) > 10)
        read_pkl_dict = utils.file_load_py_dict(tmp_pkl_filename)
        self.assertEqual(test_dict, read_pkl_dict)
        # check pkl and py files are different.
        self.assertTrue(
            os.path.getsize(tmp_pkl_filename) != os.path.getsize(
                tmp_py_filename))


class StrUtilsTest(unittest.TestCase):

    def test_strip_namespace(self):
        self.assertEqual('country/IND',
                         utils.strip_namespace('dcid:country/IND'))
        self.assertEqual('ipcc_50/26.25_81.75_IND',
                         utils.strip_namespace('dcs:ipcc_50/26.25_81.75_IND'))
        self.assertEqual('s2CellId/0x1128250000000000',
                         utils.strip_namespace('s2CellId/0x1128250000000000'))

    def test_add_namespace(self):
        self.assertEqual('dcid:country/IND', utils.add_namespace('country/IND'))
        self.assertEqual('dcid:ipcc_50/26.25_81.75_IND',
                         utils.add_namespace('dcs:ipcc_50/26.25_81.75_IND'))
        self.assertEqual('dcid:s2CellId/0x1128250000000000',
                         utils.add_namespace('s2CellId/0x1128250000000000'))

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

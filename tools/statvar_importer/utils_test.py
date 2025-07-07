# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import os
from unittest.mock import patch
import pandas as pd

from utils import (capitalize_first_char, str_from_number, pvs_has_any_prop,
                   is_place_dcid, get_observation_period_for_date,
                   get_observation_date_format, get_filename_for_url,
                   download_csv_from_url, shard_csv_data, convert_xls_to_csv,
                   prepare_input_data)


class TestCapitalizeFirstChar(unittest.TestCase):

    def test_hello(self):
        self.assertEqual(capitalize_first_char("hello"), "Hello")

    def test_already_capitalized(self):
        self.assertEqual(capitalize_first_char("Hello"), "Hello")

    def test_empty_string(self):
        self.assertEqual(capitalize_first_char(""), "")

    def test_numeric_first_char(self):
        self.assertEqual(capitalize_first_char("1hello"), "1hello")

    def test_none_input(self):
        self.assertEqual(capitalize_first_char(None), None)

    def test_integer_input(self):
        self.assertEqual(capitalize_first_char(123), 123)

    def test_space_first_char(self):
        self.assertEqual(capitalize_first_char(" h"), " h")

    def test_single_char(self):
        self.assertEqual(capitalize_first_char("h"), "H")


class TestStrFromNumber(unittest.TestCase):

    def test_integer(self):
        self.assertEqual(str_from_number(10), "10")

    def test_float(self):
        self.assertEqual(str_from_number(10.0), "10")

    def test_float_with_decimal(self):
        self.assertEqual(str_from_number(10.123), "10.123")

    def test_precision(self):
        self.assertEqual(str_from_number(10.123456, precision_digits=3),
                         "10.123")

    def test_rounding(self):
        self.assertEqual(str_from_number(10.999, precision_digits=2), "11.0")

    def test_trailing_zeros(self):
        self.assertEqual(str_from_number(10.1200, precision_digits=4), "10.12")


class TestPvsHasAnyProp(unittest.TestCase):

    def test_prop_exists(self):
        self.assertTrue(
            pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop1"]))

    def test_one_of_props_exists(self):
        self.assertTrue(
            pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop2", "prop3"]))

    def test_prop_does_not_exist(self):
        self.assertFalse(
            pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop3"]))

    def test_prop_is_none(self):
        self.assertFalse(
            pvs_has_any_prop({
                "prop1": None,
                "prop2": "val2"
            }, ["prop1"]))

    def test_empty_pvs(self):
        self.assertFalse(pvs_has_any_prop({}, ["prop1"]))

    def test_empty_props(self):
        self.assertFalse(pvs_has_any_prop({"prop1": "val1"}, []))

    def test_none_props(self):
        self.assertFalse(pvs_has_any_prop({"prop1": "val1"}, None))

    def test_none_pvs(self):
        self.assertFalse(pvs_has_any_prop(None, ["prop1"]))


class TestIsPlaceDcid(unittest.TestCase):

    def test_dcid_prefix(self):
        # Assumes valid if it has a dcid: prefix.
        self.assertTrue(is_place_dcid("dcid:country/USA"))

    def test_dcs_prefix(self):
        # Assumes valid if it has a dcs: prefix.
        self.assertTrue(is_place_dcid("dcs:country/USA"))

    def test_no_prefix_valid(self):
        # Valid non-prefixed DCID.
        self.assertTrue(is_place_dcid("country/USA"))

    def test_no_slash(self):
        # Invalid non-prefixed DCID (no slash).
        self.assertFalse(is_place_dcid("countryUSA"))

    def test_special_chars_with_prefix(self):
        # Assumes valid because of prefix (heuristic).
        self.assertTrue(is_place_dcid("dcid:!@#"))

    def test_special_chars_no_prefix(self):
        # Invalid non-prefixed DCID (special chars).
        self.assertFalse(is_place_dcid("country/USA!"))

    def test_empty_string(self):
        self.assertFalse(is_place_dcid(""))

    def test_none(self):
        self.assertFalse(is_place_dcid(None))


class TestGetObservationPeriodForDate(unittest.TestCase):

    def test_year(self):
        self.assertEqual(get_observation_period_for_date("2023"), "P1Y")

    def test_year_month(self):
        self.assertEqual(get_observation_period_for_date("2023-01"), "P1M")

    def test_year_month_day(self):
        self.assertEqual(get_observation_period_for_date("2023-01-15"), "P1D")

    def test_slashes(self):
        # default (counts hyphens only, so 0 hyphens -> P1Y)
        self.assertEqual(get_observation_period_for_date("2023/01/15", "P1D"),
                         "P1Y")

    def test_invalid_date(self):
        # Contains one hyphen
        self.assertEqual(get_observation_period_for_date("invalid-date", "PXY"),
                         "P1M")

    def test_extra_hyphen(self):
        # default
        self.assertEqual(
            get_observation_period_for_date("2023-01-15-extra", "P1D"), "P1D")


class TestGetObservationDateFormat(unittest.TestCase):

    def test_year(self):
        self.assertEqual(get_observation_date_format("2023"), "%Y")

    def test_year_month(self):
        self.assertEqual(get_observation_date_format("2023-01"), "%Y-%m")

    def test_year_month_day(self):
        self.assertEqual(get_observation_date_format("2023-01-15"), "%Y-%m-%d")

    def test_slashes(self):
        # Relies on hyphens
        self.assertEqual(get_observation_date_format("2023/01/15"), "%Y")

    def test_extra_hyphen(self):
        self.assertEqual(get_observation_date_format("2023-01-15-extra"),
                         "%Y-%m-%d")


class TestGetFilenameForUrl(unittest.TestCase):

    @patch('utils.file_util.file_get_matching')
    def test_no_existing_files(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_query_params(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            get_filename_for_url("http://example.com/data.tar.gz?param=1#frag",
                                 "/tmp"), os.path.join("/tmp", "data.tar.gz"))

    @patch('utils.file_util.file_get_matching')
    def test_filename_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [os.path.join("/tmp", "data.csv")]
        self.assertEqual(
            get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data-1.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_filename_and_suffixed_exist(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [
            os.path.join("/tmp", "data.csv"),
            os.path.join("/tmp", "data-1.csv")
        ]
        self.assertEqual(
            get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data-2.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_no_extension(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            get_filename_for_url("http://example.com/datafile", "/tmp"),
            os.path.join("/tmp", "datafile"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_no_extension_and_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [os.path.join("/tmp", "datafile")]
        self.assertEqual(
            get_filename_for_url("http://example.com/datafile", "/tmp"),
            os.path.join("/tmp", "datafile-1"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_multiple_dots(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            get_filename_for_url("http://example.com/archive.data.csv", "/tmp"),
            os.path.join("/tmp", "archive.data.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_multiple_dots_and_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [
            os.path.join("/tmp", "archive.data.csv")
        ]
        self.assertEqual(
            get_filename_for_url("http://example.com/archive.data.csv", "/tmp"),
            os.path.join("/tmp", "archive.data-1.csv"))


class TestDownloadCsvFromUrl(unittest.TestCase):

    @patch('utils.download_file_from_url')
    @patch('utils.get_filename_for_url')
    def test_single_url(self, mock_get_filename, mock_download):
        mock_get_filename.return_value = '/tmp/data.csv'
        mock_download.return_value = '/tmp/data.csv'
        files = download_csv_from_url('http://example.com/data.csv', [])
        self.assertEqual(files, ['/tmp/data.csv'])
        mock_get_filename.assert_called_once_with('http://example.com/data.csv',
                                                  './')
        mock_download.assert_called_once_with(url='http://example.com/data.csv',
                                              output_file='/tmp/data.csv',
                                              overwrite=False)

    @patch('utils.download_file_from_url')
    def test_single_url_with_filename(self, mock_download):
        mock_download.return_value = '/tmp/my_data.csv'
        files = download_csv_from_url('http://example.com/data.csv',
                                      ['/tmp/my_data.csv'])
        self.assertEqual(files, ['/tmp/my_data.csv'])
        mock_download.assert_called_once_with(url='http://example.com/data.csv',
                                              output_file='/tmp/my_data.csv',
                                              overwrite=False)

    @patch('utils.download_file_from_url')
    @patch('utils.get_filename_for_url')
    def test_multiple_urls(self, mock_get_filename, mock_download):
        mock_get_filename.side_effect = ['/tmp/data1.csv', '/tmp/data2.csv']
        mock_download.side_effect = ['/tmp/data1.csv', '/tmp/data2.csv']
        urls = ['http://example.com/data1.csv', 'http://example.com/data2.csv']
        files = download_csv_from_url(urls, [])
        self.assertEqual(files, ['/tmp/data1.csv', '/tmp/data2.csv'])
        self.assertEqual(mock_get_filename.call_count, 2)
        self.assertEqual(mock_download.call_count, 2)

    @patch('utils.download_file_from_url')
    def test_download_fails(self, mock_download):
        mock_download.return_value = None
        files = download_csv_from_url('http://example.com/data.csv',
                                      ['/tmp/my_data.csv'])
        self.assertEqual(files, [])

    def test_empty_urls(self):
        files = download_csv_from_url([], [])
        self.assertEqual(files, [])


class TestShardCsvData(unittest.TestCase):

    @patch('utils.file_util.FileIO')
    @patch('utils.pd.read_csv')
    @patch('utils.pd.DataFrame.to_csv')
    @patch('utils.file_util.file_is_local')
    @patch('utils.os.path.exists')
    def test_shard_csv_data(self, mock_exists, mock_is_local, mock_to_csv,
                            mock_read_csv, mock_file_io):
        mock_exists.return_value = False
        mock_is_local.return_value = True
        df = pd.DataFrame({
            'col1': ['a', 'b', 'c'],
            'col2': [1, 2, 3],
        })
        mock_read_csv.return_value = df
        files = shard_csv_data(['test.csv'], 'col1')
        self.assertEqual(len(files), 3)
        self.assertEqual(mock_to_csv.call_count, 3)

    def test_empty_files(self):
        files = shard_csv_data([], 'col1')
        self.assertEqual(files, [])


class TestConvertXlsToCsv(unittest.TestCase):

    @patch('utils.pd.ExcelFile')
    @patch('utils.pd.read_excel')
    @patch('utils.pd.DataFrame.to_csv')
    def test_convert_xls_to_csv(self, mock_to_csv, mock_read_excel,
                                mock_excel_file):
        mock_excel_file.return_value.sheet_names = ['sheet1', 'sheet2']
        df = pd.DataFrame({'col1': ['a', 'b', 'c'], 'col2': [1, 2, 3]})
        mock_read_excel.return_value = df
        files = convert_xls_to_csv(['test.xlsx'], [])
        self.assertEqual(len(files), 2)
        self.assertEqual(mock_to_csv.call_count, 2)

    @patch('utils.pd.ExcelFile')
    def test_convert_xls_to_csv_no_xls(self, mock_excel_file):
        files = convert_xls_to_csv(['test.csv'], [])
        self.assertEqual(files, ['test.csv'])
        mock_excel_file.assert_not_called()

    def test_empty_files(self):
        files = convert_xls_to_csv([], [])
        self.assertEqual(files, [])


class TestPrepareInputData(unittest.TestCase):

    @patch('utils.file_util.file_get_matching')
    @patch('utils.download_csv_from_url')
    @patch('utils.convert_xls_to_csv')
    @patch('utils.shard_csv_data')
    def test_local_csv_found(self, mock_shard, mock_convert, mock_download,
                             mock_get_matching):
        mock_get_matching.return_value = ['test.csv']
        mock_convert.return_value = ['test.csv']
        config = {'input_data': 'test.csv'}
        files = prepare_input_data(config)
        self.assertEqual(files, ['test.csv'])
        mock_download.assert_not_called()
        mock_convert.assert_called_once_with(['test.csv'], [])
        mock_shard.assert_not_called()

    @patch('utils.file_util.file_get_matching', return_value=[])
    @patch('utils.download_csv_from_url')
    @patch('utils.convert_xls_to_csv')
    @patch('utils.shard_csv_data')
    def test_download_and_convert(self, mock_shard, mock_convert, mock_download,
                                  mock_get_matching):
        mock_download.return_value = ['downloaded.xlsx']
        mock_convert.return_value = ['converted.csv']
        config = {
            'data_url': 'http://example.com/data.xlsx',
            'input_xls': ['Sheet1']
        }
        files = prepare_input_data(config)
        self.assertEqual(files, ['converted.csv'])
        mock_download.assert_called_once()
        mock_convert.assert_called_once_with(['downloaded.xlsx'], ['Sheet1'])
        mock_shard.assert_not_called()

    @patch('utils.file_util.file_get_matching')
    @patch('utils.download_csv_from_url')
    @patch('utils.convert_xls_to_csv')
    @patch('utils.shard_csv_data')
    def test_sharding_enabled(self, mock_shard, mock_convert, mock_download,
                              mock_get_matching):
        mock_get_matching.return_value = ['test.csv']
        mock_convert.return_value = ['test.csv']
        mock_shard.return_value = ['shard1.csv', 'shard2.csv']
        config = {
            'input_data': 'test.csv',
            'shard_input_by_column': 'country',
            'parallelism': 2
        }
        files = prepare_input_data(config)
        self.assertEqual(files, ['shard1.csv', 'shard2.csv'])
        mock_download.assert_not_called()
        mock_convert.assert_called_once()
        mock_shard.assert_called_once()

    def test_no_input_data(self):
        with self.assertRaises(RuntimeError):
            prepare_input_data({})


if __name__ == '__main__':
    unittest.main()

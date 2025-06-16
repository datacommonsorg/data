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

from utils import (_capitalize_first_char, _str_from_number, _pvs_has_any_prop,
                   _is_place_dcid, _get_observation_period_for_date,
                   _get_observation_date_format, _get_filename_for_url)


class TestCapitalizeFirstChar(unittest.TestCase):

    def test_hello(self):
        self.assertEqual(_capitalize_first_char("hello"), "Hello")

    def test_already_capitalized(self):
        self.assertEqual(_capitalize_first_char("Hello"), "Hello")

    def test_empty_string(self):
        self.assertEqual(_capitalize_first_char(""), "")

    def test_numeric_first_char(self):
        self.assertEqual(_capitalize_first_char("1hello"), "1hello")

    def test_none_input(self):
        self.assertEqual(_capitalize_first_char(None), None)

    def test_integer_input(self):
        self.assertEqual(_capitalize_first_char(123), 123)

    def test_space_first_char(self):
        self.assertEqual(_capitalize_first_char(" h"), " h")

    def test_single_char(self):
        self.assertEqual(_capitalize_first_char("h"), "H")


class TestStrFromNumber(unittest.TestCase):

    def test_integer(self):
        self.assertEqual(_str_from_number(10), "10")

    def test_float(self):
        self.assertEqual(_str_from_number(10.0), "10")

    def test_float_with_decimal(self):
        self.assertEqual(_str_from_number(10.123), "10.123")

    def test_precision(self):
        self.assertEqual(_str_from_number(10.123456, precision_digits=3),
                         "10.123")

    def test_rounding(self):
        self.assertEqual(_str_from_number(10.999, precision_digits=2), "11.0")

    def test_trailing_zeros(self):
        self.assertEqual(_str_from_number(10.1200, precision_digits=4), "10.12")


class TestPvsHasAnyProp(unittest.TestCase):

    def test_prop_exists(self):
        self.assertTrue(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop1"]))

    def test_one_of_props_exists(self):
        self.assertTrue(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop2", "prop3"]))

    def test_prop_does_not_exist(self):
        self.assertFalse(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop3"]))

    def test_prop_is_none(self):
        self.assertFalse(
            _pvs_has_any_prop({
                "prop1": None,
                "prop2": "val2"
            }, ["prop1"]))

    def test_empty_pvs(self):
        self.assertFalse(_pvs_has_any_prop({}, ["prop1"]))

    def test_empty_props(self):
        self.assertFalse(_pvs_has_any_prop({"prop1": "val1"}, []))

    def test_none_props(self):
        self.assertFalse(_pvs_has_any_prop({"prop1": "val1"}, None))

    def test_none_pvs(self):
        self.assertFalse(_pvs_has_any_prop(None, ["prop1"]))


class TestIsPlaceDcid(unittest.TestCase):

    def test_dcid_prefix(self):
        self.assertTrue(_is_place_dcid("dcid:country/USA"))

    def test_dcs_prefix(self):
        self.assertTrue(_is_place_dcid("dcs:country/USA"))

    def test_no_prefix(self):
        self.assertTrue(_is_place_dcid("country/USA"))

    def test_geoid_prefix(self):
        self.assertTrue(_is_place_dcid("geoId/06"))

    def test_dc_g_prefix(self):
        self.assertTrue(_is_place_dcid("dc/g/Establishment_School"))

    def test_no_slash(self):
        self.assertFalse(_is_place_dcid("countryUSA"))

    def test_extra_text(self):
        self.assertFalse(_is_place_dcid("dcid:country/USA extra"))

    def test_special_chars(self):
        self.assertFalse(_is_place_dcid("dcid:!@#"))

    def test_empty_string(self):
        self.assertFalse(_is_place_dcid(""))

    def test_none(self):
        self.assertFalse(_is_place_dcid(None))

    def test_dcid_only(self):
        self.assertFalse(_is_place_dcid("dcid:"))

    def test_dcs_only(self):
        self.assertFalse(_is_place_dcid("dcs:"))

    def test_trailing_slash(self):
        # Needs a part after slash
        self.assertFalse(_is_place_dcid("country/"))

    def test_leading_slash(self):
        # Needs a part before slash
        self.assertFalse(_is_place_dcid("/USA"))


class TestGetObservationPeriodForDate(unittest.TestCase):

    def test_year(self):
        self.assertEqual(_get_observation_period_for_date("2023"), "P1Y")

    def test_year_month(self):
        self.assertEqual(_get_observation_period_for_date("2023-01"), "P1M")

    def test_year_month_day(self):
        self.assertEqual(_get_observation_period_for_date("2023-01-15"), "P1D")

    def test_slashes(self):
        # default (counts hyphens only, so 0 hyphens -> P1Y)
        self.assertEqual(_get_observation_period_for_date("2023/01/15", "P1D"),
                         "P1Y")

    def test_invalid_date(self):
        # Contains one hyphen
        self.assertEqual(
            _get_observation_period_for_date("invalid-date", "PXY"), "P1M")

    def test_extra_hyphen(self):
        # default
        self.assertEqual(
            _get_observation_period_for_date("2023-01-15-extra", "P1D"), "P1D")


class TestGetObservationDateFormat(unittest.TestCase):

    def test_year(self):
        self.assertEqual(_get_observation_date_format("2023"), "%Y")

    def test_year_month(self):
        self.assertEqual(_get_observation_date_format("2023-01"), "%Y-%m")

    def test_year_month_day(self):
        self.assertEqual(_get_observation_date_format("2023-01-15"), "%Y-%m-%d")

    def test_slashes(self):
        # Relies on hyphens
        self.assertEqual(_get_observation_date_format("2023/01/15"), "%Y")

    def test_extra_hyphen(self):
        self.assertEqual(_get_observation_date_format("2023-01-15-extra"),
                         "%Y-%m-%d")


class TestGetFilenameForUrl(unittest.TestCase):

    @patch('utils.file_util.file_get_matching')
    def test_no_existing_files(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            _get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_query_params(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            _get_filename_for_url("http://example.com/data.tar.gz?param=1#frag",
                                  "/tmp"), os.path.join("/tmp", "data.tar.gz"))

    @patch('utils.file_util.file_get_matching')
    def test_filename_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [os.path.join("/tmp", "data.csv")]
        self.assertEqual(
            _get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data-1.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_filename_and_suffixed_exist(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [
            os.path.join("/tmp", "data.csv"),
            os.path.join("/tmp", "data-1.csv")
        ]
        self.assertEqual(
            _get_filename_for_url("http://example.com/data.csv", "/tmp"),
            os.path.join("/tmp", "data-2.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_no_extension(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            _get_filename_for_url("http://example.com/datafile", "/tmp"),
            os.path.join("/tmp", "datafile"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_no_extension_and_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [os.path.join("/tmp", "datafile")]
        self.assertEqual(
            _get_filename_for_url("http://example.com/datafile", "/tmp"),
            os.path.join("/tmp", "datafile-1"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_multiple_dots(self, mock_file_get_matching):
        mock_file_get_matching.return_value = []
        self.assertEqual(
            _get_filename_for_url("http://example.com/archive.data.csv",
                                  "/tmp"),
            os.path.join("/tmp", "archive.data.csv"))

    @patch('utils.file_util.file_get_matching')
    def test_url_with_multiple_dots_and_exists(self, mock_file_get_matching):
        mock_file_get_matching.return_value = [
            os.path.join("/tmp", "archive.data.csv")
        ]
        self.assertEqual(
            _get_filename_for_url("http://example.com/archive.data.csv",
                                  "/tmp"),
            os.path.join("/tmp", "archive.data-1.csv"))


if __name__ == '__main__':
    unittest.main()

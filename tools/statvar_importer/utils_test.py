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
from utils import (_capitalize_first_char, _str_from_number, _pvs_has_any_prop,
                   _is_place_dcid, _get_observation_period_for_date,
                   _get_observation_date_format)


class UtilsTest(unittest.TestCase):

    def test_capitalize_first_char(self):
        self.assertEqual(_capitalize_first_char("hello"), "Hello")
        self.assertEqual(_capitalize_first_char("Hello"), "Hello")
        self.assertEqual(_capitalize_first_char(""), "")
        self.assertEqual(_capitalize_first_char("1hello"), "1hello")
        self.assertEqual(_capitalize_first_char(None), None)
        self.assertEqual(_capitalize_first_char(123), 123)
        self.assertEqual(_capitalize_first_char(" h"), " h")
        self.assertEqual(_capitalize_first_char("h"), "H")

    def test_str_from_number(self):
        self.assertEqual(_str_from_number(10), "10")
        self.assertEqual(_str_from_number(10.0), "10")
        self.assertEqual(_str_from_number(10.123), "10.123")
        self.assertEqual(_str_from_number(10.123456, precision_digits=3),
                         "10.123")
        self.assertEqual(_str_from_number(10.999, precision_digits=2),
                         "11.0")  # check rounding
        self.assertEqual(_str_from_number(10.1200, precision_digits=4),
                         "10.12")  # check trailing zeros

    def test_pvs_has_any_prop(self):
        self.assertTrue(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop1"]))
        self.assertTrue(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop2", "prop3"]))
        self.assertFalse(
            _pvs_has_any_prop({
                "prop1": "val1",
                "prop2": "val2"
            }, ["prop3"]))
        self.assertFalse(
            _pvs_has_any_prop({
                "prop1": None,
                "prop2": "val2"
            }, ["prop1"]))
        self.assertFalse(_pvs_has_any_prop({}, ["prop1"]))
        self.assertFalse(_pvs_has_any_prop({"prop1": "val1"}, []))
        self.assertFalse(_pvs_has_any_prop({"prop1": "val1"}, None))
        self.assertFalse(_pvs_has_any_prop(None, ["prop1"]))

    def test_is_place_dcid(self):
        self.assertTrue(_is_place_dcid("dcid:country/USA"))
        self.assertTrue(_is_place_dcid("dcs:country/USA"))
        self.assertTrue(_is_place_dcid("country/USA"))
        self.assertTrue(_is_place_dcid("geoId/06"))
        self.assertTrue(_is_place_dcid("dc/g/Establishment_School"))
        self.assertFalse(_is_place_dcid("countryUSA"))
        self.assertFalse(_is_place_dcid("dcid:country/USA extra"))
        self.assertFalse(_is_place_dcid("dcid:!@#"))
        self.assertFalse(_is_place_dcid(""))
        self.assertFalse(_is_place_dcid(None))
        self.assertFalse(_is_place_dcid("dcid:"))
        self.assertFalse(_is_place_dcid("dcs:"))
        self.assertFalse(_is_place_dcid("country/"))  # Needs a part after slash
        self.assertFalse(_is_place_dcid("/USA"))  # Needs a part before slash

    def test_get_observation_period_for_date(self):
        self.assertEqual(_get_observation_period_for_date("2023"), "P1Y")
        self.assertEqual(_get_observation_period_for_date("2023-01"), "P1M")
        self.assertEqual(_get_observation_period_for_date("2023-01-15"), "P1D")
        self.assertEqual(
            _get_observation_period_for_date("2023/01/15", "P1D"),
            "P1Y")  # default (counts hyphens only, so 0 hyphens -> P1Y)
        self.assertEqual(_get_observation_period_for_date(
            "invalid-date", "PXY"), "P1M")  # Contains one hyphen
        self.assertEqual(
            _get_observation_period_for_date("2023-01-15-extra", "P1D"),
            "P1D")  # default

    def test_get_observation_date_format(self):
        self.assertEqual(_get_observation_date_format("2023"), "%Y")
        self.assertEqual(_get_observation_date_format("2023-01"), "%Y-%m")
        self.assertEqual(_get_observation_date_format("2023-01-15"), "%Y-%m-%d")
        self.assertEqual(_get_observation_date_format("2023/01/15"),
                         "%Y")  # Relies on hyphens
        self.assertEqual(_get_observation_date_format("2023-01-15-extra"),
                         "%Y-%m-%d")


if __name__ == '__main__':
    unittest.main()

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
"""
Unit tests for constants module used in US BTS LATCH import.
"""

import math
import os
import sys
import unittest
import numpy as np
import pandas as pd

_MODULE_DIR = os.path.dirname(__file__)
sys.path.insert(0, _MODULE_DIR)

# pylint: disable=wrong-import-position
import constants

# pylint: enable=wrong-import-position


# pylint: disable=protected-access
class TestConstants(unittest.TestCase):
    """Tests for helper functions and lambda formatters in constants.py."""

    def test_is_null_or_none_with_null_values(self):
        """Verifies that null, NaN, None, and empty representations return True."""
        null_values = [
            None,
            float("nan"),
            math.nan,
            np.nan,
            pd.NA,
            "",
            "   ",
            "nan",
            "NaN",
            "NAN",
            "none",
            "None",
            "NONE",
            "<na>",
            "<NA>",
        ]
        for val in null_values:
            with self.subTest(val=val):
                self.assertTrue(constants._is_null_or_none(val))

    def test_is_null_or_none_with_valid_values(self):
        """Verifies that valid integers, strings, floats, and booleans return False."""
        valid_values = [
            0,
            0.0,
            "0",
            1,
            "1",
            "valid",
            "Household",
            False,
            "False",
        ]
        for val in valid_values:
            with self.subTest(val=val):
                self.assertFalse(constants._is_null_or_none(val))

    def test_household_prop(self):
        """Verifies household size property formatting and null suppression."""
        self.assertEqual(constants._HOUSEHOLD_PROP("1"), "With1Person")
        self.assertEqual(constants._HOUSEHOLD_PROP("5"), "With5Person")
        self.assertEqual(constants._HOUSEHOLD_PROP(0), "With0Person")
        self.assertEqual(constants._HOUSEHOLD_PROP("0"), "With0Person")

        null_inputs = [None, float("nan"), np.nan, pd.NA, "nan", "", "<NA>"]
        for val in null_inputs:
            with self.subTest(val=val):
                self.assertIsNone(constants._HOUSEHOLD_PROP(val))

    def test_noofvehicles_prop(self):
        """Verifies vehicle count property formatting and null suppression."""
        self.assertEqual(constants._NOOFVEHICLES_PROP("0"),
                         "With0AvailableVehicles")
        self.assertEqual(constants._NOOFVEHICLES_PROP(0),
                         "With0AvailableVehicles")
        self.assertEqual(constants._NOOFVEHICLES_PROP("2"),
                         "With2AvailableVehicles")

        null_inputs = [None, float("nan"), np.nan, pd.NA, "nan", "", "<NA>"]
        for val in null_inputs:
            with self.subTest(val=val):
                self.assertIsNone(constants._NOOFVEHICLES_PROP(val))

    def test_measured_prop(self):
        """Verifies measuredProperty mapper lookup and null suppression."""
        self.assertEqual(constants._MEASURED_PROP("pmiles"),
                         "personMilesTraveled")
        self.assertEqual(constants._MEASURED_PROP("ptrp"), "personTrips")
        self.assertEqual(constants._MEASURED_PROP("vmiles"),
                         "vehicleMilesTraveled")
        self.assertEqual(constants._MEASURED_PROP("vtrp"), "vehicleTrips")
        self.assertEqual(constants._MEASURED_PROP("custom_prop"), "custom_prop")

        null_inputs = [None, float("nan"), np.nan, pd.NA, "nan", ""]
        for val in null_inputs:
            with self.subTest(val=val):
                self.assertIsNone(constants._MEASURED_PROP(val))

    def test_pv_format(self):
        """Verifies _PV_FORMAT creates valid dcs references or empty strings."""
        self.assertEqual(
            constants._PV_FORMAT(("typeOf", "StatisticalVariable")),
            '"typeOf": "dcs:StatisticalVariable"',
        )
        self.assertEqual(
            constants._PV_FORMAT(("statType", "meanValue")),
            '"statType": "dcs:meanValue"',
        )

        null_inputs = [None, float("nan"), np.nan, pd.NA, "nan", ""]
        for val in null_inputs:
            with self.subTest(val=val):
                self.assertEqual(constants._PV_FORMAT(("householdSize", val)),
                                 "")

    def test_pv_format_numbers(self):
        """Verifies _PV_FORMAT_NUMBERS creates literal values or empty strings."""
        self.assertEqual(
            constants._PV_FORMAT_NUMBERS(("statType", "measurementResult")),
            '"statType": "measurementResult"',
        )

        null_inputs = [None, float("nan"), np.nan, pd.NA, "nan", ""]
        for val in null_inputs:
            with self.subTest(val=val):
                self.assertEqual(
                    constants._PV_FORMAT_NUMBERS(("numberOfVehicles", val)), "")

    def test_sv_node_format(self):
        """Verifies SV_NODE_FORMAT prefixes with Node: dcid:."""
        self.assertEqual(
            constants.SV_NODE_FORMAT("test_statvar"),
            "Node: dcid:test_statvar",
        )

    def test_default_prop(self):
        """Verifies _DEFAULT_PROP returns the input unchanged."""
        self.assertEqual(constants._DEFAULT_PROP("urban_group"), "urban_group")


if __name__ == "__main__":
    unittest.main()

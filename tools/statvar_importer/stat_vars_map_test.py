# Copyright 2024 Google LLC
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
"""Unit tests for stat_vars_map.py."""

import os
import sys
import unittest

from absl import app
from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), "util"))

from stat_vars_map import StatVarsMap


class TestStatVarsMap(unittest.TestCase):

    def test_create_stat_vars_map(self):
        """Test that the StatVarsMap class can be instantiated."""
        stat_vars_map = StatVarsMap()
        self.assertIsNotNone(stat_vars_map)

    def test_add_statvar(self):
        """Test that a statvar can be added to the map."""
        stat_vars_map = StatVarsMap()
        statvar_pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "measuredProperty": "dcs:count",
        }
        self.assertTrue(stat_vars_map.add_statvar("test_statvar", statvar_pvs))
        self.assertIn("test_statvar", stat_vars_map._statvars_map)

    def test_add_statvar_obs(self):
        """Test that a statvar observation can be added to the map."""
        stat_vars_map = StatVarsMap()
        statvar_pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "measuredProperty": "dcs:count",
        }
        stat_vars_map.add_statvar("test_statvar", statvar_pvs)
        svobs_pvs = {
            "variableMeasured": "dcs:test_statvar",
            "observationAbout": "dcs:country/USA",
            "observationDate": "2023",
            "value": "100",
        }
        self.assertTrue(stat_vars_map.add_statvar_obs(svobs_pvs))
        # The key is a semicolon-separated string of property-value pairs,
        # sorted alphabetically by property.
        self.assertIn(
            "observationAbout=dcs:country/USA;observationDate=2023;variableMeasured=dcs:test_statvar",
            stat_vars_map._statvar_obs_map)

    def test_generate_statvar_dcid(self):
        """Test that a dcid can be generated for a statvar."""
        stat_vars_map = StatVarsMap()
        pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "measuredProperty": "dcs:count",
            "gender": "dcs:Male",
        }
        dcid = stat_vars_map.generate_statvar_dcid(pvs)
        self.assertEqual(dcid, "Count_Person_Male")

    def test_generate_statvar_dcid_with_quantity_range(self):
        """Test that a dcid can be generated for a statvar with a quantity range."""
        stat_vars_map = StatVarsMap()
        pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "measuredProperty": "dcs:count",
            "age": "[18 24 Years]",
        }
        dcid = stat_vars_map.generate_statvar_dcid(pvs)
        self.assertEqual(dcid, "Count_Person_18To24Years")

    def test_drop_invalid_statvars(self):
        """Test that invalid statvars are dropped."""
        stat_vars_map = StatVarsMap(
            config_dict={"required_statvar_properties": ["populationType"]})
        statvar_pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "measuredProperty": "dcs:count",
        }
        stat_vars_map.add_statvar("test_statvar", statvar_pvs)
        stat_vars_map.drop_invalid_statvars()
        self.assertNotIn("test_statvar", stat_vars_map._statvars_map)

    def test_get_svobs_key(self):
        """Test that the key for a statvar observation is generated correctly."""
        stat_vars_map = StatVarsMap()
        pvs = {
            "variableMeasured": "dcs:test_statvar",
            "observationAbout": "dcs:country/USA",
            "observationDate": "2023",
            "value": "100",
        }
        key = stat_vars_map.get_svobs_key(pvs)
        self.assertEqual(
            key,
            "observationAbout=dcs:country/USA;observationDate=2023;variableMeasured=dcs:test_statvar"
        )


    def test_aggregate_value(self):
        """Test that duplicate statvar observations are aggregated correctly."""
        stat_vars_map = StatVarsMap(
            config_dict={"aggregate_duplicate_svobs": "sum"})
        statvar_pvs = {
            "typeOf": "dcs:StatisticalVariable",
            "populationType": "dcs:Person",
            "measuredProperty": "dcs:count",
        }
        stat_vars_map.add_statvar("test_statvar", statvar_pvs)
        svobs_pvs1 = {
            "variableMeasured": "dcs:test_statvar",
            "observationAbout": "dcs:country/USA",
            "observationDate": "2023",
            "value": "100",
        }
        stat_vars_map.add_statvar_obs(svobs_pvs1)
        svobs_pvs2 = {
            "variableMeasured": "dcs:test_statvar",
            "observationAbout": "dcs:country/USA",
            "observationDate": "2023",
            "value": "200",
        }
        stat_vars_map.add_statvar_obs(svobs_pvs2)
        key = list(stat_vars_map._statvar_obs_map.keys())[0]
        self.assertEqual(stat_vars_map._statvar_obs_map[key]["value"], 300)
        self.assertEqual(
            stat_vars_map._statvar_obs_map[key]["measurementMethod"],
            "dcs:DataCommonsAggregate",
        )


if __name__ == "__main__":
    app.run(unittest.main)

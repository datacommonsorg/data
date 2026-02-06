# Copyright 2026 Google LLC
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
import sys
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.un.boundaries import country_boundaries


class CountryBoundariesTest(unittest.TestCase):

    def test_existing_codes_filters_to_dc_countries(self):
        all_countries = pd.DataFrame({"iso3cd": ["USA", "CAN", "MEX"]})
        with tempfile.TemporaryDirectory() as output_dir:
            generator = country_boundaries.CountryBoundariesGenerator(
                input_file="input.geojson", output_dir=output_dir)
            with mock.patch.object(country_boundaries.dc,
                                   "get_property_values",
                                   return_value={
                                       "Country": ["country/CAN", "country/USA"]
                                   }):
                self.assertEqual(generator.existing_codes(all_countries),
                                 ["CAN", "USA"])

    def test_get_countries_in_parses_response(self):
        response_payload = {
            "data": {
                "Earth": {
                    "arcs": {
                        "containedInPlace+": {
                            "nodes": [{
                                "dcid": "country/USA"
                            }, {
                                "dcid": "country/CAN"
                            }]
                        }
                    }
                },
                "asia": {
                    "arcs": {
                        "containedInPlace+": {
                            "nodes": [{
                                "dcid": "country/JPN"
                            }]
                        }
                    }
                },
                "europe": {},
            }
        }
        response = mock.Mock()
        response.json.return_value = response_payload
        with mock.patch.dict(country_boundaries.os.environ,
                             {"MIXER_API_KEY": "test-key"},
                             clear=False):
            with mock.patch.object(country_boundaries.requests,
                                   "post",
                                   return_value=response):
                result = country_boundaries.get_countries_in(
                    ["Earth", "asia", "europe"])
        self.assertEqual(
            result, {
                "Earth": ["country/USA", "country/CAN"],
                "asia": ["country/JPN"],
                "europe": [],
            })


if __name__ == "__main__":
    unittest.main()

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


class FakeNode:

    def __init__(self, dcid=None, value=None):
        self.dcid = dcid
        self.value = value


class FakeArc:

    def __init__(self, nodes):
        self.nodes = nodes


class FakeNodeData:

    def __init__(self, arcs):
        self.arcs = arcs


class FakeNodeResponse:

    def __init__(self, data):
        self.data = data


class FakeNodeEndpoint:

    def __init__(self,
                 fetch_response=None,
                 fetch_property_values_response=None):
        self._fetch_response = fetch_response
        self._fetch_property_values_response = fetch_property_values_response

    def fetch(self, node_dcids, expression):
        return self._fetch_response

    def fetch_property_values(self, node_dcids, properties, out=True):
        return self._fetch_property_values_response


class FakeClient:

    def __init__(self, node):
        self.node = node


class CountryBoundariesTest(unittest.TestCase):

    def test_existing_codes_filters_to_dc_countries(self):
        all_countries = pd.DataFrame({"iso3cd": ["USA", "CAN", "MEX"]})
        response = FakeNodeResponse({
            "Country":
                FakeNodeData({
                    "typeOf":
                        FakeArc([
                            FakeNode(dcid="country/CAN"),
                            FakeNode(dcid="country/USA")
                        ])
                })
        })
        client = FakeClient(
            FakeNodeEndpoint(fetch_property_values_response=response))
        with tempfile.TemporaryDirectory() as output_dir:
            generator = country_boundaries.CountryBoundariesGenerator(
                input_file="input.geojson", output_dir=output_dir)
            with mock.patch.object(country_boundaries,
                                   "get_datacommons_client",
                                   return_value=client):
                self.assertEqual(generator.existing_codes(all_countries),
                                 ["CAN", "USA"])

    def test_get_countries_in_parses_response(self):
        response = FakeNodeResponse({
            "Earth":
                FakeNodeData({
                    "containedInPlace+":
                        FakeArc([
                            FakeNode(dcid="country/USA"),
                            FakeNode(dcid="country/CAN")
                        ])
                }),
            "asia":
                FakeNodeData({
                    "containedInPlace+": FakeArc([FakeNode(dcid="country/JPN")])
                }),
            "europe":
                FakeNodeData({}),
        })
        client = FakeClient(FakeNodeEndpoint(fetch_response=response))
        with mock.patch.object(country_boundaries,
                               "get_datacommons_client",
                               return_value=client):
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

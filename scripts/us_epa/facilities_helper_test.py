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
"""Tests for facilities_helper.py."""

import sys
import unittest
from pathlib import Path
from unittest import mock

# Kept at scripts/us_epa/ instead of scripts/us_epa/util/ because the repo's
# unittest discovery for scripts/us_epa would import it as
# util.facilities_helper_test and collide with the top-level data/util package.
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.us_epa.util import facilities_helper as fh


class FacilitiesHelperTest(unittest.TestCase):

    def test_get_all_statvars_returns_empty_set_for_empty_input(self):
        with mock.patch.object(fh, "get_datacommons_client") as mock_client:
            self.assertEqual(fh.get_all_statvars([]), set())

        mock_client.assert_not_called()

    def test_get_all_statvars_fetches_and_unions_variables(self):
        facilities = [f"epaGhgrpFacilityId/{i}" for i in range(55)]
        mock_client = mock.Mock()
        mock_client.observation.fetch.side_effect = [
            mock.Mock(to_dict=mock.Mock(
                return_value={
                    "byVariable": {
                        "Count_Person": {
                            "byEntity": {
                                facilities[0]: {}
                            }
                        },
                        "Median_Age_Person": {
                            "byEntity": {
                                facilities[1]: {}
                            }
                        },
                    }
                })),
            mock.Mock(to_dict=mock.Mock(
                return_value={
                    "byVariable": {
                        "Count_Person": {
                            "byEntity": {
                                facilities[50]: {}
                            }
                        },
                        "Count_Household": {
                            "byEntity": {
                                facilities[54]: {}
                            }
                        },
                    }
                })),
        ]

        with mock.patch.object(fh,
                               "get_datacommons_client",
                               return_value=mock_client):
            stat_vars = fh.get_all_statvars(facilities)

        self.assertEqual(stat_vars, {
            "Count_Person",
            "Median_Age_Person",
            "Count_Household",
        })
        self.assertEqual(mock_client.observation.fetch.call_count, 2)
        self.assertEqual(
            mock_client.observation.fetch.call_args_list[0].kwargs, {
                "entity_dcids":
                    facilities[:50],
                "variable_dcids": [],
                "select": [
                    fh.ObservationSelect.VARIABLE,
                    fh.ObservationSelect.ENTITY,
                ],
            })
        self.assertEqual(
            mock_client.observation.fetch.call_args_list[1].kwargs, {
                "entity_dcids":
                    facilities[50:],
                "variable_dcids": [],
                "select": [
                    fh.ObservationSelect.VARIABLE,
                    fh.ObservationSelect.ENTITY,
                ],
            })

    def test_get_all_statvars_allows_entities_missing_from_response(self):
        mock_response = mock.Mock(to_dict=mock.Mock(
            return_value={
                "byVariable": {
                    "Count_Person": {
                        "byEntity": {
                            "epaGhgrpFacilityId/1": {}
                        }
                    }
                }
            }))
        mock_client = mock.Mock()
        mock_client.observation.fetch.return_value = mock_response

        with mock.patch.object(fh,
                               "get_datacommons_client",
                               return_value=mock_client):
            stat_vars = fh.get_all_statvars(
                ["epaGhgrpFacilityId/1", "epaGhgrpFacilityId/2"])

        self.assertEqual(stat_vars, {"Count_Person"})


if __name__ == "__main__":
    unittest.main()

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
"""Tests for generate_svobs_helper()."""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.us_epa.parent_company import process_parent_company


class GenerateSvobsHelperTest(unittest.TestCase):

    def test_generate_svobs_helper_wires_statvars_and_svobs(self):
        ownership = {
            ("epaGhgrpFacilityId/1001", "2018"): {
                "EpaParentCompany/A": 100.0,
            },
            ("epaGhgrpFacilityId/1001", "2019"): {
                "EpaParentCompany/A": 100.0,
            },
            ("epaGhgrpFacilityId/1002", "2019"): {
                "EpaParentCompany/B": 100.0,
            },
        }
        facility_sv_map = {"epaGhgrpFacilityId/1001": {"Count_Person": {}}}
        facets = {"facet-1": {"observationPeriod": "P1Y"}}

        with mock.patch.object(process_parent_company,
                               "_facility_year_company_percentages",
                               return_value=ownership):
            with mock.patch.object(process_parent_company.fh,
                                   "get_all_statvars",
                                   return_value={"Count_Person"
                                                }) as mock_statvars:
                with mock.patch.object(process_parent_company.fh,
                                       "get_all_svobs",
                                       return_value=(facility_sv_map,
                                                     facets)) as mock_svobs:
                    with mock.patch.object(
                            process_parent_company,
                            "process_svobs") as mock_process_svobs:
                        process_parent_company.generate_svobs_helper(
                            "ownership.csv", "/tmp/svobs")

        statvars_facilities = mock_statvars.call_args.args[0]
        self.assertEqual(set(statvars_facilities), {
            "epaGhgrpFacilityId/1001",
            "epaGhgrpFacilityId/1002",
        })
        self.assertEqual(set(mock_svobs.call_args.args[0]), {
            "epaGhgrpFacilityId/1001",
            "epaGhgrpFacilityId/1002",
        })
        self.assertEqual(mock_svobs.call_args.args[1], {"Count_Person"})
        mock_process_svobs.assert_called_once_with("/tmp/svobs", ownership,
                                                   facility_sv_map, facets)


if __name__ == "__main__":
    unittest.main()

# Copyright 2025 Google LLC
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
"""Tests for download_existing_facilities.py."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import requests_mock
from absl.testing import absltest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.us_epa.parent_company.download_existing_facilities import (
    download_existing_facilities,)
from scripts.us_epa.parent_company.download_existing_facilities import (
    _V2_SPARQL_URL,)


class DownloadExistingFacilitiesTest(absltest.TestCase):

    def test_download_existing_facilities(self):
        response = {
            "header": ["?dcid"],
            "rows": [
                {
                    "cells": [{
                        "value": "epaGhgrpFacilityId/1001"
                    }]
                },
                {
                    "cells": [{
                        "value": "epaGhgrpFacilityId/1002"
                    }]
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            with requests_mock.Mocker() as mocker:
                mocker.post(_V2_SPARQL_URL, json=response)
                with mock.patch(
                        "scripts.us_epa.parent_company."
                        "download_existing_facilities.get_dc_api_key",
                        return_value="test-key"):
                    output_path = download_existing_facilities(tmp_dir)

                self.assertTrue(os.path.exists(output_path))
                with open(output_path, "r", encoding="utf-8") as handle:
                    contents = handle.read()
                self.assertEqual(
                    contents,
                    "epaGhgrpFacilityId\n"
                    "epaGhgrpFacilityId/1001\n"
                    "epaGhgrpFacilityId/1002\n",
                )
                self.assertLen(mocker.request_history, 1)
                request = mocker.request_history[0]
                self.assertEqual(request.headers.get("X-API-Key"), "test-key")
                self.assertEqual(
                    request.json().get("query"),
                    "SELECT DISTINCT ?dcid WHERE {?a typeOf "
                    "EpaReportingFacility . ?a dcid ?dcid }",
                )


if __name__ == "__main__":
    absltest.main()

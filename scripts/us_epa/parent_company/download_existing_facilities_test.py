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
"""Tests for download_existing_facilities.py."""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

from absl.testing import absltest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.us_epa.parent_company.download_existing_facilities import (
    download_existing_facilities,)


class DownloadExistingFacilitiesTest(absltest.TestCase):

    def test_download_existing_facilities(self):
        facility_nodes = [
            mock.Mock(dcid="epaGhgrpFacilityId/1001"),
            mock.Mock(dcid="epaGhgrpFacilityId/1002"),
            mock.Mock(dcid="epaGhgrpFacilityId/1001"),
            mock.Mock(dcid=None),
        ]
        mock_response = mock.Mock()
        mock_response.get_properties.return_value = {
            "EpaReportingFacility": {
                "typeOf": facility_nodes,
            }
        }
        mock_client = mock.Mock()
        mock_client.node.fetch_property_values.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch(
                    "scripts.us_epa.parent_company."
                    "download_existing_facilities.get_datacommons_client",
                    return_value=mock_client):
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
            mock_client.node.fetch_property_values.assert_called_once_with(
                node_dcids="EpaReportingFacility",
                properties="typeOf",
                out=False,
            )


if __name__ == "__main__":
    absltest.main()

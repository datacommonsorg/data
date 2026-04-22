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

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main

class TestMain(unittest.TestCase):

    @patch.dict(os.environ, {
        "SPANNER_INSTANCE": "test-instance",
        "SPANNER_DATABASE": "test-db",
        "SPANNER_PROJECT": "test-proj"
    })
    @patch('main.spanner.Client')
    @patch('main.get_latest_lock_timestamp')
    @patch('main.get_updated_nodes')
    @patch('main.filter_and_convert_nodes')
    @patch('main.generate_embeddings_partitioned')
    def test_main_e2e_success(self, mock_generate, mock_filter, mock_nodes, mock_timestamp, mock_spanner):
        mock_database = MagicMock()
        mock_instance = MagicMock()
        mock_instance.database.return_value = mock_database
        mock_spanner.return_value.instance.return_value = mock_instance

        timestamp_val = datetime(2026, 4, 20, 12, 0, 0)
        mock_timestamp.return_value = timestamp_val
        mock_nodes.return_value = [{"subject_id": "dc/1", "name": "Node 1", "types": ["Topic"]}]
        mock_filter.return_value = [("dc/1", "Node 1", ["Topic"])]
        mock_generate.return_value = 1

        try:
            main.main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        mock_spanner.assert_called_once_with(project="test-proj")
        mock_timestamp.assert_called_once_with(mock_database)
        mock_nodes.assert_called_once_with(mock_database, timestamp_val, ["StatisticalVariable", "Topic"])
        mock_filter.assert_called_once()
        mock_generate.assert_called_once()

if __name__ == '__main__':
    unittest.main()

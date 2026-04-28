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
from datetime import datetime
import sys
import os

# Add parent directory of current file (src directory) to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_utils import (
    get_latest_lock_timestamp,
    get_updated_nodes,
    filter_and_convert_nodes,
    generate_embeddings_partitioned
)

class TestEmbeddingUtils(unittest.TestCase):

    def test_get_latest_lock_timestamp(self):
        mock_database = MagicMock()
        mock_snapshot = MagicMock()
        mock_database.snapshot.return_value.__enter__.return_value = mock_snapshot
        expected_timestamp = datetime(2026, 4, 20, 12, 0, 0)
        mock_snapshot.execute_sql.return_value = [(expected_timestamp,)]

        timestamp = get_latest_lock_timestamp(mock_database)
        self.assertEqual(timestamp, expected_timestamp)

    def test_get_updated_nodes(self):
        mock_database = MagicMock()
        mock_snapshot = MagicMock()
        mock_database.snapshot.return_value.__enter__.return_value = mock_snapshot

        class MockField:
            def __init__(self, name):
                self.name = name

        class MockResults:
            def __init__(self, rows, field_names):
                self.rows = rows
                self.fields = [MockField(name) for name in field_names]

            def __iter__(self):
                return iter(self.rows)

        mock_snapshot.execute_sql.return_value = MockResults(
            rows=[("dc/1", "Node 1", ["Topic"])],
            field_names=["subject_id", "name", "types"]
        )

        nodes = list(get_updated_nodes(mock_database, None, ["Topic"]))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["subject_id"], "dc/1")
        self.assertEqual(nodes[0]["name"], "Node 1")
        self.assertEqual(nodes[0]["types"], ["Topic"])

    def test_filter_and_convert_nodes(self):
        nodes = [
            {"subject_id": "dc/1", "name": "Node 1", "types": ["Topic"]},
            {"subject_id": "dc/2", "name": None, "types": ["StatisticalVariable"]},
            {"subject_id": "dc/3", "name": "Node 3", "types": ["Topic", "StatisticalVariable"]},
            {"subject_id": "dc/4", "name": "", "types": ["StatisticalVariable"]}
        ]

        converted = list(filter_and_convert_nodes(nodes))
        self.assertEqual(len(converted), 2)
        self.assertEqual(converted[0], ("dc/1", "Node 1", ["Topic"]))
        self.assertEqual(converted[1], ("dc/3", "Node 3", ["Topic", "StatisticalVariable"]))

    @patch('embedding_utils._BATCH_SIZE', 2)
    def test_generate_embeddings_partitioned(self):
        mock_database = MagicMock()

        nodes = [
            ("dc/1", "Node 1", ["Topic"]),
            ("dc/2", "Node 2", ["Topic"]),
            ("dc/3", "Node 3", ["Topic"]),
            ("dc/4", "Node 4", ["Topic"]),
            ("dc/5", "Node 5", ["Topic"]),
            ("dc/6", "Node 6", ["Topic"]),
            ("dc/7", "Node 7", ["Topic"]),
            ("dc/8", "Node 8", ["Topic"])
        ]

        def side_effect(func):
            mock_transaction = MagicMock()
            mock_transaction.execute_update.return_value = 2
            return func(mock_transaction)

        mock_database.run_in_transaction.side_effect = side_effect

        affected_rows = generate_embeddings_partitioned(mock_database, nodes)
        self.assertEqual(affected_rows, 8)
        self.assertEqual(mock_database.run_in_transaction.call_count, 4)

if __name__ == '__main__':
    unittest.main()

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

import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

import main

class TestMain(unittest.TestCase):

    @patch.dict(os.environ, {
        "SPANNER_INSTANCE": "test-instance",
        "SPANNER_DATABASE": "test-db",
        "SPANNER_PROJECT": "test-proj"
    })
    @patch('main.spanner.Client')
    def test_main_e2e_success(self, mock_spanner):
        mock_database = MagicMock()
        mock_instance = MagicMock()
        mock_instance.database.return_value = mock_database
        mock_spanner.return_value.instance.return_value = mock_instance

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

        expected_timestamp = datetime(2026, 4, 20, 12, 0, 0)

        mock_snapshot.execute_sql.side_effect = [
            [(expected_timestamp,)],
            MockResults(
                rows=[
                    ("dc/1", "Node 1", ["Topic"]),
                    ("dc/2", None, ["Topic"])
                ],
                field_names=["subject_id", "name", "types"]
            )
        ]

        transactions = []
        def run_in_transaction_side_effect(func):
            mock_transaction = MagicMock()
            mock_transaction.execute_update.return_value = 1
            transactions.append(mock_transaction)
            return func(mock_transaction)

        mock_database.run_in_transaction.side_effect = run_in_transaction_side_effect

        try:
            main.main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        mock_spanner.assert_called_once_with(project="test-proj")
        
        # Assertions for get_latest_lock_timestamp and get_updated_nodes
        self.assertEqual(mock_database.snapshot.call_count, 2)
        call_args_list = mock_snapshot.execute_sql.call_args_list
        self.assertEqual(len(call_args_list), 2)
        
        # Check first call (lock timestamp)
        self.assertIn("IngestionLock", call_args_list[0].args[0])
        
        # Check second call (updated nodes)
        args2, kwargs2 = call_args_list[1]
        self.assertIn("Node", args2[0])
        self.assertEqual(kwargs2["params"]["timestamp"], expected_timestamp)
        self.assertEqual(kwargs2["params"]["node_types"], ["StatisticalVariable", "Topic"])
        
        # Assertions for generate_embeddings_partitioned
        mock_database.run_in_transaction.assert_called_once()
        self.assertEqual(len(transactions), 1)
        transactions[0].execute_update.assert_called_once()
        args_tx, kwargs_tx = transactions[0].execute_update.call_args
        self.assertIn("INSERT OR UPDATE INTO NodeEmbeddings", args_tx[0])
        
        # Verify data passed to generate_embeddings_partitioned reached execute_update
        batch = kwargs_tx["params"]["nodes"]
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0][0], "dc/1")
        self.assertEqual(batch[0][1], "Node 1")

if __name__ == '__main__':
    unittest.main()

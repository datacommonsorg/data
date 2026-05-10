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
import os

import main

class TestMain(unittest.TestCase):

    @patch.dict(os.environ, {
        "SPANNER_INSTANCE_ID": "test-instance",
        "SPANNER_DATABASE_ID": "test-db",
        "SPANNER_PROJECT_ID": "test-proj"
    })
    @patch('main.SpannerClient')
    def test_embedding_ingestion_success(self, mock_spanner_client_class):
        # Mock SpannerClient instance and its database
        mock_spanner_client = MagicMock()
        mock_database = MagicMock()
        mock_spanner_client.database = mock_database
        mock_spanner_client_class.return_value = mock_spanner_client

        # Mock snapshot and execute_sql
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

        # Mock side effect for execute_sql
        # First call: get_latest_lock_timestamp
        # Second call: get_updated_nodes
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

        # Mock transaction for generate_embeddings_partitioned
        transactions = []
        def run_in_transaction_side_effect(func):
            mock_transaction = MagicMock()
            mock_transaction.execute_update.return_value = 1
            transactions.append(mock_transaction)
            return func(mock_transaction)

        mock_database.run_in_transaction.side_effect = run_in_transaction_side_effect

        # Mock request object
        mock_request = MagicMock()
        mock_request.get_json.return_value = {
            "actionType": "embedding_ingestion",
            "enableEmbeddings": True
        }

        # Call the function
        response, status_code = main.ingestion_helper(mock_request)

        # Assertions
        self.assertEqual(status_code, 200)
        self.assertIn("OK", response)

        # Verify SpannerClient was initialized
        mock_spanner_client_class.assert_called_once()

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
        self.assertIn("INSERT OR UPDATE INTO NodeEmbedding", args_tx[0])

        # Verify data passed to generate_embeddings_partitioned reached execute_update
        batch = kwargs_tx["params"]["nodes"]
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0][0], "dc/1")
        self.assertEqual(batch[0][1], "Node 1")

if __name__ == '__main__':
    unittest.main()

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

# Add the current directory to path so we can import spanner_client
sys.path.append(os.path.dirname(__file__))
from spanner_client import SpannerClient

class TestSpannerClient(unittest.TestCase):

    @patch('google.cloud.spanner.Client')
    def test_initialize_database_all_exist(self, mock_spanner_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db
        
        # Mock snapshot results (all tables exist)
        mock_snapshot = MagicMock()
        mock_db.snapshot.return_value.__enter__.return_value = mock_snapshot
        mock_snapshot.execute_sql.return_value = [
            ["table", "Node"], ["table", "Edge"], ["table", "Observation"],
            ["table", "NodeEmbedding"], ["table", "ImportStatus"],
            ["table", "IngestionHistory"], ["table", "ImportVersionHistory"],
            ["table", "IngestionLock"],
            ["index", "NodeEmbeddingIndex"],
            ["model", "NodeEmbeddingModel"]
        ]
        
        client = SpannerClient("project", "instance", "database")
        
        # Run method
        client.initialize_database()
        
        # Verify update_ddl was NOT called
        mock_db.update_ddl.assert_not_called()

    @patch('spanner_client.DatabaseAdminClient')
    @patch('google.cloud.spanner.Client')
    def test_initialize_database_none_exist(self, mock_spanner_client,
                                            mock_admin_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_db.name = "projects/test-project/instances/test-instance/databases/test-db"
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db

        # Mock DatabaseAdminClient
        mock_admin_instance = MagicMock()
        mock_admin_client.return_value = mock_admin_instance
        mock_operation = MagicMock()
        mock_admin_instance.update_database_ddl.return_value = mock_operation

        # Mock snapshot results (no tables exist)
        mock_snapshot = MagicMock()
        mock_db.snapshot.return_value.__enter__.return_value = mock_snapshot
        mock_snapshot.execute_sql.return_value = []

        client = SpannerClient("project", "instance", "database")

        def open_side_effect(file_path, mode='r', *args, **kwargs):
            m = MagicMock()
            if 'storage.pb' in str(file_path):
                m.__enter__.return_value.read.return_value = b'dummy proto data'
            else:
                m.__enter__.return_value.read.return_value = 'CREATE TABLE Node;'
            return m

        # Run method with patched open
        with patch('builtins.open', side_effect=open_side_effect):
            client.initialize_database()

        # Verify update_database_ddl WAS called
        mock_admin_instance.update_database_ddl.assert_called_once()
        mock_operation.result.assert_called_once()
        
        # Verify placeholder replacement
        args, kwargs = mock_admin_instance.update_database_ddl.call_args
        request = kwargs.get('request') if kwargs else args[0]
        statements = request.statements
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0], "CREATE TABLE Node")

    @patch('spanner_client.DatabaseAdminClient')
    @patch('google.cloud.spanner.Client')
    def test_initialize_database_with_embeddings(self, mock_spanner_client, mock_admin_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_db.name = "projects/test-project/instances/test-instance/databases/test-db"
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db

        # Mock DatabaseAdminClient
        mock_admin_instance = MagicMock()
        mock_admin_client.return_value = mock_admin_instance
        mock_operation = MagicMock()
        mock_admin_instance.update_database_ddl.return_value = mock_operation

        # Mock snapshot results (no tables exist)
        mock_snapshot = MagicMock()
        mock_db.snapshot.return_value.__enter__.return_value = mock_snapshot
        mock_snapshot.execute_sql.return_value = []

        client = SpannerClient("project", "instance", "database")

        def open_side_effect(file_path, mode='r', *args, **kwargs):
            m = MagicMock()
            if 'storage.pb' in str(file_path):
                m.__enter__.return_value.read.return_value = b'dummy proto data'
            elif 'embedding_schema.sql' in str(file_path):
                m.__enter__.return_value.read.return_value = 'CREATE TABLE NodeEmbedding; CREATE MODEL M REMOTE OPTIONS (endpoint = \'{{ embeddings_endpoint }}\');'
            else:
                m.__enter__.return_value.read.return_value = 'CREATE TABLE Node;'
            return m

        # Run method with patched open and parameter
        with patch('builtins.open', side_effect=open_side_effect):
            client.initialize_database(enable_embeddings=True)

        # Verify update_database_ddl WAS called
        mock_admin_instance.update_database_ddl.assert_called_once()
        
        # Verify that both schemas were loaded
        args, kwargs = mock_admin_instance.update_database_ddl.call_args
        request = kwargs.get('request') if kwargs else args[0]
        statements = request.statements
        self.assertEqual(len(statements), 3)
        self.assertEqual(statements[0], "CREATE TABLE Node")
        self.assertEqual(statements[1], "CREATE TABLE NodeEmbedding")
        self.assertIn("projects/project/locations", statements[2])

    @patch('google.cloud.spanner.Client')
    def test_initialize_database_inconsistent_state(self, mock_spanner_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db
        
        # Mock snapshot results (some tables exist)
        mock_snapshot = MagicMock()
        mock_db.snapshot.return_value.__enter__.return_value = mock_snapshot
        mock_snapshot.execute_sql.return_value = [["table", "Node"]]
        
        client = SpannerClient("project", "instance", "database")
        
        # Run method and expect exception
        with self.assertRaises(RuntimeError):
            client.initialize_database()

    @patch('google.cloud.spanner.Client')
    def test_acquire_lock_new_row(self, mock_spanner_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db
        
        mock_transaction = MagicMock()
        def run_in_transaction_side_effect(callback, *args, **kwargs):
            return callback(mock_transaction, *args, **kwargs)
        mock_db.run_in_transaction.side_effect = run_in_transaction_side_effect
        
        # Mock execute_sql to return empty results (no row found)
        mock_transaction.execute_sql.return_value = []
        
        client = SpannerClient("project", "instance", "database")
        
        # Run method
        result = client.acquire_lock("workflow-123", 3600)
        
        # Verify
        self.assertTrue(result)
        mock_transaction.execute_update.assert_called_once()
        args, _ = mock_transaction.execute_update.call_args
        self.assertIn("INSERT INTO IngestionLock", args[0])

    @patch('google.cloud.spanner.Client')
    def test_acquire_lock_existing_row(self, mock_spanner_client):
        # Setup mock
        mock_instance = MagicMock()
        mock_db = MagicMock()
        mock_spanner_client.return_value.instance.return_value = mock_instance
        mock_instance.database.return_value = mock_db
        
        mock_transaction = MagicMock()
        def run_in_transaction_side_effect(callback, *args, **kwargs):
            return callback(mock_transaction, *args, **kwargs)
        mock_db.run_in_transaction.side_effect = run_in_transaction_side_effect
        
        # Mock execute_sql to return existing lock (owner is None)
        mock_transaction.execute_sql.return_value = [[None, None]]
        
        client = SpannerClient("project", "instance", "database")
        
        # Run method
        result = client.acquire_lock("workflow-123", 3600)
        
        # Verify
        self.assertTrue(result)
        mock_transaction.execute_update.assert_called_once()
        args, _ = mock_transaction.execute_update.call_args
        self.assertIn("UPDATE IngestionLock", args[0])

if __name__ == '__main__':
    unittest.main()

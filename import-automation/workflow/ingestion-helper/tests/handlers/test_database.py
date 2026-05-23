import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to find handlers and spanner_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from handlers.database import handle_initialize_database, handle_seed_database

class TestDatabaseHandlers(unittest.TestCase):

    @patch('handlers.database.FLAGS')
    def test_handle_initialize_database(self, mock_flags):
        mock_flags.enable_embeddings = False
        
        mock_spanner = MagicMock()
        request_json = {}
        
        response, status_code = handle_initialize_database(mock_spanner, request_json)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.initialize_database.assert_called_once_with(enable_embeddings=False)

    @patch('handlers.database.FLAGS')
    def test_handle_initialize_database_enable_embeddings(self, mock_flags):
        mock_flags.enable_embeddings = False
        
        mock_spanner = MagicMock()
        request_json = {'enableEmbeddings': True}
        
        response, status_code = handle_initialize_database(mock_spanner, request_json)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.initialize_database.assert_called_once_with(enable_embeddings=True)

    def test_handle_seed_database(self):
        mock_spanner = MagicMock()
        
        response, status_code = handle_seed_database(mock_spanner)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.seed_database.assert_called_once()

if __name__ == '__main__':
    unittest.main()

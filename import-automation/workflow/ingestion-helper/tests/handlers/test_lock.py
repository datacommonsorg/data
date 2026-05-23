import unittest
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path to find handlers and spanner_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from handlers.lock import handle_acquire_lock, handle_release_lock

class TestLockHandlers(unittest.TestCase):

    def test_handle_acquire_lock_success(self):
        mock_spanner = MagicMock()
        mock_spanner.acquire_lock.return_value = True
        
        request_json = {'workflowId': 'wf123', 'timeout': 3600}
        response, status_code = handle_acquire_lock(mock_spanner, request_json)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.acquire_lock.assert_called_once_with('wf123', 3600)

    def test_handle_acquire_lock_failure(self):
        mock_spanner = MagicMock()
        mock_spanner.acquire_lock.return_value = False
        
        request_json = {'workflowId': 'wf123', 'timeout': 3600}
        response, status_code = handle_acquire_lock(mock_spanner, request_json)
        
        self.assertEqual(status_code, 500)
        self.assertEqual(response, 'Failed to acquire lock')

    def test_handle_acquire_lock_missing_param(self):
        mock_spanner = MagicMock()
        
        request_json = {'workflowId': 'wf123'} # missing timeout
        response, status_code = handle_acquire_lock(mock_spanner, request_json)
        
        self.assertEqual(status_code, 400)
        self.assertIn('timeout', response)

    def test_handle_release_lock_success(self):
        mock_spanner = MagicMock()
        mock_spanner.release_lock.return_value = True
        
        request_json = {'workflowId': 'wf123'}
        response, status_code = handle_release_lock(mock_spanner, request_json)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.release_lock.assert_called_once_with('wf123')

    def test_handle_release_lock_failure(self):
        mock_spanner = MagicMock()
        mock_spanner.release_lock.return_value = False
        
        request_json = {'workflowId': 'wf123'}
        response, status_code = handle_release_lock(mock_spanner, request_json)
        
        self.assertEqual(status_code, 500)
        self.assertEqual(response, 'Failed to release lock')

if __name__ == '__main__':
    unittest.main()

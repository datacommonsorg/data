import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to find handlers and spanner_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from handlers.imports import handle_get_import_info, handle_update_ingestion_status, handle_update_import_status

class TestImportHandlers(unittest.TestCase):

    def test_handle_get_import_info(self):
        mock_spanner = MagicMock()
        mock_spanner.get_import_info.return_value = [{'importName': 'test_import'}]
        
        request_json = {'importList': ['test_import']}
        
        with patch('handlers.imports.jsonify', side_effect=lambda x: x):
            response = handle_get_import_info(mock_spanner, request_json)
            
        self.assertEqual(response, [{'importName': 'test_import'}])
        mock_spanner.get_import_info.assert_called_once_with(['test_import'])

    @patch('handlers.imports.FLAGS')
    @patch('handlers.imports.import_utils')
    def test_handle_update_ingestion_status_success(self, mock_import_utils, mock_flags):
        mock_flags.project_id = 'test-project'
        mock_flags.location = 'us-central1'
        
        mock_spanner = MagicMock()
        mock_import_utils.get_ingestion_metrics.return_value = {'nodes': 10}
        
        request_json = {
            'importList': [{'importName': 'import1'}],
            'workflowId': 'wf123',
            'jobId': 'job123',
            'status': 'SUCCESS'
        }
        
        response, status_code = handle_update_ingestion_status(mock_spanner, request_json)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_spanner.update_ingestion_status.assert_called_once_with(['import1'], 'wf123', 'SUCCESS')
        mock_spanner.update_ingestion_history.assert_called_once()
        mock_spanner.update_import_version_history.assert_called_once()

    @patch('handlers.imports.FLAGS')
    @patch('handlers.imports.import_utils')
    def test_handle_update_import_status_staging(self, mock_import_utils, mock_flags):
        mock_flags.project_id = 'test-project'
        mock_flags.location = 'us-central1'
        
        mock_spanner = MagicMock()
        mock_storage = MagicMock()
        
        request_json = {
            'importName': 'import1',
            'status': 'STAGING',
            'latestVersion': 'gs://bucket/import1/v1'
        }
        
        mock_import_utils.get_import_params.return_value = {'import_name': 'import1', 'status': 'STAGING'}
        mock_import_utils.get_next_refresh.return_value = None
        
        response, status_code = handle_update_import_status(mock_spanner, mock_storage, request_json)
            
        self.assertEqual(status_code, 200)
        self.assertEqual(response, 'OK')
        mock_storage.update_version_file.assert_called()
        mock_spanner.update_import_status.assert_called_once()

if __name__ == '__main__':
    unittest.main()

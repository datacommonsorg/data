import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to find handlers and spanner_client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from handlers.cache import handle_clear_redis_cache

class TestCacheHandlers(unittest.TestCase):

    @patch('handlers.cache.os.environ')
    @patch('handlers.cache.redis.Redis')
    def test_handle_clear_redis_cache_success(self, mock_redis, mock_environ):
        mock_environ.get.side_effect = lambda k, d=None: 'localhost' if k == 'REDIS_HOST' else ('6379' if k == 'REDIS_PORT' else d)
        
        mock_r = MagicMock()
        mock_redis.return_value = mock_r
        
        request_json = {}
        
        # Mock flask.jsonify
        with patch('handlers.cache.jsonify', side_effect=lambda x: x):
            response, status_code = handle_clear_redis_cache(request_json)
            
        self.assertEqual(status_code, 200)
        self.assertEqual(response['status'], 'SUCCESS')
        mock_r.flushall.assert_called_once_with(asynchronous=True)

    @patch('handlers.cache.os.environ')
    def test_handle_clear_redis_cache_skipped(self, mock_environ):
        mock_environ.get.return_value = None # REDIS_HOST not set
        
        request_json = {}
        
        with patch('handlers.cache.jsonify', side_effect=lambda x: x):
            response, status_code = handle_clear_redis_cache(request_json)
            
        self.assertEqual(status_code, 200)
        self.assertEqual(response['status'], 'SKIPPED')

if __name__ == '__main__':
    unittest.main()

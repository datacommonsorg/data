import unittest
from unittest import mock
import subprocess

from app.service import dashboard_api
from app.service import iap

class IAPRequestMock(mock.MagicMock):

    def __init__(self, client_id):
        assert client_id == 'id'


@mock.patch('app.utils.pttime', lambda: '2020-07-15T12:07:17.365264-07:00')
class DashboardAPITest(unittest.TestCase):

    @mock.patch('app.configs.get_dashboard_oauth_client_id', lambda: 'id')
    @mock.patch('app.service.iap.IAPRequest', mock.MagicMock(spec=iap.IAPRequest))
    def setUp(self):
        self.dashboard = dashboard_api.DashboardAPI()

    def test_log_helper(self):
        with mock.patch('app.service.dashboard_api.DashboardAPI.log') as log:
            self.assertRaises(ValueError, self.dashboard._log_helper, 'message', 'level')

            args = {
                'message': 'message',
                'level': 'level',
                'run_id': 'run',
                'attempt_id': 'attempt',
                'time_logged': 'time'
            }
            self.dashboard._log_helper(**args)
            log.assert_called_with(args)

            args = {
                'message': 'message',
                'level': 'level',
                'run_id': 'run'
            }
            expected = {
                'message': 'message',
                'level': 'level',
                'run_id': 'run',
                'time_logged': '2020-07-15T12:07:17.365264-07:00'
            }
            self.dashboard._log_helper(**args)
            log.assert_called_with(expected)

    def test_construct_log(self):
        self.assertRaises(ValueError, dashboard_api.construct_log, 'message')

        args = {
            'message': 'message',
            'attempt_id': 'attempt'
        }
        expected = {
            'message': 'message',
            'level': 'info',
            'attempt_id': 'attempt',
            'time_logged': '2020-07-15T12:07:17.365264-07:00'
        }
        self.assertEqual(expected, dashboard_api.construct_log(**args))

        process = subprocess.run(
            'echo "out" & >&2 echo "err" & exit 1',
            shell=True, text=True, capture_output=True)
        args = {
            'message': 'message',
            'process': process,
            'run_id': 'run',
            'level': 'info',
            'time_logged': 'time'
        }
        expected = {
            'message': 'message',
            'time_logged': 'time',
            'return_code': 1,
            'run_id': 'run',
            'stdout': 'out\n',
            'stderr': 'err\n',
            'level': 'critical',
            'args': 'echo "out" & >&2 echo "err" & exit 1'
        }
        self.assertEqual(expected, dashboard_api.construct_log(**args))

    def test_update_attempt(self):
        attempt = {'hello': 'world'}
        self.dashboard.update_attempt(attempt, 'id')
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/id',
            json={'hello': 'world'})

        attempt = {'hello': 'world', 'attempt_id': 'id'}
        self.dashboard.update_attempt(attempt)
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/id',
            json={'hello': 'world', 'attempt_id': 'id'})

    def test_update_run(self):
        run = {'hello': 'world'}
        self.dashboard.update_run(run, 'id')
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/system_runs/id',
            json={'hello': 'world'})

        run = {'hello': 'world', 'run_id': 'id'}
        self.dashboard.update_run(run)
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/system_runs/id',
            json={'hello': 'world', 'run_id': 'id'})

    def test_critical(self):
        self.assertRaises(ValueError, self.dashboard.critical, 'message')

        args = {
            'message': 'message',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time',
        }
        expected = {
            'message': 'message',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time',
            'level': 'critical'
        }
        self.dashboard.critical(**args)
        self.dashboard.iap.post.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/logs', json=expected)

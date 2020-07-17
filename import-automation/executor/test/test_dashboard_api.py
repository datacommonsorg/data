import unittest
from unittest import mock
import subprocess

from app.service import dashboard_api
from app.service import iap


@mock.patch('app.utils.pttime', lambda: '2020-07-15T12:07:17.365264-07:00')
class DashboardAPITest(unittest.TestCase):

    @mock.patch('app.configs.get_dashboard_oauth_client_id',
                lambda: 'id')
    @mock.patch('app.service.iap.IAPRequest',
                mock.MagicMock(spec=iap.IAPRequest))
    def setUp(self):
        self.dashboard = dashboard_api.DashboardAPI()

    @mock.patch('app.service.dashboard_api.DashboardAPI.log')
    def test_log_helper(self, log):
        args = {
            'message': 'message',
            'level': 'level',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time'
        }
        self.dashboard._log_helper(**args)
        log.assert_called_with(args)
        with mock.patch('app.service.dashboard_api.DashboardAPI.log') as log:
            self.assertRaises(ValueError, self.dashboard._log_helper, 'message', 'level')

    @mock.patch('app.service.dashboard_api.DashboardAPI.log')
    def test_log_helper_time(self, log):
        """Tests that time_logged is generated if not supplied."""
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

    @mock.patch('app.service.dashboard_api.DashboardAPI.log')
    def test_log_helper_raise(self, _):
        """Tests that at least one of run_id and attempt_id
        need to be specified."""
        self.assertRaises(ValueError, self.dashboard._log_helper, 'message',
                          'level')

    def test_construct_log(self):
        """Tests that level and time_logged are added if not supplied."""
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

    def test_construct_log_raise(self):
        """Tests that at least one of run_id and attempt_id
        need to be supplied."""
        self.assertRaises(ValueError, dashboard_api.construct_log, 'message')

    def test_construct_log_process(self):
        """Tests logging a subprocess."""
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

    def test_update_attempt_id(self):
        """Tests that attempt_id can be found in the attempt body
        if not supplied as an argument."""
        attempt = {'hello': 'world', 'attempt_id': 'id'}
        self.dashboard.update_attempt(attempt)
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/import_attempts/id',
            json={'hello': 'world', 'attempt_id': 'id'})

    def test_update_attempt_no_id(self):
        """Tests that an exception is raised if attempt_id is not found."""
        attempt = {'hello': 'world'}
        self.assertRaises(ValueError, self.dashboard.update_attempt, attempt)

    def test_update_run(self):
        run = {'hello': 'world'}
        self.dashboard.update_run(run, 'id')
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/system_runs/id',
            json={'hello': 'world'})

    def test_update_run_id(self):
        """Tests that run_id can be found in the run body
        if not supplied as an argument."""
        run = {'hello': 'world', 'run_id': 'id'}
        self.dashboard.update_run(run)
        self.dashboard.iap.patch.assert_called_with(
            'https://datcom-data.uc.r.appspot.com/system_runs/id',
            json={'hello': 'world', 'run_id': 'id'})

    def test_update_run_no_id(self):
        """Tests that an exception is raised if run_id is not found."""
        run = {'hello': 'world'}
        self.assertRaises(ValueError, self.dashboard.update_run, run)

    @mock.patch('app.service.dashboard_api.DashboardAPI.log')
    def test_levels(self, log):
        """Tests that the convenient logging functions add the right
        logging levels.  """
        args = {
            'message': 'message',
            'time_logged': 'time',
            'run_id': 'run'
        }
        funcs = [
            (self.dashboard.critical, 'critical'),
            (self.dashboard.error, 'error'),
            (self.dashboard.warning, 'warning'),
            (self.dashboard.info, 'info'),
            (self.dashboard.debug, 'debug')
        ]
        for func, level in funcs:
            func(**args)
            self.assertEqual(level, log.call_args[0][0]['level'])

    @mock.patch('app.configs.standalone', lambda: True)
    @mock.patch('app.service.iap.IAPRequest')
    def test_standalone(self, iap_request):
        # Tests that no IAP calls are made in standalone mode
        dashboard = dashboard_api.DashboardAPI(client_id=1)
        dashboard.iap = iap_request()
        logging_funcs = [
            dashboard.critical,
            dashboard.error,
            dashboard.warning,
            dashboard.info,
            dashboard.debug
        ]
        log = {
            'message': 'message',
            'run_id': 'run',
            'attempt_id': 'attempt',
            'time_logged': 'time'
        }
        for func in logging_funcs:
            func(**log)

        dashboard.init_run({})
        dashboard.init_attempt({})
        dashboard.update_run({'run_id': 'run'})
        dashboard.update_attempt({'attempt_id': 'attempt'})

        dashboard.iap.get.assert_not_called()
        dashboard.iap.put.assert_not_called()
        dashboard.iap.post.assert_not_called()
        dashboard.iap.patch.assert_not_called()
        dashboard.iap._request.assert_not_called()

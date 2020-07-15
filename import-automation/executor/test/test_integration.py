import os
import unittest
import logging
from unittest import mock
import uuid

from app import main
from app import utils


class DashboardAPIMock(mock.MagicMock):
    pass
    # def __init__(self):
    #     self.attempts = {}
    #     self.runs = {}
    #     self.logs = {}
    #
    # def info(self, message, attempt_id=None, run_id=None, time_logged=None):
    #     return self._log(message, 'info', attempt_id, run_id, time_logged)
    #
    # def warning(self, message, attempt_id=None, run_id=None, time_logged=None):
    #     return self._log(message, 'warning', attempt_id, run_id, time_logged)
    #
    # def severe(self, message, attempt_id=None, run_id=None, time_logged=None):
    #     return self._log(message, 'critical', attempt_id, run_id, time_logged)
    #
    # def _log(self, message, level, attempt_id=None, run_id=None, time_logged=None):
    #     if not attempt_id and not run_id:
    #         raise ValueError('Neither attempt_id or run_id is specified')
    #     if not time_logged:
    #         time_logged = utils.utctime()
    #
    #     log = {
    #         'message': message,
    #         'level': level,
    #         'time_logged': time_logged
    #     }
    #     if attempt_id:
    #         log['attempt_id'] = attempt_id
    #         attempt = self.attempts[attempt_id]
    #         logs = attempt.setdefault('logs', [])
    #         logs.append(log)
    #     if run_id:
    #         log['run_id'] = run_id
    #         run = self.runs[run_id]
    #         logs = run.setdefault('logs', [])
    #         logs.append(log)
    #
    # def init_run(self, system_run):
    #     run_id = uuid.uuid4().hex
    #     system_run['run_id'] = run_id
    #     self.runs[run_id] = system_run
    #     return system_run
    #
    # def init_attempt(self, import_attempt):
    #     attempt_id = uuid.uuid4().hex
    #     import_attempt['attempt_id'] = attempt_id
    #     self.attempts[attempt_id] = import_attempt
    #     return import_attempt
    #
    # def update_attempt(self, import_attempt, attempt_id=None):
    #     if not attempt_id:
    #         attempt_id = import_attempt['attempt_id']
    #     attempt = self.attempts[attempt_id]
    #     for k, v in import_attempt.items():
    #         attempt[k] = v
    #     return attempt
    #
    # def update_run(self, system_run, run_id=None):
    #     if not run_id:
    #         run_id = system_run['run_id']
    #     run = self.runs[run_id]
    #     for k, v in system_run.items():
    #         run[k] = v
    #     return run


class GCSBucketIOMock:
    def __init__(self, path_prefix='', bucket_name='', bucket=None, client=None):
        self.data = {}

    def upload_file(self, src, dest):
        self.data[dest] = src
        with open(src) as file:
            logging.warning(f'Generated {src}: {file.readline()}')

    def update_version(self, version):
      logging.warning(f'Version: {version}')


def get_github_auth_access_token_mock():
    return os.environ.get('GITHUB_ACCESS_TOKEN', '')


@mock.patch('app.service.gcs_io.GCSBucketIO',
            GCSBucketIOMock)
class IntegrationTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ['TMPDIR'] = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.environ.pop('TMPDIR')

    def setUp(self):
        self.app = main.FLASK_APP.test_client()

    @mock.patch('app.configs.get_github_auth_access_token', get_github_auth_access_token_mock)
    @mock.patch('app.service.dashboard_api.DashboardAPI', DashboardAPIMock)
    def test_commit(self):
        self.app.post('/', json={'COMMIT_SHA': '9804f2fd2c5422a9f6b896e9c6862db61f9a8a08'})

    def test_update(self):
        with mock.patch('app.configs.standalone', return_value=True):
            self.app.post('/update', json={'absolute_import_name': 'scripts/us_fed/treasury_constant_maturity_rates:all'})

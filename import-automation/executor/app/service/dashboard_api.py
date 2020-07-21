# Copyright 2020 Google LLC
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

"""
Import progress dashboard API client.
"""

import logging
import subprocess

from app import utils
from app import configs
from app.service import iap_request

_DASHBOARD_API_HOST = 'https://datcom-data.uc.r.appspot.com'

_DASHBOARD_RUN_LIST = _DASHBOARD_API_HOST + '/system_runs'
_DASHBOARD_RUN_BY_ID = _DASHBOARD_RUN_LIST + '/{run_id}'

_DASHBOARD_ATTEMPT_LIST = _DASHBOARD_API_HOST + '/import_attempts'
_DASHBOARD_ATTEMPT_BY_ID = _DASHBOARD_ATTEMPT_LIST + '/{attempt_id}'

_DASHBOARD_LOG_LIST = _DASHBOARD_API_HOST + '/logs'
_DASHBOARD_LOG_BY_ID = _DASHBOARD_LOG_LIST + '/{log_id}'


class LogLevel:
    """Allowed log levels of a log.
    The level of a log can only be one of these.
    """
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    DEBUG = 'debug'


class DashboardAPI:
    """Import progress dashboard API client.

    Attributes:
        iap: IAPRequest object for making HTTP requests to
            Identity-Aware Proxy protected resources.
    """

    def __init__(self, client_id: str):
        """Constructs a DashboardAPI.

        Args:
            client_id: Oauth2 client id for authentication.
        """
        self.iap = iap_request.IAPRequest(client_id)

    def critical(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(message, LogLevel.CRITICAL,
                                attempt_id, run_id, time_logged)

    def error(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(message, LogLevel.ERROR,
                                attempt_id, run_id, time_logged)

    def warning(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(message, LogLevel.WARNING,
                                attempt_id, run_id, time_logged)

    def info(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(message, LogLevel.INFO,
                                attempt_id, run_id, time_logged)

    def debug(self, message, attempt_id=None, run_id=None, time_logged=None):
        return self._log_helper(message, LogLevel.DEBUG,
                                attempt_id, run_id, time_logged)

    def init_run(self, system_run):
        return self.iap.post(_DASHBOARD_RUN_LIST, json=system_run).json()

    def init_attempt(self, import_attempt):
        return self.iap.post(_DASHBOARD_ATTEMPT_LIST,
                             json=import_attempt).json()

    def update_attempt(self, import_attempt, attempt_id=None):
        if not attempt_id:
            attempt_id = import_attempt.get('attempt_id')
            if not attempt_id:
                raise ValueError('attempt_id not supplied as an argument and '
                                 'not found the in the attempt body')
        return self.iap.patch(
            _DASHBOARD_ATTEMPT_BY_ID.format_map({'attempt_id': attempt_id}),
            json=import_attempt).json()

    def update_run(self, system_run, run_id=None):
        if not run_id:
            run_id = system_run.get('run_id')
            if not run_id:
                raise ValueError('run_id not supplied as an argument and '
                                 'not found the in the run body')
        return self.iap.patch(
            _DASHBOARD_RUN_BY_ID.format_map({'run_id': run_id}),
            json=system_run).json()

    def _log_helper(self,
                    message: str,
                    level: str,
                    attempt_id: str = None,
                    run_id: str = None,
                    time_logged: str = None):
        """
        Args:
            message: Log message as a string.
            level: Log level as a string.
            process: subprocess.CompletedProcess object that has been executed and
                that needs to be logged.
            time_logged: Time logged in ISO format with UTC timezone as a string.
            run_id: ID of the system run to link to as a string.
            attempt_id: ID of the import attempt to link to as a string.

        Raises:
            ValueError: Neither run_id nor attempt_id is specified.
        """
        if not run_id and not attempt_id:
            raise ValueError('Neither run_id nor attempt_id is specified')
        if not time_logged:
            time_logged = utils.utctime()
        log = {
            'message': message,
            'level': level,
            'time_logged': time_logged
        }
        if run_id:
            log['run_id'] = run_id
        if attempt_id:
            log['attempt_id'] = attempt_id
        response = self.iap.post(_DASHBOARD_LOG_LIST, json=log)
        response.raise_for_status()
        return response.json()

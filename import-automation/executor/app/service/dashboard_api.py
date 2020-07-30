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

from typing import Dict

from app import utils
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
    CRITICAL: str = 'critical'
    ERROR: str = 'error'
    WARNING: str = 'warning'
    INFO: str = 'info'
    DEBUG: str = 'debug'


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

    def critical(self,
                 message: str,
                 attempt_id: str = None,
                 run_id: str = None,
                 time_logged: str = None) -> Dict:
        """Logs a message with level CRITICAL. See _log_helper."""
        return self._log_helper(message, LogLevel.CRITICAL, attempt_id, run_id,
                                time_logged)

    def error(self,
              message: str,
              attempt_id: str = None,
              run_id: str = None,
              time_logged: str = None) -> Dict:
        """Logs a message with level ERROR. See _log_helper."""
        return self._log_helper(message, LogLevel.ERROR, attempt_id, run_id,
                                time_logged)

    def warning(self,
                message: str,
                attempt_id: str = None,
                run_id: str = None,
                time_logged: str = None) -> Dict:
        """Logs a message with level WARNING. See _log_helper."""
        return self._log_helper(message, LogLevel.WARNING, attempt_id, run_id,
                                time_logged)

    def info(self,
             message: str,
             attempt_id: str = None,
             run_id: str = None,
             time_logged: str = None) -> Dict:
        """Logs a message with level INFO. See _log_helper."""
        return self._log_helper(message, LogLevel.INFO, attempt_id, run_id,
                                time_logged)

    def debug(self,
              message: str,
              attempt_id: str = None,
              run_id: str = None,
              time_logged: str = None) -> Dict:
        """Logs a message with level DEBUG. See _log_helper."""
        return self._log_helper(message, LogLevel.DEBUG, attempt_id, run_id,
                                time_logged)

    def init_run(self, system_run: Dict) -> Dict:
        """Initializes an system run.

        Args:
            system_run: System run as a dict.

        Returns:
            Initialized system run returned from the dashboard as a dict.

        Raises:
            Same exceptions as IAPRequest.post.
        """
        return self.iap.post(_DASHBOARD_RUN_LIST, json=system_run).json()

    def init_attempt(self, import_attempt: Dict) -> Dict:
        """Initializes an import attempt.

        Args:
            import_attempt: Import attempt as a dict.

        Returns:
            Initialized import attempt returned from the dashboard as a dict.

        Raises:
            Same exceptions as IAPRequest.post.
        """
        return self.iap.post(_DASHBOARD_ATTEMPT_LIST,
                             json=import_attempt).json()

    def update_attempt(self, import_attempt: Dict, attempt_id: str) -> Dict:
        """Updates some fields of an import attempt.

        Args:
            import_attempt: Import attempt with the fields to update, as a dict.
            attempt_id: ID of the import attempt, as a string.

        Returns:
            Updated import attempt returned from the dashboard, as a dict.
        """
        return self.iap.patch(_DASHBOARD_ATTEMPT_BY_ID.format_map(
            {'attempt_id': attempt_id}),
                              json=import_attempt).json()

    def update_run(self, system_run: Dict, run_id: str) -> Dict:
        """Updates some fields of a system run.

        Args:
            system_run: System run with the fields to update, as a dict.
            run_id: ID of the system run, as a string.

        Returns:
            Updated system run returned from the dashboard, as a dict.
        """
        return self.iap.patch(_DASHBOARD_RUN_BY_ID.format_map(
            {'run_id': run_id}),
                              json=system_run).json()

    def _log_helper(self,
                    message: str,
                    level: str,
                    attempt_id: str = None,
                    run_id: str = None,
                    time_logged: str = None) -> Dict:
        """Posts a progress log to the import progress dashboard.

        Args:
            message: Log message as a string.
            level: Log level as a string.
            run_id: ID of the system run to link to as a string.
            attempt_id: ID of the import attempt to link to as a string.
            time_logged: Time logged in ISO 8601 format with UTC timezone
                as a string.

        Returns:
            The posted progress log as a dict.

        Raises:
            ValueError: Neither run_id nor attempt_id is specified.
        """
        if not run_id and not attempt_id:
            raise ValueError('Neither run_id nor attempt_id is specified')
        if not time_logged:
            time_logged = utils.utctime()
        log = {'message': message, 'level': level, 'time_logged': time_logged}
        if run_id:
            log['run_id'] = run_id
        if attempt_id:
            log['attempt_id'] = attempt_id
        response = self.iap.post(_DASHBOARD_LOG_LIST, json=log)
        response.raise_for_status()
        return response.json()

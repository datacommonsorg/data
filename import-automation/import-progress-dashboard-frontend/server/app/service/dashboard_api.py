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

from typing import Dict, List

from server.app.service import iap_request

_DASHBOARD_API_HOST = 'https://datcom-data.uc.r.appspot.com'

_DASHBOARD_RUN_LIST = _DASHBOARD_API_HOST + '/system_runs'
_DASHBOARD_RUN_BY_ID = _DASHBOARD_RUN_LIST + '/{run_id}'
_DASHBOARD_RUN_BY_ID_LOGS = _DASHBOARD_RUN_BY_ID + '/logs'

_DASHBOARD_ATTEMPT_LIST = _DASHBOARD_API_HOST + '/import_attempts'
_DASHBOARD_ATTEMPT_BY_ID = _DASHBOARD_ATTEMPT_LIST + '/{attempt_id}'
_DASHBOARD_ATTEMPT_BY_ID_LOGS = _DASHBOARD_ATTEMPT_BY_ID + '/logs'

_DASHBOARD_LOG_LIST = _DASHBOARD_API_HOST + '/logs'
_DASHBOARD_LOG_BY_ID = _DASHBOARD_LOG_LIST + '/{log_id}'


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

    def get_system_runs(self) -> List[Dict]:
        """Returns all the system runs."""
        return self._get_json(_DASHBOARD_RUN_LIST)

    def get_import_attempt(self, attempt_id) -> Dict:
        """Returns the import attempt with the attempt_id."""
        return self._get_json(
            _DASHBOARD_ATTEMPT_BY_ID.format_map({'attempt_id': attempt_id}))

    def get_logs_by_run_id(self, run_id: str) -> List[Dict]:
        """Returns the logs of a system run with the run_id."""
        return self._get_json(
            _DASHBOARD_RUN_BY_ID_LOGS.format_map({'run_id': run_id}))

    def get_logs_by_attempt_id(self, attempt_id: str) -> List[Dict]:
        """Returns the logs of an import attempt with the attempt_id."""
        return self._get_json(
            _DASHBOARD_ATTEMPT_BY_ID_LOGS.format_map({'attempt_id': attempt_id
                                                     }))

    def _get_json(self, query):
        """Sends a GET request and returns the json from the response."""
        response = self.iap.get(query)
        response.raise_for_status()
        return response.json()

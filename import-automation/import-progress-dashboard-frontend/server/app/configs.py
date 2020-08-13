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
Configurations for the server.
"""

import os

from google.cloud import logging


def _is_production():
    return 'DASHBOARD_FRONTEND_PRODUCTION' in os.environ


def _setup_logging():
    """Connects the default logger to Google Cloud Logging.
    Only logs at INFO level or higher will be captured.
    """
    client = logging.Client()
    client.get_default_handler()
    client.setup_logging()


def get_dashboard_oauth_client_id():
    """Gets the client ID used to authenticate with Identity-Aware Proxy
    from the environment variable DASHBOARD_OAUTH_CLIENT_ID."""
    return os.environ.get('DASHBOARD_OAUTH_CLIENT_ID')


if _is_production():
    _setup_logging()

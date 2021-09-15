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
Class for making HTTP requests to Identity-Aware Proxy-protected applications.
"""

import requests

import google.auth.transport.requests
from google.oauth2 import id_token


class IAPRequest:
    """Class for making HTTP requests to Identity-Aware Proxy-protected
    applications.

    Attributes:
        client_id: Oauth client ID used to authenticate with
            Identity-Aware Proxy, as a string.
    """
    def __init__(self, client_id: str):
        self.client_id = client_id

    def get(self, url: str, **kwargs) -> requests.Response:
        """Makes a GET request. See _request."""
        return self._request(url, 'GET', **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """Makes a PUT request. See _request."""
        return self._request(url, 'PUT', **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Makes a POST request. See _request."""
        return self._request(url, 'POST', **kwargs)

    def patch(self, url: str, **kwargs) -> requests.Response:
        """Makes a PATCH request. See _request."""
        return self._request(url, 'PATCH', **kwargs)

    def _request(self, url: str, method: str, **kwargs) -> requests.Response:
        """Makes a request to an application protected by Identity-Aware Proxy.

        For valid values for method and kwargs, see
        https://requests.readthedocs.io/en/master/api/?highlight=request#requests.request.

        Args:
            url: The Identity-Aware Proxy-protected URL to fetch.
            method: The request method to use.
            **kwargs: Any of the parameters defined for the requests.request.

        Returns:
            The response as a request.Response object.

        Raises:
            Same exceptions as google.oauth2.id_token.fetch_id_token.
            Same exceptions as request.request.
        """
        # Obtain an OpenID Connect (OIDC) token from metadata server or
        # using service account.
        google_open_id_connect_token = id_token.fetch_id_token(
            google.auth.transport.requests.Request(), self.client_id)

        # Fetch the Identity-Aware Proxy-protected URL, including an
        # Authorization header containing "Bearer " followed by a
        # Google-issued OpenID Connect token for the service account.
        headers = kwargs.setdefault('headers', {})
        headers['Authorization'] = f'Bearer {google_open_id_connect_token}'
        response = requests.request(method, url, **kwargs)

        return response

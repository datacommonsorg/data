from google.auth.transport.requests import Request
from google.oauth2 import id_token

import requests


def get(client_id, url, **kwargs):
    return _request(client_id, url, 'GET', **kwargs)


def put(client_id, url, **kwargs):
    return _request(client_id, url, 'PUT', **kwargs)


def post(client_id, url, **kwargs):
    return _request(client_id, url, 'POST', **kwargs)


def patch(client_id, url, **kwargs):
    return _request(client_id, url, 'PATCH', **kwargs)


def _request(client_id, url, method, **kwargs):
    """Makes a request to an application protected by Identity-Aware Proxy.

    Args:
      client_id: The client ID used by Identity-Aware Proxy.
      url: The Identity-Aware Proxy-protected URL to fetch.
      method: The request method to use
              ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE')
      **kwargs: Any of the parameters defined for the request function:
                https://github.com/requests/requests/blob/master/requests/api.py

    Returns:
      The Response.
    """
    # Obtain an OpenID Connect (OIDC) token from metadata server or
    # using service account.
    google_open_id_connect_token = id_token.fetch_id_token(Request(), client_id)

    # Fetch the Identity-Aware Proxy-protected URL, including an
    # Authorization header containing "Bearer " followed by a
    # Google-issued OpenID Connect token for the service account.
    headers = kwargs.setdefault('headers', {})
    headers['Authorization'] = 'Bearer {}'.format(google_open_id_connect_token)
    response = requests.request(method, url, **kwargs)

    return response

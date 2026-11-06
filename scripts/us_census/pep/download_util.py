# Copyright 2026 Google LLC
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
"""Shared download, retry, and WAF detection utilities for Census PEP family."""

import os
import tempfile
from absl import logging
import requests
from requests.adapters import HTTPAdapter
from retry import retry
from urllib3.util.retry import Retry

DEFAULT_USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) DataCommonsImport/1.0 '
                      '(https://datacommons.org)')

TRANSIENT_STATUS_CODES = (408, 429, 500, 502, 503, 504, 520)


class TransientDownloadError(Exception):
    """Raised when a transient download error occurs (e.g. WAF, HTML block)."""


def is_html_response(content_type: str = '', first_bytes: bytes = b'') -> bool:
    """Returns True if the response headers or body indicate an HTML/WAF error page."""
    if 'html' in (content_type or '').lower():
        return True
    if first_bytes:
        head = first_bytes[:512].lstrip().lower()
        if (head.startswith(b'<html') or head.startswith(b'<!doctype html') or
                b'<title>request rejected</title>' in head or
                b'the requested url was rejected' in head or
                head.startswith(b'<head') or head.startswith(b'<body')):
            return True
    return False


def create_retry_session(retries: int = 5,
                         backoff_factor: int = 2) -> requests.Session:
    """Creates a requests.Session configured with retry and backoff for transient errors."""
    session = requests.Session()
    session.headers.update({
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': '*/*',
    })
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=list(TRANSIENT_STATUS_CODES),
        allowed_methods=['HEAD', 'GET'],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


@retry(exceptions=(TransientDownloadError,
                   requests.exceptions.RequestException),
       tries=3,
       delay=5,
       backoff=2)
def head_with_html_retry(session: requests.Session,
                         url: str,
                         timeout: int = 30) -> requests.Response:
    """Performs a HEAD request with retry when the server returns HTML for a non-HTML URL."""
    response = session.head(url, timeout=timeout, allow_redirects=True)
    if response.status_code in TRANSIENT_STATUS_CODES:
        raise TransientDownloadError(
            f'Server returned transient status code {response.status_code} for URL: {url}'
        )
    content_type = response.headers.get('Content-Type', '').lower()
    if (response.status_code == 200 and 'html' in content_type and
            not url.lower().endswith(('.html', '.htm'))):
        raise TransientDownloadError(
            f'Server returned HTML (Content-Type: {content_type}) for non-HTML URL: {url}'
        )
    return response


@retry(exceptions=(TransientDownloadError,
                   requests.exceptions.RequestException),
       tries=3,
       delay=5,
       backoff=2)
def download_with_retry(session: requests.Session,
                        url: str,
                        dest_path: str,
                        timeout: int = 120):
    """Downloads a URL to dest_path atomically, retrying on HTTP errors or HTML/WAF pages."""
    logging.info(f'Downloading file from URL: {url} -> {dest_path}')
    with session.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')
        if (not url.lower().endswith(('.html', '.htm')) and
                is_html_response(content_type)):
            raise TransientDownloadError(
                f'Server returned HTML error page (Content-Type: {content_type}) for non-HTML URL: {url}'
            )
        dest_dir = os.path.dirname(os.path.abspath(dest_path)) or '.'
        os.makedirs(dest_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dest_dir)
        try:
            first_chunk = b''
            with os.fdopen(fd, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        if not first_chunk:
                            first_chunk = chunk[:512]
                            if (not url.lower().endswith(
                                ('.html', '.htm')) and is_html_response(
                                    content_type, first_chunk)):
                                raise TransientDownloadError(
                                    f'Server returned HTML error page (Content-Type: {content_type}) for non-HTML URL: {url}'
                                )
                        f.write(chunk)
            if not first_chunk:
                raise TransientDownloadError(
                    f'Downloaded empty file from URL: {url}')
            os.replace(tmp_path, dest_path)
            tmp_path = None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
    logging.info(f'Downloaded file: {dest_path}')


def atomic_to_csv(df, target_path: str, **kwargs):
    """Writes a DataFrame to CSV atomically via a temporary file."""
    dest_dir = os.path.dirname(os.path.abspath(target_path)) or '.'
    os.makedirs(dest_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dest_dir)
    os.close(fd)
    try:
        df.to_csv(tmp_path, **kwargs)
        os.replace(tmp_path, target_path)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def atomic_to_excel(df, target_path: str, **kwargs):
    """Writes a DataFrame to Excel atomically via a temporary file."""
    dest_dir = os.path.dirname(os.path.abspath(target_path)) or '.'
    os.makedirs(dest_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dest_dir)
    os.close(fd)
    try:
        df.to_excel(tmp_path, **kwargs)
        os.replace(tmp_path, target_path)
        tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# Aliases for backwards compatibility with existing PEP code
_create_retry_session = create_retry_session
_is_html_response = is_html_response
_head_with_html_retry = head_with_html_retry

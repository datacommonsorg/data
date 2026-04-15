# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Library to download URLs.

This contains the following utilities to download data from URLS:
1. request_url()
  This is a wrapper around requests.request with some additional features such as:
  - retry downloads with timeouts
  - use caches for frequently accessed URLs.
  - URLs with 'http://', 'https://' or 'gs://'
    For URLs with 'gs://' clients can authenticate with Google Cloud Service
    using 'gcloud auth login'.
  - http methods: GET or POST

  Example:
  To download a list of all countries in DataCommons:
     import download_util
     countries = download_util.request_url(
            url='https://api.datacommons.org/v2/node',
            params={
                'nodes': ['Earth'],
                'property': '<-containedInPlace+{typeOf:Country}'
            },
            output='JSON')

  To download a list of all countries in DataCommons:
     response_json = download_util.request_url(
                          url='https://httpbin.org/post',
                          params={'param1': 'value1'},
                          method='POST',
                          output='JSON')

2. download_file_from_url()
  Download a file from a URL.
  If the URL ends with a '.gz', it downloads the compressed file, inflates it
  and returns the uncompressed file.

  Example: To download csv with the latest population for all states in India:
    filename = download_util.download_file_from_url(
        url='https://autopush.datacommons.org/api/csv/within',
        params={
            'parentPlace': 'country/IND',
            'childType': 'AdministrativeArea1',
            'statVars': ['Count_Person']
        },
        method='POST',
        output_file='india_state_population.csv')

3. set_test_response():
  For tests that use the above functions, use this to seed the response for a URL.
  When the caller requests for the URL later, the pre-filled response is returned.

   class MyTest(unittest.TestCase):
      def setUp():
        # Setup response for a test URL.
        download_util.test_set_response(
          'http://myserver.com', {'name': 'abc'},
          {'dcid': '123'})

      def test_my_function(self):
          ...
          server_resp = download_util.request_url('http://myserver.com', {'name': 'abc'})
          # server_resp will be set to {'dcid': '123'} set earlier.
  '''

import gzip
import json
import os
import requests
import requests_cache
import time
import urllib

from absl import logging
from google.cloud import storage
from typing import Union

# Response pre-filled for tests.
_PREFILLED_RESPONSE = {}


def request_url(url: str,
                params: dict = {},
                method: str = 'GET',
                headers: dict = {},
                output: str = 'text',
                timeout: int = 30,
                retries: int = 3,
                retry_secs: int = 5,
                use_cache: bool = False) -> Union[str, dict, bytes]:
    '''Wrapper around requests to make a HTTP request and return the response.
    Returns the response from the http request in the specified format(text/json/bytes).

    Args:
      url: URL to download.
        if it begins with 'gs://', returns the GCS file with GCS project in prams.
      params: Parameters to be passed for the download.
      method: 'GET' or 'POST'
      output: the output format, 'text', 'json' or 'bytes'
      timeout: timeout in seconds.
      retries: Number of retries in case of HTTP errors.
      retry_sec: Interval in seconds between retries for which caller is blocked.
      use_cache: If True, uses request cache for faster response.

    Returns:
      The response from the URL download in the output format whcih is one of:
      str, JSON or bytes
    '''
    # Check if the response is pre-filled for tests.
    key = _get_prefilled_key(url, params)
    if key in _PREFILLED_RESPONSE:
        return _PREFILLED_RESPONSE[key]

    if url.startswith('gs:'):
        # Download GCS URL using Google Cloud Storage APIs.
        logging.info(f'Downloading GCS file: {url} with params: {params}')
        return download_gcs_file(url=url, params=params)
    elif os.path.exists(url):
        # URL is a local file. Return its contents.
        logging.info(f'Reading local file: {url}')
        with open(url, 'r') as file:
            return file.read()

    # Download URL
    logging.info(
        f'Downloading URL: {url} with params: {params}, method: {method}')
    if not retries or retries <= 0:
        retries = 1
    # Setup request cache
    if not requests_cache.is_installed():
        requests_cache.install_cache(expires_after=300)
    cache_context = None
    if use_cache:
        cache_context = requests_cache.enabled()
        logging.debug(f'Using requests_cache for URL {url}')
    else:
        cache_context = requests_cache.disabled()
        logging.debug(f'Using requests_cache for URL {url}')
    with cache_context:
        for attempt in range(retries):
            try:
                logging.debug(
                    f'Downloading URL {url}, headers:{headers} params:{params}, {method} #{attempt}, retries={retries}'
                )
                if 'get' in method.lower():
                    response = requests.get(url,
                                            headers=headers,
                                            params=params,
                                            timeout=timeout)
                else:
                    response = requests.post(url,
                                             headers=headers,
                                             json=params,
                                             timeout=timeout)
                logging.debug(
                    f'Got API response {response} for {url}, {params}')
                if response.ok:
                    if 'json' in output.lower():
                        return response.json()
                    elif 'text' in output:
                        return response.text
                    else:
                        return response.content
            except KeyError:
                # Exception in case of API error.
                return None
            except (requests.exceptions.ConnectTimeout,
                    requests.exceptions.ConnectionError, urllib.error.URLError,
                    urllib.error.HTTPError) as e:
                logging.debug(f'Got exception {e} for {url}, {params}')

            # retry in case of errors
            if attempt >= retries:
                raise urllib.error.URLError
            else:
                logging.debug(f'Retrying URL {url} after {retry_secs} secs ...')
                time.sleep(retry_secs)
    return None


def download_gcs_file(url: str, params: dict = {}) -> bytes:
    '''Downloads a GCS file from the given URL.
    Assumes the client is authenticated and has access to the project.

    Args:
      url: Google cloud storage URL of the form 'gs://<gcs-bucket>/<file-path>'
      params: Dictionary with the following parameters
        for Google Cloud Storage access:
          'gcs_project': GCS project ID
          'gcs_bucket': GCS bucket name for the file
    Returns:
      The content from the file as bytes.
    '''
    gcs_path_params = url.split('/', 3)
    gcs_project_id = params.get('gcs_project', '')
    gcs_bucket_name = params.get('gcs_bucket', gcs_path_params[2])
    if ':' in gcs_bucket_name:
        # Bucket has both project and bucket.
        gcs_project_id, gcs_bucket_name = gcs_bucket_name.split(':', 1)
    blob_path = gcs_path_params[3]
    logging.debug(
        f'Reading GCS file from project:{gcs_project_id}, bucket:{gcs_bucket_name}, path:{blob_path}'
    )
    storage_client = storage.Client(gcs_project_id)
    bucket = storage_client.bucket(gcs_bucket_name)
    blob = bucket.blob(blob_path)

    with blob.open("r") as f:
        return f.read()


def download_file_from_url(url: str,
                           params: dict = {},
                           method: str = 'GET',
                           timeout: int = 30,
                           retries: int = 3,
                           retry_secs: int = 5,
                           output_file: str = None,
                           overwrite: bool = True) -> str:
    '''Download a URL and save it as output_file.
    If the url is compressed, the output_file is uncompressed.

    Args:
      url: URL to download
      params: dictionary of additional parameter:values to be passed when downloading.
      method: HTTP download method whcih is one of 'GET' or 'POST'
      timeout: timeout in seconds.
      retries: Number of retries in case of HTTP errors.
      retry_sec: Interval in seconds between retries for which caller is blocked.
      output_file: filename to save the output.
        if not specified, the filename if picked from the url.
        if set to empty string '', the downloaded content is returned as a string.
      overwrite: If set to False, will not download url if the output_file exists.

    Returns:
      filename if the file is downloaded successfully.
    '''
    if output_file is None:
        # Get output file from the URL after stripping any params.
        url_path = url.split('?', maxsplit=1)[0].split('#', maxsplit=1)[0]
        output_file = url_path[url_path.rfind('/') + 1:]

    if os.path.exists(output_file) and not overwrite:
        logging.debug(
            f'Skipping download {url} for existing file: {output_file}')
        return output_file

    content = request_url(url=url,
                          params=params,
                          method=method,
                          timeout=timeout,
                          retries=retries,
                          retry_secs=retry_secs,
                          output='bytes')

    if content is None:
        logging.error(f'Failed to download {output_file} from {url}, {params}')
        return None

    if not output_file:
        return content

    logging.info(f'Saving {len(content)} bytes from {url} into {output_file}')
    output_dir = os.path.dirname(output_file)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'wb') as fp:
        fp.write(content)

    # Uncompress file if required.
    file_name, file_ext = os.path.splitext(output_file)
    if file_ext == '.gz':
        # uncompress file.
        output_file = file_name
        uncompressed_content = gzip.decompress(content)
        logging.info(
            f'Saving uncompressed {len(uncompressed_content)} bytes from {url} into {output_file}'
        )
        with open(output_file, 'wb') as fp:
            fp.write(uncompressed_content)

    return output_file


def set_test_url_download_response(url: str, params: dict, response: str):
    '''Sets a pre-filled response for tests.
    Args:
      url: string with the URL without parameters.
      params: dictionary of {parameter:value} for the URL request
      response: string to be returned as response for request to this URL.
    '''
    key = _get_prefilled_key(url, params)
    _PREFILLED_RESPONSE[key] = response


def _get_prefilled_key(url: str, params: dict) -> str:
    '''Returns the key for the URL with params.'''
    key = url
    key += '&'.join([f'{p}={params[p]}' for p in sorted(params.keys())])
    return key

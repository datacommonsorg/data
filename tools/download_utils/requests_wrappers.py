# Copyright 2021 Google LLC
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
Wrapper functions for easy use of requests library.
"""

import json
import logging
import requests
import time


def request_url_json(url: str, max_retries: int = 1, retry_interval: int = 10) -> dict:
    """Get JSON object version of reponse to GET request to given URL.
        Handles exception ReadTimeout.
  Args:
    url: URL to make the GET request.

  Returns:
    JSON decoded response from the GET call.
      Empty dict is returned in case the call times out after max_retries.
  """
    logging.info('Requesting url: %s', url)
    try:
        req = requests.get(url)
        if req.status_code == requests.codes.ok:
            response_data = req.json()
        else:
            response_data = {'http_err_code': req.status_code}
            logging.error('HTTP status code: ' + str(req.status_code))
        return response_data
    except requests.exceptions.ReadTimeout:
        if max_retries> 0:
          logging.warning('Timeout occoured, retrying after 10s.')
          time.sleep(10)
          return request_url_json(url, max_retries - 1, retry_interval)
        else:
          return {}


def request_post_json(url: str, data_: dict, max_retries: int = 1, retry_interval: int = 10) -> dict:
    """Get JSON object version of reponse to POST request to given URL.

  Args:
    url: URL to make the POST request.
    data_: payload for the POST request

  Returns:
    JSON decoded response from the POST call.
      Empty dict is returned in case the call fails.
  """
    try:
      headers = {'Content-Type': 'application/json'}
      req = requests.post(url, data=json.dumps(data_), headers=headers)
      logging.info('Post request url: %s', req.request.url)

      if req.status_code == requests.codes.ok:
          response_data = req.json()
      else:
          response_data = {'http_err_code': req.status_code}
          logging.error('Error: HTTP status code: %s', str(req.status_code))
      return response_data
    except requests.exceptions.ReadTimeout:
      if max_retries> 0:
          logging.warning('Timeout occoured, retrying after 10s.')
          time.sleep(10)
          return request_post_json(url, data_, max_retries - 1, retry_interval)
      else:
        return {}

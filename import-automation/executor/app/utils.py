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

import os
import shutil
import re
import datetime

import pytz
import requests


def utctime():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pacific_time():
    return datetime.datetime.now(pytz.timezone('America/Los_Angeles')).isoformat()


def list_to_str(a_list, sep=', '):
    return sep.join(a_list)


def _get_filename(response):
    """Parses the filename of a downloaded file from a requests.Response object.

    The filename is the value associated with the 'filename' key in the
    Content-Disposition header. If the header does not exist, the base name
    of the url is returned.

    Args:
        response: requests.Response object containing the HTTP response for
            the downloaded file.

    Returns:
        The filename of the downloaded file as a string.

    Raises:
        ValueError: The Content-Disposition header exists but 'filename' key
            does not exist.
    """
    header = response.headers.get('Content-Disposition')
    if not header:
        return os.path.basename(response.url)
    name_list = re.findall(r'filename=(.+)', header)
    if not name_list or not name_list[0]:
        raise ValueError('filename not found in Content-Disposition header')
    return name_list[0]


def download_file(url, dest_dir):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        filename = _get_filename(response)
        path = os.path.join(dest_dir, filename)
        with open(path, 'wb') as out:
            shutil.copyfileobj(response.raw, out)
        return path

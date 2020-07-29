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

import time
import os
import shutil
import re
import datetime
from typing import List

import pytz
import requests


def utctime():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def pacific_time():
    return datetime.datetime.now(
        pytz.timezone('America/Los_Angeles')).isoformat()


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


def download_file(url: str, dest_dir: str, timeout: float = None) -> str:
    """Downloads a file from a web URL to a directory.

    Args:
        url: File url as a string.
        dest_dir: Directory to download the file into, as a string.
        timeout: Maximum number of seconds for the file transfer, as a float.
            The actual timeout will be a rough approximation to this, likely
            several seconds longer.

    Returns:
        Path to the downloaded file of the form
        <dest_dir>/<filename of the download file>.

    Raises:
        requests.Timeout: Downloading timed out.
    """
    # 9.05 is the connect timeout and 27 is the read timeout. See
    # https://requests.readthedocs.io/en/master/user/advanced/#timeouts.
    with requests.get(url, stream=True, timeout=(9.05, 27)) as response:
        response.raise_for_status()
        filename = _get_filename(response)
        path = os.path.join(dest_dir, filename)
        with open(path, 'wb') as out:
            start = time.time()
            for data in response.iter_content(chunk_size=4096):
                out.write(data)
                if timeout is not None and time.time() - start > timeout:
                    raise requests.Timeout(f'Downloading {url} timed out')
        return path


def parse_tag_list(message: str, tag: str, allowed_chars: str) -> List[str]:
    """Parses a comma separated list following a tag.

    Example:
        The function call
            parse_tag_list('abc IMPORTS=foo,bar abc', 'IMPORTS', 'a-z')
        returns ['foo', 'bar'].

    Args:
        message: The message containing the list, as a string.
        tag: The tag preceding the list, as a string.
        allowed_chars: Valid characters in an element. This should be in regex
            format, e.g. 'A-Za-z' and 'abc'.

    Returns:
        A list of elements each as a string.
    """
    targets = set()
    pattern = r'(?:{}=)([{},]+)'.format(tag, allowed_chars)
    target_lists = re.findall(pattern, message)
    for target_list in target_lists:
        for target in target_list.split(','):
            targets.add(target)
    return list(targets)

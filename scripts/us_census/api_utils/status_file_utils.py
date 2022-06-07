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
Function library to make manage the status of URL downloads and their storage.
"""

import json
import logging
import os
from shutil import copy2
import base64

_VALID_STATUS = ['pending', 'ok', 'fail', 'fail_http']


def url_to_download(url_dict: dict) -> bool:
    """Check if the URL needs be requested.

        Args:
            url_dict: Dictionary object with URL and relevant metadata.
        
        Returns:
            Boolean value which is set if URL needs to be requested.
    """
    url_fix_status(url_dict)

    if url_dict['status'] == 'pending' or url_dict['status'].startswith(
            'fail') or url_dict['force_fetch']:
        return True
    else:
        return False


def url_fix_status(url_dict):
    if 'status' not in url_dict:
        url_dict['status'] = 'pending'
    if 'force_fetch' not in url_dict:
        url_dict['force_fetch'] = False

    if not url_dict['force_fetch'] and os.path.isfile(url_dict['store_path']):
        url_dict['status'] = 'ok'
    elif not url_dict['status'].startswith('fail'):
        url_dict['status'] = 'pending'


# read status file, reconcile url list
def read_update_status(filename: str,
                       url_list: list,
                       force_fetch_all: bool = False) -> list:
    """Read a status file and sync it with the given url list.
        Sync checks if the file still exists, force fetch, new store path and
            updates the status according to those conditions.
        
        Args:
            filename: Path of the status file.
            url_list: New URL list.
            force_fetch_all: Boolean value to force download of all the URLs.

        Returns:
            List of URL with metadata dict objects.
    """
    filename = os.path.expanduser(filename)

    if filename and os.path.isfile(filename):
        prev_status = json.load(open(filename))
    else:
        prev_status = []
    if force_fetch_all:
        for cur_url in url_list:
            cur_url['force_fetch'] = True
    final_list = sync_status_list(prev_status, url_list)

    # write back to the log file
    json.dump(final_list, open(filename, 'w'), indent=2)
    return final_list


# add urls or sync 2 url list
# TODO optimise the implementation, takes more than 10 hours if both lists are ~600k
def sync_status_list(log_list: list, new_list: list) -> list:
    """Syncs two URL lists to checks if the file still exists, force fetch, new store path and
            update the status according to those conditions.
        
        Args:
            log_list: Existing/base URL list.
            new_list: List of new URLs.
    """
    ret_list = log_list.copy()
    for cur_url in new_list:
        if 'method' not in cur_url:
            cur_url['method'] = 'get'
        # if cur_url['method'].casefold() == 'get' and 'data' in cur_url:
        #     cur_url['url'] = url_add_data(cur_url['url'], cur_url['data'])
        elif 'data' not in cur_url:
            cur_url['data'] = None

        # store_path default value, expand user and abs
        if 'store_path' not in cur_url:
            # add file name
            # TODO make the filename work for post request which would have same URL with different data
            # cur_url['store_path'] = os.path.join(store_path, base64.b64encode(cur_url['url']))
            raise ValueError('Each url must have an associated store_path')
        cur_url['store_path'] = os.path.expanduser(cur_url['store_path'])
        cur_url['store_path'] = os.path.abspath(cur_url['store_path'])
        os.makedirs(os.path.dirname(cur_url['store_path']), exist_ok=True)

        # search in status
        url_found = False
        for i, log_url in enumerate(log_list):
            if not url_found:
                is_same = False
                # same url
                if cur_url['url'] == log_url['url']:
                    # same method
                    if cur_url['method'] == log_url['method']:
                        # same data
                        if 'data' in cur_url and 'data' in log_url:
                            if cur_url['data'] == log_url['data']:
                                is_same = True
                        # no data
                        # TODO check, handle case when data is None
                        elif cur_url['method'].casefold() == 'get':
                            is_same = True
                        elif cur_url['method'].casefold(
                        ) != 'get' and 'data' not in cur_url and 'data' not in log_url:
                            is_same = True

                if is_same:
                    url_found = True
                    # copy the related data
                    if 'http_code' in log_url:
                        cur_url['http_code'] = log_url['http_code']
                    if 'force_fetch' not in cur_url:
                        cur_url['force_fetch'] = False
                    if cur_url['force_fetch']:
                        cur_url['status'] = 'pending'
                        cur_url.pop('http_code', None)
                    else:
                        # check file existence
                        if os.path.isfile(cur_url['store_path']):
                            cur_url['status'] = 'ok'
                        # copy file if store_path is different and status ok
                        elif os.path.isfile(log_url['store_path']
                                           ) and log_url['status'] == 'ok':
                            copy2(log_url['store_path'], cur_url['store_path'])
                            cur_url['status'] = 'ok'
                        elif log_url['status'] == 'fail_http' or log_url[
                                'status'] == 'fail':
                            cur_url['status'] = log_url['status']
                        else:
                            cur_url['status'] = 'pending'
                            cur_url.pop('http_code', None)
                    ret_list[i] = cur_url

        if not url_found:
            # force fetch
            url_fix_status(cur_url)
            cur_url.pop('http_code', None)
            ret_list.append(cur_url)

        if 'status' not in cur_url:
            cur_url['status'] = 'pending'
        if cur_url['status'] not in _VALID_STATUS:
            logging.warning('Warning: Found invalid status for %s',
                            cur_url['url'])
            cur_url['status'] = 'pending'
    return ret_list


# get to be downloaded urls
def get_pending_url_list(url_list: list) -> list:
    """Filters URLs with pending status.

        Args:
            url_list: List of URL with metadata dict object.

        Returns:
            List of URL dict objects that are pending.
    """
    pending_url_list = []
    for cur_url in url_list:
        url_fix_status(cur_url)
        if cur_url['status'] == 'pending':
            pending_url_list.append(cur_url)
    return pending_url_list


def get_failed_url_list(url_list: list) -> list:
    """Filters URLs with failed(any kind) status.

        Args:
            url_list: List of URL with metadata dict object.

        Returns:
            List of URL dict objects that have failed(any kind).
    """
    pending_url_list = []
    for cur_url in url_list:
        url_fix_status(cur_url)
        if cur_url['status'].startswith('fail'):
            pending_url_list.append(cur_url)
    return pending_url_list


def get_failed_http_url_list(url_list: list) -> list:
    """Filters URLs with HTTP failure status.

        Args:
            url_list: List of URL with metadata dict object.

        Returns:
            List of URL dict objects that have HTTP failure.
    """
    pending_url_list = []
    for cur_url in url_list:
        url_fix_status(cur_url)
        if cur_url['status'] == 'fail_http':
            pending_url_list.append(cur_url)
    return pending_url_list


def get_pending_or_fail_url_list(url_list: list) -> list:
    """Filters URLs with pending or failed status.

        Args:
            url_list: List of URL with metadata dict object.

        Returns:
            List of URL dict objects that are pending or failed.
    """
    pending_url_list = []
    for cur_url in url_list:
        url_fix_status(cur_url)
        if cur_url['status'] == 'pending' or cur_url['status'].startswith(
                'fail'):
            pending_url_list.append(cur_url)
    return pending_url_list
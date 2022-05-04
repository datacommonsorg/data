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
Function library to make parallel requests and process the response.
"""

import json
import logging
import os
import time
import asyncio
import aiohttp
from typing import Any, Callable, Union
from aiolimiter import AsyncLimiter

from .status_file_utils import get_pending_or_fail_url_list, url_to_download


async def async_save_resp_json(response: Any, filename: str):
    """Parses and stores json response to a file in async manner.

        Args:
            resp: Response object recieved from aiohttp call.
            store_path: Path of the file to store the result.
    """
    try:
        resp_data = await response.json()
    except asyncio.TimeoutError:
        logging.error('Error: Response parsing timing out.')
        return -1
    logging.debug('Writing downloaded data to file: %s', filename)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as fp:
        json.dump(resp_data, fp, indent=2)
    return 0


def default_url_filter(url_list: list) -> list:
    """Filters out URLs that are to be queried.

        Args:
            url_list: List of URL with metadata dict object.
        
        Returns:
            List of URL with metadata dict object that need to be queried.
    """
    ret_list = []
    for cur_url in url_list:
        if cur_url['status'] == 'pending' or cur_url['status'].startswith(
                'fail'):
            ret_list.append(cur_url)
    return ret_list


def download_url_list_iterations(url_list: list,
                                 url_api_modifier: Callable[[dict], str],
                                 api_key: str,
                                 process_and_store: Callable[[Any, str], int],
                                 url_filter: Union[Callable[[list], list],
                                                   None] = None,
                                 max_itr: int = 3,
                                 rate_params: dict = {}) -> int:
    """Attempt to download a list of URLs in multiple iteration.
        Each iteration attempts to download calls that failed in previous iteration.
        NOTE: An extra iteration might occour to attempt failed calls using requests library rather than parallel calls.

        Args:
            url_list: List of URL with metadata dict object.
            url_api_modifier: Function to attach API key to url.
            api_key: User's API key provided by US Census.
            process_and_store: Function to parse, process and store the response to the passed store path.
            url_filter: Function to filter out URLs that are to be requested.
            max_itr: Maximum number iterations to be performed.
                NOTE: An extra iteration might occour to attempt failed calls using requests library rather than parallel calls.
            rate_params: Dict with parameters to set parallel request rate limits.
        
        Returns:
            Count of url requests that failed.
    """
    loop_ctr = 0
    if not url_filter:
        url_filter = default_url_filter
    logging.info('downloading URLs')

    cur_url_list = url_filter(url_list)
    failed_urls_ctr = len(url_list)
    prev_failed_ctr = failed_urls_ctr + 1
    while failed_urls_ctr > 0 and loop_ctr < max_itr and prev_failed_ctr > failed_urls_ctr:
        prev_failed_ctr = failed_urls_ctr
        logging.info('downloading URLs iteration:%d', loop_ctr)
        download_url_list(cur_url_list, url_api_modifier, api_key,
                          process_and_store, rate_params)
        cur_url_list = url_filter(url_list)
        failed_urls_ctr = len(cur_url_list)
        logging.info('failed request count: %d', failed_urls_ctr)
        loop_ctr += 1
    return failed_urls_ctr


# TODO add back off decorator with aiohttp.ClientConnectionError as the trigger exception,
#      try except might need to change for decorator to work
async def fetch(session: Any, cur_url: dict, semaphore: Any, limiter: Any,
                url_api_modifier: Callable[[dict], str], api_key: str,
                process_and_store: Callable[[Any, str], int]):
    """Fetch a single URL in async fashion.
        NOTE: The function catches all exceptions and marks the status as 'fail'.

        Args:
            session: aiohttp ClientSession object.
            cur_url: URL with metadata dict object.
            semaphore: asyncio Semaphore object.
            limiter: AsyncLimiter object.
            url_api_modifier: Function to attach API key to url.
            api_key: User's API key provided by US Census.
            process_and_store: Function to parse, process and store the response to the passed store path.
    """
    if url_to_download(cur_url):
        logging.debug('%s', cur_url['url'])
        await semaphore.acquire()
        async with limiter:
            final_url = url_api_modifier(cur_url, api_key)
            try:
                # TODO allow other methods like POST
                async with session.get(final_url) as response:
                    http_code = response.status
                    logging.info('%s response code %d', cur_url['url'],
                                 http_code)
                    # TODO allow custom call back function that returns boolean value for success
                    if http_code == 200:
                        logging.debug(
                            'Calling function %s with store path : %s',
                            process_and_store.__name__, cur_url['store_path'])
                        store_ret = await process_and_store(
                            response, cur_url['store_path'])
                        if store_ret < 0:
                            cur_url['status'] = 'fail'
                        else:
                            cur_url['status'] = 'ok'
                        cur_url['http_code'] = str(http_code)
                    else:
                        cur_url['status'] = 'fail_http'
                        cur_url['http_code'] = str(http_code)
                        logging.error("Error: HTTP status code: %s",
                                      str(http_code))
                    semaphore.release()
                    # return response
            except Exception as e:
                cur_url['status'] = 'fail'
                cur_url.pop('http_code', None)
                logging.error('%s failed fetch with exception %s',
                              cur_url['url'],
                              type(e).__name__)


# async download
async def async_download_url_list(url_list: list,
                                  url_api_modifier: Callable[[dict],
                                                             str], api_key: str,
                                  process_and_store: Callable[[Any, str], int],
                                  rate_params: dict):
    """Creates async ClientSession and relevent objects for rate limiting.
        Initiate request for each URL, and wait for them to complete.

        Args:
            url_list: List of URL with metadata dict object.
            url_api_modifier: Function to attach API key to url.
            api_key: User's API key provided by US Census.
            process_and_store: Function to parse, process and store the response to the passed store path.
            rate_params: Dict with parameters to set parallel request rate limits.
    """
    # create semaphore
    semaphore = asyncio.Semaphore(rate_params['max_parallel_req'])
    # limiter
    limiter = AsyncLimiter(rate_params['req_per_unit_time'],
                           rate_params['unit_time'])
    # create session
    conn = aiohttp.TCPConnector(limit_per_host=rate_params['limit_per_host'])
    timeout = aiohttp.ClientTimeout(total=3600)
    async with aiohttp.ClientSession(connector=conn,
                                     timeout=timeout) as session:
        # loop over each url
        fut_list = []
        for cur_url in url_list:
            fut_list.append(
                fetch(session, cur_url, semaphore, limiter, url_api_modifier,
                      api_key, process_and_store))
        responses = asyncio.gather(*fut_list)
        # TODO update download_status file at regular intervals if feasible
        await responses


def download_url_list(url_list: list, url_api_modifier: Callable[[dict], str],
                      api_key: str, process_and_store: Callable[[Any, str],
                                                                int],
                      rate_params: dict):
    """Synchronous wrapper to the function for making asynchrous calls.

        Args:
            url_list: List of URL with metadata dict object.
            url_api_modifier: Function to attach API key to url.
            api_key: User's API key provided by US Census.
            process_and_store: Function to parse, process and store the response to the passed store path.
            rate_params: Dict with parameters to set parallel request rate limits.
        
        Returns:
            Count of URL requests that failed.
    """
    logging.debug('Downloading url list of size %d', len(url_list))

    if not url_api_modifier:
        url_api_modifier = lambda u, a: u['url']

    if 'max_parallel_req' not in rate_params:
        rate_params['max_parallel_req'] = 500
    if 'limit_per_host' not in rate_params:
        rate_params['limit_per_host'] = 0
    if 'req_per_unit_time' not in rate_params:
        rate_params['req_per_unit_time'] = 50
    # time in sec, rate would be limited to req_per_unit_time requests per unit_time
    if 'unit_time' not in rate_params:
        rate_params['unit_time'] = 1

    start_t = time.time()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        async_download_url_list(url_list, url_api_modifier, api_key,
                                process_and_store, rate_params))
    loop.run_until_complete(future)
    end_t = time.time()
    logging.info("The time required to download %d URLs : %d", len(url_list),
                 (end_t - start_t))

    return len(get_pending_or_fail_url_list(url_list))
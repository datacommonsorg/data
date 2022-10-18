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
'''Wrapper utilities for data commons API.'''

import sys
import os
import datacommons as dc
import requests_cache
import time
import urllib

from absl import logging
from collections import OrderedDict

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from mcf_file_util import add_namespace, strip_namespace

def dc_api_wrapper(function,
                   args: dict,
                   retries: int = 3,
                   retry_secs: int = 5,
                   use_cache: bool = False,
                   api_root: str = None):
    '''Wrapper for a DC APi call with retries and caching.
    Returns the result from the DC APi call function.
    In case of errors, retries the function with a delay a fixed number of times.

    Args:
      function: The DataCommons API function.
      args: dictionary with any the keyword arguments for the DataCommons API function.
      retries: Number of retries in case of HTTP errors.
      retry_sec: Interval in seconds between retries for which caller is blocked.
      use_cache: If True, uses request cache for faster response.
      api_root: The API server to use. Default is 'http://api.datacommons.org'.
         To use autopush with more recent data, set it to 'http://autopush.api.datacommons.org'

    Returns:
      The response from the DataCommons API call.
    '''
    if api_root:
        dc.utils._API_ROOT = api_root
        logging.debug(f'Setting DC API root to {api_root} for {function}')
    if not retries or retries <= 0:
        retries = 1
    # Setup request cache
    if not requests_cache.is_installed():
        requests_cache.install_cache(expires_after=300)
    cache_context = None
    if use_cache:
        cache_context = requests_cache.enabled()
        logging.debug(f'Using requests_cache for DC API {function}')
    else:
        cache_context = requests_cache.disabled()
        logging.debug(f'Using requests_cache for DC API {function}')
    with cache_context:
        for attempt in range(retries):
            try:
                logging.debug(
                    f'Invoking DC API {function}, #{attempt} with {args}, retries={retries}'
                )
                response = function(**args)
                logging.debug(f'Got API response {response} for {function}, {args}')
                return response
            except KeyError:
                # Exception in case of API error.
                return None
            except urllib.error.URLError:
                # Exception when server is overloaded, retry after a delay
                if attempt >= retries:
                    raise urllib.error.URLError
                else:
                    logging.debug(
                        f'Retrying API {function} after {retry_secs}...')
                    time.sleep(retry_secs)
    return None


def dc_api_batched_wrapper(function, dcids: list, args: dict,
                           config: dict = None) -> dict:
    '''A wrapper for DC API on dcids with batching support.
    Returns the dictionary result for the function call across all arguments.
  It batches the dcids to make multiple calls to the DC API and merges all results.

  Args:
    function: DC API to be invoked. It should have dcids as one of the arguments
      and should return a dictionary with dcid as the key.
    dcids: List of dcids to be invoked with the function.
        The namespace is stripped from the dcid before the call to the DC API.
    args: Additional arguments for the function call.
    config: dictionary of DC API configuration settings.
      The supported settings are:
        dc_api_batch_size: Number of dcids to invoke per API call.
        dc_api_retries: Number of times an API can be retried.
        dc_api_retry_sec: Interval in seconds between retries.
        dc_api_use_cache: Enable/disable request cache for the DC API call.
        dc_api_root: The server to use for the DC API calls.

  Returns:
    Merged function return values across all dcids.
  '''
    if not config:
      config = {}
    api_result = {}
    index = 0
    num_dcids = len(dcids)
    api_batch_size = config.get('dc_api_batch_size', 10)
    logging.info(
        f'Calling DC API {function} on {len(dcids)} dcids in batches of {api_batch_size} with args: {args}...'
    )
    while index < num_dcids:
        #  dcids in batches.
        dcids_batch = [
            strip_namespace(x) for x in dcids[index:index + api_batch_size]
        ]
        index += api_batch_size
        args['dcids'] = dcids_batch
        batch_result = dc_api_wrapper(function, args,
                                      config.get('dc_api_retries', 3),
                                      config.get('dc_api_retry_secs', 5),
                                      config.get('dc_api_use_cache', False),
                                      config.get('dc_api_root', None))
        if batch_result:
            api_result.update(batch_result)
            logging.debug(f'Got DC API result for {function}: {batch_result}')
    logging.debug(f'Returning response {api_result} for {function}, {dcids}, {args}')
    return api_result


def dc_api_is_defined_dcid(dcids: list, wrapper_config: dict = None) -> dict:
    '''Returns a dicttionary with dcids mapped to True/False based on whether
    the dcid is defined in the API and has a 'typeOf' property.
       Uses the property_value() DC API to lookup 'typeOf' for each dcid.
       dcids not defined in KG get a value of False.
    Args:
      dcids: List of dcids. The namespace is stripped from the dcid.
      wrapper_config: dictionary of configurationparameters for the wrapper.
         See dc_api_batched_wrapper and dc_api_wrapper for details.
    Returns:
      dictionary with each input dcid mapped to a True/False value.
    '''
    api_function = dc.get_property_values
    args = {
        'prop': 'typeOf',
        'out': True,
    }
    api_result = dc_api_batched_wrapper(api_function, dcids, args, wrapper_config)
    response = {}
    for dcid in dcids:
        dcid_stripped = strip_namespace(dcid)
        if dcid_stripped in api_result and api_result[dcid_stripped]:
            response[dcid] = True
        else:
            response[dcid] = False
    return response


def dc_api_get_node_property_values(dcids: list, wrapper_config: dict = None) -> dict:
    '''Returns all the property values for a set of dcids from the DC API.
    Args:
      dcids: list of dcids to lookup
      wrapper_config: configuration parameters for the wrapper.
         See dc_api_batched_wrapper() and dc_api_wrapper() for details.
    Returns:
      dictionary with each dcid with the namspace 'dcid:' as the key
      mapped to a dictionary of property:value.
    '''
    predefined_nodes = OrderedDict()
    api_function = dc.get_triples
    api_triples = dc_api_batched_wrapper(api_function, dcids, {}, wrapper_config)
    if api_triples:
        for dcid, triples in api_triples.items():
            pvs = {}
            for d, prop, val in triples:
                pvs[prop] = val
            if len(pvs) > 0:
                if 'Node' not in pvs:
                    pvs['Node'] = add_namespace(dcid)
                predefined_nodes[add_namespace(dcid)] = pvs
    return predefined_nodes

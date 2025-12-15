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
"""Wrapper utilities for data commons API.

It uses the DataCommonsClient library module for V2 DC APIs by default
and adds support for batched requests, retries and HTTP caching.
DC V2 API requires an environment variable set for DC_API_KEY.
Please refer to https://docs.datacommons.org/api/python/v2
for more details.

To use the legacy datacommons library module, set the config:
  'dc_api_version': 'V1'
"""

from collections import OrderedDict
import os
import sys
import time
import urllib
import requests
import threading

from absl import logging
from datacommons_client.client import DataCommonsClient
from datacommons_client.utils.error_handling import DCConnectionError, DCStatusError, APIError
import datacommons as dc
import requests_cache

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)

from download_util import request_url

# Path for reconciliation API in the dc.utils._API_ROOT
# For more details, please refer to:
# https://github.com/datacommonsorg/reconciliation#usage
# Resolve Id
# https://api.datacommons.org/v1/recon/resolve/id
_DC_API_PATH_RESOLVE_ID = '/v1/recon/resolve/id'
# Resolve latlng coordinate
# https://api.datacommons.org/v2/resolve
_DC_API_PATH_RESOLVE_COORD = '/v2/resolve'
# Default API key for limited tests
_DEFAULT_DC_API_KEY = 'AIzaSyCTI4Xz-UW_G2Q2RfknhcfdAnTHq5X5XuI'

_API_ROOT_LOCK = threading.Lock()
_DEFAULT_API_ROOT = 'https://api.datacommons.org'


def dc_api_wrapper(
    function,
    args: dict,
    retries: int = 3,
    retry_secs: int = 1,
    use_cache: bool = False,
    api_root: str = None,
):
    """Wrapper for a DC API call with retries and caching.

  Returns the result from the DC APi call function. In case of errors, retries
  the function with a delay a fixed number of times.

  Args:
    function: The DataCommons API function.
    args: dictionary with any the keyword arguments for the DataCommons API
      function.
    retries: Number of retries in case of HTTP errors.
    retry_sec: Interval in seconds between retries for which caller is blocked.
    use_cache: If True, uses request cache for faster response.
    api_root: The API server to use. Default is 'http://api.datacommons.org'. To
      use autopush with more recent data, set it to
      'http://autopush.api.datacommons.org'

  Returns:
    The response from the DataCommons API call.
  """
    if not retries or retries <= 0:
        retries = 1
    # Setup request cache
    if not requests_cache.is_installed():
        requests_cache.install_cache(expires_after=3600)
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
                    f'Invoking DC API {function}, #{attempt} with {args},'
                    f' retries={retries}')

                response = None
                if api_root:
                    # All calls serialize here to prevent races while updating the
                    # global Data Commons API root.
                    with _API_ROOT_LOCK:
                        original_api_root = dc.utils._API_ROOT
                        if api_root:
                            dc.utils._API_ROOT = api_root
                            logging.debug(
                                f'Setting DC API root to {api_root} for {function}'
                            )
                        try:
                            response = function(**args)
                        finally:
                            dc.utils._API_ROOT = original_api_root
                else:
                    response = function(**args)

                logging.debug(
                    f'Got API response {response} for {function}, {args}')
                return response
            except KeyError as e:
                # Exception in case of missing dcid. Don't retry.
                logging.error(f'Got exception for api: {function}, {e}')
                return None
            except (DCConnectionError, requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                # Retry network errors
                if _should_retry_status_code(None, attempt, retries):
                    logging.debug(
                        f'Got exception {e}, retrying API {function} after'
                        f' {retry_secs}...')
                    time.sleep(retry_secs)
                else:
                    logging.error(
                        f'Got exception for api: {function}, {e}, no more retries'
                    )
                    raise e
            except (urllib.error.HTTPError, DCStatusError, APIError) as e:
                # Retry 5xx and 429, but not other 4xx
                status_code = getattr(e, 'code', None) or getattr(
                    e, 'status_code', None)
                if _should_retry_status_code(status_code, attempt, retries):
                    logging.debug(
                        f'Got exception {e}, retrying API {function} after'
                        f' {retry_secs}...')
                    time.sleep(retry_secs)
                else:
                    # Don't retry other errors (e.g. 400, 404, 401)
                    logging.error(f'Got exception for api: {function}, {e}')
                    raise e
    return None


def _should_retry_status_code(status_code: int, attempt: int,
                              max_retries: int) -> bool:
    """Returns True if the request should be retried.
    Request can be retried for HTTP status codes like 429 or 5xx
    if the number of attempts is less than max_retries."""
    if status_code:
        if (status_code != 429 and status_code < 500):
            # Do no retry for error codes like 401
            logging.error(f'Got status: {status_code}, not retrying.')
            return False
    if attempt >= max_retries:
        logging.error(
            f'Got status: {status_code} after {attempt} retries, not retrying.')
        return False
    return True


def dc_api_batched_wrapper(
    function,
    dcids: list,
    args: dict,
    dcid_arg_kw: str = 'dcids',
    headers: dict = {},
    config: dict = None,
) -> dict:
    """A wrapper for DC API on dcids with batching support.

    Returns the dictionary result for the function call across all arguments.
  It batches the dcids to make multiple calls to the DC API and merges all
  results.

  Args:
    function: DC API to be invoked. It should have dcids as one of the arguments
      and should return a dictionary with dcid as the key.
    dcids: List of dcids to be invoked with the function. The namespace is
      stripped from the dcid before the call to the DC API.
    args: Additional arguments for the function call.
    config: dictionary of DC API configuration settings. The supported settings
      are:
        dc_api_batch_size: Number of dcids to invoke per API call.
        dc_api_retries: Number of times an API can be retried.
        dc_api_retry_sec: Interval in seconds between retries.
        dc_api_use_cache: Enable/disable request cache for the DC API call.
        dc_api_root: The server to use for the DC API calls.

  Returns:
    Merged function return values across all dcids.
  """
    if not config:
        config = {}
    api_result = {}
    index = 0
    num_dcids = len(dcids)
    dc_api_root = config.get('dc_api_root', None)
    if config.get('dc_api_version', 'V2') == 'V2':
        # V2 API assumes api root is set in the function's client
        dc_api_root = None
    api_batch_size = config.get('dc_api_batch_size', dc.utils._MAX_LIMIT)
    logging.debug(
        f'Calling DC API {function} on {len(dcids)} dcids in batches of'
        f' {api_batch_size} with args: {args}...')
    while index < num_dcids:
        #  dcids in batches.
        dcids_batch = [
            _strip_namespace(x) for x in dcids[index:index + api_batch_size]
        ]
        index += api_batch_size
        args[dcid_arg_kw] = dcids_batch
        batch_result = dc_api_wrapper(
            function,
            args,
            config.get('dc_api_retries', 3),
            config.get('dc_api_retry_secs', 5),
            config.get('dc_api_use_cache', False),
            dc_api_root,
        )
        if batch_result:
            dc_api_merge_results(api_result, batch_result)
            logging.debug(f'Got DC API result for {function}: {batch_result}')
    logging.debug(
        f'Returning response {api_result} for {function}, {dcids}, {args}')
    return api_result


def dc_api_merge_results(results: dict, new_result: dict) -> dict:
    """Returns the merged dictionary with new_result added into results."""
    if results is None:
        results = {}
    if not new_result:
        return results
    if not isinstance(new_result, dict):
        # This is a V2 response. Extract the dict.
        new_result = new_result.to_dict()
        if 'data' in new_result:
            new_result = new_result['data']
    # Update new_result into results if keys are different.
    for key, value in new_result.items():
        old_value = results.get(key)
        if not old_value:
            # New key, add it.
            results[key] = value
        else:
            if isinstance(old_value, dict) and isinstance(value, dict):
                # Merge the nested dicts.
                dc_api_merge_results(old_value, value)
            elif isinstance(old_value, list) and isinstance(value, list):
                # Append new list
                old_value.extend(value)
            else:
                # Replace with new value
                old_value = value
            results[key] = old_value

    return results


def get_datacommons_client(config: dict = None) -> DataCommonsClient:
    """Returns a DataCommonsClient object initialized using config."""
    if config is None:
        config = {}
    api_key = config.get('dc_api_key', os.environ.get('DC_API_KEY'))
    if not api_key:
        logging.log_first_n(
            logging.WARNING, f'Using default DC API key with limited quota. '
            'Please set an API key in the environment variable: DC_API_KEY.'
            'Refer https://docs.datacommons.org/api/python/v2/#authentication '
            'for more details.',
            n=1)
        api_key = _DEFAULT_DC_API_KEY
    dc_instance = config.get('dc_api_root')
    url = None
    # Check if API root is a host or url endpoint.
    if dc_instance:
        if dc_instance.startswith('http'):
            parsed_url = urllib.parse.urlparse(dc_instance)
            if parsed_url and parsed_url.path and parsed_url.path != '/':
                # API endpoint is a URL.
                url = dc_instance
                dc_instance = None
            else:
                # DataCommonsClient uses custom DC path /core/api/v2
                # with dc_instance.
                # Set the URL to v2 prod endpoint.
                url = urllib.parse.urljoin(dc_instance, 'v2')
                dc_instance = None
    return DataCommonsClient(api_key=api_key, dc_instance=dc_instance, url=url)


def dc_api_is_defined_dcid(dcids: list, config: dict = {}) -> dict:
    """Returns a dictionary with dcids mapped to True/False based on whether
  the dcid is defined in the API and has a 'typeOf' property.
     Uses the property_value() DC API to lookup 'typeOf' for each dcid.
     dcids not defined in KG get a value of False.
  Args:
    dcids: List of dcids. The namespace is stripped from the dcid.
    config: dictionary of configurationparameters for the wrapper. See
      dc_api_batched_wrapper and dc_api_wrapper for details.

  Returns:
    dictionary with each input dcid mapped to a True/False value.
  """
    # Set parameters for V2 node API.
    client = get_datacommons_client(config)
    api_function = client.node.fetch_property_values
    args = {'properties': 'typeOf'}
    dcid_arg_kw = 'node_dcids'
    if config.get('dc_api_version', 'V2') != 'V2':
        # Set parameters for V1 API.
        api_function = dc.get_property_values
        args = {
            'prop': 'typeOf',
            'out': True,
        }
        dcid_arg_kw = 'dcids'

    api_result = dc_api_batched_wrapper(function=api_function,
                                        dcids=dcids,
                                        args=args,
                                        dcid_arg_kw=dcid_arg_kw,
                                        config=config)
    response = {}
    for dcid in dcids:
        dcid_stripped = _strip_namespace(dcid)
        if dcid_stripped in api_result and api_result[dcid_stripped]:
            response[dcid] = True
        else:
            response[dcid] = False
    return response


def dc_api_get_node_property(dcids: list, prop: str, config: dict = {}) -> dict:
    """Returns a dictionary keyed by dcid with { prop:value } for each dcid.

     Uses the get_property_values() DC API to lookup the property for each dcid.

  Args:
    dcids: List of dcids. The namespace is stripped from the dcid.
    config: dictionary of configurationparameters for the wrapper. See
      dc_api_batched_wrapper and dc_api_wrapper for details.

  Returns:
    dictionary with each input dcid mapped to a True/False value.
  """
    is_v2 = config.get('dc_api_version', 'V2') == 'V2'
    # Set parameters for V2 node API.
    client = get_datacommons_client(config)
    api_function = client.node.fetch_property_values
    args = {'properties': prop}
    dcid_arg_kw = 'node_dcids'
    if not is_v2:
        # Set parameters for V1 API.
        api_function = dc.get_property_values
        args = {
            'prop': prop,
            'out': True,
        }
        dcid_arg_kw = 'dcids'
    api_result = dc_api_batched_wrapper(function=api_function,
                                        dcids=dcids,
                                        args=args,
                                        dcid_arg_kw=dcid_arg_kw,
                                        config=config)
    response = {}
    for dcid in dcids:
        dcid_stripped = _strip_namespace(dcid)
        node_data = api_result.get(dcid_stripped)
        if not node_data:
            continue

        if is_v2:
            values = []
            arcs = node_data.get('arcs', {})
            prop_nodes = arcs.get(prop, {}).get('nodes', [])
            for node in prop_nodes:
                val_dcid = node.get('dcid')
                if val_dcid:
                    values.append(val_dcid)
                value = node.get('value')
                if value:
                    value = '"' + value + '"'
                    values.append(value)
            if values:
                response[dcid] = {prop: ','.join(values)}
        else:  # V1
            if node_data:
                response[dcid] = {prop: node_data}
    return response


def dc_api_get_node_property_values(dcids: list, config: dict = {}) -> dict:
    """Returns all the property values for a set of dcids from the DC API.

  Args:
    dcids: list of dcids to lookup
    config: configuration parameters for the wrapper. See
      dc_api_batched_wrapper() and dc_api_wrapper() for details.

  Returns:
    dictionary with each dcid with the namspace 'dcid:' as the key
    mapped to a dictionary of property:value.
  """
    if config.get('dc_api_version', 'V2') != 'V2':
        return dc_api_v1_get_node_property_values(dcids, config)
    # Lookup node properties using V2 node API
    client = get_datacommons_client(config)
    api_function = client.node.fetch
    args = {'expression': '->*'}
    dcid_arg_kw = 'node_dcids'
    api_result = dc_api_batched_wrapper(function=api_function,
                                        dcids=dcids,
                                        args=args,
                                        dcid_arg_kw=dcid_arg_kw,
                                        config=config)
    response = {}
    for dcid, arcs in api_result.items():
        pvs = {}
        for prop, node_values in arcs.get('arcs', {}).items():
            for node in node_values.get('nodes', []):
                # Get property value as reference to another node
                value = node.get('dcid')
                if not value:
                    # Property value is a string.
                    value = node.get('value')
                    if value:
                        value = '"' + value + '"'
                if value:
                    if prop in pvs:
                        value = pvs[prop] + ',' + value
                    pvs[prop] = value
            if len(pvs) > 0:
                if 'Node' not in pvs:
                    pvs['Node'] = _add_namespace(dcid)
                response[_add_namespace(dcid)] = pvs
    return response


def dc_api_v1_get_node_property_values(dcids: list, config: dict = {}) -> dict:
    """Returns all the property values for a set of dcids from the DC V1 API.

  Args:
    dcids: list of dcids to lookup
    config: configuration parameters for the wrapper. See
      dc_api_batched_wrapper() and dc_api_wrapper() for details.

  Returns:
    dictionary with each dcid with the namspace 'dcid:' as the key
    mapped to a dictionary of property:value.
  """
    predefined_nodes = OrderedDict()
    api_function = dc.get_triples
    api_triples = dc_api_batched_wrapper(api_function, dcids, {}, config=config)
    if api_triples:
        for dcid, triples in api_triples.items():
            if (_strip_namespace(dcid) not in dcids and
                    _add_namespace(dcid) not in dcids):
                continue
            pvs = {}
            for d, prop, val in triples:
                if d == dcid and val:
                    # quote string values with spaces if needed
                    if ' ' in val and val[0] != '"':
                        val = '"' + val + '"'
                    if prop in pvs:
                        val = pvs[prop] + ',' + val
                    pvs[prop] = val
            if len(pvs) > 0:
                if 'Node' not in pvs:
                    pvs['Node'] = _add_namespace(dcid)
                predefined_nodes[_add_namespace(dcid)] = pvs
    return predefined_nodes


def dc_api_resolve_placeid(dcids: list,
                           in_prop: str = 'placeId',
                           *,
                           config: dict = {}) -> dict:
    """Returns the resolved dcid for each of the placeid.

  Args:
    dcids: list of placeids to be resolved.
    in_prop: The property of the input IDs.
    config: optional dictionary with DC API settings (uses 'dc_api_root' when
      provided).

  Returns:
    dictionary keyed by input placeid with reoslved dcid as value.
  """
    if not config:
        config = {}
    if config.get('dc_api_version', 'V2') == 'V2':
        client = get_datacommons_client(config)
        api_function = client.resolve.fetch
        args = {'expression': f'<-{in_prop}->dcid'}
        dcid_arg_kw = 'node_ids'
        api_result = dc_api_batched_wrapper(function=api_function,
                                            dcids=dcids,
                                            args=args,
                                            dcid_arg_kw=dcid_arg_kw,
                                            config=config)
        results = {}
        if api_result:
            for node in api_result.get('entities', []):
                place_id = node.get('node')
                if place_id:
                    candidates = node.get('candidates', [])
                    if candidates:
                        dcid = candidates[0].get('dcid')
                        if dcid:
                            results[place_id] = dcid
        return results

    # V1 implementation
    api_root = config.get('dc_api_root', _DEFAULT_API_ROOT)
    data = {'in_prop': in_prop, 'out_prop': 'dcid'}
    data['ids'] = dcids
    num_ids = len(dcids)
    api_url = api_root + _DC_API_PATH_RESOLVE_ID
    logging.debug(
        f'Looking up {api_url} dcids for {num_ids} placeids: {data["ids"]}')
    recon_resp = request_url(url=api_url,
                             params=data,
                             method='POST',
                             output='json')
    # Extract the dcid for each place from the response
    results = {}
    if recon_resp:
        for entity in recon_resp.get('entities', []):
            place_id = entity.get('inId', '')
            out_dcids = entity.get('outIds', None)
            if place_id and out_dcids:
                results[place_id] = out_dcids[0]
    return results


def dc_api_resolve_latlng(lat_lngs: list,
                          *,
                          return_v1_response: bool = False,
                          config: dict = None) -> dict:
    """Resolves geographic coordinates to Data Commons places.

    Each object in the list is of the form:

    {
        'latitude': lat,
        'longitude': lng,
    }

    if return_v1_response is True, a v1 response of this form is returned:
    
    {
      "placeCoordinates": [
          {
              "latitude": 37.42,
              "longitude": -122.08,
              "placeDcids": [
                  "geoId/0649670"
              ],
              "places": [
                  {
                      "dcid": "geoId/0649670",
                      "dominantType": "City"
                  }
              ]
          }
      ]
    }

    Otherwise, it returns a response of this form:

    {
        "37.42-122.08": {
            "latitude": 37.42,
            "longitude": -122.08,
            "placeDcids": ["geoId/0649670"],
            "places": [{
                "dcid": "geoId/0649670",
                "dominantType": "City"
            }]
        }
    }

  Args:
    latlngs: list of latlngs to be resolved.
    config: optional dictionary with DC API settings (uses 'dc_api_root' when
      provided).

  Returns:
    dictionary containing the resolved place information.
  """
    if not config:
        config = {}
    api_root = config.get('dc_api_root', _DEFAULT_API_ROOT)
    v1_data = {}
    v1_data['coordinates'] = lat_lngs
    num_ids = len(lat_lngs)
    api_url = api_root + _DC_API_PATH_RESOLVE_COORD
    logging.debug(
        f'Looking up {api_url} coordinates for {num_ids} placeids: {v1_data}')
    v2_data = _convert_v1_to_v2_coordinate_request(v1_data)
    v2_resp = request_url(url=api_url,
                          params=v2_data,
                          method='POST',
                          output='json')
    # Extract the dcids for each place from the response
    results = {}
    if v2_resp:
        v1_resp = _convert_v2_to_v1_coordinate_response(v2_resp)

        if return_v1_response:
            return v1_resp

        for entity in v1_resp.get('placeCoordinates', []):
            latlngs = entity.get('placeDcids', '')
            lat = entity.get('latitude', '')
            lng = entity.get('longitude', '')
            place_id = f'{lat}{lng}'
            if place_id and latlngs:
                results[place_id] = entity
    return results


def _convert_v2_to_v1_coordinate_response(v2_response: dict) -> dict:
    """Converts a v2 coordinate resolution response to a v1 response.
    """
    v1_response = {'placeCoordinates': []}
    for entity in v2_response.get('entities', []):
        node = entity.get('node', '')
        if '#' not in node:
            continue
        lat_str, lng_str = node.split('#')
        try:
            lat = float(lat_str)
            lng = float(lng_str)
        except ValueError:
            continue

        place_coordinate = {
            'latitude': lat,
            'longitude': lng,
            'placeDcids': [
                candidate.get('dcid')
                for candidate in entity.get('candidates', [])
            ],
            'places': entity.get('candidates', [])
        }
        v1_response['placeCoordinates'].append(place_coordinate)
    return v1_response


def _convert_v1_to_v2_coordinate_request(v1_request: dict) -> dict:
    """Converts a v1 coordinate resolution request to a v2 request.
    """
    v2_request = {'nodes': [], 'property': '<-geoCoordinate->dcid'}
    for coordinate in v1_request.get('coordinates', []):
        lat = coordinate.get('latitude')
        lng = coordinate.get('longitude')
        if lat is not None and lng is not None:
            v2_request['nodes'].append(f'{lat}#{lng}')
    return v2_request


def _add_namespace(value: str, namespace: str = 'dcid') -> str:
    """Returns the value with a namespace prefix for references.

  Args:
    value: string to which namespace is to be added.

  Returns:
    value with the namespace prefix if the value is not a quoted string
    and doesn't have a namespace already.
    O/w return the value as is.

  Any sequence of letters followed by a ':' is treated as a namespace.
  Quoted strings are assumed to start with '"' and won't get a namespace.
  """
    if value and isinstance(value, str):
        if value[0].isalpha() and value.find(':') < 0:
            return f'{namespace}:{value}'
    return value


def _strip_namespace(value: str) -> str:
    """Returns the value without the namespace prefix.

  Args:
    value: string from which the namespace prefix is to be removed.

  Returns:
    value without the namespace prefix if there was a namespace

  Any sequence of letters followed by a ':' is treated as a namespace.
  Quoted strings are assumed to start with '"' and won't be filtered.
  """
    if value and isinstance(value, str) and value[0].isalnum():
        return value[value.find(':') + 1:].strip()
    return value

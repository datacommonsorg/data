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
''' Utility function to filter MCF nodes.'''

from collections import OrderedDict
from itertools import islice

import datacommons as dc
import logging
import os
import requests_cache
import sys
import time
import urllib

from absl import app
from absl import flags

_FLAGS = flags.FLAGS

flags.DEFINE_string('input_mcf', '',
                    'Comma seperated list of MCF input files with nodes')
flags.DEFINE_string(
    'ignore_mcf', '',
    'Comma separated list of MCF files with nodes to be dropped from output')
flags.DEFINE_string('output_mcf', '', 'MCF output file with nodes')

# Allows the following module imports to work when running as a script
# relative to data/scripts/
#sys.path.append(os.path.sep.join([
#     '..' for x in filter(lambda x: x == os.path.sep,
#                              os.path.abspath(__file__).split('scripts/')[1])
#                              ]))

from mcf_file_util import load_mcf_nodes, add_namespace, strip_namespace, write_mcf_nodes
from mcf_diff import diff_mcf_node_pvs, add_counter, print_counters, get_diff_config


def dc_api_wrapper(function,
                   args: dict,
                   retries: int = 3,
                   retry_secs: int = 5,
                   use_cache: bool = False,
                   api_root: str = None):
    '''Returns the result from the DC APi call function.
    Retries the function in case of errors.

    Args:
      function: The DataCOmmons API function.
      args: dictionary with ann the arguments fr the DataCommons APi function.
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
        for attempt in range(0, retries):
            try:
                logging.debug(
                    f'Invoking DC API {function} with {args}, retries={retries}'
                )
                return function(**args)
            except KeyError:
                # Exception in case of API error.
                return None
            except urllib.error.URLError:
                # Exception when server is overloaded, retry after a delay
                if attempt >= retries:
                    raise RuntimeError
                else:
                    logging.debug(
                        f'Retrying API {function} after {retry_secs}...')
                    time.sleep(retry_secs)
    return None


def dc_api_batched_wrapper(function, dcids: list, args: dict,
                           config: dict) -> dict:
    '''Returns the dictionary result for the function cal on all APIs.
  It batches the dcids to make multiple calls to the DC API and merges all results.

  Args:
    function: DC API to be invoked. It should have dcids as one of the arguments
      and should return a dictionary with dcid as the key.
    dcids: List of dcids to be invoked with the function.
    args: Additional arguments for the function call.
    config: dictionary of DC API configuration settings.
      The supported settings are:
        dc_api_batch_size: Number of dcids to invoke per API call.
        dc_api_retries: Number of times an API can be retried.
        dc_api_retry_sec: Interval in seconds between retries.
        dc_api_use_cache: Enable/disable request cache for the DC API call.
        dc_api_root: The server to use fr the DC API calls.

  Returns:
    Merged function return values across all dcids.
  '''
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
    return api_result


def dc_api_get_defined_dcids(dcids: list, config: dict) -> dict:
    '''Returns a dict with dcids mapped to list of types in the DataCommons KG.
       Uses the property_value API to lookup 'typeOf' for each dcid.
       dcids not defined in KG are dropped in the response.
    '''
    api_function = dc.get_property_values
    args = {
        'prop': 'typeOf',
        'out': True,
    }
    api_result = dc_api_batched_wrapper(api_function, dcids, args, config)
    response = {}
    # Remove empty results for dcids not defined in KG.
    for dcid in dcids:
      if dcid in api_result and api_result[dcid]:
        response[dcid] = True
      else:
        response[dcid] = False
    return response


def get_node_pvs_from_api(dcids: list, max_retries: int = 3) -> dict:
    '''Returns dictionary of PVs if the dcid is defined in DC.
       It invokes the get_triples API.

       Note: It is more efficient to query API for a set of dcids
       rather than one at a time.
    '''
    try:
        # Fetch one property for the dcid
        # Can also use other APIs like dc.get_property_labels(dcids, out=True)
        logging.debug(f'Looking up API for {dcids}...')
        return dc.get_triples(dcids)
    except KeyError:
        # Generated when dcid is not in the response, indicating it is not defined
        return None
    except urllib.error.URLError:
        # Generated when server is overloaded, retry after a delay
        if max_retries <= 0:
            raise RuntimeError
        else:
            time.sleep(5)
            logging.debug(f'Retrying API for {dcids}...')
            return get_node_pvs_from_api(dcids, max_retries - 1)
    return None


def get_nodes_from_api(lookup_dcids: list, config: dict) -> dict:
    '''Lookup PVs for dcids from the DataCommons API.'''
    predefined_nodes = OrderedDict()
    index = 0
    num_dcids = len(lookup_dcids)
    api_batch_size = config.get('dc_api_batch_size', 10)
    logging.info(
        f'Looking up {len(lookup_dcids)} dcids from API in batches of {api_batch_size}...'
    )
    while index < num_dcids:
        # Lookup dcids in batches.
        dcids = [
            strip_namespace(x)
            for x in lookup_dcids[index:index + api_batch_size]
        ]
        index += api_batch_size
        api_triples = get_node_pvs_from_api(dcids)
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


def filter_mcf_nodes(input_nodes: dict,
                     ignore_nodes: dict,
                     config: dict,
                     counters: dict = {}) -> dict:
    '''Function to filter MCF nodes removing any nodes in ignore_nodes.'''
    output_nodes = OrderedDict()
    logging.info(
        f'Filtering {len(input_nodes)} nodes with {len(ignore_nodes)} ignored nodes'
    )
    for dcid, pvs in input_nodes.items():
        # Check if dcid exists in ignore nodes and is equivalent.
        ignore_pvs = ignore_nodes.get(add_namespace(dcid), None)
        if ignore_pvs:
            # Compare if nodes have any difference in PVs.
            node_diff_counter = {}
            has_diff, diff_str = diff_mcf_node_pvs(node1=pvs,
                                                   node2=ignore_pvs,
                                                   config=config,
                                                   counters=node_diff_counter)
            if has_diff:
                logging.debug(
                    f'Diff in ignored Node: {dcid}, diff:\n{diff_str}\n')
                add_counter(counters, f'error-input-ignore-node-diff', 1)
            else:
                logging.debug(f'Ignored Node: {dcid},\n{pvs}\n')
                add_counter(counters, f'input-nodes-ignored', 1)
        else:
            output_nodes[dcid] = pvs
    return output_nodes


def filter_mcf_file(input_mcf_files: str,
                    ignore_mcf_files: str,
                    config: dict,
                    output_mcf: str,
                    counters: dict = {}) -> dict:
    '''Function to filter MCF nodes in input and write to the output file.'''
    # Load nodes from MCF files.
    input_nodes = load_mcf_nodes(input_mcf_files)
    ignore_nodes = load_mcf_nodes(ignore_mcf_files)
    add_counter(counters, 'input-nodes', len(input_nodes))
    add_counter(counters, 'ignore-nodes-loaded', len(input_nodes))

    # Remove any ignored nodes from input.
    output_nodes = filter_mcf_nodes(input_nodes, ignore_nodes, config, counters)

    # Remove any predefined nodes.
    if config.get('ignore_existing_nodes', False):
        existing_nodes = get_nodes_from_api(list(output_nodes.keys()), config)
        add_counter(counters, 'existing-nodes-from-api', len(existing_nodes))
        output_nodes = filter_mcf_nodes(output_nodes, existing_nodes, config,
                                        counters)

    # Save the filtered nodes into an MCF file.
    if output_mcf:
        write_mcf_nodes([output_nodes], output_mcf)
        print(f'Wrote {len(output_nodes)} nodes to {output_mcf}')
    add_counter(counters, f'output-nodes', len(output_nodes))
    return counters


def main(_):
    counters = filter_mcf_file(_FLAGS.input_mcf, _FLAGS.ignore_mcf,
                               get_diff_config(), _FLAGS.output_mcf)
    print_counters(counters)


if __name__ == '__main__':
    app.run(main)

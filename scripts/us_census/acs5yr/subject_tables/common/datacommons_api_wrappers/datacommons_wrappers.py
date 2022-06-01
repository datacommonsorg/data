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
Wrappers for fetching schema from DataCommons API.
"""

import ast
import copy
import json
import logging
import os
from absl import app
from absl import flags
from sys import path

FLAGS = flags.FLAGS

flags.DEFINE_string('dcid', None, 'dcid of the node to query')
flags.DEFINE_string('dc_output_path', './prefetched_outputs/',
                    'Path to store the output')
flags.DEFINE_boolean('force_fetch', False,
                     'forces api query and not return cached result')

_MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
path.insert(1, os.path.join(_MODULE_DIR, '../../../../../../'))

from tools.download_utils.requests_wrappers import request_post_json

# logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("urllib3")
# requests_log.setLevel(logging.DEBUG)
# HTTPConnection.debuglevel = 1
# requests_log.propagate = True


def dc_check_existence(dcid_list: list,
                       use_autopush: bool = True,
                       max_items: int = 450) -> dict:
    """Checks if a given list of dcids are present in DC.
        REST API is used to query the data with retry on timeout.
        Uses caching of responses to avoid repeated calls.

    Args:
        dcid_list: List of dcids to be queried for existence.
        use_autopush: Boolean value to use autopush API and not public API.
        max_items: Limit of items to be queried in a single POST request.


    Returns:
        Dict object with dcids as key values and boolean values signifying existence as values.
    """
    data_ = {}
    ret_dict = {}
    if use_autopush:
        url_prefix = 'autopush.'
    else:
        url_prefix = ''

    chunk_size = max_items
    dcid_list_chunked = [
        dcid_list[i:i + chunk_size]
        for i in range(0, len(dcid_list), chunk_size)
    ]
    for dcid_chunk in dcid_list_chunked:
        data_["dcids"] = dcid_chunk
        req = request_post_json(
            f'https://{url_prefix}api.datacommons.org/node/property-labels',
            data_)
        resp_dicts = req['payload']
        resp_dicts = ast.literal_eval(resp_dicts)
        for cur_dcid in resp_dicts:
            if not resp_dicts[cur_dcid]:
                ret_dict[cur_dcid] = False
            elif not resp_dicts[cur_dcid]['inLabels'] and not resp_dicts[
                    cur_dcid]['outLabels']:
                ret_dict[cur_dcid] = False
            else:
                ret_dict[cur_dcid] = True

    return ret_dict


# fetch pvs from dc, enums from dc


def fetch_dcid_properties_enums(dcid: str,
                                cache_path: str = _MODULE_DIR +
                                '/prefetched_outputs',
                                use_autopush: bool = True,
                                force_fetch: bool = False):
    """Fetches all the properties and it's possible values for a given dcid.

    Args:
      dcid: DCID of the object whose properties and enum values need to be fetched.
      cache_path: Path of the directory where previously fetched results are stored.
      use_autopush: Boolean value to use autopush or not.
      force_fetch: Boolean value to force API call and disregard the cache.
    
    Returns:
      Dict object with properties as keys and list of possible enum values as values.
  """
    cache_path = os.path.expanduser(cache_path)
    if not os.path.exists(cache_path):
        os.makedirs(cache_path, exist_ok=True)

    if use_autopush:
        api_prefix = 'autopush.'
    else:
        api_prefix = ''

    dc_props = {}

    # get list of properties for each population type
    if force_fetch or not os.path.isfile(
            os.path.join(cache_path, f'{dcid}_dc_props.json')):
        data_ = {}
        data_["dcids"] = [dcid]
        data_["property"] = "domainIncludes"
        data_["direction"] = "in"
        population_props = request_post_json(
            f'https://{api_prefix}api.datacommons.org/node/property-values',
            data_)
        dc_population_pvs = population_props['payload']
        dc_population_pvs = ast.literal_eval(dc_population_pvs)

        if dc_population_pvs[dcid]:
            dc_props = {}
            for prop_dict in dc_population_pvs[dcid]['in']:
                dc_props[prop_dict['dcid']] = []

        with open(os.path.join(cache_path, f'{dcid}_dc_props.json'), 'w') as fp:
            json.dump(dc_props, fp, indent=2)
    else:
        dc_props = json.load(
            open(os.path.join(cache_path, f'{dcid}_dc_props.json'), 'r'))

    # check if the list has enum type
    if force_fetch or not os.path.isfile(
            os.path.join(cache_path, f'{dcid}_dc_props_types.json')):
        data_ = {}
        data_['dcids'] = list(dc_props.keys())
        data_['property'] = 'rangeIncludes'
        data_['direction'] = 'out'
        if data_['dcids']:
            population_props_types = request_post_json(
                f'https://{api_prefix}api.datacommons.org/node/property-values',
                data_)
            population_props_types = ast.literal_eval(
                population_props_types['payload'])
            for property_name in population_props_types:
                if population_props_types[property_name]:
                    for temp_dict in population_props_types[property_name][
                            'out']:
                        dc_props[property_name].append(temp_dict['dcid'])
            with open(os.path.join(cache_path, f'{dcid}_dc_props_types.json'),
                      'w') as fp:
                json.dump(dc_props, fp, indent=2)
    else:
        dc_props = json.load(
            open(os.path.join(cache_path, f'{dcid}_dc_props_types.json'), 'r'))

    # get enum value list
    if force_fetch or not os.path.isfile(
            os.path.join(cache_path, f'{dcid}_dc_props_enum_values.json')):
        new_dict = copy.deepcopy(dc_props)
        for property_name in new_dict.keys():
            dc_props[property_name] = []
            for type_name in new_dict[property_name]:
                if 'enum' in type_name.lower():
                    data_ = {}
                    data_['dcids'] = [type_name]
                    data_['property'] = 'typeOf'
                    data_['direction'] = 'in'
                    enum_values = request_post_json(
                        f'https://{api_prefix}api.datacommons.org/node/property-values',
                        data_)
                    enum_values = ast.literal_eval(enum_values['payload'])
                    if enum_values[type_name]:
                        for temp_dict in enum_values[type_name]['in']:
                            dc_props[property_name].append(temp_dict['dcid'])

        with open(os.path.join(cache_path, f'{dcid}_dc_props_enum_values.json'),
                  'w') as fp:
            json.dump(dc_props, fp, indent=2)
    else:
        dc_props = json.load(
            open(os.path.join(cache_path, f'{dcid}_dc_props_enum_values.json'),
                 'r'))

    return dc_props


def main(argv):
    print(
        json.dumps(fetch_dcid_properties_enums(FLAGS.dcid, FLAGS.dc_output_path,
                                               FLAGS.force_fetch),
                   indent=2))


if __name__ == '__main__':
    flags.mark_flags_as_required(['dcid'])
    app.run(main)

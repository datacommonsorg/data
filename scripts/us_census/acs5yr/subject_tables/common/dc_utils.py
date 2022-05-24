# Copyright 2022 Google LLC
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
"""Data Commons REST API utils."""

import copy
import ast
import json
import os
from absl import app
from absl import flags
import requests
import time

module_dir_ = os.path.dirname(__file__)
_FLAGS = flags.FLAGS

flags.DEFINE_string('dcid', None, 'dcid of the node to query')
flags.DEFINE_string('dc_output_path', './prefetched_outputs/',
                    'Path to store the output')
flags.DEFINE_boolean('force_fetch', False,
                     'forces api query and not return cached result')


def request_url_json(url: str) -> dict:
    """Get JSON object version of reponse to GET request to given URL.

  Args:
    url: URL to make the GET request.

  Returns:
    JSON decoded response from the GET call.
      Empty dict is returned in case the call fails.
  """
    try:
        req = requests.get(url)
    except requests.exceptions.ReadTimeout:
        print(f'Timeout occoured with url: {url}, retrying after 10s.')
        time.sleep(10)
        try:
            req = requests.get(url)
        except requests.exceptions.ReadTimeout:
            print(f'Timeout occoured with url: {url}, request failed.')
            return {}

    if req.status_code == requests.codes.ok:
        response_data = req.json()
    else:
        response_data = {'http_err_code': req.status_code}
        print('HTTP status code: ' + str(req.status_code))
    return response_data


def request_post_json(url: str, data_: dict) -> dict:
    """Get JSON object version of reponse to POST request to given URL.

  Args:
    url: URL to make the POST request.
    data_: payload for the POST request

  Returns:
    JSON decoded response from the POST call.
      Empty dict is returned in case the call fails.
  """
    headers = {'Content-Type': 'application/json'}
    req = None
    while req is None:
        try:
            req = requests.post(url, data=json.dumps(data_), headers=headers)
        except requests.exceptions.ConnectionError:
            print('Connection refused by server. Waiting for 5 seconds')
            time.sleep(5)
            continue

    if req.status_code == requests.codes.ok:
        response_data = req.json()
    else:
        response_data = {'http_err_code': req.status_code}
        print('HTTP status code: ' + str(req.status_code))
    return response_data


# fetch pvs from dc, enums from dc
def fetch_dcid_properties_enums(class_dcid,
                                output_path=module_dir_ + '/prefetched_outputs',
                                force_fetch=False):
    output_path = os.path.expanduser(output_path)
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    dc_props = {}

    # get list of properties for each population type
    if force_fetch or not os.path.isfile(
            os.path.join(output_path, f'{class_dcid}_dc_props.json')):
        # population_props = request_url_json(
        #     f'https://autopush.api.datacommons.org/node/property-values?dcids={class_dcid}&property=domainIncludes&direction=in'
        # )
        data_ = {}
        data_["dcids"] = [class_dcid]
        data_["property"] = "domainIncludes"
        data_["direction"] = "in"
        if data_['dcids']:
            population_props = request_post_json(
                'https://autopush.api.datacommons.org/node/property-values',
                data_)
            dc_population_pvs = population_props['payload']
            dc_population_pvs = ast.literal_eval(dc_population_pvs)

            if dc_population_pvs[class_dcid]:
                dc_props = {}
                for prop_dict in dc_population_pvs[class_dcid]['in']:
                    dc_props[prop_dict['dcid']] = []

            with open(os.path.join(output_path, f'{class_dcid}_dc_props.json'),
                      'w') as fp:
                json.dump(dc_props, fp, indent=2)
    else:
        with open(os.path.join(output_path, f'{class_dcid}_dc_props.json'),
                  'r') as f:
            dc_props = json.load(f)

    # check if the list has enum type
    if force_fetch or not os.path.isfile(
            os.path.join(output_path, f'{class_dcid}_dc_props_types.json')):
        # population_props_types = request_url_json(
        #     f'https://autopush.api.datacommons.org/node/property-values?dcids={"&dcids=".join(dc_props.keys())}&property=rangeIncludes&direction=out'
        # )
        data_ = {}
        data_['dcids'] = list(dc_props.keys())
        data_['property'] = 'rangeIncludes'
        data_['direction'] = 'out'
        if data_['dcids']:
            population_props_types = request_post_json(
                'https://autopush.api.datacommons.org/node/property-values',
                data_)
            population_props_types = ast.literal_eval(
                population_props_types['payload'])
            for property_name in population_props_types:
                if population_props_types[property_name]:
                    for temp_dict in population_props_types[property_name][
                            'out']:
                        dc_props[property_name].append(temp_dict['dcid'])

            with open(
                    os.path.join(output_path,
                                 f'{class_dcid}_dc_props_types.json'),
                    'w') as fp:
                json.dump(dc_props, fp, indent=2)

    else:
        with open(
                os.path.join(output_path, f'{class_dcid}_dc_props_types.json'),
                'r') as f:
            dc_props = json.load(f)

    # get enum value list
    if force_fetch or not os.path.isfile(
            os.path.join(output_path,
                         f'{class_dcid}_dc_props_enum_values.json')):
        new_dict = copy.deepcopy(dc_props)
        for property_name in new_dict.keys():
            dc_props[property_name] = []
            for type_name in new_dict[property_name]:
                if 'enum' in type_name.lower():
                    # enum_values = request_url_json(
                    #     f'https://autopush.api.datacommons.org/node/property-values?dcids={type_name}&property=typeOf&direction=in'
                    # )
                    data_ = {}
                    data_['dcids'] = [type_name]
                    data_['property'] = 'typeOf'
                    data_['direction'] = 'in'
                    if data_['dcids']:
                        enum_values = request_post_json(
                            'https://autopush.api.datacommons.org/node/property-values',
                            data_)
                        enum_values = ast.literal_eval(enum_values['payload'])
                        if enum_values[type_name]:
                            for temp_dict in enum_values[type_name]['in']:
                                dc_props[property_name].append(
                                    temp_dict['dcid'])

        with open(
                os.path.join(output_path,
                             f'{class_dcid}_dc_props_enum_values.json'),
                'w') as fp:
            json.dump(dc_props, fp, indent=2)
    else:
        with open(
                os.path.join(output_path,
                             f'{class_dcid}_dc_props_enum_values.json'),
                'r') as f:
            dc_props = json.load(f)

    return dc_props


def main(argv):
    print(
        json.dumps(fetch_dcid_properties_enums(_FLAGS.dcid,
                                               _FLAGS.dc_output_path,
                                               _FLAGS.force_fetch),
                   indent=2))


if __name__ == '__main__':
    flags.mark_flags_as_required(['dcid'])
    app.run(main)

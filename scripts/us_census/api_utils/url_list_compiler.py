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
Function library to make create list of URLs to be queried for census data download.
"""

import base64
import json
import logging
import os
from absl import app
from absl import flags
from operator import ge
from sys import path
from typing import Any, Union

from census_api_helpers import *
from .status_file_utils import sync_status_list

FLAGS = flags.FLAGS

flags.DEFINE_integer('start_year', 2010,
                     'Start year of the data to be downloaded')
flags.DEFINE_integer('end_year', 2019, 'End year of the data to be downloaded')
flags.DEFINE_list('summary_levels', None,
                  'List of summary levels to be downloaded e.g. 040, 060')
flags.DEFINE_string(
    'output_path', None,
    'The folder where downloaded data is to be stored. Each dataset and table will have a sub directory created within this folder'
)
flags.DEFINE_boolean('all_summaries', None,
                     'Download data for all available summary levels')
flags.DEFINE_boolean('force_fetch_data', False,
                     'Force download of all data from API')
"""TODO
    - Add support for specific geos. e.g. a particular state.
    - Accept a config to create data sample download. (A set of specific geos from each summary level)
"""


def get_url_variables(dataset: str, year: str, variables_str: str,
                      geo_str: str) -> str:
    return f"https://api.census.gov/data/{year}/{dataset}?for={geo_str}&get={variables_str}"


def get_url_table(dataset: str, year: str, table_id: str, geo_str: str) -> str:
    return f"https://api.census.gov/data/{year}/{dataset}?get=group({table_id})&for={geo_str}"


def save_resp_json(resp: Any, store_path: str):
    """Parses and stores json response to a file.

        Args:
            resp: Response object recieved from aiohttp call.
            store_path: Path of the file to store the result.
    """
    resp_data = resp.json()
    logging.info('Writing downloaded data to file: %s', store_path)
    json.dump(resp_data, open(store_path, 'w'), indent=2)


def _goestr_to_file_name(geo_str: str) -> str:
    geo_str = geo_str.replace(':*', '')
    geo_str = geo_str.replace('%20', '-')
    geo_str = geo_str.replace(' ', '-')
    geo_str = geo_str.replace('/', '')
    # geo_str = geo_str.replace('&in=state:', '_state_')
    geo_str = geo_str.replace('&in=', '_')
    geo_str = geo_str.replace(':', '')
    return geo_str


def get_file_name_table(output_path: str, table_id: str, year: str,
                        geo_str: str) -> str:
    table_id = table_id.upper()
    output_path = os.path.expanduser(output_path)
    output_path = os.path.abspath(output_path)
    # TODO use base64 for long filename
    file_name = os.path.join(
        output_path, table_id + '_' + str(year) + '_' +
        _goestr_to_file_name(geo_str) + '.csv')
    return file_name


def get_file_name_variables(output_path: str, table_id: str, year: str,
                            chunk_id: int, geoStr: str) -> str:
    table_id = table_id.upper()
    output_path = os.path.expanduser(output_path)
    output_path = os.path.abspath(output_path)
    file_name = os.path.join(
        output_path, table_id + '_' + str(year) + '_' +
        _goestr_to_file_name(geoStr) + '_' + str(chunk_id) + '.csv')
    return file_name


def _get_url_entry_table(dataset: str,
                         year: str,
                         table_id: str,
                         geo_str: str,
                         output_path: str,
                         force_fetch: bool = False) -> dict:
    temp_dict = {}
    temp_dict['url'] = get_url_table(dataset, year, table_id, geo_str)
    temp_dict['store_path'] = get_file_name_table(output_path, table_id, year,
                                                  geo_str)
    temp_dict['status'] = 'pending'
    if force_fetch:
        temp_dict['force_fetch'] = True
    return temp_dict


def get_table_url_list(dataset: str,
                       table_id: str,
                       q_variable: str,
                       year_list: list,
                       output_path: str,
                       api_key: str,
                       s_level_list: Union[list, str] = 'all',
                       force_fetch_config: bool = False,
                       force_fetch_data: bool = False) -> list:
    """Compile a list of URLs that need to requested to download a group/table in census dataset.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            table_id: ID of the US census group that needs to be downloaded.
            q_variable: Variable to be used to find list of available geo IDs.
            year_list: list of years for which the data is to be downloaded.
            output_path: Folder under which the downloaded data needs to be stored.
                            NOTE: sub folders would be created for dataset and group.
            api_key: User's API key provided by US Census.
            s_level_list: List of summary level IDs for which the data is to be downloaded. 
                            'all' for all available summary levels
            force_fetch_config: Boolean value to force recomputation of API config of US census.
            force_fetch_data: Boolean value to force download of all relevant URLs.
        
        Returns:
            List of URL metadata dict objects that need to requested to download data.
    """
    table_id = table_id.upper()
    if dataset not in get_list_datasets(force_fetch=force_fetch_config):
        print(dataset, 'not found')
        return []
    if table_id not in get_dataset_groups(dataset,
                                          force_fetch=force_fetch_config):
        print(table_id, 'not found in ', dataset)
        return []
    available_years = get_dataset_groups_years(dataset,
                                               table_id,
                                               force_fetch=force_fetch_config)
    geo_config = get_summary_level_config(dataset, q_variable, api_key,
                                          force_fetch_config)
    # get list of all s levels
    if s_level_list == 'all':
        s_level_list = []
        for year, year_dict in geo_config.items():
            for s_level in year_dict['summary_levels']:
                if s_level not in s_level_list:
                    s_level_list.append(s_level)
    ret_list = []
    for year in year_list:
        if year in available_years:
            print('Compiling urls for', year)
            for s_level in s_level_list:
                if s_level in geo_config[year]['summary_levels']:
                    req_str_list = get_str_list_required(
                        geo_config[year], s_level)
                    s_dict = geo_config[year]['summary_levels'][s_level]
                    if req_str_list:
                        for geo_req in req_str_list:
                            ret_list.append(
                                _get_url_entry_table(
                                    dataset, year, table_id,
                                    f"{s_dict['str']}:*{geo_req}", output_path,
                                    force_fetch_data))
                    else:
                        ret_list.append(
                            _get_url_entry_table(dataset, year, table_id,
                                                 f"{s_dict['str']}:*",
                                                 output_path, force_fetch_data))
                else:
                    print('Warning:', s_level, 'not available for year', year)
    ret_list = sync_status_list([], ret_list)
    return ret_list


def get_variables_url_list(dataset: str,
                           table_id,
                           q_variable,
                           variables_year_dict,
                           output_path,
                           api_key,
                           s_level_list='all',
                           force_fetch_config=False,
                           force_fetch_data=False):
    # TODO implement the method
    pass
    # table_id = table_id.upper()
    # ret_list = []

    # geo_config = get_summary_level_config(dataset, q_variable, api_key, force_fetch_config)
    # # get list of all s levels
    # if s_level_list == 'all':
    #     s_level_list = []
    #     for year, year_dict in geo_config.items():
    #         for s_level in year_dict['summary_levels']:
    #             if s_level not in s_level_list:
    #                 s_level_list.append(s_level)

    # year_list = []
    # for year in variables_year_dict:
    #     year_list.append(year)

    # for year in variables_year_dict:
    #     # limited to 50 variables including NAME
    #     n = 49
    #     variables_chunked = [variables_year_dict[year][i:i + n] for i in range(0, len(variables_year_dict[year]), n)]
    #     logging.info('variable list divided into %d chunks for year %d', len(variables_chunked), year)
    # for geo_id in geo_url_map:
    #     geo_str = geo_url_map[geo_id]['urlStr']
    #     if geo_url_map[geo_id]['needsStateID']:
    #         for state_id in states_by_year[year]:
    #             geo_str_state = geo_str + state_id
    #             for i, cur_vars in enumerate(variables_chunked):
    #                 variable_list_str = ','.join(cur_vars)
    #                 temp_dict = {}
    #                 temp_dict['url'] = get_url_variables(dataset, year, 'NAME,' + variable_list_str, geo_str_state)
    #                 temp_dict['store_path'] = get_file_name_variables(output_path, table_id, year, i, geo_str_state)
    #                 temp_dict['status'] = 'pending'
    #                 ret_list.append(temp_dict)
    #     else:
    #         for i, cur_vars in enumerate(variables_chunked):
    #             variable_list_str = ','.join(cur_vars)
    #             temp_dict = {}
    #             temp_dict['url'] = get_url_variables(dataset, year, 'NAME,' + variable_list_str, geo_str)
    #             temp_dict['store_path'] = get_file_name_variables(output_path, table_id, year, i, geo_str)
    #             temp_dict['status'] = 'pending'
    #             ret_list.append(temp_dict)
    # return ret_list


def main(argv):
    # geo_url_map = json.load(open(FLAGS.geo_map))
    year_list_int = list(range(FLAGS.start_year, FLAGS.end_year + 1))
    year_list = [str(y) for y in year_list_int]
    out_path = os.path.expanduser(FLAGS.output_path)
    if FLAGS.summary_levels:
        s_list = FLAGS.summary_levels
    else:
        s_list = 'all'
    url_list = get_table_url_list(FLAGS.dataset,
                                  FLAGS.table_id,
                                  FLAGS.q_variable,
                                  year_list,
                                  out_path,
                                  FLAGS.api_key,
                                  s_level_list=s_list,
                                  force_fetch_config=FLAGS.force_fetch_config,
                                  force_fetch_data=FLAGS.force_fetch_data)
    os.makedirs(os.path.join(out_path, FLAGS.table_id), exist_ok=True)
    print('Writing URLs to file')
    with open(os.path.join(out_path, FLAGS.table_id, 'download_status.json'),
              'w') as fp:
        json.dump(url_list, fp, indent=2)


if __name__ == '__main__':
    flags.mark_flags_as_required(['table_id', 'output_path', 'api_key'])
    flags.mark_flags_as_mutual_exclusive(['summary_levels', 'all_summaries'],
                                         required=True)
    app.run(main)

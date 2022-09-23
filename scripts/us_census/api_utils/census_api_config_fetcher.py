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
Function library to fetch the census API configuration and create usable configs.
"""

import json
import logging
import os
import sys
from absl import app
from absl import flags
from collections import OrderedDict
from sys import path

module_dir_ = os.path.dirname(os.path.realpath(__file__))
module_parentdir_ = os.path.join(module_dir_, '..')
CONFIG_PATH_ = os.path.join(module_dir_, 'config_files')
path.insert(1, os.path.join(module_dir_, '../../../'))

from .download_utils import download_url_list_iterations, async_save_resp_json
from tools.download_utils.requests_wrappers import request_url_json
from .status_file_utils import get_pending_or_fail_url_list, sync_status_list

FLAGS = flags.FLAGS

flags.DEFINE_boolean(
    'force_fetch_config', False,
    'Force download of config and list of required geos from API')


def _generate_url_prefix(dataset: str, year: str = None) -> str:
    if year:
        return f'http://api.census.gov/data/{year}/{dataset}/'
    else:
        return f'http://api.census.gov/data/{dataset}/'


def generate_url_geography(dataset: str, year: str = None) -> str:
    return _generate_url_prefix(dataset, year) + 'geography.json'


def generate_url_groups(dataset: str, year: str = None) -> str:
    return _generate_url_prefix(dataset, year) + 'groups.json'


def generate_url_variables(dataset: str, year: str = None) -> str:
    return _generate_url_prefix(dataset, year) + 'variables.json'


def generate_url_tags(dataset: str, year: str = None) -> str:
    return _generate_url_prefix(dataset, year) + 'tags.json'


def generate_url_group_variables(dataset: str,
                                 group_id: str,
                                 year: str = None) -> str:
    return _generate_url_prefix(dataset, year) + f'groups/{group_id}.json'


def fetch_dataset_config(store_path: str = CONFIG_PATH_,
                         force_fetch: bool = False) -> dict:
    """Fetches primary entry point for API config, extracts list of datasets and their detailed config links.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object received from API.
  """
    store_path = os.path.expanduser(store_path)
    if not os.path.exists(store_path):
        os.makedirs(store_path, exist_ok=True)
    if force_fetch or not os.path.isfile(
            os.path.join(store_path, 'dataset_list.json')):
        datasets = request_url_json('https://api.census.gov/data.json')
        if 'http_err_code' not in datasets:
            with open(os.path.join(store_path, 'dataset_list.json'), 'w') as fp:
                json.dump(datasets, fp, indent=2)
    else:
        datasets = json.load(
            open(os.path.join(store_path, 'dataset_list.json'), 'r'))
    return datasets


def compile_year_map(store_path: str = CONFIG_PATH_,
                     force_fetch: bool = False) -> dict:
    """Extracts basic dataset and year information from API config.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset, available years, dataset identifier and title.
  """
    if not force_fetch and os.path.isfile(
            os.path.join(store_path, 'dataset_year.json')):
        dataset_dict = json.load(
            open(os.path.join(store_path, 'dataset_year.json'), 'r'))
    else:
        datasets = fetch_dataset_config(store_path, force_fetch)
        dataset_dict = {}
        error_dict = {}
        for cur_dataset_dict in datasets['dataset']:
            link_tree = '/'.join(cur_dataset_dict['c_dataset'])
            if cur_dataset_dict['c_isAvailable']:
                if link_tree not in dataset_dict:
                    dataset_dict[link_tree] = {}
                    dataset_dict[link_tree]['years'] = {}

                identifier = cur_dataset_dict['identifier']
                identifier = identifier[identifier.rfind('/') + 1:]

                if 'c_vintage' in cur_dataset_dict:
                    year = cur_dataset_dict['c_vintage']
                    dataset_dict[link_tree]['years'][year] = {}
                    dataset_dict[link_tree]['years'][year][
                        'title'] = cur_dataset_dict['title']
                    dataset_dict[link_tree]['years'][year][
                        'identifier'] = identifier

                elif 'c_isTimeseries' in cur_dataset_dict and cur_dataset_dict[
                        'c_isTimeseries']:
                    year = None

                    if 'title' not in dataset_dict[link_tree]:
                        dataset_dict[link_tree]['title'] = cur_dataset_dict[
                            'title']
                    elif dataset_dict[link_tree]['title'] != cur_dataset_dict[
                            'title']:
                        if 'timeseries_multiple_titles' not in error_dict:
                            error_dict['timeseries_multiple_titles'] = []
                        error_dict['timeseries_multiple_titles'].append(
                            link_tree)
                        print(link_tree, 'found multiple title')

                    if 'identifier' not in dataset_dict[link_tree]:
                        dataset_dict[link_tree]['identifier'] = identifier
                    elif dataset_dict[link_tree]['identifier'] != identifier:
                        if 'timeseries_multiple_identifiers' not in error_dict:
                            error_dict['timeseries_multiple_identifiers'] = []
                        error_dict['timeseries_multiple_identifiers'].append(
                            link_tree)
                        print(link_tree, 'found multiple identifiers')
                else:
                    year = None
                    if 'linktree_unkown_type' not in error_dict:
                        error_dict['linktree_unkown_type'] = []
                    error_dict['linktree_unkown_type'].append(link_tree)
                    print('/'.join(cur_dataset_dict['c_dataset']),
                          'year not available and not timeseries')

                if cur_dataset_dict['distribution'][
                        0]['accessURL'] != _generate_url_prefix(
                            link_tree, year)[:-1]:
                    if 'url_mismatch' not in error_dict:
                        error_dict['url_mismatch'] = []
                    error_dict['url_mismatch'].append({
                        'expected':
                            _generate_url_prefix(link_tree, year)[:-1],
                        'actual':
                            cur_dataset_dict['distribution'][0]['accessURL']
                    })
                    print(link_tree, 'accessURL unexpected')

                if cur_dataset_dict['c_geographyLink'] != generate_url_geography(
                        link_tree, year):
                    if 'url_mismatch' not in error_dict:
                        error_dict['url_mismatch'] = []
                    error_dict['url_mismatch'].append({
                        'expected': generate_url_geography(link_tree, year),
                        'actual': cur_dataset_dict['c_geographyLink']
                    })
                    print(link_tree, 'c_geographyLink unexpected')

                if cur_dataset_dict['c_groupsLink'] != generate_url_groups(
                        link_tree, year):
                    if 'url_mismatch' not in error_dict:
                        error_dict['url_mismatch'] = []
                    error_dict['url_mismatch'].append({
                        'expected': generate_url_groups(link_tree, year),
                        'actual': cur_dataset_dict['c_groupsLink']
                    })
                    print(link_tree, 'c_groupsLink unexpected')

                if cur_dataset_dict['c_variablesLink'] != generate_url_variables(
                        link_tree, year):
                    if 'url_mismatch' not in error_dict:
                        error_dict['url_mismatch'] = []
                    error_dict['url_mismatch'].append({
                        'expected': generate_url_variables(link_tree, year),
                        'actual': cur_dataset_dict['c_variablesLink']
                    })
                    print(link_tree, 'c_variablesLink unexpected')

                if 'c_tagsLink' in cur_dataset_dict:
                    if cur_dataset_dict['c_tagsLink'] != generate_url_tags(
                            link_tree, year):
                        if 'url_mismatch' not in error_dict:
                            error_dict['url_mismatch'] = []
                        error_dict['url_mismatch'].append({
                            'expected': generate_url_tags(link_tree, year),
                            'actual': cur_dataset_dict['c_tagsLink']
                        })
                        print(link_tree, 'c_tagsLink unexpected')

                if len(cur_dataset_dict['distribution']) > 1:
                    if 'link_tree_multiple_distribution' not in error_dict:
                        error_dict['link_tree_multiple_distribution'] = []
                    error_dict['link_tree_multiple_distribution'].append(
                        link_tree)
                    print(link_tree, 'has multiple distribution')

                if 'c_tagsLink' not in cur_dataset_dict:
                    if 'missing_tags' not in error_dict:
                        error_dict['missing_tags'] = []
                    error_dict['missing_tags'].append(link_tree)
                    print(link_tree, 'c_tagsLink not present')
            else:
                if 'unavailable_link_trees' not in error_dict:
                    error_dict['unavailable_link_trees'] = []
                error_dict['unavailable_link_trees'].append(link_tree)
                print(link_tree, 'not available')

        with open(os.path.join(store_path, 'dataset_year.json'), 'w') as fp:
            json.dump(dataset_dict, fp, indent=2)
        if error_dict:
            with open(os.path.join(store_path, 'errors_dataset_year.json'),
                      'w') as fp:
                json.dump(error_dict, fp, indent=2)

    return dataset_dict


def fetch_dataset_config_cache(param: str,
                               store_path: str = CONFIG_PATH_,
                               force_fetch: bool = False):
    """Fetches detailed information about passed paramater for each dataset from API.

    Args:
      param: Parameter to get details about. (Can be one of 'groups', 'geography', 'variables', 'group_variables')
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.
  """
    if param not in ['groups', 'geography', 'variables', 'group_variables']:
        error_dict = {'invalid_param': [param]}
        with open(
                os.path.join(store_path,
                             f'errors_dataset_{param}_download.json'),
                'w') as fp:
            json.dump(error_dict, fp, indent=2)
        return
    print('Fetching', param, 'config cache files')
    store_path = os.path.abspath(store_path)

    dataset_dict = compile_year_map(store_path, force_fetch)
    if param == 'group_variables':
        dataset_dict = compile_non_group_variables_map(store_path, force_fetch)
    error_dict = {}
    url_list = []

    cache_path = os.path.join(store_path, 'api_cache')
    if not os.path.exists(cache_path):
        os.makedirs(cache_path, exist_ok=True)

    for dataset in dataset_dict:
        if 'years' in dataset_dict[dataset]:
            for year in dataset_dict[dataset]['years']:
                if param == 'groups':
                    temp_url = generate_url_groups(dataset, year)
                elif param == 'geography':
                    temp_url = generate_url_geography(dataset, year)
                elif param == 'variables':
                    temp_url = generate_url_variables(dataset, year)
                else:
                    temp_url = None

                file_path = os.path.join(cache_path, dataset, str(year))
                file_name = os.path.join(file_path, f'{param}.json')
                if not os.path.exists(file_path):
                    os.makedirs(file_path, exist_ok=True)

                if temp_url:
                    temp_dict = {}
                    temp_dict['url'] = temp_url
                    temp_dict['store_path'] = file_name
                    temp_dict['status'] = 'pending'
                    temp_dict['force_fetch'] = force_fetch
                    url_list.append(temp_dict)

                if param == 'group_variables':
                    for group_id in dataset_dict[dataset]['years'][year][
                            'groups']:
                        temp_url = generate_url_group_variables(
                            dataset, group_id, year)
                        file_name = os.path.join(file_path, group_id + '.json')
                        if temp_url not in url_list:
                            temp_dict = {}
                            temp_dict['url'] = temp_url
                            temp_dict['store_path'] = file_name
                            temp_dict['status'] = 'pending'
                            temp_dict['force_fetch'] = force_fetch
                            url_list.append(temp_dict)
        else:
            if param == 'groups':
                temp_url = generate_url_groups(dataset)
            elif param == 'geography':
                temp_url = generate_url_geography(dataset)
            elif param == 'variables':
                temp_url = generate_url_variables(dataset)
            else:
                temp_url = None

            file_path = os.path.join(cache_path, dataset)
            file_name = os.path.join(file_path, f'{param}.json')
            if not os.path.exists(file_path):
                os.makedirs(file_path, exist_ok=True)
            if temp_url and temp_url not in url_list:
                temp_dict = {}
                temp_dict['url'] = temp_url
                temp_dict['store_path'] = file_name
                temp_dict['status'] = 'pending'
                temp_dict['force_fetch'] = force_fetch
                url_list.append(temp_dict)
            if param == 'group_variables':
                for group_id in dataset_dict[dataset]['groups']:
                    temp_url = generate_url_group_variables(dataset, group_id)
                    file_name = os.path.join(file_path, group_id + '.json')
                    if temp_url not in url_list:
                        temp_dict = {}
                        temp_dict['url'] = temp_url
                        temp_dict['store_path'] = file_name
                        temp_dict['status'] = 'pending'
                        temp_dict['force_fetch'] = force_fetch
                        url_list.append(temp_dict)

    url_list = sync_status_list([], url_list)
    status_path = os.path.join(cache_path, f'{param}_cache_status.json')
    with open(status_path, 'w') as fp:
        json.dump(url_list, fp, indent=2)

    rate_params = {}
    rate_params['max_parallel_req'] = 50
    rate_params['limit_per_host'] = 20
    rate_params['req_per_unit_time'] = 10
    rate_params['unit_time'] = 1

    failed_urls_ctr = download_url_list_iterations(url_list,
                                                   None,
                                                   '',
                                                   async_save_resp_json,
                                                   rate_params=rate_params)

    with open(status_path, 'w') as fp:
        json.dump(url_list, fp, indent=2)

    if error_dict:
        with open(
                os.path.join(store_path,
                             f'errors_dataset_{param}_download.json'),
                'w') as fp:
            json.dump(get_pending_or_fail_url_list(url_list), fp, indent=2)


def compile_groups_map(store_path: str = CONFIG_PATH_,
                       force_fetch: bool = False) -> dict:
    """Fetches detailed information about groups available in a dataset from API.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset, available years, dataset identifier and title, available groups.
  """
    if os.path.isfile(os.path.join(store_path,
                                   'dataset_groups.json')) and not force_fetch:
        dataset_dict = json.load(
            open(os.path.join(store_path, 'dataset_groups.json'), 'r'))
    else:
        dataset_dict = compile_year_map(store_path, force_fetch)
        error_dict = {}
        fetch_dataset_config_cache('groups', store_path, force_fetch)
        cache_path = os.path.join(store_path, 'api_cache')
        for dataset in dataset_dict:
            if 'years' in dataset_dict[dataset]:
                for year in dataset_dict[dataset]['years']:
                    cache_file = os.path.join(cache_path, dataset, str(year),
                                              'groups.json')
                    temp_url = generate_url_groups(dataset, year)
                    if os.path.isfile(cache_file):
                        group_list = json.load(open(cache_file, 'r'))
                    else:
                        group_list = request_url_json(temp_url)
                    if 'http_err_code' not in group_list:
                        if len(group_list) != 1:
                            if 'groups_extra_keys' not in error_dict:
                                error_dict['groups_extra_keys'] = []
                            error_dict['groups_extra_keys'].append(temp_url)
                            print(temp_url, 'has unexpected number of keys ')
                        group_list = group_list['groups']
                        dataset_dict[dataset]['years'][year]['groups'] = {}
                        for cur_group in group_list:
                            dataset_dict[dataset]['years'][year]['groups'][
                                cur_group['name']] = {}
                            dataset_dict[dataset]['years'][year]['groups'][
                                cur_group['name']]['title'] = cur_group[
                                    'description']
                            # check only 3 key values
                            if len(cur_group) != 3:
                                if 'groups_extra_keys' not in error_dict:
                                    error_dict['groups_extra_keys'] = []
                                error_dict['groups_extra_keys'].append(temp_url)
                                print(temp_url,
                                      'has unexpected number of keys ')
                            # check variables url
                            if cur_group[
                                    'variables'] != generate_url_group_variables(
                                        dataset, cur_group['name'], year):
                                if 'url_mismatch' not in error_dict:
                                    error_dict['url_mismatch'] = []
                                error_dict['url_mismatch'].append({
                                    'expected':
                                        generate_url_group_variables(
                                            dataset, cur_group['name'], year),
                                    'actual':
                                        cur_group['variables']
                                })
                                print(dataset, 'group_variablesLink unexpected')

            else:
                cache_file = os.path.join(cache_path, dataset, 'groups.json')
                temp_url = generate_url_groups(dataset)
                if os.path.isfile(cache_file):
                    group_list = json.load(open(cache_file, 'r'))
                else:
                    group_list = request_url_json(temp_url)
                if 'http_err_code' not in group_list:
                    if len(group_list) != 1:
                        if 'groups_extra_keys' not in error_dict:
                            error_dict['groups_extra_keys'] = []
                        error_dict['groups_extra_keys'].append(temp_url)
                        print(temp_url, 'not available')
                    group_list = group_list['groups']
                    dataset_dict[dataset]['groups'] = {}
                    for cur_group in group_list:
                        dataset_dict[dataset]['groups'][cur_group['name']] = {}
                        dataset_dict[dataset]['groups'][cur_group['name']][
                            'title'] = cur_group['description']
                        # check only 3 key values
                        if len(cur_group) != 3:
                            if 'groups_extra_keys' not in error_dict:
                                error_dict['groups_extra_keys'] = []
                            error_dict['groups_extra_keys'].append(temp_url)
                            print(temp_url, 'has unexpected number of keys ')
                        # check variables url
                        if cur_group[
                                'variables'] != generate_url_group_variables(
                                    dataset, cur_group['name']):
                            if 'url_mismatch' not in error_dict:
                                error_dict['url_mismatch'] = []
                            error_dict['url_mismatch'].append({
                                'expected':
                                    generate_url_group_variables(
                                        dataset, cur_group['name']),
                                'actual':
                                    cur_group['variables']
                            })
                            print(dataset, 'group_variablesLink unexpected')

        with open(os.path.join(store_path, 'dataset_groups.json'), 'w') as fp:
            json.dump(dataset_dict, fp, indent=2)
        if error_dict:
            with open(os.path.join(store_path, 'errors_dataset_groups.json'),
                      'w') as fp:
                json.dump(error_dict, fp, indent=2)

    return dataset_dict


def compile_geography_map(store_path: str = CONFIG_PATH_,
                          force_fetch: bool = False) -> dict:
    """Fetches detailed information about geography available in a dataset from API.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset, available years, dataset identifier and title, 
        available groups, geography information.
  """
    if os.path.isfile(os.path.join(
            store_path, 'dataset_geography.json')) and not force_fetch:
        dataset_dict = json.load(
            open(os.path.join(store_path, 'dataset_geography.json'), 'r'))
    else:
        dataset_dict = compile_groups_map(store_path, force_fetch)
        error_dict = {}
        fetch_dataset_config_cache('geography', store_path, force_fetch)
        cache_path = os.path.join(store_path, 'api_cache')
        for dataset in dataset_dict:
            if 'years' in dataset_dict[dataset]:
                for year in dataset_dict[dataset]['years']:
                    cache_file = os.path.join(cache_path, dataset, str(year),
                                              'geography.json')
                    temp_url = generate_url_geography(dataset, year)
                    if os.path.isfile(cache_file):
                        geo_list = json.load(open(cache_file, 'r'))
                    else:
                        geo_list = request_url_json(temp_url)
                    if 'http_err_code' not in geo_list:
                        if len(geo_list) != 1:
                            if 'groups_extra_keys' not in error_dict:
                                error_dict['groups_extra_keys'] = []
                            error_dict['groups_extra_keys'].append(temp_url)
                            print(temp_url, 'has unexpected number of keys ')
                        if 'fips' in geo_list:
                            geo_list = geo_list['fips']
                            dataset_dict[dataset]['years'][year][
                                'geos'] = OrderedDict()
                            geo_config = dataset_dict[dataset]['years'][year][
                                'geos']
                            geo_config['required_geos'] = []
                            geo_config['summary_levels'] = OrderedDict()
                            for cur_geo in geo_list:
                                if 'geoLevelDisplay' in cur_geo and 'geoLevelId' in cur_geo and cur_geo[
                                        'geoLevelDisplay'] != cur_geo[
                                            'geoLevelId']:
                                    if 'geo_multiple_id' not in error_dict:
                                        error_dict['geo_multiple_id'] = []
                                    error_dict['geo_multiple_id'].append(
                                        temp_url + ' ' + cur_geo['name'])
                                    print(cur_geo['name'],
                                          'has multiple geoId ')
                                # On manual check each geo level had 7 entries usually or 3
                                # This is a sanity check for some important data that might have been missed.
                                if len(cur_geo) > 7:
                                    if 'groups_extra_keys' not in error_dict:
                                        error_dict['groups_extra_keys'] = []
                                    error_dict['groups_extra_keys'].append(
                                        temp_url)
                                    print(temp_url,
                                          'has unexpected number of keys ')

                                if 'geoLevelId' in cur_geo:
                                    s_level = cur_geo['geoLevelId']
                                elif 'geoLevelDisplay' in cur_geo:
                                    s_level = cur_geo['geoLevelDisplay']
                                else:
                                    s_level = cur_geo['name']
                                    if 'geo_missing_id' not in error_dict:
                                        error_dict['geo_missing_id'] = []
                                    error_dict['geo_missing_id'].append(
                                        temp_url + ' ' + cur_geo['name'])
                                    print(cur_geo['name'],
                                          'has no geoId, using name instead.')
                                if s_level not in geo_config:
                                    geo_config['summary_levels'][s_level] = {}
                                    geo_config['summary_levels'][s_level][
                                        'str'] = cur_geo['name']
                                    if 'requires' in cur_geo:
                                        geo_config['summary_levels'][s_level][
                                            'geo_filters'] = cur_geo['requires']
                                    else:
                                        geo_config['summary_levels'][s_level][
                                            'geo_filters'] = []
                                    if 'wildcard' in cur_geo:
                                        geo_config['summary_levels'][s_level][
                                            'wildcard'] = cur_geo['wildcard']
                                    else:
                                        geo_config['summary_levels'][s_level][
                                            'wildcard'] = []
                                    geo_config['summary_levels'][s_level][
                                        'requires'] = []
                                    for geo in geo_config['summary_levels'][
                                            s_level]['geo_filters']:
                                        if geo not in geo_config[
                                                'summary_levels'][s_level][
                                                    'wildcard']:
                                            geo_config['summary_levels'][
                                                s_level]['requires'].append(geo)
                                            if geo not in geo_config[
                                                    'required_geos']:
                                                geo_config[
                                                    'required_geos'].append(geo)
                                else:
                                    if 'geo_multiple_id' not in error_dict:
                                        error_dict['geo_multiple_id'] = []
                                    error_dict['geo_multiple_id'].append(
                                        temp_url + ' ' + cur_geo['name'])
                                    print(cur_geo['name'],
                                          'has multiple geoId ')
                        else:
                            if 'fips_missing' not in error_dict:
                                error_dict['fips_missing'] = []
                            error_dict['fips_missing'].append(temp_url)
                            print(temp_url, 'fips missing')
            else:
                cache_file = os.path.join(cache_path, dataset, 'geography.json')
                temp_url = generate_url_geography(dataset)

                if os.path.isfile(cache_file):
                    geo_list = json.load(open(cache_file, 'r'))
                else:
                    geo_list = request_url_json(temp_url)
                if 'http_err_code' not in geo_list:
                    if len(geo_list) != 1:
                        if 'groups_extra_keys' not in error_dict:
                            error_dict['groups_extra_keys'] = []
                        error_dict['groups_extra_keys'].append(temp_url)
                        print(temp_url, 'has unexpected number of keys ')
                    if 'fips' in geo_list:
                        geo_list = geo_list['fips']
                        dataset_dict[dataset]['geos'] = OrderedDict()
                        geo_config = dataset_dict[dataset]['geos']
                        geo_config['required_geos'] = []
                        geo_config['summary_levels'] = OrderedDict()
                        for cur_geo in geo_list:
                            if 'geoLevelDisplay' in cur_geo and 'geoLevelId' in cur_geo and cur_geo[
                                    'geoLevelDisplay'] != cur_geo['geoLevelId']:
                                if 'geo_multiple_id' not in error_dict:
                                    error_dict['geo_multiple_id'] = []
                                error_dict['geo_multiple_id'].append(
                                    temp_url + ' ' + cur_geo['name'])
                                print(cur_geo['name'], 'has multiple geoId ')
                            # On manual check each geo level had 7 entries usually or 3
                            # This is a sanity check for some important data that might have been missed.
                            if len(cur_geo) > 7:
                                if 'groups_extra_keys' not in error_dict:
                                    error_dict['groups_extra_keys'] = []
                                error_dict['groups_extra_keys'].append(temp_url)
                                print(temp_url,
                                      'has unexpected number of keys ')

                            if 'geoLevelId' in cur_geo:
                                s_level = cur_geo['geoLevelId']
                            elif 'geoLevelDisplay' in cur_geo:
                                s_level = cur_geo['geoLevelId']
                            else:
                                s_level = cur_geo['name']
                                if 'geo_missing_id' not in error_dict:
                                    error_dict['geo_missing_id'] = []
                                error_dict['geo_missing_id'].append(
                                    temp_url + ' ' + cur_geo['name'])
                                print(cur_geo['name'],
                                      'has no geoId, using name instead.')
                            if s_level not in geo_config:
                                geo_config['summary_levels'][s_level] = {}
                                geo_config['summary_levels'][s_level][
                                    'str'] = cur_geo['name']
                                if 'requires' in cur_geo:
                                    geo_config['summary_levels'][s_level][
                                        'geo_filters'] = cur_geo['requires']
                                else:
                                    geo_config['summary_levels'][s_level][
                                        'geo_filters'] = []
                                if 'wildcard' in cur_geo:
                                    geo_config['summary_levels'][s_level][
                                        'wildcard'] = cur_geo['wildcard']
                                else:
                                    geo_config['summary_levels'][s_level][
                                        'wildcard'] = []
                                geo_config['summary_levels'][s_level][
                                    'requires'] = []
                                for geo in geo_config['summary_levels'][
                                        s_level]['geo_filters']:
                                    if geo not in geo_config['summary_levels'][
                                            s_level]['wildcard']:
                                        geo_config['summary_levels'][s_level][
                                            'requires'].append(geo)
                                        if geo not in geo_config[
                                                'required_geos']:
                                            geo_config['required_geos'].append(
                                                geo)
                            else:
                                if 'geo_multiple_id' not in error_dict:
                                    error_dict['geo_multiple_id'] = []
                                error_dict['geo_multiple_id'].append(
                                    temp_url + ' ' + cur_geo['name'])
                                print(cur_geo['name'], 'has multiple geoId ')
                    else:
                        if 'fips_missing' not in error_dict:
                            error_dict['fips_missing'] = []
                        error_dict['fips_missing'].append(temp_url)
                        print(temp_url, 'fips missing')

        with open(os.path.join(store_path, 'dataset_geography.json'),
                  'w') as fp:
            json.dump(dataset_dict, fp, indent=2)
        if error_dict:
            with open(os.path.join(store_path, 'errors_dataset_geography.json'),
                      'w') as fp:
                json.dump(error_dict, fp, indent=2)

    return dataset_dict


def compile_non_group_variables_map(store_path: str = CONFIG_PATH_,
                                    force_fetch: bool = False) -> dict:
    """Fetches detailed information about dataset without groups available in a dataset from API.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset, available years, dataset identifier and title, 
        available groups, geography information, non group variables.
  """
    if os.path.isfile(
            os.path.join(
                store_path,
                'dataset_non_group_variables.json')) and not force_fetch:
        dataset_dict = json.load(
            open(os.path.join(store_path, 'dataset_non_group_variables.json'),
                 'r'))
    else:
        dataset_dict = compile_geography_map(store_path, force_fetch)
        error_dict = {}
        fetch_dataset_config_cache('variables', store_path, force_fetch)
        cache_path = os.path.join(store_path, 'api_cache')
        for dataset in dataset_dict:
            if 'years' in dataset_dict[dataset]:
                for year in dataset_dict[dataset]['years']:
                    cache_file = os.path.join(cache_path, dataset, str(year),
                                              'variables.json')
                    temp_url = generate_url_variables(dataset, year)
                    if os.path.isfile(cache_file):
                        variable_list = json.load(open(cache_file, 'r'))
                    else:
                        variable_list = request_url_json(temp_url)
                    if 'http_err_code' not in variable_list:
                        if len(variable_list) != 1:
                            if 'groups_extra_keys' not in error_dict:
                                error_dict['groups_extra_keys'] = []
                            error_dict['groups_extra_keys'].append(temp_url)
                            print(temp_url, 'has unexpected number of keys ')
                        if 'variables' in variable_list:
                            variable_list = variable_list['variables']
                            dataset_dict[dataset]['years'][year][
                                'variables'] = {}
                            for cur_variable in variable_list:
                                if 'group' not in variable_list[
                                        cur_variable] or variable_list[
                                            cur_variable]['group'] == 'N/A':
                                    dataset_dict[dataset]['years'][year][
                                        'variables'][cur_variable] = {}
                                    dataset_dict[dataset]['years'][year][
                                        'variables'][cur_variable][
                                            'label'] = variable_list[
                                                cur_variable]['label']
                                    if 'concept' in variable_list[cur_variable]:
                                        dataset_dict[dataset]['years'][year][
                                            'variables'][cur_variable][
                                                'concept'] = variable_list[
                                                    cur_variable]['concept']
                                    if 'predicateType' in variable_list[
                                            cur_variable]:
                                        dataset_dict[dataset]['years'][year][
                                            'variables'][cur_variable][
                                                'predicateType'] = variable_list[
                                                    cur_variable][
                                                        'predicateType']
                        else:
                            if 'variables_missing' not in error_dict:
                                error_dict['variables_missing'] = []
                            error_dict['variables_missing'].append(temp_url)
                            print(temp_url, 'has no variables section')
            else:
                cache_file = os.path.join(cache_path, dataset, year,
                                          'variables.json')
                temp_url = generate_url_variables(dataset)
                if os.path.isfile(cache_file):
                    variable_list = json.load(open(cache_file, 'r'))
                else:
                    variable_list = request_url_json(temp_url)
                if 'http_err_code' not in variable_list:
                    if len(variable_list) != 1:
                        if 'groups_extra_keys' not in error_dict:
                            error_dict['groups_extra_keys'] = []
                        error_dict['groups_extra_keys'].append(temp_url)
                        print(temp_url, 'has unexpected number of keys ')
                    if 'variables' in variable_list:
                        variable_list = variable_list['variables']
                        dataset_dict[dataset]['variables'] = {}
                        for cur_variable in variable_list:
                            if 'group' not in variable_list[
                                    cur_variable] or variable_list[
                                        cur_variable]['group'] == 'N/A':
                                dataset_dict[dataset]['variables'][
                                    cur_variable] = {}
                                dataset_dict[dataset]['variables'][
                                    cur_variable]['label'] = variable_list[
                                        cur_variable]['label']
                                if 'concept' in variable_list[cur_variable]:
                                    dataset_dict[dataset]['variables'][
                                        cur_variable][
                                            'concept'] = variable_list[
                                                cur_variable]['concept']
                                if 'predicateType' in variable_list[
                                        cur_variable]:
                                    dataset_dict[dataset]['variables'][
                                        cur_variable][
                                            'predicateType'] = variable_list[
                                                cur_variable]['predicateType']
                    else:
                        if 'variables_missing' not in error_dict:
                            error_dict['variables_missing'] = []
                        error_dict['variables_missing'].append(temp_url)
                        print(temp_url, 'has no variables section')

        with open(os.path.join(store_path, 'dataset_non_group_variables.json'),
                  'w') as fp:
            json.dump(dataset_dict, fp, indent=2)
        if error_dict:
            with open(
                    os.path.join(store_path,
                                 'errors_dataset_non_group_variables.json'),
                    'w') as fp:
                json.dump(error_dict, fp, indent=2)

    return dataset_dict


def compile_dataset_based_map(store_path: str = CONFIG_PATH_,
                              force_fetch: bool = False) -> dict:
    # compile_year_map(store_path)
    # compile_groups_map(store_path, force_fetch)
    # compile_geography_map(store_path, force_fetch)
    dataset_dict = compile_non_group_variables_map(store_path, force_fetch)
    # dataset_dict = compile_group_variables_map(store_path, force_fetch)

    return dataset_dict


def compile_dataset_group_map(store_path: str = CONFIG_PATH_,
                              force_fetch: bool = False) -> dict:
    """Extracts list of groups available in each dataset.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset as key and list of available groups as value.
  """
    if os.path.isfile(os.path.join(
            store_path, 'dataset_groups_list.json')) and not force_fetch:
        out_dict = json.load(
            open(os.path.join(store_path, 'dataset_groups_list.json'), 'r'))
    else:
        dataset_dict = compile_non_group_variables_map(store_path, force_fetch)
        out_dict = {}
        for dataset_id, dataset_detail in dataset_dict.items():
            out_dict[dataset_id] = []
            if 'years' in dataset_detail:
                for year in dataset_detail['years']:
                    for group_id in dataset_detail['years'][year]['groups']:
                        if group_id not in out_dict[dataset_id]:
                            out_dict[dataset_id].append(group_id)
            else:
                for group_id in dataset_dict['groups']:
                    if group_id not in out_dict[dataset_id]:
                        out_dict[dataset_id].append(group_id)

        with open(os.path.join(store_path, 'dataset_groups_list.json'),
                  'w') as fp:
            json.dump(out_dict, fp, indent=2)

    return out_dict


def compile_dataset_group_years_map(store_path: str = CONFIG_PATH_,
                                    force_fetch: bool = False) -> dict:
    """Extracts list of available years for dataset and each group available in each dataset.

    Args:
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset as key and list of available years, list of available years for each group as value.
  """
    if os.path.isfile(os.path.join(
            store_path, 'dataset_years_groups.json')) and not force_fetch:
        out_dict = json.load(
            open(os.path.join(store_path, 'dataset_years_groups.json'), 'r'))
    else:
        dataset_dict = compile_non_group_variables_map(store_path, force_fetch)
        out_dict = {}
        for dataset_id, dataset_detail in dataset_dict.items():
            out_dict[dataset_id] = {}
            out_dict[dataset_id]['years'] = []
            out_dict[dataset_id]['groups'] = {}
            if 'years' in dataset_detail:
                for year in dataset_detail['years']:
                    out_dict[dataset_id]['years'].append(year)
                    for group_id in dataset_detail['years'][year]['groups']:
                        if group_id not in out_dict[dataset_id]['groups']:
                            out_dict[dataset_id]['groups'][group_id] = []
                        out_dict[dataset_id]['groups'][group_id].append(year)
            else:
                for group_id in dataset_detail['groups']:
                    if group_id not in out_dict[dataset_id]['groups']:
                        out_dict[dataset_id]['groups'][group_id] = []
                    out_dict[dataset_id]['groups'][group_id].append(year)

        with open(os.path.join(store_path, 'dataset_years_groups.json'),
                  'w') as fp:
            json.dump(out_dict, fp, indent=2)

    return out_dict


def get_variables_name(dataset: str,
                       table_id: str,
                       year: str,
                       store_path: str = CONFIG_PATH_,
                       force_fetch: bool = False) -> dict:
    """Extracts mapping of variable id to it's string name.

    Args:
      dataset: Dataset of US census(e.g. acs/acs5/subject).
      table_id: ID of the US census group that needs to be downloaded.
      year: Year for which the variable lookup is required.
      store_path: Path where the config is to be stored.
      force_fetch: Boolean value to force API config update rather than using the cache.

    Returns:
      Dict object with dataset as key and list of available years, list of available years for each group as value.
  """
    if year:
        ret_path = os.path.join(store_path, 'api_cache', dataset, year,
                                f'{table_id.upper()}.json')
    else:
        ret_path = os.path.join(store_path, 'api_cache', dataset,
                                f'{table_id.upper()}.json')

    if os.path.isfile(ret_path):
        return json.load(open(ret_path))
    else:
        fetch_dataset_config_cache('group_variables', force_fetch=force_fetch)
        if os.path.isfile(ret_path):
            return json.load(open(ret_path))
        else:
            return None


def main(argv):
    compile_dataset_based_map(force_fetch=FLAGS.force_fetch_config)
    fetch_dataset_config_cache('group_variables',
                               force_fetch=FLAGS.force_fetch_config)
    compile_dataset_group_map(force_fetch=FLAGS.force_fetch_config)
    compile_dataset_group_years_map(force_fetch=FLAGS.force_fetch_config)


if __name__ == '__main__':
    app.run(main)

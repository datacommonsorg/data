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
Function library to extract usable form of API configuration.
"""

import base64
import itertools
from absl import app
from absl import flags

from census_api_config_fetcher import *

FLAGS = flags.FLAGS

flags.DEFINE_boolean('available_datasets', False,
                     'Print list of available datasets.')
flags.DEFINE_boolean('available_years', False,
                     'Print list of available years for given dataset.')
flags.DEFINE_boolean('available_groups', False,
                     'Print list of available groups for given dataset.')
flags.DEFINE_boolean(
    'available_years_group', False,
    'Print list of available years for given group and dataset.')
flags.DEFINE_boolean(
    'available_summary_levels', False,
    'Print list of available summary levels for given dataset.')

flags.DEFINE_boolean('summary_level_config', False,
                     'Create summary level config file for future use.')
flags.DEFINE_string(
    'dataset', 'acs/acs5/subject',
    'The dataset from which to download data. Default: acs/acs5/subject')
flags.DEFINE_string('table_id', None,
                    'Table ID of the subject table to be downloaded e.g.S0101')
flags.DEFINE_string('q_variable', 'S0101_C01_001E',
                    'Variable to be used to compile list of all required IDs.')
flags.DEFINE_string(
    'api_key', None,
    'API key sourced from census via https://api.census.gov/data/key_signup.html'
)


def get_list_datasets(force_fetch: bool = False) -> list:
    """Extracts the list of datasets present in the API.

        Args:
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            List of datasets available in the API.
    """
    d = compile_year_map(force_fetch=force_fetch)
    return sorted(list(d.keys()))


def get_dataset_years(dataset: str, force_fetch: bool = False) -> list:
    """Extracts the list of available years for a given dataset present in the API.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            List of available years in a dataset in the API.
    """
    d = compile_dataset_group_years_map(force_fetch=force_fetch)
    if dataset in d:
        return sorted(d[dataset]['years'])
    else:
        return None


def get_dataset_groups(dataset: str, force_fetch: bool = False) -> list:
    """Extracts the list of available groups/tables for a given dataset present in the API.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            List of available groups in a dataset available in the API.
    """
    d = compile_dataset_group_map(force_fetch=force_fetch)
    if dataset in d:
        return sorted(d[dataset])
    else:
        return None


def get_dataset_groups_years(dataset: str,
                             group: str,
                             force_fetch: bool = False) -> list:
    """Extracts the list of available years given a group for a given dataset present in the API.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            group: ID of the US census group that needs to be downloaded.
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            List of available years for given dataset, group available in the API.
    """
    d = compile_dataset_group_years_map(force_fetch=force_fetch)
    if dataset in d and group in d[dataset]['groups']:
        return sorted(d[dataset]['groups'][group])
    else:
        return None


def get_dataset_summary_levels(dataset: str, force_fetch: bool = False) -> list:
    """Extracts the list of available summary levels for a given dataset present in the API.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            List of available summary levels given a dataset available in the API.
    """
    ret_list = []
    dataset_geo = compile_geography_map(force_fetch=force_fetch)
    if dataset in dataset_geo:
        d = dataset_geo[dataset]['years']
        for y in d:
            if 'geos' in d[y]:
                for s in d[y]['geos']['summary_levels']:
                    if s not in ret_list:
                        ret_list.append(s)
        return sorted(ret_list)
    else:
        return None


def get_identifier(dataset: str, year: str, force_fetch: bool = False) -> str:
    """Extracts the identifier for a given dataset present in the API.(Useful for file name creation)

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            year: Year for which to extract the identifier.
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            Idendifier string given a dataset, year available in the API.
    """
    d = compile_groups_map(force_fetch=force_fetch)
    if dataset in d:
        if 'years' in d[dataset] and year in d[dataset]['years']:
            return d[dataset]['years'][year]['identifier']
        else:
            return None
    else:
        return None


def get_yearwise_variable_column_map(dataset: str,
                                     table_id: str,
                                     year_list: list,
                                     force_fetch: bool = False) -> dict:
    """Extracts the variable ID to name mapping for a given dataset, table_id, yearlist present in the API.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            table_id: ID of the US census group that needs to be downloaded.
            year_list: List of years for which to extract the variable information.
            force_fetch: Boolean value to force API config update rather than using the cache.

        Returns:
            Dictionary with mapping from variable ID to variable name.
    """
    ret_dict = {}
    for year in year_list:
        ret_dict[(year)] = {}
        temp_dict = get_variables_name(dataset,
                                       table_id,
                                       year,
                                       force_fetch=force_fetch)
        if temp_dict:
            for var in temp_dict['variables']:
                ret_dict[year][var] = temp_dict['variables'][var]['label']
    return ret_dict


def url_add_api_key(url_dict: dict, api_key: str) -> str:
    """Attaches the api key to a given url

        Args:
            url_dict: Dict with the request url and it's relevant metadata.
            api_key: User's API key provided by US Census.
        
        Returns:
            URL with attached API key information.
    """
    return (url_dict['url'] + f'&key={api_key}').replace(' ', '%20')


def find_summary_level(s_level_dict: dict, geo_str: str) -> str:
    for s_level in s_level_dict:
        if s_level_dict[s_level]['str'] == geo_str:
            return s_level
    return ''


def is_required_hierarchical(req_list: list, geo_config_year: dict) -> bool:
    last_geo = req_list[-1]
    last_geo_id = find_summary_level(geo_config_year['summary_levels'],
                                     last_geo)
    return (req_list[:-1] == geo_config_year['summary_levels'][last_geo_id]
            ['geo_filters'])
    # NOTE: alternative implimentation could be(would need changes to compile_hierarchy_geo_str_list):
    # is_hierarchy = True
    # for cur_req in req_list[:-1]:
    #     if cur_req not in geo_config_year['summary_levels'][last_geo_id]['geo_filters']:
    #         is_hierarchy = False
    # return is_hierarchy


def compile_hierarchy_req_str_list(geo_list: dict, str_list: list) -> list:
    """Recursively go through geo config to get list ids and combine with their str.
        An example of hierarchial required geo ids would be:
        county subdivision:
        {
            '<state id>': {
                '<county id>': {
                    '<county subdivision id>': '<county subdivision name>'
                }

            }
        }
        Args:
            geo_list: Dict of geo ids required for a particular summary level.
            str_list: List API query prefix string for each level of dict.
        
        Returns:
            List of required geo strings to be added to API call.
    """
    ret_list = []
    for k, v in geo_list.items():
        if isinstance(v, dict):
            new_list = str_list.copy()
            new_list[1] = f'{str_list[0]}{k}{str_list[1]}'
            ret_list.extend(compile_hierarchy_req_str_list(v, new_list[1:]))
        else:
            ret_list.append(f'{str_list[0]}{k}')
    return ret_list


def geo_get_all_id(geo_list: dict, geo_str: str) -> list:
    ret_list = []
    for k, v in geo_list.items():
        if isinstance(v, dict):
            ret_list.extend(geo_get_all_id(v, geo_str))
        else:
            ret_list.append(f'{geo_str}{k}')
    return ret_list


def compile_non_hierarchy_req_str_list(all_geo_list: dict,
                                       req_geos: dict) -> list:
    """Fetches a list of all geo ids present for a given list of summary level and creates all combinations of the two.
        
        Args:
            all_geo_list: Dict with list of geos ids previously fetched.
            req_geos: Dict with list of all required geos with it's dependent geos.
        
        Returns:
            List of required geo strings to be added to API call.
    """
    id_list = []
    for cur_geo in req_geos:
        cur_id_list = geo_get_all_id(all_geo_list[cur_geo], req_geos[cur_geo])
        id_list.append(cur_id_list)
    tuple_list = list(itertools.product(*id_list))
    ret_list = [''.join(s) for s in tuple_list]

    return ret_list


# NOTE: code assumes that all fields appear in sequence and dependent geo levels are already present if list
def get_str_list_required(geo_config_year: dir, s_level: str) -> list:
    """Compiles a list of all required geo id strings for a given summary level.

        Args:
            geo_config_year: Compiled geo configurations from API data.
                NOTE: code assumes that all fields in required section appear in sequence 
                        and dependent geo levels are already present in the list.
            s_level: Summary level id to be queried.
        
        Returns:
            List of required geo strings to be attached to API call.
    """
    req_list = geo_config_year['summary_levels'][s_level]['requires'].copy()
    if len(req_list) > 0:
        str_list = []
        str_list.append('&in=' + req_list[0] + ':')
        if len(req_list) > 1:
            for s in req_list[1:]:
                str_list.append(' ' + s + ':')
        is_hierarchy = is_required_hierarchical(req_list, geo_config_year)
        if is_hierarchy:
            req_str_list = compile_hierarchy_req_str_list(
                geo_config_year['required_geo_lists'][req_list[-1]], str_list)
        else:
            req_dict = {}
            for i, r in enumerate(req_list):
                req_dict[r] = str_list[i]
            req_str_list = compile_non_hierarchy_req_str_list(
                geo_config_year['required_geo_lists'], req_dict)
    else:
        req_str_list = ['']

    return list(set(req_str_list))


def _get_config_temp_filename(year: str, geo_str: str, req_str: str) -> str:
    s = f"{year}__{geo_str}__{req_str}"
    s = base64.b64encode(s.encode()).decode("utf-8", errors='ignore')
    return f"{s}.json"


def _update_geo_list(json_resp: list, geo_config: dict, year: str, geo_str: str,
                     s_level: str):
    if geo_str not in geo_config[year]['required_geo_lists']:
        geo_config[year]['required_geo_lists'][geo_str] = {}

    name_i = json_resp[0].index('NAME')
    geo_i = json_resp[0].index(geo_str)
    filter_i = []

    for filter in geo_config[year]['summary_levels'][s_level]['geo_filters']:
        filter_i.append(json_resp[0].index(filter))
    for t in json_resp[1:]:
        d = geo_config[year]['required_geo_lists'][geo_str]
        for req_i in filter_i:
            if t[req_i] not in d:
                d[t[req_i]] = {}
            d = d[t[req_i]]
        d[t[geo_i]] = t[name_i]


def get_yearwise_required_geos(dataset: str,
                               geo_config: dict,
                               q_variable: str,
                               api_key: str = '',
                               force_fetch=False) -> dict:
    """Compiles a list of all the available geo IDs for list of summary levels needed to to make API calls.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            geo_config: Dict containing the list of summary levels and their dependencies.
            q_variable: Variable to be used to find list of available geo IDs.
            api_key: User's API key provided by US Census.
            force_fetch: Boolean value to force recomputation of API config of US census.
        
        Returns:
            Dict containing the list of summary levels and their dependencies along with a list of required geo IDs.
    """
    output_path = os.path.expanduser(CONFIG_PATH_)
    output_path = os.path.join(output_path, 'api_cache', dataset,
                               'required_geos')
    status_path = os.path.join(output_path, 'download_status.json')
    rate_params = {}
    rate_params['max_parallel_req'] = 50
    rate_params['limit_per_host'] = 20
    rate_params['req_per_unit_time'] = 10
    rate_params['unit_time'] = 1
    for year in geo_config:
        if 'required_geo_lists' not in geo_config[year]:
            geo_config[year]['required_geo_lists'] = {}
        for geo_str in geo_config[year]['required_geos']:
            s_level = find_summary_level(geo_config[year]['summary_levels'],
                                         geo_str)
            if s_level:
                if force_fetch or geo_str not in geo_config[year][
                        'required_geo_lists']:
                    req_str_list = get_str_list_required(
                        geo_config[year], s_level)
                    url_list = []
                    for req_str in req_str_list:
                        temp_dict = {}
                        temp_dict[
                            'url'] = f"https://api.census.gov/data/{year}/{dataset}?get=NAME,{q_variable}&for={geo_str}:*{req_str}"
                        temp_dict['store_path'] = os.path.join(
                            output_path,
                            _get_config_temp_filename(year, geo_str, req_str))
                        temp_dict['status'] = 'pending'
                        temp_dict['force_fetch'] = force_fetch
                        url_list.append(temp_dict)

                    url_list = sync_status_list([], url_list)
                    with open(status_path, 'w') as fp:
                        json.dump(url_list, fp, indent=2)

                    failed_ctr = download_url_list_iterations(
                        url_list,
                        url_add_api_key,
                        api_key,
                        async_save_resp_json,
                        rate_params=rate_params)
                    with open(status_path, 'w') as fp:
                        json.dump(url_list, fp, indent=2)

                    if failed_ctr > 0:
                        download_url_list_iterations(url_list,
                                                     url_add_api_key,
                                                     api_key,
                                                     async_save_resp_json,
                                                     rate_params=rate_params)
                        with open(status_path, 'w') as fp:
                            json.dump(url_list, fp, indent=2)

                    for cur_url in url_list:
                        dir, filename = os.path.split(cur_url['store_path'])
                        s = base64.b64decode(filename.encode()).decode(
                            "utf-8", errors='ignore')
                        arg = s.split('__')
                        temp = json.load(open(cur_url['store_path']))
                        _update_geo_list(temp, geo_config, arg[0], arg[1],
                                         s_level)
            else:
                print('Warning:', geo_str, 'not found')
    return geo_config


def get_summary_level_config(dataset: str,
                             q_variable: str,
                             api_key: str = '',
                             force_fetch: bool = False) -> dict:
    """Computes a list of summary levels available, their dependencies and list of required geo IDs for API calls.

        Args:
            dataset: Dataset of US census(e.g. acs/acs5/subject).
            q_variable: Variable to be used to find list of available geo IDs.
            api_key: User's API key provided by US Census.
            force_fetch: Boolean value to force recomputation of API config of US census.
        
        Returns:
            Dict containing the list of summary levels and their dependencies along with a list of required geo IDs.
    """
    output_path = os.path.expanduser(CONFIG_PATH_)
    output_path = os.path.join(output_path, 'api_cache', dataset)
    basic_cache_path = os.path.join(output_path,
                                    'yearwise_summary_level_config_basic.json')
    cache_path = os.path.join(output_path, 'yearwise_summary_level_config.json')

    if not force_fetch and os.path.isfile(basic_cache_path):
        geo_config = json.load(open(basic_cache_path, 'r'))
    else:
        geo_config = {}
        dataset_geo = compile_geography_map(force_fetch=force_fetch)
        if dataset in dataset_geo:
            d = dataset_geo[dataset]['years']
            for y in d:
                if 'geos' in d[y]:
                    geo_config[y] = d[y]['geos']
            os.makedirs(os.path.dirname(basic_cache_path), exist_ok=True)
            with open(basic_cache_path, 'w') as fp:
                json.dump(geo_config, fp, indent=2)
        else:
            print('Error: Dataset', dataset, 'not found')
            return {}
    if not force_fetch and os.path.isfile(cache_path):
        geo_config = json.load(open(cache_path, 'r'))
    else:
        geo_config = get_yearwise_required_geos(dataset,
                                                geo_config,
                                                q_variable,
                                                api_key,
                                                force_fetch=force_fetch)
        with open(cache_path, 'w') as fp:
            json.dump(geo_config, fp, indent=2)

    return geo_config


def main(argv):
    if FLAGS.available_datasets:
        print(
            json.dumps(get_list_datasets(force_fetch=FLAGS.force_fetch_config),
                       indent=2))
    if FLAGS.available_years:
        print(FLAGS.dataset, 'is available for years:')
        print(
            json.dumps(get_dataset_years(FLAGS.dataset,
                                         force_fetch=FLAGS.force_fetch_config),
                       indent=2))
    if FLAGS.available_groups:
        print(FLAGS.dataset, 'has following tables available:')
        print(
            json.dumps(get_dataset_groups(FLAGS.dataset,
                                          force_fetch=FLAGS.force_fetch_config),
                       indent=2))
    if FLAGS.available_years_group:
        if not FLAGS.table_id:
            print('Error: Table ID required to get year list.')
            return
        print(FLAGS.table_id, 'in', FLAGS.dataset,
              'has following years available:')
        print(
            json.dumps(get_dataset_groups_years(
                FLAGS.dataset,
                FLAGS.table_id,
                force_fetch=FLAGS.force_fetch_config),
                       indent=2))
    if FLAGS.available_summary_levels:
        print(FLAGS.dataset, 'has following summary levels available:')
        print(
            json.dumps(get_dataset_summary_levels(
                FLAGS.dataset, force_fetch=FLAGS.force_fetch_config),
                       indent=2))

    if FLAGS.summary_level_config:
        get_summary_level_config(FLAGS.dataset, FLAGS.q_variable, FLAGS.api_key,
                                 FLAGS.force_fetch_config)


if __name__ == '__main__':
    app.run(main)

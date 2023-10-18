# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions."""
import os
import sys
import csv
import pandas as pd

from geo_id_resolver import convert_to_place_dcid

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid


def create_csv_mcf(csv_files: list, cleaned_csv_path: str, config: dict,
                   output_cols: list, write_output_csv) -> list:
    """Creates StatVars according to values in csv_files and write the final
    output to a csv.

    Args:
        csv_files: A list of CSV file paths to process.
        cleaned_csv_path: Path of the final cleaned CSV file.
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/table2/config.json for
          an example.

    Returns:
        A list of statvars.
    """
    statvars = []
    with open(cleaned_csv_path, 'w', encoding='utf-8') as output_f:
        writer = csv.DictWriter(output_f, fieldnames=output_cols)
        writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8') as input_f:
                reader = csv.DictReader(input_f)
                statvars_list = write_output_csv(reader, writer, config)
                statvars.extend(statvars_list)
    return statvars


def update_statvars(statvar_list: list, key_value: dict):
    """Given a list of statvars and a key:value pair, this functions adds the
    key value pair to each statvar.
    """
    for d in statvar_list:
        d.update(key_value)


def get_dpv(statvar: dict, config: dict) -> list:
    """A function that goes through the statvar dict and the config and returns
    a list of properties to ignore when generating the dcid.

    Args:
        statvar: A dictionary of prop:values of the statvar
        config: A dict which maps constraint props to the statvar based on
          values in the CSV. See scripts/fbi/hate_crime/config.json for
          an example. The 'dpv' key is used to identify dependent properties.

    Returns:
        A list of properties to ignore when generating the dcid
    """
    ignore_props = []
    for spec in config['dpv']:
        if spec['cprop'] in statvar:
            dpv_prop = spec['dpv']['prop']
            dpv_val = spec['dpv']['val']
            if dpv_val == statvar.get(dpv_prop, None):
                ignore_props.append(dpv_prop)
    return ignore_props


def create_mcf(stat_vars: list, mcf_file_path: str):
    """Writes all statvars to a .mcf file."""
    dcid_set = set()
    with open(mcf_file_path, 'w', encoding='utf-8') as f:
        for sv in stat_vars:
            dcid = sv['Node']
            if dcid in dcid_set:
                continue
            dcid_set.add(dcid)
            statvar_mcf_list = [f'Node: dcid:{dcid}']
            for p, v in sv.items():
                if p != 'Node':
                    statvar_mcf_list.append(f'{p}: dcs:{v}')
            statvar_mcf = '\n'.join(statvar_mcf_list) + '\n\n'
            f.write(statvar_mcf)


def update_statvar_dcids(statvar_list: list, config: dict):
    """Given a list of statvars, generates the dcid for each statvar after
    accounting for dependent PVs.
    """
    for d in statvar_list:
        ignore_props = get_dpv(d, config)
        dcid = get_statvar_dcid(d, ignore_props=ignore_props)
        d['Node'] = dcid


def agg_hate_crime_df(df: pd.DataFrame,
                      groupby_cols: list = None,
                      agg_dict: dict = None,
                      multi_index: bool = False) -> pd.DataFrame:
    """Utility function where different aggregations of the a dataframe can be
    computed. By default aggregations are done by year, place and state.

    Args:
        df: dataframe to aggregate on.
        groupby_cols: list of additional columns to be used for group by.
          Default aggregation is done with columns like year, place and state,
          additional columns based on which groupby needs to be done can be
          specified as a list. Defaults to
          ['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'].
        agg_dict: dictionary where the key is the column to aggregate on and
          it's value is the aggregation method. Defaults to {}.
        multi_index: Flag if set returns multi-index dataframe.

    Returns:
        The aggregated dataframe after calling pandas.DataFrame.groupby().
        Returns the original dataframe if agg_dict is None.

    Example:
        To aggregate the incident counts by year, place and state, use
        agg_hate_crime_df(df, groupby_cols=[], agg_dict={'INCIDENT_ID':'count'})
    """
    if groupby_cols is None:
        groupby_cols = ['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR']
    if agg_dict is None:
        agg_dict = {}
    agg_tuple = list(agg_dict.items())[-1]
    return df.groupby(by=groupby_cols,
                      as_index=multi_index).agg(Value=agg_tuple)


def flatten_by_column(df: pd.DataFrame,
                      column_name: str,
                      sep: str = ';') -> pd.DataFrame:
    """Transforms each element which contains multiple values to a row,
    replicating index values

    Args:
        df: A pandas dataframe to flatten
        column_name: The column where elements contain multiple values
        sep: The separator in elements with multiple values

    Returns:
        A dataframe after calling pandas.DataFrame.explode().
    """
    df_copy = df.copy()
    df_copy[column_name] = df_copy[column_name].str.split(sep)
    return df_copy.explode(column_name)


def make_time_place_aggregation(dataframe,
                                groupby_cols=None,
                                agg_dict=None,
                                multi_index=False,
                                country=True):
    """Utility function where different aggregations of the hate crime dataset
    is done, by year and geo type (country, state, and city).

    Args:
        dataframe: dataframe to aggregate on.
        groupby_cols: list of additional columns to be used for group by.
          Default aggregation is done with columns like year, place and state,
          additional columns based on which groupby needs to be done can be
          specified as a list. Defaults to [].
        agg_dict: dictionary where the key is the column to aggregate on and
          it's value is the aggregation method. Defaults to {}
        multi_index: Flag if set returns multi-index dataframe.
        country: Set to true to generate country level aggregations

    Returns:
        A list whose elements are dataframes aggregated at a country, state,
        and city level.
    """
    if groupby_cols is None:
        groupby_cols = []
    if agg_dict is None:
        agg_dict = {}
    agg_list = []

    if country == True:
        # Year + Country
        agg_country = agg_hate_crime_df(dataframe,
                                        groupby_cols=(['DATA_YEAR'] +
                                                      groupby_cols),
                                        agg_dict=agg_dict,
                                        multi_index=multi_index)
        agg_country['Place'] = 'country/USA'
        agg_list.append(agg_country)

    # Year + State
    agg_state = agg_hate_crime_df(dataframe,
                                  groupby_cols=(['DATA_YEAR', 'STATE_ABBR'] +
                                                groupby_cols),
                                  agg_dict=agg_dict,
                                  multi_index=multi_index)
    agg_state['Place'] = agg_state.apply(
        lambda row: convert_to_place_dcid(row['STATE_ABBR']), axis=1)
    agg_state.drop(columns=['STATE_ABBR'], inplace=True)
    agg_list.append(agg_state)

    # Year + City
    city_df = dataframe[dataframe['AGENCY_TYPE_NAME'] == 'City']
    agg_city = agg_hate_crime_df(
        city_df,
        groupby_cols=(['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] +
                      groupby_cols),
        agg_dict=agg_dict,
        multi_index=multi_index)
    agg_city['Place'] = agg_city.apply(lambda row: convert_to_place_dcid(
        row['STATE_ABBR'], row['PUB_AGENCY_NAME'], 'City'),
                                       axis=1)
    agg_city.drop(columns=['PUB_AGENCY_NAME', 'STATE_ABBR'], inplace=True)
    agg_list.append(agg_city)

    return agg_list

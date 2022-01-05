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
"""Utility functions for the FBI Hate Crime import."""

import pandas as pd
from geo_id_resolver import state_to_dcid, county_to_dcid, city_to_dcid


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
    return df.groupby(by=groupby_cols, as_index=multi_index).agg(Value=agg_tuple)


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
                                country=False):
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
                                        groupby_cols=(['DATA_YEAR'] + groupby_cols),
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
        lambda row: state_to_dcid(row['STATE_ABBR']), axis=1)
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
    agg_city['Place'] = agg_city.apply(
        lambda row: city_to_dcid(row['STATE_ABBR'], row['PUB_AGENCY_NAME']),
        axis=1)
    agg_city.drop(columns=['PUB_AGENCY_NAME', 'STATE_ABBR'], inplace=True)
    agg_list.append(agg_city)

    return agg_list

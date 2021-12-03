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

import pandas as pd

def agg_hate_crime_df(df, groupby_cols=['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'], agg_dict={}, multi_index=False):
    """
    Utiltiy function where different aggregations of the hate crime dataset is done, by specific how specific columns
    needs to be aggregated. By default aggregations are done by year, place and state.
    
    Params:
    - df (pandas.DataFrame): raw dataframe of fbi_hatecrimes csv file
    - groupby_cols (list): list of additional columns to be used for group by. Default aggregation is done with
    columns like year, place and state, additional columns based on which groupby needs to be done can be specified 
    as a list. (default: [])
    - agg_dict (dictionary): dictionary containing which column is aggregated by which aggregation method.(default: {})
    - multi_index (bool): Flag if set returns multi-index dataframe (default: False)
    
    Output:
    - agg_df (pandas.DataFrame): output will be the aggregated dataframe
    
    Example:
    To aggregate the incident counts by year, place and state, the function call will be:
    agg_hate_crime_df(df, groupby_cols=[], agg_dict={'INCIDENT_ID':'count'})
    """
    #columns_to_groupby = ['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] + groupby_cols
    
    if not agg_dict:
        print("ERROR: Atleast one column with an aggregation method is required, the given call has an empty agg_dict param. No aggregations are attempted.")
        return df
    else:
        return df.groupby(by=groupby_cols, as_index=multi_index).agg(agg_dict)

def flatten_by_column(df, column_name, sep=";"):
    df_copy = df.copy()
    df_copy[column_name] = df_copy[column_name].str.split(sep)
    return df_copy.explode(column_name)

def make_time_place_aggregation(dataframe, groupby_cols=[], agg_dict={}, multi_index=False):
    """
    Utiltiy function where different aggregations of the hate crime dataset is done, by specific how specific columns
    needs to be aggregated. By default aggregations are done by year, place and state.
    
    Params:
    - dataframe (pandas.DataFrame): raw dataframe of fbi_hatecrimes csv file
    - groupby_cols (list): list of additional columns to be used for group by. Default aggregation is done with
    columns like year, place and state, additional columns based on which groupby needs to be done can be specified 
    as a list. (default: [])
    - agg_dict (dictionary): dictionary containing which column is aggregated by which aggregation method.(default: {})
    - multi_index (bool): Flag if set returns multi-index dataframe (default: False)
    
    Output:
    - agg_df (pandas.DataFrame): output will be the aggregated dataframe
    
    Example:
    To aggregate the incident counts by year, place and state, the function call will be:
    agg_hate_crime_df(df, groupby_cols=[], agg_dict={'INCIDENT_ID':'count'})
    """
    ## Year + Country
    agg_country = agg_hate_crime_df(dataframe, groupby_cols=(['DATA_YEAR'] + groupby_cols), agg_dict=agg_dict, multi_index=multi_index)
    agg_country['STATE_ABBR'] = 'USA'
    
    ## Year + State
    agg_state = agg_hate_crime_df(dataframe, groupby_cols=(['DATA_YEAR', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=False)

    ## Year + County
    county_df = dataframe[dataframe['AGENCY_TYPE_NAME'] == 'County']
    county_df['STATE_ABBR'] = county_df['PUB_AGENCY_NAME'] + ' ' + county_df['STATE_ABBR']
    agg_county = agg_hate_crime_df(county_df, groupby_cols=(['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=multi_index)

    ## Year + City
    city_df = dataframe[dataframe['AGENCY_TYPE_NAME'] == 'City']
    city_df['STATE_ABBR'] = city_df['PUB_AGENCY_NAME'] + ' ' + city_df['STATE_ABBR']
    agg_city = agg_hate_crime_df(city_df, groupby_cols=(['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=multi_index)

    return agg_country, agg_state, agg_county, agg_city
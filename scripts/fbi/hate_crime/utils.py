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
    df_f = df.copy()
    df_f[column_name] = df_f[column_name].str.split(sep)
    return df_f.explode(column_name)

def make_time_place_aggregation(df, groupby_cols=[], agg_dict={}, multi_index=False):
    #TODO: Fill this for year, city, county, state
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
    ## Year
    count_incident_by_year = agg_hate_crime_df(df, groupby_cols=(['DATA_YEAR'] + groupby_cols), agg_dict=agg_dict, multi_index=multi_index)
    
    ## City
    count_incident_by_city = agg_hate_crime_df(df[df['AGENCY_TYPE_NAME'] == 'City'], groupby_cols=(['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=multi_index)

    ## State
    count_incident_by_state = agg_hate_crime_df(df, groupby_cols=(['DATA_YEAR', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=False)

    ## County
    count_incident_by_county = agg_hate_crime_df(df[df['AGENCY_TYPE_NAME'] == 'County'], groupby_cols=(['DATA_YEAR', 'PUB_AGENCY_NAME', 'STATE_ABBR'] + groupby_cols), agg_dict=agg_dict, multi_index=False)

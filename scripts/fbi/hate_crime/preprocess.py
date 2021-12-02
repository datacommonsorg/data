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

import os
import sys
import pandas as pd
import json
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(
    _SCRIPT_PATH, '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

YEAR_INDEX = 0

INPUT_COLUMNS = ['INCIDENT_ID', 'DATA_YEAR', 'OFFENDER_RACE', 'OFFENDER_ETHNICITY',
       'OFFENSE_NAME', 'LOCATION_NAME', 'BIAS_DESC', 
       'VICTIM_TYPES', 'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS']

OUTPUT_COLUMNS = [
    'Year', 'StatVar', 'Quantity'
]

map_dict = {
  "Anti-Black or African American": "race",
  "Anti-White": "race",
  "Anti-Native Hawaiian or Other Pacific Islander": "race",
  "Anti-Arab": "race",
  "Anti-Asian": "race",
  "Anti-American Indian or Alaska Native": "race",
  "Anti-Other Race/Ethnicity/Ancestry": "race",
  "Anti-Multiple Races, Group": "race",
  "Anti-Protestant": "religion",
  "Anti-Other Religion": "religion",
  "Anti-Jewish": "religion",
  "Anti-Islamic (Muslim)": "religion",
  "Anti-Jehovah's Witness": "religion",
  "Anti-Mormon": "religion",
  "Anti-Buddhist": "religion",
  "Anti-Sikh": "religion",
  "Anti-Other Christian": "religion",
  "Anti-Hindu": "religion",
  "Anti-Catholic": "religion",
  "Anti-Eastern Orthodox (Russian, Greek, Other)": "religion",
  "Anti-Atheism/Agnosticism": "religion",
  "Anti-Multiple Religions, Group": "religion",
  "Anti-Heterosexual": "sexualOrientation",
  "Anti-Lesbian (Female)": "sexualOrientation",
  "Anti-Lesbian, Gay, Bisexual, or Transgender (Mixed Group)": "sexualOrientation",
  "Anti-Bisexual": "sexualOrientation",
  "Anti-Gay (Male)": "sexualOrientation",
  "Anti-Hispanic or Latino": "ethnicity",
  "Anti-Physical Disability": "disabilityStatus",
  "Anti-Mental Disability": "disabilityStatus",
  "Anti-Male": "gender",
  "Anti-Female": "gender",
  "Anti-Transgender": "TransgenderAndGenderNonConforming",
  "Anti-Gender Non-Conforming": "TransgenderAndGenderNonConforming",
  "Unknown (offender's motivation not known)": "Unknown"
}

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
  df[column_name] = df[column_name].str.split(sep)
  return df.explode(column_name)

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

def add_bias_type(row):
  if len(row['BIAS_DESC'].split(";")) > 1:
    row['BIAS_AGAINST'] = 'MultipleBias'

  elif row['BIAS_DESC'] in map_dict:
    row['BIAS_AGAINST'] = map_dict[row['BIAS_DESC']]
  
  else:
    print(f"WARNING: No bias type found for {row['BIAS_DESC']}")
  
  return row

def _write_mcf(df, config, mcf_file_name):
    statvar_list = []
    df_copy = df.copy()
    df_copy['StatVar'] = ''
    for idx, row in df_copy.iterrows():
        statvar = {**config['_COMMON_']}
        for col in df_copy.columns:
            if col in config and row[col] in config[col]:
                statvar.update(config[col][row[col]])
            # else:
            #     print("ERROR: Col not in config")

        statvar['populationType'] = row['POPULATION_TYPE']
        statvar['Node'] = get_statvar_dcid(statvar)
        df_copy.at[idx, 'StatVar'] = statvar['Node']
        statvar_list.append(statvar)
    
    dcid_set = set()
    final_mcf = ''
    for sv in statvar_list:
        statvar_mcf_list = []
        dcid = sv['Node']
        if dcid in dcid_set:
            continue
        dcid_set.add(dcid)
        for p, v in sv.items():
            if p != 'Node':
                statvar_mcf_list.append(f'{p}: dcs:{v}')
        statvar_mcf = 'Node: dcid:' + dcid + '\n' + '\n'.join(statvar_mcf_list)
        final_mcf += statvar_mcf + '\n\n'

    with open(mcf_file_name, 'w') as f:
        f.write(final_mcf)

    return df_copy

def _write_cleaned_csv(df, csv_file_name, mode='w'):

    with open(csv_file_name, mode) as output_f:
        writer = csv.DictWriter(output_f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
 
if __name__ == "__main__":
    df = pd.read_csv('source_data/hate_crime.csv', low_memory=False)
    df = df[INPUT_COLUMNS]

    df['BIAS_AGAINST'] = ''
    incident_df = df.apply(add_bias_type, axis=1)
    offense_df = flatten_by_column(incident_df, 'OFFENSE_NAME')

    incident_df['POPULATION_TYPE'] = 'CriminalIncidents'
    offense_df['POPULATION_TYPE'] = 'CriminalActivities'

    with open('config.json', 'r') as f:
        config = json.load(f)

    incident_df = _write_mcf(incident_df, config, 'output.mcf')

    count_incident_by_year = agg_hate_crime_df(incident_df, groupby_cols=['DATA_YEAR', 'StatVar'], agg_dict={'INCIDENT_ID': 'count'}, multi_index=False)
    count_incident_by_year.to_csv('test.csv', index=False)
    
    _write_cleaned_csv(incident_df, 'cleaned.csv')

    # for p in incident_df[incident_df['MULTIPLE_BIAS'] == 'S']['BIAS_DESC'].unique():
    #     print(p)

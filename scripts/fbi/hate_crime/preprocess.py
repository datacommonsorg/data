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
from utils import flatten_by_column, make_time_place_aggregation

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(
    _SCRIPT_PATH, '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

YEAR_INDEX = 0

INPUT_COLUMNS = ['INCIDENT_ID', 'DATA_YEAR', 'OFFENDER_RACE', 'OFFENDER_ETHNICITY',
       'STATE_ABBR', 'OFFENSE_NAME', 'LOCATION_NAME', 'BIAS_DESC', 'AGENCY_TYPE_NAME',
       'VICTIM_TYPES', 'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS', 'PUB_AGENCY_NAME']

OUTPUT_COLUMNS = [
    'Year', 'Place', 'StatVar', 'Quantity'
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

def add_bias_type(row):
  if len(row['BIAS_DESC'].split(";")) > 1:
    row['BIAS_AGAINST'] = 'MultipleBias'

  elif row['BIAS_DESC'] in map_dict:
    row['BIAS_AGAINST'] = map_dict[row['BIAS_DESC']]
  
  else:
    print(f"WARNING: No bias type found for {row['BIAS_DESC']}")
  
  return row

def _write_mcf(df, config, f):
    statvar_list = []
    statvar_dcid_list = []
    df_copy = df.copy()
    for idx, row in df_copy.iterrows():
        statvar = {**config['_COMMON_']}
        for col in df_copy.columns:
            if col in config:
                if row[col] in config[col]:
                    statvar.update(config[col][row[col]])
            # else:
            #     print(f"ERROR: {col} not in config")

        statvar['populationType'] = row['POPULATION_TYPE']
        statvar['Node'] = get_statvar_dcid(statvar)
        statvar_dcid_list.append(statvar['Node'])
        statvar_list.append(statvar)
    
    df_copy['StatVar'] = statvar_dcid_list
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

    f.write(final_mcf)

    return df_copy

def _write_cleaned_csv(df, csv_file_name, mode='w'):

    with open(csv_file_name, mode) as output_f:
        writer = csv.DictWriter(output_f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
 
if __name__ == "__main__":
    df = pd.read_csv('source_data/hate_crime.csv', usecols=INPUT_COLUMNS)

    df['BIAS_AGAINST'] = ''
    incident_df = df.apply(add_bias_type, axis=1)
    offense_df = flatten_by_column(incident_df, 'OFFENSE_NAME')

    incident_df['POPULATION_TYPE'] = 'CriminalIncidents'
    offense_df['POPULATION_TYPE'] = 'CriminalActivities'

    with open('config.json', 'r') as f:
        config = json.load(f)

    with open('output.mcf', 'w') as f:
        incident_df = _write_mcf(incident_df, config, f)
        offense_df = _write_mcf(offense_df, config, f)

    count_incident_by_year, count_incident_by_state, count_incident_by_county, count_incident_by_city = make_time_place_aggregation(incident_df, groupby_cols=['StatVar'], agg_dict={'INCIDENT_ID': 'count'}, multi_index=False)

    final_df = pd.concat([count_incident_by_year, count_incident_by_state, count_incident_by_county, count_incident_by_city])
    print(final_df.head())
    final_df.to_csv('test.csv')

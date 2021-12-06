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
import numpy as np
from utils import flatten_by_column, make_time_place_aggregation

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../util/'))  # for statvar_dcid_generator

from statvar_dcid_generator import get_statvar_dcid

# Columns to input from source data
_INPUT_COLUMNS = [
    'INCIDENT_ID', 'DATA_YEAR', 'OFFENDER_RACE', 'OFFENDER_ETHNICITY',
    'STATE_ABBR', 'OFFENSE_NAME', 'BIAS_DESC', 'AGENCY_TYPE_NAME',
    'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS', 'PUB_AGENCY_NAME'
]

# Columns which do not contribute to a constraint property value in stat var
_NONPV_COLUMNS = [
    'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS', 'INCIDENT_ID', 'DATA_YEAR',
    'STATE_ABBR', 'AGENCY_TYPE_NAME', 'PUB_AGENCY_NAME', 'LOCATION_NAME',
    'BIAS_AGAINST'
]

# A dict to map bias descriptions to their bias category
_BIAS_CATEGORY_MAP = {
    'Anti-Black or African American':
        'race',
    'Anti-White':
        'race',
    'Anti-Native Hawaiian or Other Pacific Islander':
        'race',
    'Anti-Arab':
        'race',
    'Anti-Asian':
        'race',
    'Anti-American Indian or Alaska Native':
        'race',
    'Anti-Other Race/Ethnicity/Ancestry':
        'race',
    'Anti-Multiple Races, Group':
        'race',
    'Anti-Protestant':
        'religion',
    'Anti-Other Religion':
        'religion',
    'Anti-Jewish':
        'religion',
    'Anti-Islamic (Muslim)':
        'religion',
    'Anti-Jehovah\'s Witness':
        'religion',
    'Anti-Mormon':
        'religion',
    'Anti-Buddhist':
        'religion',
    'Anti-Sikh':
        'religion',
    'Anti-Other Christian':
        'religion',
    'Anti-Hindu':
        'religion',
    'Anti-Catholic':
        'religion',
    'Anti-Eastern Orthodox (Russian, Greek, Other)':
        'religion',
    'Anti-Atheism/Agnosticism':
        'religion',
    'Anti-Multiple Religions, Group':
        'religion',
    'Anti-Heterosexual':
        'sexualOrientation',
    'Anti-Lesbian (Female)':
        'sexualOrientation',
    'Anti-Lesbian, Gay, Bisexual, or Transgender (Mixed Group)':
        'sexualOrientation',
    'Anti-Bisexual':
        'sexualOrientation',
    'Anti-Gay (Male)':
        'sexualOrientation',
    'Anti-Hispanic or Latino':
        'ethnicity',
    'Anti-Physical Disability':
        'disabilityStatus',
    'Anti-Mental Disability':
        'disabilityStatus',
    'Anti-Male':
        'gender',
    'Anti-Female':
        'gender',
    'Anti-Transgender':
        'TransgenderOrGenderNonConforming',
    'Anti-Gender Non-Conforming':
        'TransgenderOrGenderNonConforming',
    'Unknown (offender\'s motivation not known)':
        'UnknownBias'
}


def add_bias_type(row):
    if len(row['BIAS_DESC'].split(';')) > 1:
        row['BIAS_AGAINST'] = 'MultipleBias'

    elif row['BIAS_DESC'] in _BIAS_CATEGORY_MAP:
        row['BIAS_AGAINST'] = _BIAS_CATEGORY_MAP[row['BIAS_DESC']]

    else:
        print(f"WARNING: No bias type found for {row['BIAS_DESC']}")

    return row


def _gen_statvar_mcf(df, config, population_type='CriminalIncidents'):
    statvar_list = []
    statvar_dcid_list = []
    df_copy = df.copy()
    for _, row in df_copy.iterrows():
        statvar = {**config['_COMMON_']}
        for col in df_copy.columns:
            if col == 'BIAS_AGAINST':
                statvar['biasMotivation'] = row[col]
            elif col in config:
                if row[col] in config[col]:
                    statvar.update(config[col][row[col]])
        statvar['populationType'] = population_type
        statvar['Node'] = get_statvar_dcid(statvar)
        statvar_dcid_list.append(statvar['Node'])
        statvar_list.append(statvar)
    df_copy['StatVar'] = statvar_dcid_list
    return df_copy, statvar_list


def _write_statvar_mcf(statvar_list, f):
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


def create_aggr(input_df, config, statvar_list, groupby_cols, agg_dict,
                population_type):
    output_df_list = make_time_place_aggregation(input_df,
                                                 groupby_cols=groupby_cols,
                                                 agg_dict=agg_dict,
                                                 multi_index=False)

    output_df_list.pop(2)  # Remove county level data
    output_df_list.pop(0)  # Remove country level data

    for idx in range(len(output_df_list)):
        output_df_list[idx], statvars = _gen_statvar_mcf(
            output_df_list[idx], config, population_type=population_type)
        statvar_list.extend(statvars)

    return output_df_list


def _write_to_csv(df, csv_file_name):
    df['Place'].replace('', np.nan, inplace=True)
    df.dropna(subset=['Place'], inplace=True)
    df.to_csv(csv_file_name, index=False)


if __name__ == '__main__':
    df = pd.read_csv('source_data/hate_crime.csv', usecols=_INPUT_COLUMNS)
    fill_col = df.columns[df.isnull().any()].tolist()
    df[fill_col] = df[fill_col].fillna('Unknown')
    df['BIAS_AGAINST'] = ''
    incident_df = df.apply(add_bias_type, axis=1)

    offense_df = flatten_by_column(incident_df, 'OFFENSE_NAME')

    with open('config.json', 'r') as f:
        config = json.load(f)

    # Incidents by StatVar
    incident_df, statvar_list = _gen_statvar_mcf(
        incident_df, config, population_type='CriminalIncidents')

    incident_by_statvar = make_time_place_aggregation(
        incident_df,
        groupby_cols=['StatVar'],
        agg_dict={'INCIDENT_ID': 'count'},
        multi_index=False)
    incident_by_statvar.pop(2)  # Drop county level
    final_df = pd.concat(incident_by_statvar)
    _write_to_csv(final_df, 'output.csv')

    with open('output.mcf', 'w') as f:
        _write_statvar_mcf(statvar_list, f)

    # Aggregations

    # Total Incidents
    statvar_list = []
    output_df_list = create_aggr(incident_df,
                                 config,
                                 statvar_list,
                                 groupby_cols=[],
                                 agg_dict={'INCIDENT_ID': 'count'},
                                 population_type='CriminalIncidents')
    final_df = pd.concat(output_df_list)
    _write_to_csv(final_df, 'total_incidents.csv')

    # Total Incidents by Bias
    single_bias_incidents = incident_df[incident_df['MULTIPLE_BIAS'] == 'S']
    single_bias_offense = offense_df[offense_df['MULTIPLE_BIAS'] == 'S']

    bias_list = []
    output_df_list = create_aggr(single_bias_incidents, config, statvar_list,
                                 ['BIAS_DESC'], {'INCIDENT_ID': 'count'},
                                 'CriminalIncidents')
    bias_list.extend(output_df_list)

    # Total incidents by bias single/multiple
    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['MULTIPLE_BIAS'], {'INCIDENT_ID': 'count'},
                                 'CriminalIncidents')
    bias_list.extend(output_df_list)

    # Total incidents by bias type
    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['BIAS_AGAINST'], {'INCIDENT_ID': 'count'},
                                 'CriminalIncidents')
    bias_list.extend(output_df_list)

    final_df = pd.concat(bias_list)
    _write_to_csv(final_df, 'bias.csv')

    # Total incidents by offense type
    output_df_list = create_aggr(offense_df, config, statvar_list,
                                 ['OFFENSE_NAME'], {'INCIDENT_ID': 'nunique'},
                                 'CriminalIncidents')

    final_df = pd.concat(output_df_list)
    _write_to_csv(final_df, 'offense.csv')

    offense_list = []

    # Total incidents by single bias and offense
    output_df_list = create_aggr(single_bias_offense, config, statvar_list,
                                 ['BIAS_DESC', 'OFFENSE_NAME'],
                                 {'INCIDENT_ID': 'nunique'},
                                 'CriminalIncidents')
    offense_list.extend(output_df_list)

    # Total incidents by bias single/multiple and offense
    output_df_list = create_aggr(offense_df, config, statvar_list,
                                 ['MULTIPLE_BIAS', 'OFFENSE_NAME'],
                                 {'INCIDENT_ID': 'nunique'},
                                 'CriminalIncidents')
    offense_list.extend(output_df_list)

    # Total incidents by bias type and offense
    output_df_list = create_aggr(offense_df, config, statvar_list,
                                 ['BIAS_AGAINST', 'OFFENSE_NAME'],
                                 {'INCIDENT_ID': 'nunique'},
                                 'CriminalIncidents')
    offense_list.extend(output_df_list)

    final_df = pd.concat(offense_list)
    _write_to_csv(final_df, 'offense_by_bias.csv')

    # Total incidents by offender race
    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_RACE'], {'INCIDENT_ID': 'count'},
                                 'CriminalIncidents')

    final_df = pd.concat(output_df_list)
    _write_to_csv(final_df, 'offender_race.csv')

    # Total incidents by offender ethnicity
    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_ETHNICITY'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')

    final_df = pd.concat(output_df_list)
    _write_to_csv(final_df, 'offender_ethnicity.csv')

    # Total incidents by offender race and bias
    offender_race_list = []
    output_df_list = create_aggr(single_bias_incidents, config, statvar_list,
                                 ['OFFENDER_RACE', 'BIAS_DESC'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_race_list.extend(output_df_list)

    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_RACE', 'MULTIPLE_BIAS'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_race_list.extend(output_df_list)

    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_RACE', 'BIAS_AGAINST'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_race_list.extend(output_df_list)

    final_df = pd.concat(offender_race_list)
    _write_to_csv(final_df, 'offender_race_by_bias.csv')

    # Total incidents by offender ethnicity and bias
    offender_ethnicity_list = []
    output_df_list = create_aggr(single_bias_incidents, config, statvar_list,
                                 ['OFFENDER_ETHNICITY', 'BIAS_DESC'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_ethnicity_list.extend(output_df_list)

    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_ETHNICITY', 'MULTIPLE_BIAS'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_ethnicity_list.extend(output_df_list)

    output_df_list = create_aggr(incident_df, config, statvar_list,
                                 ['OFFENDER_ETHNICITY', 'BIAS_AGAINST'],
                                 {'INCIDENT_ID': 'count'}, 'CriminalIncidents')
    offender_ethnicity_list.extend(output_df_list)

    final_df = pd.concat(offender_ethnicity_list)
    _write_to_csv(final_df, 'offender_ethnicity_by_bias.csv')

    with open('aggregation.mcf', 'w') as f:
        _write_statvar_mcf(statvar_list, f)

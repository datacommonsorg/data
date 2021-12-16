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
"""A script to process FBI Hate Crime data."""

import os
import sys
import json
import pandas as pd
import numpy as np
from utils import flatten_by_column, make_time_place_aggregation

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))

from statvar_dcid_generator import get_statvar_dcid

# Columns to input from source data
_INPUT_COLUMNS = [
    'INCIDENT_ID', 'DATA_YEAR', 'OFFENDER_RACE', 'OFFENDER_ETHNICITY',
    'STATE_ABBR', 'OFFENSE_NAME', 'BIAS_DESC', 'AGENCY_TYPE_NAME',
    'MULTIPLE_OFFENSE', 'MULTIPLE_BIAS', 'PUB_AGENCY_NAME'
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

# A dict to map offenses to categories of crime
_OFFENSE_CATEGORY_MAP = {
    'FalsePretenseOrSwindleOrConfidenceGame': 'CrimeAgainstProperty',
    'MurderAndNonNegligentManslaughter': 'CrimeAgainstPerson',
    'Impersonation': 'CrimeAgainstProperty',
    'SimpleAssault': 'CrimeAgainstPerson',
    'WeaponLawViolations': 'CrimeAgainstSociety',
    'StatutoryRape': 'CrimeAgainstPerson',
    'TheftOfMotorVehiclePartsOrAccessories': 'CrimeAgainstProperty',
    'CreditCardOrAutomatedTellerMachineFraud': 'CrimeAgainstProperty',
    'SexualAssaultWithAnObject': 'CrimeAgainstPerson',
    'HumanTrafficking_CommercialSexActs': 'CrimeAgainstPerson',
    'HackingOrComputerInvasion': 'CrimeAgainstProperty',
    'PocketPicking': 'CrimeAgainstProperty',
    'Intimidation': 'CrimeAgainstPerson',
    'Burglary': 'CrimeAgainstProperty',
    'PurseSnatching': 'CrimeAgainstProperty',
    'IdentityTheft': 'CrimeAgainstProperty',
    'StolenPropertyOffenses': 'CrimeAgainstProperty',
    'Fondling': 'CrimeAgainstPerson',
    'TheftFromCoinOperatedMachineOrDevice': 'CrimeAgainstProperty',
    'Arson': 'CrimeAgainstProperty',
    'BettingOrWagering': 'CrimeAgainstSociety',
    'WireFraud': 'CrimeAgainstProperty',
    'DestructionOrDamageOrVandalismOfProperty': 'CrimeAgainstProperty',
    'NegligentManslaughter': 'CrimeAgainstPerson',
    'Sodomy': 'CrimeAgainstPerson',
    'AggravatedAssault': 'CrimeAgainstPerson',
    'Robbery': 'CrimeAgainstProperty',
    'AnimalCruelty': 'CrimeAgainstSociety',
    'PurchasingProstitution': 'CrimeAgainstSociety',
    'ExtortionOrBlackmail': 'CrimeAgainstProperty',
    'WelfareFraud': 'CrimeAgainstProperty',
    'TheftFromMotorVehicle': 'CrimeAgainstProperty',
    'CounterfeitingOrForgery': 'CrimeAgainstProperty',
    'MotorVehicleTheft': 'CrimeAgainstProperty',
    'Bribery': 'CrimeAgainstProperty',
    'ForcibleRape': 'CrimeAgainstPerson',
    'Shoplifting': 'CrimeAgainstProperty',
    'DrugEquipmentViolations': 'CrimeAgainstSociety',
    'PornographyOrObsceneMaterial': 'CrimeAgainstSociety',
    'TheftFromBuilding': 'CrimeAgainstProperty',
    'Prostitution': 'CrimeAgainstSociety',
    'AssistingOrPromotingProstitution': 'CrimeAgainstSociety',
    'Embezzlement': 'CrimeAgainstProperty',
    'Incest': 'CrimeAgainstPerson',
    'UCR_AllOtherLarceny': 'CrimeAgainstProperty',
    'DrugOrNarcoticViolations': 'CrimeAgainstSociety',
    'KidnappingOrAbduction': 'CrimeAgainstPerson'
}

# A dict to map locations to instances of LocationOfCrimeEnum
_LOCATION_MAP = {
    'Cyberspace': '',
    'Rest Area': '',
    'Commercial/Office Building': '',
    'Grocery/Supermarket': '',
    'School-Elementary/Secondary': '',
    'Construction Site': '',
    'Air/Bus/Train Terminal': '',
    'Camp/Campground': '',
    'Military Installation': '',
    'Government/Public Building': '',
    'Church/Synagogue/Temple/Mosque': '',
    'Park/Playground': '',
    'Farm Facility': '',
    'Community Center': '',
    'Other/Unknown': '',
    'Abandoned/Condemned Structure': '',
    'Department/Discount Store': '',
    'Amusement Park': '',
    'Highway/Road/Alley/Street/Sidewalk': '',
    'Jail/Prison/Penitentiary/Corrections Facility': '',
    'Tribal Lands': '',
    'Arena/Stadium/Fairgrounds/Coliseum': '',
    'Auto Dealership New/Used': '',
    'Shelter-Mission/Homeless': '',
    'Hotel/Motel/Etc.': '',
    'Field/Woods': '',
    'Specialty Store': '',
    'Industrial Site': '',
    'School/College': '',
    'Residence/Home': '',
    'Restaurant': '',
    'Gambling Facility/Casino/Race Track': '',
    'Convenience Store': '',
    'Rental Storage Facility': '',
    'School-College/University': '',
    'ATM Separate from Bank': '',
    'Service/Gas Station': '',
    'Parking/Drop Lot/Garage': '',
    'Bank/Savings and Loan': '',
    'Dock/Wharf/Freight/Modal Terminal': '',
    'Bar/Nightclub': '',
    'Lake/Waterway/Beach': '',
    'Shopping Mall': '',
    "Drug Store/Doctor's Office/Hospital": '',
    'Liquor Store': '',
    'Daycare Facility': ''
}

# A dict to map victim types to instances of VictimTypeEnum
_VICTIM_TYPE_MAP = {
    'Financial Institution': 'FinancialInstitution',
    'Law Enforcement Officer': 'LawEnforcementOfficer',
    'Society/Public': 'Society',
    'Individual': 'Person',
    'Government': 'Government',
    'Unknown': 'UCR_UnknownVictimType',
    'Religious Organization': 'ReligiousOrganization',
    'Business': 'Business',
    'Other': 'UCR_OtherVictimType'
}

# A dict to generate aggregations on the source data
_AGGREGATIONS = {
    'total_incidents.csv': [{  # Total Criminal Incidents
        'df': 'incident_df',
        'args': {
            'groupby_cols': [],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'bias.csv': [
        {  # Incidents grouped by bias motivation (anti-white, ...)
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped into single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by bias category (race,religion, gender, ...)
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
    ],
    'offense.csv': [{  # Incidents by crime type (arson, robbery, ...)
        'df': 'offense_df',
        'args': {
            'groupby_cols': ['OFFENSE_NAME'],
            'agg_dict': {
                'INCIDENT_ID': 'nunique'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'offense_by_bias.csv': [
        {  # Incidents by crime type and bias motivation
            'df': 'single_bias_offenses',
            'args': {
                'groupby_cols': ['BIAS_DESC', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and single bias / multiple bias
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['MULTIPLE_BIAS', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents grouped by crime type and bias category
            'df': 'offense_df',
            'args': {
                'groupby_cols': ['BIAS_CATEGORY', 'OFFENSE_NAME'],
                'agg_dict': {
                    'INCIDENT_ID': 'nunique'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'offender_race.csv': [{  # Total incidents by offender race
        'df': 'incident_df',
        'args': {
            'groupby_cols': ['OFFENDER_RACE'],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'offender_ethnicity.csv': [{  # Total incidents by offender ethnicity
        'df': 'incident_df',
        'args': {
            'groupby_cols': ['OFFENDER_ETHNICITY'],
            'agg_dict': {
                'INCIDENT_ID': 'count'
            },
            'population_type': 'CriminalIncidents'
        }
    }],
    'offender_race_by_bias.csv': [
        {  # Incidents by offender race and bias motivation
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender race and single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender race and bias category
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_RACE', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ],
    'offender_ethnicity_by_bias.csv': [
        {  # Incidents by offender ethnicity and bias motivation
            'df': 'single_bias_incidents',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_DESC'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender ethnicity and single bias / multiple bias
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'MULTIPLE_BIAS'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        },
        {  # Incidents by offender ethnicity and bias category
            'df': 'incident_df',
            'args': {
                'groupby_cols': ['OFFENDER_ETHNICITY', 'BIAS_CATEGORY'],
                'agg_dict': {
                    'INCIDENT_ID': 'count'
                },
                'population_type': 'CriminalIncidents'
            }
        }
    ]
}


def _create_df_dict(df: pd.DataFrame) -> dict:
    """Applies transformations on the hate crime dataframe. These transformed
    dataframes are then used in the aggregations.

    Args:
        df: A pandas.DataFrame of the hate crime data.

    Returns:
        A dictionary which has transformation name as key and the transformed
        dataframe as it's value.
    """
    df['BIAS_CATEGORY'] = ''

    df_dict = {}
    df_dict['incident_df'] = df.apply(_add_bias_category, axis=1)
    df_dict['offense_df'] = flatten_by_column(df_dict['incident_df'],
                                              'OFFENSE_NAME')
    df_dict['offense_df'] = df_dict['offense_df'].apply(_add_offense_category,
                                                        axis=1)
    df_dict['single_bias_incidents'] = df_dict['incident_df'][
        df_dict['incident_df']['MULTIPLE_BIAS'] == 'S']
    df_dict['single_bias_offenses'] = df_dict['offense_df'][
        df_dict['offense_df']['MULTIPLE_BIAS'] == 'S']

    return df_dict


def _add_bias_category(row):
    """A function to add the bias category based on the bias motivation. To be
    used with pandas.DataFrame.apply().
    """
    row['BIAS_CATEGORY'] = _BIAS_CATEGORY_MAP.get(row['BIAS_DESC'],
                                                  'MultipleBias')
    return row


def _add_offense_category(row):
    """A function to add the offense category based on the offense type. To be
    used with pandas.DataFrame.apply()
    """
    row['OFFENSE_CATEGORY'] = _OFFENSE_CATEGORY_MAP.get(row['OFFENSE_NAME'],
                                                        'MultipleOffense')
    return row


def _get_dpv(statvar: dict, config: dict) -> list:
    """A function that goes through the statvar dict and the config and returns
    a list of properties to ignore when generating the dcid.

    Args:
        statvar: A dictionary of prop:values of the statvar
        config: A dict which expects the keys to be the column name and
          value to be another dict. This dict maps column values to key-value
          pairs of a statvar. See scripts/fbi/hate_crime/config.json for an
          example. In this function, the '_DPV_' key is used to identify 
          dependent properties.

    Returns:
        A list of properties to ignore when generating the dcid
    """
    ignore_props = []
    for spec in config['_DPV_']:
        if spec['cprop'] in statvar:
            dpv_prop = spec['dpv']['prop']
            dpv_val = spec['dpv']['val']
            if dpv_val == statvar.get(dpv_prop, None):
                ignore_props.append(dpv_prop)
    return ignore_props


def _gen_statvar_mcf(df: pd.DataFrame,
                     config: dict,
                     population_type: str = 'CriminalIncidents'):
    """A function that creates statvars and assigns the dcid after going through
    each row in the dataframe.

    Args:
        df: A pandas dataframe whose rows are referenced to create the statvar.
        config: A dict which expects the keys to be the column name and
          value to be another dict. This dict maps column values to key-value
          pairs of a statvar. See scripts/fbi/hate_crime/config.json for an
          example.
        population_type: The populationType to assign to each statvar.

    Returns:
        A modified dataframe with an additional column 'StatVar' whose value is
        the statvar dcid for it's corresponding row. Also returns a statvar list
        which containts all the generated statvars.
    """
    statvar_list = []
    statvar_dcid_list = []
    df_copy = df.copy()
    for _, row in df_copy.iterrows():
        statvar = {**config['_COMMON_']}
        for col in df_copy.columns:
            if col in config:
                if row[col] in config[col]:
                    statvar.update(config[col][row[col]])
        statvar['populationType'] = population_type
        ignore_props = _get_dpv(statvar, config)
        statvar['Node'] = get_statvar_dcid(statvar, ignore_props=ignore_props)
        statvar_dcid_list.append(statvar['Node'])
        statvar_list.append(statvar)
    df_copy['StatVar'] = statvar_dcid_list
    return df_copy, statvar_list


def _write_statvar_mcf(statvar_list: list, f):
    """Writes statvars to a file.

    Args:
        statvar_list: A list of statvars. Each statvar is expected to be a dict.
        f: file handle for the .mcf file.
    """
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


def _create_aggr(input_df: pd.DataFrame, config: dict, statvar_list: list,
                 groupby_cols: list, agg_dict: dict, population_type: str):
    """A wrapper function that calls utils.make_time_place_aggregations and uses
    it's output to generate statvar MCF.

    Args:
        df: A list of statvars. Each statvar is expected to be a dict.
        f: file handle for the .mcf file.

    Returns:
        A list of transformed dataframes with an additional column in each
        that points to it's statvar dcid.
    """
    output_df_list = make_time_place_aggregation(input_df,
                                                 groupby_cols=groupby_cols,
                                                 agg_dict=agg_dict,
                                                 multi_index=False)

    for idx in range(len(output_df_list)):
        output_df_list[idx], statvars = _gen_statvar_mcf(
            output_df_list[idx], config, population_type=population_type)
        statvar_list.extend(statvars)

    return output_df_list


def _write_to_csv(df: pd.DataFrame, csv_file_name: str):
    """Writes a dataframe to a .csv file. Removes rows with an empty place value
    before writing.

    Args:
        df: A pandas dataframe to write to csv.
        csv_file_name: The filename of the csv.
    """
    df['Place'].replace('', np.nan, inplace=True)
    df.dropna(subset=['Place'], inplace=True)
    df.to_csv(csv_file_name, index=False)


if __name__ == '__main__':
    source_data_path = os.path.join(_SCRIPT_PATH, 'source_data',
                                    'hate_crime.csv')
    df = pd.read_csv(source_data_path, usecols=_INPUT_COLUMNS)

    with open('config.json', 'r') as f:
        config = json.load(f)

    fill_col = df.columns[df.isnull().any()].tolist()
    df[fill_col] = df[fill_col].fillna('Unknown')

    df_dict = _create_df_dict(df)

    # Incidents by StatVar
    df_dict['incident_df'], statvar_list = _gen_statvar_mcf(
        df_dict['incident_df'], config, population_type='CriminalIncidents')

    incident_by_statvar = make_time_place_aggregation(
        df_dict['incident_df'],
        groupby_cols=['StatVar'],
        agg_dict={'INCIDENT_ID': 'count'},
        multi_index=False)
    output_csv_path = os.path.join(_SCRIPT_PATH, 'output', 'output.csv')
    _write_to_csv(pd.concat(incident_by_statvar), output_csv_path)

    output_mcf_path = os.path.join(_SCRIPT_PATH, 'output', 'output.mcf')
    with open(output_mcf_path, 'w') as f:
        _write_statvar_mcf(statvar_list, f)

    # Aggregations
    statvar_list = []
    if not os.path.exists(os.path.join(_SCRIPT_PATH, 'aggregations')):
        os.mkdir(os.path.join(_SCRIPT_PATH, 'aggregations'))

    for file_name, aggregations in _AGGREGATIONS.items():
        aggr_list = []
        for aggr_map in aggregations:
            aggr_df = df_dict[aggr_map['df']]
            aggr = _create_aggr(aggr_df, config, statvar_list,
                                **aggr_map['args'])
            aggr_list.extend(aggr)
        aggr_csv_path = os.path.join(_SCRIPT_PATH, 'aggregations', file_name)
        _write_to_csv(pd.concat(aggr_list), aggr_csv_path)

    aggr_mcf_path = os.path.join(_SCRIPT_PATH, 'aggregations',
                                 'aggregation.mcf')
    with open(aggr_mcf_path, 'w') as f:
        _write_statvar_mcf(statvar_list, f)

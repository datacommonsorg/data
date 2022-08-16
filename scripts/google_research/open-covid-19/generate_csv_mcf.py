# Copyright 2020 Google LLC
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
"""
Script for generating the Open COVID-19 Data open source at
https://github.com/google-research/open-covid-19-data under CC-BY license.

The script generates three files:
1) open_covid_19_data.csv
2) open_covid_19_data.tmcf
3) open_covid_19_data_geos.mcf

"open_covid_19_data_geos.mcf" contains node MCFs for geos in the dataset that do
not come up DCIDs for local resolution. "open_covid_19_data_geos_resolved.mcf"
contains the resolved geos.
"""

import re
import collections
from typing import Dict, List, Iterable

import pandas as pd
import numpy as np
import requests
import frozendict

# Data CSV
CSV_URL = 'https://raw.githubusercontent.com/google-research/open-covid-19-data/master/data/exports/cc_by/aggregated_cc_by.csv'
# CSV containing mappings from "region_code" to "datacommons_id"
LOCATIONS_URL = 'https://raw.githubusercontent.com/google-research/open-covid-19-data/master/data/exports/locations/locations.csv'
# Output filenames
CSV_OUT = 'open_covid_19_data.csv'
TMCF_OUT = 'open_covid_19_data.tmcf'
GEOS_OUT = 'open_covid_19_data_geos.mcf'
# Columns that contain integers
INTEGRAL_COLS = ('confirmed_cases', 'confirmed_deaths', 'cases_cumulative',
                 'cases_new', 'deaths_cumulative', 'deaths_new',
                 'tests_cumulative', 'tests_new', 'hospitalized_current',
                 'hospitalized_new', 'hospitalized_cumulative', 'icu_current',
                 'icu_cumulative', 'ventilator_current', 'school_closing',
                 'workplace_closing', 'restrictions_on_gatherings',
                 'close_public_transit', 'stay_at_home_requirements',
                 'restrictions_on_internal_movement', 'income_support',
                 'public_information_campaigns', 'school_closing_flag',
                 'workplace_closing_flag', 'restrictions_on_gatherings_flag',
                 'close_public_transit_flag', 'stay_at_home_requirements_flag',
                 'restrictions_on_internal_movement_flag',
                 'income_support_flag', 'public_information_campaigns_flag',
                 'international_travel_controls', 'debt_contract_relief',
                 'testing_policy', 'contact_tracing')
# Columns that do not contain integers
NON_INTEGRAL_COLS = (
    'open_covid_region_code', 'region_name', 'date',
    'cases_cumulative_per_million', 'cases_new_per_million',
    'deaths_cumulative_per_million', 'deaths_new_per_million',
    'tests_cumulative_per_thousand', 'tests_new_per_thousand', 'test_units',
    'cancel_public_events_flag', 'fiscal_measures', 'international_support',
    'emergency_investment_in_healthcare', 'investment_in_vaccines',
    'stringency_index', 'stringency_index_for_display',
    'government_response_index', 'government_response_index_for_display',
    'containment_health_index', 'containment_health_index_for_display',
    'economic_support_index', 'economic_support_index_for_display')
# Required columns
REQUIRED_COLS = INTEGRAL_COLS + NON_INTEGRAL_COLS
# Columns whose template MCFs can be produced without special processing
REGULAR_COLS = ('cases_cumulative', 'cases_new', 'deaths_cumulative',
                'deaths_new', 'tests_cumulative_people_tested',
                'tests_cumulative_samples_tested',
                'tests_cumulative_tests_performed',
                'tests_cumulative_units_unclear', 'tests_new_people_tested',
                'tests_new_samples_tested', 'tests_new_tests_performed',
                'tests_new_units_unclear', 'hospitalized_current',
                'hospitalized_new', 'hospitalized_cumulative', 'icu_current',
                'icu_cumulative', 'ventilator_current')
# Columns that contain computed indices
INDEX_COLS = ('stringency_index', 'government_response_index',
              'containment_health_index', 'economic_support_index')
# Columns that contain computed indices that are smoothed for display.
# These columns have the measurementQualifier "SmoothedByRepeatingLatestPoint".
DISPLAY_COLS = ('stringency_index_for_display',
                'government_response_index_for_display',
                'containment_health_index_for_display',
                'economic_support_index_for_display')
# Columns that contain confirmed numbers.
# These columns have the measurementMethod "OxCGRTViaOpenCovid19Data".
CONFIRMED_COLS = ('confirmed_cases', 'confirmed_deaths')
# Incomplete column names to StatVar DCIDs mappings.
# The policy columns need to be added.
COL_TO_STATVAR_PARTIAL = frozendict.frozendict({
    'cases_cumulative':
        'CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedCase',
    'cases_new':
        'IncrementalCount_MedicalConditionIncident_COVID_19_ConfirmedCase',
    'deaths_cumulative':
        'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased',
    'deaths_new':
        'IncrementalCount_MedicalConditionIncident_COVID_19_PatientDeceased',
    'tests_cumulative_people_tested':
        'CumulativeCount_Person_COVID_19_Tested_PCR',
    'tests_cumulative_samples_tested':
        'CumulativeCount_MedicalTest_COVID_19_PCR',
    'tests_cumulative_tests_performed':
        'CumulativeCount_MedicalTest_COVID_19_PCR',
    'tests_cumulative_units_unclear':
        'CumulativeCount_MedicalTest_COVID_19_PCR',
    'tests_new_people_tested':
        'IncrementalCount_Person_COVID_19_Tested_PCR',
    'tests_new_samples_tested':
        'IncrementalCount_MedicalTest_COVID_19_PCR',
    'tests_new_tests_performed':
        'IncrementalCount_MedicalTest_COVID_19_PCR',
    'tests_new_units_unclear':
        'IncrementalCount_MedicalTest_COVID_19_PCR',
    'hospitalized_current':
        'Count_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'hospitalized_new':
        'IncrementalCount_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'hospitalized_cumulative':
        'CumulativeCount_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'icu_current':
        'Count_MedicalConditionIncident_COVID_19_PatientInICU',
    'icu_cumulative':
        'CumulativeCount_MedicalConditionIncident_COVID_19_PatientInICU',
    'ventilator_current':
        'Count_MedicalConditionIncident_COVID_19_PatientOnVentilator',
    'international_travel_controls':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_InternationalTravelRestriction',
    'debt_contract_relief':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_GovernmentBenefit_DebtOrContractRelief',
    'testing_policy':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_TestingEligibility',
    'contact_tracing':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_ContactTracing',
    'emergency_investment_in_healthcare':
        'Amount_Legislation_COVID19Pandemic_GovernmentOrganization_ShortTermSpending_HealthcareExpenditure',
    'investment_in_vaccines':
        'Amount_Legislation_COVID19Pandemic_GovernmentOrganization_ShortTermSpending_VaccineExpenditure',
    'fiscal_measures':
        'Amount_Legislation_COVID19Pandemic_GovernmentOrganization_ShortTermSpending_EconomicStimulusExpenditure',
    'international_support':
        'Amount_Legislation_COVID19Pandemic_GovernmentOrganization_ShortTermSpending_InternationalAidExpenditure',
    'confirmed_cases':
        'CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedCase',
    'confirmed_deaths':
        'CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedPatientDeceased',
    'stringency_index':
        'Covid19StringencyIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'stringency_index_for_display':
        'Covid19StringencyIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'government_response_index':
        'Covid19ResponseIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'government_response_index_for_display':
        'Covid19ResponseIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'containment_health_index':
        'Covid19ContainmentAndHealthIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'containment_health_index_for_display':
        'Covid19ContainmentAndHealthIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'economic_support_index':
        'Covid19EconomicSupportIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
    'economic_support_index_for_display':
        'Covid19EconomicSupportIndex_Legislation_COVID19Pandemic_GovernmentOrganization',
})
# Policy column names to StatVar DCID prefixes.
# Flag values need to be appended to the key prefixes and spatial coverage
# suffixes need to be appended to the value prefixes to produce
# the correct mappings.
POLICY_COL_PREFIX_TO_STATVAR_PREFIX = frozendict.frozendict({
    'school_closing':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_SchoolClosure',
    'workplace_closing':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_WorkplaceClosure',
    'restrictions_on_gatherings':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_PrivateGatheringRestriction',
    'close_public_transit':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_PublicTransitClosure',
    'stay_at_home_requirements':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_StayAtHomeRequirement',
    'restrictions_on_internal_movement':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_InternalMovementRestriction',
    'income_support':
        'PolicyExtent_Legislation_COVID19Pandemic_GovernmentOrganization_GovernmentBenefit_IncomeSupport',
    'public_information_campaigns':
        'CampaignExtent_PublicInformationCampaign_COVID19Pandemic_GovernmentOrganization'
})
# Policy column name prefixes to their units.
# Flag values need to be appended to the prefixes to produce
# the correct columns.
POLICY_COL_PREFIX_TO_UNIT = frozendict.frozendict({
    'school_closing':
        'dcs:ExtentOfPolicySchoolClosure',
    'workplace_closing':
        'dcs:ExtentOfPolicyWorkplaceClosure',
    'restrictions_on_gatherings':
        'dcs:ExtentOfPolicyPrivateGatheringRestriction',
    'close_public_transit':
        'dcs:ExtentOfPolicyPublicTransitClosure',
    'stay_at_home_requirements':
        'dcs:ExtentOfPolicyStayAtHomeRequirement',
    'restrictions_on_internal_movement':
        'dcs:ExtentOfPolicyInternalMovementRestriction',
    'income_support':
        'dcs:ExtentOfPolicyIncomeSupport',
    'public_information_campaigns':
        'dcs:ExtentOfPublicInformationCampaign',
})
# Incomplete column names to units mappings.
COL_TO_UNIT_PARTIAL = frozendict.frozendict({
    'emergency_investment_in_healthcare':
        'schema:USDollar',
    'investment_in_vaccines':
        'schema:USDollar',
    'fiscal_measures':
        'schema:USDollar',
    'international_support':
        'schema:USDollar',
    'international_travel_controls':
        'dcs:ExtentOfPolicyInternationalTravelRestriction',
    'debt_contract_relief':
        'dcs:ExtentOfPolicyDebtOrContractRelief',
    'testing_policy':
        'dcs:ExtentOfPolicyTestingEligibility',
    'contact_tracing':
        'dcs:ExtentOfPolicyContactTracing'
})


def generate_df(cols_to_keep: List[str]) -> pd.DataFrame:
    """Generates the cleaned dataframe."""
    df = pd.read_csv(CSV_URL)
    for col in INTEGRAL_COLS:
        df[col] = df[col].astype('Int64')
        if col.endswith('_flag'):
            assert get_unique_values(df[col]) == [0, 1, pd.NA]

    df = pd.merge(df,
                  pd.read_csv(LOCATIONS_URL),
                  left_on='open_covid_region_code',
                  right_on='region_code')
    df = df[df['region_code_type'] != 'other']
    df['observationAbout'] = df[['region_code',
                                 'datacommons_id']].apply(get_observation_about,
                                                          axis=1)
    assert not any(pd.isna(df['observationAbout']))
    assert get_unique_values(df['test_units']) == [
        'people tested', 'people tested (incl. non-PCR)', 'samples tested',
        'tests performed', 'units unclear', pd.NA
    ]

    # Split the test columns by units
    for col in ('tests_cumulative', 'tests_new'):
        split_col(df, col, 'test_units')
        validate_split(df, col, 'test_units')

    # Split the policy columns by flags
    for col in POLICY_COL_PREFIX_TO_STATVAR_PREFIX.keys():
        by = col + '_flag'
        split_col(df, col, by)
        validate_split(df, col, by)

    return df[cols_to_keep]


def get_observation_about(row: pd.Series) -> str:
    """Formats the observationAbout value for a place.

    Args:
        row: A pandas series of two fields 'region_code' and 'datacommons_id'.

    Returns:
        'dcid:' followed by the value of 'datacommons_id' if 'region_code' is
        not NaN. Otherwise, 'l:' followed by the value of 'region_code' for
        resolving the place locally.
    """
    if pd.isna(row.datacommons_id):
        return f'l:{row.region_code}'
    return f'dcid:{row.datacommons_id}'


def clean_col_name(col: str) -> str:
    """Replaces characters that are not letters or digits with underscores."""
    return re.sub(r'[^A-Za-z0-9]', '_', col)


def get_unique_values(series: pd.Series) -> List:
    """Returns a list of unique values in a series, including NaNs."""
    vals = list(sorted(series.dropna().unique()))
    if any(pd.isna(series)):
        vals.append(pd.NA)
    return vals


def get_col_value_name(col: str, value: str) -> str:
    """Formats column name with a value as suffix."""
    return f'{col}_{clean_col_name(value)}'


def split_col(df: pd.DataFrame, col_to_split: str, col_by: str) -> List[str]:
    """Splits a column "col_to_split" into several columns by another column
    "col_by".
    
    The function looks at the unique values in "col_by" including NaN. For each
    of these values, it creates a new column out of "col_to_split" with only
    rows where "col_by" has the value. The other rows are marked NaNs. A new
    column is named "{col_to_split}_{value}" by converting the value to a string
    and replacing characters other than letters and digits with underscores.

    Example:
        df = col1 | col2
             1    | 2
             1    | 3
             4    | 3
             5    | NaN
        split_col(df, 'col1', 'col2') modifies df to
             col1 | col2 | col1_2 | col1_3 | col1_NaN
             1    | 2    | 1      | NaN    | NaN
             1    | 3    | NaN    | 1      | NaN
             4    | 3    | NaN    | 4      | NaN
             5    | NaN  | NaN    | NaN    | 5

    Args:
        df: The dataframe to operate on.
        col_to_split: Name of the column to split.
        col_by: Name of the column to split by.
    
    Returns:
        Names of the new columns added to the input dataframe.
    """
    values = get_unique_values(df[col_by])
    new_cols = []
    for value in values:
        new_col = get_col_value_name(col_to_split, str(value))
        if pd.isna(value):
            df[new_col] = df[pd.isna(df[col_by])][col_to_split]
        else:
            df[new_col] = df[df[col_by] == value][col_to_split]
        new_cols.append(new_col)
    return new_cols


def validate_split(df: pd.DataFrame, col_splitted: str, col_by: str):
    """Validates result of executing split_col."""
    values = get_unique_values(df[col_by])
    cols = list(
        get_col_value_name(col_splitted, str(value)) for value in values)
    for row in df[[col_splitted, col_by] + cols].to_dict(orient='records'):
        # If the original column is NaN, the created columns are NaNs
        if pd.isna(row[col_splitted]):
            assert all(pd.isna(row[col]) for col in cols)
        # If the original column is not NaN, only one of the created columns
        # is not NaN and has the same value
        else:
            col = get_col_value_name(col_splitted, str(row[col_by]))
            other_cols = list(cols)
            other_cols.remove(col)
            assert all(pd.isna(row[col]) for col in other_cols)
            assert row[col_splitted] == row[col]


def get_policy_col_to_statvar(col_to_prefix: Dict[str, str]) -> Dict[str, str]:
    """Returns mappings from policy columns splitted by flags
    to the DCIDs of their StatVars."""
    col_to_statvar = {}
    for col, prefix in POLICY_COL_PREFIX_TO_STATVAR_PREFIX.items():
        col_to_statvar[f'{col}_0'] = f'{prefix}_SelectedAdministrativeAreas'
        col_to_statvar[f'{col}_1'] = f'{prefix}_AllAdministrativeAreas'
        col_to_statvar[f'{col}__NA_'] = f'{prefix}_SpatialCoverageUnknown'
    return col_to_statvar


def generate_tmcfs(col_to_statvar: Dict[str, str]) -> List[str]:
    """Generates template MCFs."""
    col_to_tmcf = generate_tmcfs_helper(REGULAR_COLS, col_to_statvar, 0,
                                        'dcs:OpenCovid19Data')
    col_to_unit = get_col_to_unit()
    col_to_tmcf = {
        **col_to_tmcf,
        **generate_tmcfs_helper(col_to_unit.keys(), col_to_statvar,
                                len(col_to_tmcf), 'dcs:OpenCovid19Data', col_to_unit)
    }
    # Index columns
    col_to_tmcf = {
        **col_to_tmcf,
        **generate_tmcfs_helper(INDEX_COLS, col_to_statvar, len(col_to_tmcf), 'dcs:OpenCovid19Data')
    }

    # Index for display columns
    col_to_tmcf = {
        **col_to_tmcf,
        **generate_tmcfs_helper(DISPLAY_COLS,
                                col_to_statvar,
                                len(col_to_tmcf),
                                'dcs:OpenCovid19Data',
                                mqual='dcs:SmoothedByRepeatingLatestPoint')
    }

    # Confirmed cases and deaths
    col_to_tmcf = {
        **col_to_tmcf,
        **generate_tmcfs_helper(CONFIRMED_COLS, col_to_statvar, len(col_to_tmcf), 'dcs:OxCGRTViaOpenCovid19Data')
    }

    assert col_to_statvar.keys() == col_to_tmcf.keys()
    return col_to_tmcf.values()


def write_strs(strs: Iterable[str], dest: str) -> None:
    """Writes strings out to a file."""
    with open(dest, 'w') as out:
        for elem in strs:
            out.write(elem)
            out.write('\n')


def generate_geo_mcfs(observation_abouts: pd.Series) -> List[str]:
    """Generates node MCFs for geos that do not come with DCIDs
    for local resolution."""
    mcfs = []
    template = ('Node: {iso}\n'
                'typeOf: schema:Place\n'
                'isoCode: "{iso}"\n')
    for value in observation_abouts.unique():
        if value.startswith('l:'):
            mcfs.append(template.format_map({'iso': value[2:]}))
    return mcfs


def generate_tmcfs_helper(cols: Iterable[str],
                          col_to_statvar: Dict[str, str],
                          starting_index: int,
                          mmethod: str,
                          col_to_unit: Dict[str, str] = None,
                          mqual: str = None) -> Dict[str, str]:
    """Generates template MCFs for columns that do not need
    special processing.

    Args:
        cols: Column names.
        col_to_statvar: Mappings from column names to StatVar DCIDs.
        starting_index: Starting node index.
        extra_line: Extra line to add to each template MCF.

    Returns:
        Mappings from column names to template MCFs.
    """
    template = ('Node: E:open_covid_19_data->E{index}\n'
                'typeOf: dcs:StatVarObservation\n'
                'variableMeasured: dcs:{statvar}\n'
                f'measurementMethod: {mmethod}\n'
                'observationAbout: C:open_covid_19_data->observationAbout\n'
                'observationDate: C:open_covid_19_data->date\n'
                'value: C:open_covid_19_data->{column_name}\n'
                'statType: dcs:measuredValue\n')
    if mqual:
        template += f'measurementQualifer: {mqual}\n'

    col_to_tmcf = {}
    for col in cols:
        tmcf = template.format_map({
            'index': starting_index,
            'statvar': col_to_statvar[col],
            'column_name': col
        })
        if col_to_unit:
            tmcf += f'unit: {col_to_unit[col]}\n'
        col_to_tmcf[col] = tmcf
        starting_index += 1
    return col_to_tmcf


def get_col_to_unit() -> Dict[str, str]:
    """Returns mappings from column names to units for columns
    that need units."""
    col_to_unit = dict(COL_TO_UNIT_PARTIAL)
    for col, unit in POLICY_COL_PREFIX_TO_UNIT.items():
        for suffix in ('_0', '_1', '__NA_'):
            col_to_unit[col + suffix] = unit
    return col_to_unit


def main():
    """Runs the script."""
    col_to_statvar = {
        **COL_TO_STATVAR_PARTIAL,
        **get_policy_col_to_statvar(POLICY_COL_PREFIX_TO_STATVAR_PREFIX)
    }
    df = generate_df(['observationAbout', 'date'] + list(col_to_statvar.keys()))
    df.to_csv(CSV_OUT, index=False)
    write_strs(generate_tmcfs(col_to_statvar), TMCF_OUT)
    write_strs(generate_geo_mcfs(df['observationAbout']), GEOS_OUT)


if __name__ == "__main__":
    main()

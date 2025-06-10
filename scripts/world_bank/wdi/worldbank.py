# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Fetches, cleans, outputs TMCFs and CSVs for all World Bank development
    indicator codes provided by the indicatorSchemaFile flag for all years
    and for all countries provided in WorldBankCountries.csv. """

import logging
import itertools
import requests
import zipfile
import io
import time
import re
import os
import sys

from absl import app
from absl import flags
from absl import logging
import pandas as pd
from retry.api import retry_call

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_FLAGS = flags.FLAGS
flags.DEFINE_boolean("fetchFromSource", True,
                     "Whether to bypass cached CSVs and fetch from source.")
flags.DEFINE_string(
    "indicatorSchemaFile",
    os.path.join(_MODULE_DIR, "schema_csvs/WorldBankIndicators_prod.csv"), "")
flags.DEFINE_string('mode', '', 'Options: download or process')

# Remaps the columns provided by World Bank API.
WORLDBANK_COL_REMAP = {
    'Country Name': 'CountryName',
    'Country Code': 'CountryCode',
    'Indicator Name': 'IndicatorName',
    'Indicator Code': 'IndicatorCode'
}

TEMPLATE_TMCF = """Node: E:WorldBank->E{idx}
typeOf: dcs:StatVarObservation
variableMeasured: C:WorldBank->StatisticalVariable
observationDate: C:WorldBank->Year
observationPeriod: C:WorldBank->observationPeriod
observationAbout: C:WorldBank->ISO3166Alpha3
value: C:WorldBank->Value{idx}
unit: C:WorldBank->unit
"""

TEMPLATE_STAT_VAR = """
Node: dcid:WorldBank/{INDICATOR}
name: "{NAME}"
description: "{DESCRIPTION}"
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
measurementDenominator: dcs:{measurementDenominator}
{CONSTRAINTS}
"""

RESOLUTION_TO_EXISTING_DCID = {
    'dcs:WorldBank/SE_TER_CUAT_BA_FE_ZS':
        'Count_Person_25OrMoreYears_Female_BachelorsDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears_Female',
    'dcs:WorldBank/SE_TER_CUAT_BA_MA_ZS':
        'Count_Person_25OrMoreYears_Male_BachelorsDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears_Male',
    'dcs:WorldBank/SE_TER_CUAT_BA_ZS':
        'Count_Person_25OrMoreYears_BachelorsDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears',
    'dcs:WorldBank/SE_TER_CUAT_DO_FE_ZS':
        'Count_Person_25OrMoreYears_Female_DoctorateDegree_AsFractionOf_Count_Person_25OrMoreYears_Female',
    'dcs:WorldBank/SE_TER_CUAT_DO_MA_ZS':
        'Count_Person_25OrMoreYears_Male_DoctorateDegree_AsFractionOf_Count_Person_25OrMoreYears_Male',
    'dcs:WorldBank/SE_TER_CUAT_DO_ZS':
        'Count_Person_25OrMoreYears_DoctorateDegree_AsFractionOf_Count_Person_25OrMoreYears',
    'dcs:WorldBank/SE_TER_CUAT_MS_FE_ZS':
        'Count_Person_25OrMoreYears_Female_MastersDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears_Female',
    'dcs:WorldBank/SE_TER_CUAT_MS_MA_ZS':
        'Count_Person_25OrMoreYears_Male_MastersDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears_Male',
    'dcs:WorldBank/SE_TER_CUAT_MS_ZS':
        'Count_Person_25OrMoreYears_MastersDegreeOrHigher_AsFractionOf_Count_Person_25OrMoreYears',
    'dcs:WorldBank/SE_TER_CUAT_ST_FE_ZS':
        'Count_Person_25OrMoreYears_Female_TertiaryEducation_AsFractionOf_Count_Person_25OrMoreYears_Female',
    'dcs:WorldBank/SE_TER_CUAT_ST_MA_ZS':
        'Count_Person_25OrMoreYears_Male_TertiaryEducation_AsFractionOf_Count_Person_25OrMoreYears_Male',
    'dcs:WorldBank/SE_TER_CUAT_ST_ZS':
        'Count_Person_25OrMoreYears_TertiaryEducation_AsFractionOf_Count_Person_25OrMoreYears',
    'dcs:WorldBank/SH_STA_OWGH_FE_ZS':
        'Count_Person_Upto4Years_Female_Overweight_AsFractionOf_Count_Person_Upto4Years_Female',
    'dcs:WorldBank/SH_STA_OWGH_MA_ZS':
        'Count_Person_Upto4Years_Male_Overweight_AsFractionOf_Count_Person_Upto4Years_Male',
    'dcs:WorldBank/SH_STA_OWGH_ZS':
        'Count_Person_Upto4Years_Overweight_AsFractionOf_Count_Person_Upto4Years',
    'dcs:WorldBank/SH_STA_SUIC_FE_P5':
        'Count_Death_IntentionalSelfHarm_Female_AsFractionOf_Count_Person_Female',
    'dcs:WorldBank/SH_STA_SUIC_MA_P5':
        'Count_Death_IntentionalSelfHarm_Male_AsFractionOf_Count_Person_Male',
    'dcs:WorldBank/SH_STA_SUIC_P5':
        'Count_Death_IntentionalSelfHarm_AsFractionOf_Count_Person',
    'dcs:WorldBank/SL_TLF_ACTI_FE_ZS':
        'Count_Person_15To64Years_Female_InLaborForce_AsFractionOf_Count_Person_15To64Years_Female',
    'dcs:WorldBank/SL_TLF_ACTI_MA_ZS':
        'Count_Person_15To64Years_Male_InLaborForce_AsFractionOf_Count_Person_15To64Years_Male',
    'dcs:WorldBank/SL_TLF_ACTI_ZS':
        'Count_Person_15To64Years_InLaborForce_AsFractionOf_Count_Person_15To64Years',
    'dcs:WorldBank/SL_TLF_TOTL_FE_ZS':
        'Count_Person_15OrMoreYears_InLaborForce_Female_AsFractionOf_Count_Person_InLaborForce',
    'dcs:WorldBank/VC_IHR_PSRC_FE_P5':
        'Count_CriminalActivities_MurderAndNonNegligentManslaughter_Female_AsFractionOf_Count_Person_Female',
    'dcs:WorldBank/VC_IHR_PSRC_MA_P5':
        'Count_CriminalActivities_MurderAndNonNegligentManslaughter_Male_AsFractionOf_Count_Person_Male',
    'dcs:WorldBank/VC_IHR_PSRC_P5':
        'Count_CriminalActivities_MurderAndNonNegligentManslaughter_AsFractionOf_Count_Person',
    'dcs:WorldBank/SP_RUR_TOTL':
        'Count_Person_Rural',
    'dcs:WorldBank/SP_URB_TOTL':
        'Count_Person_Urban',
    'dcs:WorldBank/SP_DYN_IMRT_IN':
        'Count_Death_0Years_AsFractionOf_Count_BirthEvent_LiveBirth',
    'dcs:WorldBank/SP_DYN_IMRT_MA_IN':
        'Count_Death_0Years_Male_AsFractionOf_Count_BirthEvent_LiveBirth_Male',
    'dcs:WorldBank/SP_DYN_IMRT_FE_IN':
        'Count_Death_0Years_Female_AsFractionOf_Count_BirthEvent_LiveBirth_Female',
    'dcs:WorldBank/SH_DTH_IMRT':
        'Count_Death_0Years',
    'dcs:WorldBank/SL_TLF_0714_ZS':
        'Count_Person_7To14Years_Employed_AsFractionOf_Count_Person_7To14Years',
    'dcs:WorldBank/SL_TLF_0714_MA_ZS':
        'Count_Person_7To14Years_Male_Employed_AsFractionOf_Count_Person_7To14Years_Male',
    'dcs:WorldBank/SL_TLF_0714_FE_ZS':
        'Count_Person_7To14Years_Female_Employed_AsFractionOf_Count_Person_7To14Years_Female',
    'dcs:WorldBank/SH_SVR_WAST_ZS':
        'Count_Person_Upto4Years_SevereWasting_AsFractionOf_Count_Person_Upto4Years',
    'dcs:WorldBank/SH_SVR_WAST_MA_ZS':
        'Count_Person_Upto4Years_Male_SevereWasting_AsFractionOf_Count_Person_Upto4Years_Male',
    'dcs:WorldBank/SH_SVR_WAST_FE_ZS':
        'Count_Person_Upto4Years_Female_SevereWasting_AsFractionOf_Count_Person_Upto4Years_Female',
    'dcs:WorldBank/SH_STA_WAST_ZS':
        'Count_Person_Upto4Years_Wasting_AsFractionOf_Count_Person_Upto4Years',
    'dcs:WorldBank/SH_STA_WAST_MA_ZS':
        'Count_Person_Upto4Years_Male_Wasting_AsFractionOf_Count_Person_Upto4Years_Male',
    'dcs:WorldBank/SH_STA_WAST_FE_ZS':
        'Count_Person_Upto4Years_Female_Wasting_AsFractionOf_Count_Person_Upto4Years_Female',
    'dcs:WorldBank/SH_XPD_CHEX_PC_CD':
        'Amount_EconomicActivity_ExpenditureActivity_HealthcareExpenditure_AsFractionOf_Count_Person',
    'dcs:WorldBank/SH_ALC_PCAP_LI':
        'Amount_Consumption_Alcohol_15OrMoreYears_AsFractionOf_Count_Person_15OrMoreYears',
    'dcs:WorldBank/SI_POV_GINI':
        'GiniIndex_EconomicActivity',
    'dcs:WorldBank/SE_XPD_TOTL_GB_ZS':
        'Amount_EconomicActivity_ExpenditureActivity_EducationExpenditure_Government_AsFractionOf_Amount_EconomicActivity_ExpenditureActivity_Government',
    'dcs:WorldBank/SE_XPD_TOTL_GD_ZS':
        'Amount_EconomicActivity_ExpenditureActivity_EducationExpenditure_Government_AsFractionOf_Amount_EconomicActivity_GrossDomesticProduction_Nominal',
    'dcs:WorldBank/CM_MKT_LCAP_GD_ZS':
        'Amount_Stock_AsFractionOf_Amount_EconomicActivity_GrossDomesticProduction_Nominal',
    'dcs:WorldBank/CM_MKT_LCAP_CD':
        'Amount_Stock',
    'dcs:WorldBank/BX_TRF_PWKR_DT_GD_ZS':
        'Amount_Remittance_InwardRemittance_AsFractionOf_Amount_EconomicActivity_GrossDomesticProduction_Nominal',
    'dcs:WorldBank/BX_TRF_PWKR_CD_DT':
        'Amount_Remittance_InwardRemittance',
    'dcs:WorldBank/BM_TRF_PWKR_CD_DT':
        'Amount_Remittance_OutwardRemittance',
    'dcs:WorldBank/SH_DYN_MORT':
        'MortalityRate_Person_Upto4Years_AsFractionOf_Count_BirthEvent_LiveBirth',
    'dcs:WorldBank/SH_PRV_SMOK':
        'Count_Person_15OrMoreYears_Smoking_AsFractionOf_Count_Person_15OrMoreYears',
    'dcs:WorldBank/SH_PRV_SMOK_FE':
        'Count_Person_15OrMoreYears_Female_Smoking_AsFractionOf_Count_Person_15OrMoreYears_Female',
    'dcs:WorldBank/SH_PRV_SMOK_MA':
        'Count_Person_15OrMoreYears_Male_Smoking_AsFractionOf_Count_Person_15OrMoreYears_Male',
    'dcs:WorldBank/SH_STA_DIAB_ZS':
        'Count_Person_20To79Years_Diabetes_AsFractionOf_Count_Person_20To79Years',
    'dcs:WorldBank/SP_DYN_CBRT_IN':
        'Count_BirthEvent_LiveBirth_AsFractionOf_Count_Person',
    'dcs:WorldBank/SP_DYN_LE00_FE_IN':
        'LifeExpectancy_Person_Female',
    'dcs:WorldBank/SP_DYN_LE00_MA_IN':
        'LifeExpectancy_Person_Male',
    'dcs:WorldBank/EG_ELC_FOSL_ZS':
        'Amount_Production_ElectricityFromOilGasOrCoalSources_AsFractionOf_Amount_Production_Energy',
    'dcs:WorldBank/EG_ELC_NUCL_ZS':
        'Amount_Production_ElectricityFromNuclearSources_AsFractionOf_Amount_Production_Energy',
    'dcs:WorldBank/EG_FEC_RNEW_ZS':
        'Amount_Consumption_RenewableEnergy_AsFractionOf_Amount_Consumption_Energy',
    'dcs:WorldBank/EN_POP_EL5M_ZS':
        'Count_Person_ResidingLessThan5MetersAboveSeaLevel_AsFractionOf_Count_Person',
    'dcs:WorldBank/IT_CEL_SETS_P2':
        'Count_Product_MobileCellularSubscription_AsFractionOf_Count_Person',
    'dcs:WorldBank/SE_XPD_TERT_ZS':
        'Amount_EconomicActivity_ExpenditureActivity_TertiaryEducationExpenditure_Government_AsFractionOf_Amount_EconomicActivity_ExpenditureActivity_EducationExpenditure_Government',
    'dcs:WorldBank/SH_XPD_CHEX_PP_CD':
        'Amount_EconomicActivity_ExpenditureActivity_HealthcareExpenditure_AsFractionOf_Count_Person',
    'dcs:WorldBank/SH_XPD_CHEX_PC_CD':
        'Amount_EconomicActivity_ExpenditureActivity_HealthcareExpenditure_AsFractionOf_Count_Person'
}


def read_worldbank(iso3166alpha3, mode):
    """ Fetches and tidies all ~1500 World Bank indicators
        for a given ISO 3166 alpha 3 code.

        For a particular alpha 3 code, this function fetches the entire ZIP
        file for that particular country for all World Bank indicators in a
        wide format where years are columns. The dataframe is changed into a
        narrow format so that year becomes a single column with each row
        representing a different year for a single indicator.

        Args:
            iso3166alpha3: ISO 3166 alpha 3 for a country, as a string.

        Returns:
            A tidied pandas dataframe with all indicator codes for a particular
            country in the format of (country, indicator, year, value).

        Notes:
            Takes approximately 10 seconds to download and
            tidy one country in a Jupyter notebook.
    """
    if mode in ["download", '']:
        logging.info('Downloading input file for country %s', iso3166alpha3)
        country_zip = ("http://api.worldbank.org/v2/en/country/" +
                       iso3166alpha3 + "?downloadformat=csv")
        r = retry_call(requests.get,
                       fargs=[country_zip],
                       tries=3,
                       delay=20,
                       backoff=1.5)
        if r.status_code != 200:
            logging.fatal('Failed to retrieve %s', iso3166alpha3)
        if not os.path.exists(os.path.join(_MODULE_DIR, 'source_data')):
            os.mkdir(os.path.join(_MODULE_DIR, 'source_data'))
        with open(
                os.path.join(_MODULE_DIR, 'source_data',
                             iso3166alpha3 + '.zip'), 'wb') as f:
            f.write(r.content)

        filebytes = io.BytesIO(r.content)
        myzipfile = zipfile.ZipFile(filebytes)

        # We need to select the data file which starts with "API",
        # but does not have an otherwise regular filename structure.
        file_to_open = None
        for file in myzipfile.namelist():
            if file.startswith("API"):
                file_to_open = file
                break
        assert file_to_open is not None, \
            "Failed to find data for" + iso3166alpha3

        df = None
        # Captures any text contained in double quotatations.
        line_match = re.compile(r"\"([^\"]*)\"")

        for line in myzipfile.open(file_to_open).readlines():
            # Cells are contained in quotations and comma separated.
            cols = line_match.findall(line.decode("utf-8"))

            # CSVs include header informational lines which should be ignored.
            if len(cols) > 2:
                # Use first row as the header.
                if df is None:
                    df = pd.DataFrame(columns=cols)
                else:
                    df = pd.concat(
                        [df, pd.DataFrame([cols], columns=df.columns)],
                        ignore_index=True)

        df = df.rename(columns=WORLDBANK_COL_REMAP)

        # Turn each year into its own row.
        df = df.set_index(
            ['CountryName', 'CountryCode', 'IndicatorName', 'IndicatorCode'])
        df = df.stack()
        df.index = df.index.rename('year', level=4)
        df.name = "Value"
        df = df.reset_index()

        # Convert to numeric and drop empty values.
        df['Value'] = pd.to_numeric(df['Value'])
        df = df.dropna()
        if not os.path.exists(
                os.path.join(_MODULE_DIR, 'preprocessed_source_csv')):
            os.mkdir(os.path.join(_MODULE_DIR, 'preprocessed_source_csv'))
        df.to_csv('preprocessed_source_csv/' + iso3166alpha3 + '.csv',
                  index=False)
    else:
        df = pd.read_csv('preprocessed_source_csv/' + iso3166alpha3 + '.csv')
    return df


def build_stat_vars_from_indicator_list(row):
    """ Generates World Bank StatVar for a row in the indicators dataframe. """

    def row_to_constraints(row):
        """ Helper to generate list of constraints. """
        constraints_text = ""
        next_constraint = 1
        while (f"p{next_constraint}" in row and
               not pd.isna(row[f"p{next_constraint}"])):
            variable = row[f'p{next_constraint}']
            constraint = row[f'v{next_constraint}']
            constraints_text += f"{variable}: dcs:{constraint}\n"
            next_constraint += 1
        return constraints_text

    # TODO(tjann): try to turn this into a format_map.
    # yapf: disable
    # Input all required statistical variable fields.
    new_stat_var = (TEMPLATE_STAT_VAR.replace(
        "{INDICATOR}", row['IndicatorCode'].replace(".", "_")).replace(
            "{NAME}", row['IndicatorName']).replace(
                "{DESCRIPTION}", row['SourceNote']).replace(
                    "{measuredProperty}",
                    row['measuredProp']).replace("{CONSTRAINTS}",
                                                 row_to_constraints(row)))
    # yapf: enable
    # Include or remove option fields.
    for optional_col in ([
            'populationType', 'statType', 'measurementDenominator'
    ]):
        if not pd.isna(row[optional_col]):
            new_stat_var = new_stat_var.replace(f"{{{optional_col}}}",
                                                row[optional_col])
        else:
            new_stat_var = new_stat_var.replace(
                f"{optional_col}: dcs:{{{optional_col}}}\n", "")
    return new_stat_var


def group_stat_vars_by_observation_properties(indicator_codes):
    """ Groups stat vars by their observation schemas.

        Groups Stat Vars by their inclusion of StatVar Observation
        properties like measurementMethod or Unit.
        The current template MCF schema does not support optional values in the
        CSV so we must place these stat vars into
        different template MCFs and CSVs.

        Args:
            indicator_codes: List of World Bank indicator codes with
                their Data Commons mappings, as a pandas dataframe.

        Returns:
            Array of tuples for each statistical variable grouping.
                1) template MCF, as a string.
                2) columns to include in exported csv, as a list of strings.
                3) indicator codes in this grouping, as a list of strings.
    """
    # All the statistical observation properties that we included.
    properties_of_stat_var_observation = ([
        'measurementMethod', 'scalingFactor'
    ])
    # List of tuples to return.
    tmcfs_for_stat_vars = []
    # Dataframe that tracks which values are null.
    null_status = indicator_codes.notna()

    # Iterates over all permutations of stat var properties being included.
    for permutation in list(
            itertools.product([False, True],
                              repeat=len(properties_of_stat_var_observation))):
        codes_that_match = null_status.copy()
        base_template_mcf = TEMPLATE_TMCF
        cols_to_include_in_csv = ['IndicatorCode', 'unit']

        # Loop over each obs column and whether to include it.
        for include_col, column in (zip(permutation,
                                        properties_of_stat_var_observation)):
            # Filter the dataframe by this observation.
            codes_that_match = codes_that_match.query(
                f"{column} == {include_col}")
            # Include the column in TMCF and column list.
            if include_col:
                base_template_mcf += f"{column}: C:WorldBank->{column}\n"
                cols_to_include_in_csv.append(f"{column}")

        tmcfs_for_stat_vars.append(
            (base_template_mcf, cols_to_include_in_csv,
             list(
                 indicator_codes.loc[codes_that_match.index]['IndicatorCode'])))
    return tmcfs_for_stat_vars


def download_indicator_data(worldbank_countries, indicator_codes, mode):
    """ Downloads World Bank country data for all countries and
            indicators provided.

        Retains only the unique indicator codes provided.

        Args:
            worldbank_countries: Dataframe with ISO 3166 alpha 3 code for each
                country.
            indicator_code: Dataframe with INDICATOR_CODES to include.

        Returns:
            worldbank_dataframe: A tidied pandas dataframe where each row has
            the format (indicator code, ISO 3166 alpha 3, year, value)
            for all countries and all indicators provided.
    """
    worldbank_dataframe = pd.DataFrame()
    indicators_to_keep = list(indicator_codes['IndicatorCode'].unique())

    country_df_list = []
    for index, country_code in enumerate(worldbank_countries['ISO3166Alpha3']):
        country_df = read_worldbank(country_code, mode)

        # Remove unneccessary indicators.
        country_df = country_df[country_df['IndicatorCode'].isin(
            indicators_to_keep)]

        # Map country codes to ISO.
        country_df['ISO3166Alpha3'] = country_code

        # Add new row to main datframe.
        country_df_list.append(country_df)

    worldbank_dataframe = pd.concat(country_df_list)
    # Map indicator codes to unique Statistical Variable.
    worldbank_dataframe['StatisticalVariable'] = (
        worldbank_dataframe['IndicatorCode'].apply(
            lambda code: f"WorldBank/{code.replace('.', '_')}"))
    return worldbank_dataframe.rename({'year': 'Year'}, axis=1)


def output_csv_and_tmcf_by_grouping(worldbank_dataframe,
                                    tmcfs_for_stat_vars,
                                    indicator_codes,
                                    saveOutput=True):
    """ Outputs TMCFs and CSVs for each grouping of stat vars.

        Args:
            worldbank_dataframe: Dataframe containing all indicators for all
                countries.
            tmcfs_for_stat_vars: Array of tuples of template MCF,
                columns on stat var observations,
                indicator codes for that template.
            indicator_codes -> Dataframe with INDICATOR_CODES to include.
    """
    # Only include a subset of columns in the final csv
    try:
        output_csv = worldbank_dataframe[[
            'StatisticalVariable', 'IndicatorCode', 'ISO3166Alpha3', 'Year',
            'Value', 'observationPeriod'
        ]]

        # Output tmcf and csv for each unique World Bank grouping.
        df = pd.DataFrame(columns=[
            'StatisticalVariable', 'IndicatorCode', 'ISO3166Alpha3', 'Year',
            'observationPeriod'
        ])
        if saveOutput:
            TMCF_PATH = 'output/WorldBank.tmcf'
        else:
            TMCF_PATH = 'test_data/output/output_generated.tmcf'
        with open(TMCF_PATH, 'w', newline='') as f_out:
            for index, enum in enumerate(tmcfs_for_stat_vars):
                tmcf, stat_var_obs_cols, stat_vars_in_group = enum
                if len(stat_vars_in_group) == 0:
                    continue
                f_out.write(tmcf.format_map({'idx': index}) + '\n')

                # Get only the indicator codes in that grouping.
                matching_csv = output_csv[output_csv['IndicatorCode'].isin(
                    stat_vars_in_group)]

                # Format to decimals.
                matching_csv = matching_csv.round(10)
                df = df.merge(
                    matching_csv.rename(columns={'Value': f"Value{index}"}),
                    how='outer',
                    on=[
                        'StatisticalVariable',
                        'IndicatorCode',
                        'ISO3166Alpha3',
                        'Year',
                        'observationPeriod',
                    ])
        # Include the Stat Observation columns in the output CSV.
        df = df.merge(indicator_codes[stat_var_obs_cols], on='IndicatorCode')

        # Coverting dcid to existing dcid
        df['StatisticalVariable'] = df['StatisticalVariable'].astype(str)
        df = df.replace({'StatisticalVariable': RESOLUTION_TO_EXISTING_DCID})
        if saveOutput:
            logging.info("Writing output csv")
            df.drop('IndicatorCode', axis=1).to_csv('output/WorldBank.csv',
                                                    float_format='%.10f',
                                                    index=False)
        else:
            return df
    except Exception as e:
        logging.fatal(f"Error generating output {e}")


def source_scaling_remap(row, scaling_factor_lookup, existing_stat_var_lookup):
    """ Scales values by sourceScalingFactor and inputs exisiting stat vars.

        First, this function converts all values to per capita. Some measures
        in the World Bank dataset are per thousand or per hundred thousand, but
        we need to scale these to the common denomination format. Secondly,
        some statistical variables such as Count_Person_InLaborForce are not
        World Bank specific and need to be replaced. Both of these are imputted
        from the following two lists in args.

    Args:
        scaling_factor_lookup: A dictionary of a mapping between World Bank
            indicator code to the respective numeric scaling factor.
        existing_stat_var_lookup: A dictionary of a mapping between all
            indicator to be replaced with the exisiting stat var to replace it.
    """
    indicator_code = row['IndicatorCode']
    if indicator_code in scaling_factor_lookup:
        row['Value'] = (row['Value'] /
                        int(scaling_factor_lookup[indicator_code]))

    if indicator_code in existing_stat_var_lookup:
        row['StatisticalVariable'] = ("dcid:" +
                                      existing_stat_var_lookup[indicator_code])
    return row


def process(indicator_codes, worldbank_dataframe, saveOutput=True):
    logging.info("Processing the input files")
    try:
        # Add source description to note.
        def add_source_to_description(row):
            if not pd.isna(row['Source']):
                return row['SourceNote'] + " " + str(row['Source'])
            else:
                return row['SourceNote']

        indicator_codes['SourceNote'] = indicator_codes.apply(
            add_source_to_description, axis=1)

        # Generate stat vars
        with open("output/WorldBank_StatisticalVariables.mcf", "w+") as f_out:
            # Generate StatVars for fields that don't exist. Some fields such as
            # Count_Person_Unemployed are already statistical variables so we do
            # not need to recreate them.
            for _, row in indicator_codes[
                    indicator_codes['ExistingStatVar'].isna()].iterrows():
                f_out.write(build_stat_vars_from_indicator_list(row))

        # Create template MCFs for each grouping of stat vars.
        tmcfs_for_stat_vars = (
            group_stat_vars_by_observation_properties(indicator_codes))

        # Remap columns to match expected format.
        worldbank_dataframe['Value'] = pd.to_numeric(
            worldbank_dataframe['Value'])
        worldbank_dataframe['ISO3166Alpha3'] = (
            worldbank_dataframe['ISO3166Alpha3'].apply(
                lambda code: "dcid:Earth"
                if code == "WLD" else "dcid:country/" + code))
        worldbank_dataframe['StatisticalVariable'] = \
            worldbank_dataframe['StatisticalVariable'].apply(
                lambda code: "dcs:" + code)

        # Scale values by scaling factor and replace exisiting StatVars.
        scaling_factor_lookup = (indicator_codes.set_index('IndicatorCode')
                                 ['sourceScalingFactor'].dropna().to_dict())
        existing_stat_var_lookup = (indicator_codes.set_index('IndicatorCode')
                                    ['ExistingStatVar'].dropna().to_dict())
        worldbank_dataframe = worldbank_dataframe.apply(
            lambda row: source_scaling_remap(row, scaling_factor_lookup,
                                             existing_stat_var_lookup),
            axis=1)

        # Convert integer columns.
        int_cols = (list(indicator_codes[indicator_codes['ConvertToInt'] ==
                                         True]['IndicatorCode'].unique()))
        worldbank_subset = worldbank_dataframe[
            worldbank_dataframe['IndicatorCode'].isin(int_cols)].index
        worldbank_dataframe.loc[worldbank_subset, "Value"] = (pd.to_numeric(
            worldbank_dataframe.loc[worldbank_subset, "Value"],
            downcast="integer"))
        worldbank_dataframe['observationPeriod'] = worldbank_dataframe[
            'StatisticalVariable'].apply(lambda x: '' if x in [
                'dcid:FertilityRate_Person_Female', 'dcid:LifeExpectancy_Person'
            ] else 'P1Y')
        # Output final CSVs and variables.
        df = output_csv_and_tmcf_by_grouping(worldbank_dataframe,
                                             tmcfs_for_stat_vars,
                                             indicator_codes, saveOutput)
        if not saveOutput:
            return df
    except Exception as e:
        logging.fatal(f"Error processing input file {e}")


def main(_):
    mode = _FLAGS.mode
    # Load statistical variable configuration file.
    indicator_codes = pd.read_csv(_FLAGS.indicatorSchemaFile, dtype=str)
    worldbank_countries = pd.read_csv("WorldBankCountries.csv")
    worldbank_dataframe = download_indicator_data(worldbank_countries,
                                                  indicator_codes, _FLAGS.mode)
    if mode == "" or mode == "process":
        process(indicator_codes, worldbank_dataframe)


if __name__ == '__main__':
    app.run(main)

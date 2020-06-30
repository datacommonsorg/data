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

""" Fetches, cleans, outputs TMCFs and CSVs for all WorldBank development
    indicator codes provided in WorldBankIndicators.csv for all years for
    all countries provided in WorldBankCountries.csv """

from absl import app
import pandas as pd
import itertools
import requests, zipfile, io
import re

WORLDBANK_COL_REMAP = {
    'Country Name': 'CountryName',
    'Country Code': 'CountryCode',
    'Indicator Name': 'IndicatorName',
    'Indicator Code': 'IndicatorCode'
}

# The maximum number of constraints in the indicators to generate.
MAX_CONSTRAINTS = 3

TEMPLATE_TMCF = """
Node: E:BLSJolts->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:WorldBank->StatisticalVariable
observationDate: C:WorldBank->Year
observationPeriod: P1Y
observationAbout: C:WorldBank->CountryNode
value: C:WorldBank->Value
"""

TEMPLATE_STAT_VAR = """
Node: dcid:WorldBank/{INDICATOR}
name: "{NAME}"
description: "{DESCRIPTION}"
typeOf: dcs:StatisticalVariable
populationType: {populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{CONSTRAINTS}
"""

COUNTRY_MCF = """
Node: E:WorldBank->E{X}
typeOf: dcs:Country
isoCode: dcs:{ISO_CODE}
"""


def read_worldbank(country_iso):
    """ Fetches and tidies all ~1500 Worldbank indicators for a given 3 digit ISO code.

        For a particular 3 digit ISO code, this function fetches the entire ZIP file for that
        particular country for all Worldbank indicators. The format of the file has rows for each economic indicator
        for each year. The data is tidied so that each year is a column.

        Args:
            country_iso: 3-digit ISO code for a country.

        Notes:
            Takes approximately 10 seconds to download and tidy one country in Google colab.
    """

    country_zip = f"http://api.worldbank.org/v2/en/country/{country_iso}?downloadformat=csv"
    r = requests.get(country_zip)

    filebytes = io.BytesIO(r.content)
    myzipfile = zipfile.ZipFile(filebytes)

    # We need to select data file which starts with "API",
    # but does not have an otherwise regular structure.
    file_to_open = None
    for file in myzipfile.namelist():
        if file.startswith("API"):
            file_to_open = file
            break

    assert file_to_open is not None

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
                df = df.append(pd.DataFrame([cols], columns=df.columns), ignore_index=True)

    df = df.rename(columns=WORLDBANK_COL_REMAP)

    # Turn each year into its own row.
    df = df.set_index(['CountryName', 'CountryCode', 'IndicatorName', 'IndicatorCode'])
    df = df.stack()
    df.index = df.index.rename('year', level=4)
    df.name = "Value"
    df = df.reset_index()

    # Convert to numeric and drop empty values
    df['Value'] = pd.to_numeric(df['Value'])
    df = df.dropna()

    return df


def build_stat_vars_from_indicator_list(row):
    """ Generates a WorldBank stat var for a row in the indicators dataframe. """

    def row_to_constraints(row):
        """ Helper to generate list of constraints. """
        constraints_text = ""
        next_constraint = 1

        while next_constraint <= MAX_CONSTRAINTS and not pd.isna(row[f"p{next_constraint}"]):
            variable = row[f'p{next_constraint}']
            constraint = row[f'v{next_constraint}']
            constraints_text += f"{variable}: {constraint}\n"
            next_constraint += 1

        return constraints_text

    new_stat_var = TEMPLATE_STAT_VAR.replace("{INDICATOR}", row['INDICATOR_CODE_DCID'])\
        .replace("{NAME}", row['INDICATOR_NAME'])\
        .replace("{DESCRIPTION}", row['SOURCE_NOTE'])\
        .replace("{populationType}", row['populationType'])\
        .replace("{statType}", row['StatType'])\
        .replace("{measuredProperty}", row['measuredProp'])\
        .replace("{CONSTRAINTS}", row_to_constraints(row))

    return new_stat_var


def group_stat_vars_by_observation_properties(indicator_codes):
    """ Groups Stat Vars by their inclusion of StatVar Observation properties like measurementMethod or Unit.
    The current template MCF schema does not support optional values in the CSV so we must place these stat vars into
    different template MCFs and CSVs.

        Args:
            indicator_codes: List of WorldBank indicator codes with their Data Commons mappings.

        Returns:
            Array of tuples of templace MCF, columns on stat var observations, indicator codes for that template MCF
    """

    # Group stat vars by inclusion of variable in stat var observation
    properties_belonging_to_stat_var_observation = ['measurementMethod', 'unit']

    tmcfs_for_stat_vars = []
    null_status = indicator_codes.notna()

    for permutation in list(itertools.product([False,True],repeat=len(properties_belonging_to_stat_var_observation))):
        codes_that_match = null_status.copy()
        base_template_mcf = TEMPLATE_TMCF
        cols_to_include_in_csv = ['IndicatorCode']

        for include, column in zip(permutation, properties_belonging_to_stat_var_observation):
            codes_that_match = codes_that_match.query(f"{column} == {include}")

            if include:
                base_template_mcf = base_template_mcf + f"{column}: C:WorldBank->{column}"
                cols_to_include_in_csv.append(f"{column}")

        tmcfs_for_stat_vars.append((base_template_mcf, cols_to_include_in_csv, 
            list(indicator_codes.loc[codes_that_match.index]['INDICATOR_CODE'])))

    return tmcfs_for_stat_vars


def download_indicator_data(worldbank_countries, indicator_codes):
    """ Downloads world bank country data for all countries in provided dataframe. Retains only the unique indicator codes provided.
    Additionally, creates a mapping from isoCode to MCF node.

        Args:
            worldbank_countries: Pandas dataframe with ISO_CODE for each country
            indicator_code: Pandas dataframe with INDICATOR_CODES to include

        Returns:
            worldbank_dataframe: Indicator data for all countries and all indicators provided.
            country_mcf: MCF code to resolve MCF countries via ISO code.
    """
    worldbank_dataframe = pd.DataFrame()
    indicators_to_keep = list(indicator_codes['INDICATOR_CODE'].unique())
    country_mcf = ""

    for index, country_code in enumerate(worldbank_countries['ISO_CODE']):
        country_df = read_worldbank(country_code)

        # Only retain unique list
        country_df = country_df[country_df['IndicatorCode'].isin(indicators_to_keep)]

        # Map country codes to MCF nodes
        country_df['CountryNode'] = f"E:WorldBank->E{index + 1}"
        country_mcf += COUNTRY_MCF.replace("{X}", str(index + 1)).replace("{ISO_CODE}", country_code)

        # Add to total dataframe
        worldbank_dataframe = worldbank_dataframe.append(country_df)

    # Map indicator codes to unique Statistical Variable
    worldbank_dataframe['StatisticalVariable']= worldbank_dataframe['IndicatorCode'].apply(lambda code: f"WorldBank/{code.replace('.', '_')}")
    worldbank_dataframe = worldbank_dataframe.rename({'year', 'Year'}, axis=1)

    return worldbank_dataframe, country_mcf


def output_csv_and_tmcf_by_grouping(worldbank_dataframe, tmcfs_for_stat_vars, indicator_codes, country_mcf):
    """ Outputs TMCFs and CSVs for each grouping of stat vars.

        Args: worldbank_dataframe: Dataframe containing all indicators for all
            countries tmcfs_for_stat_vars: Array of tuples of templace MCF,
            columns on stat var observations, indicator codes for that template

            MCF indicator_codes: Pandas dataframe with INDICATOR_CODES to include 
            
            country_mcf: MCF nodes for each country to prepend to each MCF file
    """
    # Only include a subset of columns in the final csv
    output_csv = worldbank_dataframe[['StatisticalVariable', 'IndicatorCode', 'CountryNode', 'Year', 'Value']]

    for index, enum in enumerate(tmcfs_for_stat_vars):
        tmcf, stat_var_obs_cols, stat_vars = enum

        if len(stat_vars) != 0:
            with open(f"WorldBank_{index}.tmcf", 'w', newline='') as f_out:
                f_out.write(tmcf)

            matching_csv = output_csv[output_csv['IndicatorCode'].isin(stat_vars)]

            # Includes IndicatorCode by default
            if len(stat_var_obs_cols) > 1:
                matching_csv = pd.merge(matching_csv, 
                                        indicator_codes[stat_var_obs_cols],
                                        on="IndicatorCode") 

            matching_csv.to_csv(f"WorldBank_{index}.csv", index=False)


def main(argv):
    # Load StatVar generation list
    indicator_codes = pd.read_csv("WorldBankIndicators.csv")

    # Generate stat vars
    with open("WorldBank_StatisticalVariables.mcf", "w+") as f_out:
        for _, row in indicator_codes.iterrows():
            f_out.write(build_stat_vars_from_indicator_list(row))

    # Create template MCFs for each grouping of stat vars
    tmcfs_for_stat_vars = group_stat_vars_by_observation_properties(indicator_codes)

    # Download data for all countries
    worldbank_countries = pd.read_csv("drive/My Drive/WorldBank/WorldBankCountries.csv")
    worldbank_dataframe, country_mcf = download_indicator_data(worldbank_countries, indicator_codes)

    # Output final CSVs and variables
    output_csv_and_tmcf_by_grouping(worldbank_dataframe, tmcfs_for_stat_vars, indicator_codes, country_mcf)

if __name__ == '__main__':
    app.run(main)

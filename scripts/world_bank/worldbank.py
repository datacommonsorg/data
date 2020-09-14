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
    indicator codes provided in WorldBankIndicators.csv for all years and for
    all countries provided in WorldBankCountries.csv. """

from absl import app
import pandas as pd
import itertools
import requests
import zipfile
import io
import re

# Remaps the columns provided by World Bank API.
WORLDBANK_COL_REMAP = {
    'Country Name': 'CountryName',
    'Country Code': 'CountryCode',
    'Indicator Name': 'IndicatorName',
    'Indicator Code': 'IndicatorCode'
}

TEMPLATE_TMCF = """
Node: E:WorldBank->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:WorldBank->StatisticalVariable
observationDate: C:WorldBank->Year
observationPeriod: "P1Y"
observationAbout: C:WorldBank->ISO3166Alpha3
value: C:WorldBank->Value
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


def read_worldbank(iso3166alpha3):
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
    country_zip = ("http://api.worldbank.org/v2/en/country/" + iso3166alpha3 +
                   "?downloadformat=csv")
    r = requests.get(country_zip)
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
                df = df.append(pd.DataFrame([cols], columns=df.columns),
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

    # yapf: disable
    # Input all required statistical variable fields.
    new_stat_var = (TEMPLATE_STAT_VAR
        .replace("{INDICATOR}", row['IndicatorCode'].replace(".", "_"))
        .replace("{NAME}", row['IndicatorName'])
        .replace("{DESCRIPTION}", row['SourceNote'])
        .replace("{measuredProperty}", row['measuredProp'])
        .replace("{CONSTRAINTS}", row_to_constraints(row))
    )
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
        'measurementMethod', 'scalingFactor', 'sourceScalingFactor', 'unit'
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
        cols_to_include_in_csv = ['IndicatorCode']

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


def download_indicator_data(worldbank_countries, indicator_codes):
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

    for index, country_code in enumerate(worldbank_countries['ISO3166Alpha3']):
        print(f"Downloading {country_code}")
        country_df = read_worldbank(country_code)

        # Remove unneccessary indicators.
        country_df = country_df[country_df['IndicatorCode'].isin(
            indicators_to_keep)]

        # Map country codes to ISO.
        country_df['ISO3166Alpha3'] = country_code

        # Add new row to main datframe.
        worldbank_dataframe = worldbank_dataframe.append(country_df)

    # Map indicator codes to unique Statistical Variable.
    worldbank_dataframe['StatisticalVariable'] = (
        worldbank_dataframe['IndicatorCode'].apply(
            lambda code: f"WorldBank/{code.replace('.', '_')}"))
    return worldbank_dataframe.rename({'year': 'Year'}, axis=1)


def output_csv_and_tmcf_by_grouping(worldbank_dataframe, tmcfs_for_stat_vars,
                                    indicator_codes):
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
    output_csv = worldbank_dataframe[[
        'StatisticalVariable', 'IndicatorCode', 'ISO3166Alpha3', 'Year', 'Value'
    ]]

    # Output tmcf and csv for each unique World Bank grouping.
    for index, enum in enumerate(tmcfs_for_stat_vars):
        tmcf, stat_var_obs_cols, stat_vars_in_group = enum
        if len(stat_vars_in_group) != 0:
            with open(f"output/WorldBank_{index}.tmcf", 'w',
                      newline='') as f_out:
                f_out.write(tmcf)

            # Output only the indicator codes in that grouping.
            matching_csv = output_csv[output_csv['IndicatorCode'].isin(
                stat_vars_in_group)]

            # Include the Stat Observation columns in the output CSV.
            if len(stat_var_obs_cols) > 1:
                matching_csv = pd.merge(matching_csv,
                                        indicator_codes[stat_var_obs_cols],
                                        on="IndicatorCode")

            # Format to decimals.
            matching_csv = matching_csv.round(10)
            matching_csv.drop("IndicatorCode",
                              axis=1).to_csv(f"output/WorldBank_{index}.csv",
                                             float_format='%.10f',
                                             index=False)


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


def main(_):
    # Load statistical variable configuration file.
    indicator_codes = pd.read_csv("WorldBankIndicators.csv")

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

    # Download data for all countries.
    worldbank_countries = pd.read_csv("WorldBankCountries.csv")
    worldbank_dataframe = download_indicator_data(worldbank_countries,
                                                  indicator_codes)

    # Remap columns to match expected format.
    worldbank_dataframe['Value'] = pd.to_numeric(worldbank_dataframe['Value'])
    worldbank_dataframe['ISO3166Alpha3'] = (
        worldbank_dataframe['ISO3166Alpha3'].apply(
            lambda code: "dcid:Earth"
            if code == "WLD" else "dcid:country/" + code))
    worldbank_dataframe['StatisticalVariable'] = \
        worldbank_dataframe['StatisticalVariable'].apply(
            lambda code: "dcs:" + code)

    # Scale values by scaling factor and replace exisiting StatVars.
    scaling_factor_lookup = (indicator_codes.set_index("IndicatorCode")
                             ['sourceScalingFactor'].dropna().to_dict())
    existing_stat_var_lookup = (indicator_codes.set_index("IndicatorCode")
                                ['ExistingStatVar'].dropna().to_dict())
    worldbank_dataframe = worldbank_dataframe.apply(
        lambda row: source_scaling_remap(row, scaling_factor_lookup,
                                         existing_stat_var_lookup),
        axis=1)

    # Convert integer columns.
    int_cols = (list(indicator_codes[indicator_codes['ConvertToInt'] == True]
                     ['IndicatorCode'].unique()))
    worldbank_subset = worldbank_dataframe[
        worldbank_dataframe['IndicatorCode'].isin(int_cols)].index
    worldbank_dataframe.loc[worldbank_subset, "Value"] = (pd.to_numeric(
        worldbank_dataframe.loc[worldbank_subset, "Value"], downcast="integer"))

    # Output final CSVs and variables.
    output_csv_and_tmcf_by_grouping(worldbank_dataframe, tmcfs_for_stat_vars,
                                    indicator_codes)


if __name__ == '__main__':
    app.run(main)

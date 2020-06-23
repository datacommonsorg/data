# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import pandas as pd
import numpy as np


def covid_harvard(confirmed_cumulative_csv: str, deaths_cumulative_csv: str, region: str):
    """Combined both confirmed_cumulaive_csv and deaths_cumulative_csv into one.
    Computes incremental daily values for all regions and dates.
    NOTE: YOU MUST IMPORT either County or State data.
    Args:
        confirmed_cumulative_csv (str): Raw CSV file from Harvard source.
        deaths_cumulative_csv (str): Raw CSV file from Harvard source.
        region (str): "County" or "State" depending on the CSV file imported.
    """
    if region not in ['State', 'County']:
        raise Exception("Invalid region!")

    print("Reading CSVs")
    confirmed_cumulative_df = pd.read_csv(confirmed_cumulative_csv)
    deaths_cumulative_df = pd.read_csv(deaths_cumulative_csv)

    print("Converting COUNTY column to fips")
    if region == 'County':
        confirmed_cumulative_df = confirmed_cumulative_df.rename(columns={'COUNTY': 'fips'})
        deaths_cumulative_df = deaths_cumulative_df.rename(columns={'COUNTY': 'fips'})

    print("Converting fips to DC geoId")
    confirmed_cumulative_df = convert_fips_to_geoId(confirmed_cumulative_df, region)
    deaths_cumulative_df = convert_fips_to_geoId(deaths_cumulative_df, region)

    print("Dropping unecessary columns")
    confirmed_cumulative_df = drop_unecessary_columns(confirmed_cumulative_df)
    deaths_cumulative_df = drop_unecessary_columns(deaths_cumulative_df)

    print("Combining DataFrames into one")
    combined = combine_dfs(confirmed_cumulative=confirmed_cumulative_df,
                                deaths_cumulative=deaths_cumulative_df)

    print("Exporting to ./output directory")
    combined.to_csv(f"./output/{region}_COVID_Harvard.csv", index=False)

def convert_fips_to_geoId(df: pd.DataFrame, region: str) -> pd.DataFrame:
    """The CSV files are in fips format.
    Let's convert it to a geoId in the formatof geoId/XX or geoId/XXXXX
    Args:
        df (Pandas DataFrame): The Pandas Dataframe containing the fips.
        region (str): The type of region of the fips. Is it a State or a County?
    Returns:
        [Pandas DataFrame]: the modified Pandas DataFrame.
    """
    # Depending on whether the region is a State or a County: geoId/XX or geoId/XXXXX
    dcid_format = "{:02}" if region == "State" else "{:05}"
    df['fips'] = df.fips.map(dcid_format.format)
    df['dcid'] = 'geoId/' + df['fips'].astype(str)
    return df

def drop_unecessary_columns(df: pd.DataFrame) -> pd.DataFrame:
    """CSV files come with some extra columns that are not needed for this import.
    Get rid of them!
    Args:
        df (Pandas DataFrame): The Pandas DataFrame containing columns to drop.
    Returns:
        [Pandas DataFrame]: the modified Pandas DataFrame.
    """
    df = df.drop(
        ['fips', 'NAME', 'POP70', 'HHD70', 'POP80', 'HHD80', 'POP90',
            'HHD90', 'POP00', 'HHD00', 'POP10', 'HHD10'], axis=1)
    df = df.set_index("dcid")
    return df

def get_value(df: pd.DataFrame, geoId: str, date: str) -> int:
    """Gets a value from the imputed Pandas DataFrame.
    It is in charge of handling any missing items.
    Args:
        df (Pandas DataFrame): The Pandas DataFrame to get the values from.
        dcid (str): The geoId of the value to query.
        date (str): The date of the value to query
    Raises:
        Exception: nullDcid: The geoId string is ""
        Exception: nullDate: The date string is ""
        Exception: nullDF: The DataFrame has no values
    Returns:
        int: the value from the DataFrame that corresponds to that geoId
    """
    if not geoId:
        raise Exception("nullgeoId")
    if not date:
        raise Exception("nullDate")
    if df.empty:
        raise Exception("nullDF")
    if not date or not geoId:
        return np.nan
    if not date in df or not geoId in df[date]:
        return np.nan
    return df[date][geoId]

def combine_dfs(confirmed_cumulative: pd.DataFrame, deaths_cumulative: pd.DataFrame):
    """Given the two DataFrames: confirmed and deaths, compute the incremental DataFrames.
    Then combine all DatFrames into one DataFrame, that will be used to export to CSV.
    Args:
        confirmed_cumulative (Pandas DataFrame): the DataFrame containing the cumulative cases
        deaths_cumulative (Pandas DataFrame): the DataFrame containing the cumulative deaths
    Returns:
        [Pandas DataFrame]: The DataFrame containing cumulative cases/deaths
        and incremental cases/deaths.
    """
    confirmed_incremental: pd.DataFrame = confirmed_cumulative.T.diff().T.fillna(0)
    deaths_incremental: pd.DataFrame = deaths_cumulative.T.diff().T.fillna(0)
    Date: list = []
    GeoId: list = []
    COVID19CumulativeCases, COVID19CumulativeDeaths = [], []
    COVID19IncrementalCases, COVID19IncrementalDeaths = [], []
    for geoId in confirmed_cumulative.index:
        for date in confirmed_cumulative:
            date_iso = date
            # Sometimes the data is in the form of XX/XX/XX, let's convert it to ISO
            if '/' in date:
                date_split = date.split('/')
                date_iso = datetime(int(date_split[2]),
                                    int(date_split[0]),
                                    int(date_split[1])).isoformat()
                date_iso = date_iso.split('T')[0]

            # Get the values from the corresponding DataFrames
            confirmed_cumulative_value = get_value(df=confirmed_cumulative,
                                                        geoId=geoId,
                                                        date=date)
            deaths_cumulative_value = get_value(df=deaths_cumulative,
                                                        geoId=geoId,
                                                        date=date)
            confirmed_incremental_value = get_value(df=confirmed_incremental,
                                                            geoId=geoId,
                                                            date=date)
            deaths_incremental_value = get_value(df=deaths_incremental,
                                                        geoId=geoId,
                                                        date=date)

            # Append the values to the correspondingb lists.
            # Instead of directly appending to the DataFrame, this is done for speed.
            Date.append(date_iso)
            GeoId.append(geoId)
            COVID19CumulativeCases.append(confirmed_cumulative_value)
            COVID19CumulativeDeaths.append(deaths_cumulative_value)
            COVID19IncrementalCases.append(confirmed_incremental_value)
            COVID19IncrementalDeaths.append(deaths_incremental_value)

    # Return a new DataFrame which will be used to export to CSV
    return pd.DataFrame({
        "Date": Date,
        "GeoId": GeoId,
        "HarvardCOVID19CumulativeCases": COVID19CumulativeCases,
        "HarvardCOVID19CumulativeDeaths": COVID19CumulativeDeaths,
        "HarvardCOVID19IncrementalCases": COVID19IncrementalCases,
        "HarvardCOVID19IncrementalDeaths": COVID19IncrementalDeaths,
    })


covid_harvard(confirmed_cumulative_csv='./input/US_State_Confirmed.csv',
             deaths_cumulative_csv='./input/US_State_Deaths.csv',
             region='State')
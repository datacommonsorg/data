# Copyright 2024 Google LLC
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
"""
This script generate output CSV
for national 1900-1979 and the file
is processed as is.
"""

import pandas as pd
import os
from absl import logging

_CODEDIR = os.path.dirname(os.path.realpath(__file__))


def process_national_1900_1970(ip_files: list) -> pd.DataFrame:
    """
    Function Loads input csv datasets
    from 1900-1979 on a National Level,
    cleans it and return cleaned dataframe.

    Args:
        ip_files (List) : list of the dataset

    Returns:
        df.columns (pd.DataFrame) : Column names of cleaned dataframe
    """
    final_df = pd.DataFrame()
    final_df2 = pd.DataFrame()
    for file in ip_files:
        try:
            filename = file
            if ".csv" in filename:
                # Extract year from the url
                year = filename[-8:-4]

                # comparing the year value as schema is chaning from 1959
                if int(year) < 1960:

                    # reading the csv format input file
                    # and converting it to a dataframe
                    df = pd.read_csv(file)
                    #Saving file to local
                    df.to_csv(_CODEDIR + "/../input_files/" +
                              f"nationals_result_{year}.csv",
                              index=False)

                    # providing proper column names
                    if len(df.columns) != 10:
                        logging.error(
                            f"Schema mismatch for {file}: expected 10 columns, but got {len(df.columns)}."
                        )
                        continue
                    df.columns = [
                        "Age", "All race total", "Count_Person_Male",
                        "Count_Person_Female", "White Total",
                        "Count_Person_Male_WhiteAlone",
                        "Count_Person_Female_WhiteAlone", "Nonwhite Total",
                        "Count_Person_Male_NonWhite", "Count_Person_Female_NonWhite"
                    ]

                    # dropping the unwanted columns
                    df.drop(columns=[
                        "Age", "All race total", "White Total", "Nonwhite Total"
                    ],
                            inplace=True)

                    # inserting year column to the dataframe
                    df.insert(loc=0, column='Year', value=year)
                    df = df.iloc[5:6, :]

                    # writing all the output to a dataframe
                    final_df = pd.concat([final_df, df], ignore_index=True)

                # for the years after 1960 as schema is changing
                else:
                    # reading the csv format input file
                    # and converting it to a dataframe
                    df2 = pd.read_csv(file)
                    df2.to_csv(_CODEDIR + "/../input_files/" +
                               f"nationals_result_{year}.csv",
                               index=False)
                    # providing proper column names
                    if len(df2.columns) != 13:
                        logging.error(
                            f"Schema mismatch for {file}: expected 13 columns, but got {len(df2.columns)}."
                        )
                        continue
                    df2.columns = [
                        "Age", "All race total", "Count_Person_Male",
                        "Count_Person_Female", "White Total",
                        "Count_Person_Male_WhiteAlone",
                        "Count_Person_Female_WhiteAlone", "Black Total",
                        "Count_Person_Male_BlackOrAfricanAmericanAlone",
                        "Count_Person_Female_BlackOrAfricanAmericanAlone",
                        "Other Races Total", "Count_Person_Male_OtherRaces",
                        "Count_Person_Female_OtherRaces"
                    ]

                    # dropping the unwanted columns
                    df2.drop(columns=[
                        "Age", "All race total", "White Total", "Black Total",
                        "Other Races Total", "Count_Person_Male_OtherRaces",
                        "Count_Person_Female_OtherRaces"
                    ],
                             inplace=True)

                    # inserting year column
                    df2.insert(loc=0, column='Year', value=year)
                    df2 = df2.iloc[4:5, :]

                    # writing all the output to a dataframe
                    final_df2 = pd.concat([final_df2, df2], ignore_index=True)
        except (pd.errors.ParserError, pd.errors.EmptyDataError, IOError,
                ValueError) as e:
            logging.error(f"Error processing {file}: {e}")
            continue

    if not final_df.empty:
        final_df = final_df.sort_values('Year')
        # inserting geoId to the final dataframe
        final_df.insert(1, 'geo_ID', 'country/USA', True)
    if not final_df2.empty:
        final_df2 = final_df2.sort_values('Year')
        final_df2.insert(1, 'geo_ID', 'country/USA', True)

    # removing numerics thousand seperator from the row values and converting to numeric
    for col in final_df.columns:
        if col not in ["Year", "geo_ID"]:
            final_df[col] = pd.to_numeric(final_df[col].astype(str).str.replace(
                ",", ""),
                                          errors='coerce')
    for col in final_df2.columns:
        if col not in ["Year", "geo_ID"]:
            final_df2[col] = pd.to_numeric(final_df2[col].astype(str).str.replace(
                ",", ""),
                                           errors='coerce')

    final_df.to_csv(_CODEDIR + "/../output_files/intermediate/" +
                    "nationals_result_1900_1959.csv",
                    index=False)
    final_df2.to_csv(_CODEDIR + "/../output_files/intermediate/" +
                     "nationals_result_1960_1979.csv",
                     index=False)

    return final_df.columns, final_df2.columns

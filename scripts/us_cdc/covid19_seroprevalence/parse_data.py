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
"""
Author: Padma Gundapaneni @padma-g
Date: 9/3/2021
Description: This script cleans a csv file of COVID-19 seroprevalence
data downloaded from the CDC. census tract, county,
URL: https://data.cdc.gov/api/views/d2tw-32xv/rows.csv?accessType=DOWNLOAD
@input_file     filepath to the original csv that needs to be cleaned
@output_file    filepath to the csv to which the cleaned data is written
python3 parse_data.py input_file output_file
"""

from datetime import datetime
import calendar
import sys
import pandas as pd

# Map of location abbreviations in the dataset to respective dcids
LOCATION_DCID_MAP = {
    'AK': 'geoId/02',
    'AL': 'geoId/01',
    'AR': 'geoId/05',
    'AZ': 'geoId/04',
    'CA': 'geoId/06',
    'CO': 'geoId/08',
    'CT': 'geoId/09',
    'DC': 'geoId/11',
    'DE': 'geoId/10',
    'FL': 'geoId/12',
    'GA': 'geoId/13',
    'HI': 'geoId/15',
    'IA': 'geoId/19',
    'ID': 'geoId/16',
    'IL': 'geoId/17',
    'IN': 'geoId/18',
    'KS': 'geoId/20',
    'KY': 'geoId/21',
    'LA': 'geoId/22',
    'MA': 'geoId/25',
    'MD': 'geoId/24',
    'ME': 'geoId/23',
    'MI': 'geoId/26',
    'MN': 'geoId/27',
    'MO': 'geoId/29',
    'MS': 'geoId/28',
    'MT': 'geoId/30',
    'NC': 'geoId/37',
    'ND': 'geoId/38',
    'NE': 'geoId/31',
    'NH': 'geoId/33',
    'NJ': 'geoId/34',
    'NM': 'geoId/35',
    'NV': 'geoId/32',
    'NY': 'geoId/36',
    'OH': 'geoId/39',
    'OK': 'geoId/40',
    'OR': 'geoId/41',
    'PA': 'geoId/42',
    'PR': 'geoId/72',
    'RI': 'geoId/44',
    'SC': 'geoId/45',
    'SD': 'geoId/46',
    'TN': 'geoId/47',
    'TX': 'geoId/48',
    'UT': 'geoId/49',
    'VA': 'geoId/51',
    'VT': 'geoId/50',
    'WA': 'geoId/53',
    'WI': 'geoId/55',
    'WV': 'geoId/54',
    'WY': 'geoId/56',
    'US': 'country/USA'
}


def get_cleaned_dates_period(date_range):
    """
    Args:
        date_range: a range of dates (ex. Jul 31 - Aug 3, 2020)
    Returns:
        - a tuple of the correctly-formatted end date and length
        of the date range, (ex. 2020-08-03, P4D)
        - returns 1 for the length of the date range
        if the date range is a single day
    """
    # Split at the comma to get the dates and the year separately
    year = date_range.split(",")[1]
    # Split the dates at the dash to get each date separately
    dates = (date_range.split(",")[0]).split("-")
    # If the date range is not a single day, set the start date
    # and end date equal to the respective items. Split each
    # date at spaces.
    if len(dates) > 1:
        start_date, end_date = (dates[0].strip() +
                                year).split(), (dates[1].strip() +
                                                year).split()
    # If the date range is a single day, set the start and end
    # dates to be the same date. Split each date at spaces.
    else:
        start_date, end_date = (dates[0].strip() +
                                year).split(), (dates[0].strip() +
                                                year).split()
    # Get the start month, day, and year using the components of the
    # split start date.
    start_month, start_day, start_year = start_date[0], int(start_date[1]), int(
        start_date[2])
    # Get the end month, day, and year using the components of the
    # split end date.
    end_month, end_day, end_year = end_date[0], int(end_date[1]), int(
        end_date[2])
    # Convert the start and end months from month abbreviations to integers
    start_month, end_month = list(calendar.month_abbr).index(start_month), list(
        calendar.month_abbr).index(end_month)
    # Create cleaned start and end dates by combining the cleaned date components
    cleaned_start_date, cleaned_end_date = (datetime(
        start_year, start_month,
        start_day)).date(), (datetime(end_year, end_month, end_day)).date()
    # Calculate the observation period by finding the difference in days
    # between the end date and the start date
    period = (cleaned_end_date - cleaned_start_date).days
    # If the period is equal to 0 (means the start date and end date are the same),
    # set the period to be 1 day.
    if period == 0:
        period = 1
    # Return the cleaned end date and correctly-formatted period of observation
    return cleaned_end_date, "P" + str(period) + "D"


def clean_col_values(value):
    """
    Args:
        value: a value in a column
    Returns:
        replaces values that are not estimates (666, 777) with blank values
            - 666 = No specimens were collected, estimates are not shown
            - 777 = Because of small cell size (n < 75), estimates are not shown
    """
    if value in (666.0, 777.0):
        value = ""
    return value


def clean_data(file_path, out_path):
    """
    Args:
        file_path: path to a comma-separated data file to be cleaned
        file_path: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    data = pd.read_csv(file_path)
    # Map the location abbreviations to their dcids
    data["Site"] = "dcid:" + data["Site"].map(LOCATION_DCID_MAP)
    # Get the cleaned end date using the date cleaning function
    data["End_Date"] = data["Date Range of Specimen Collection"].apply(
        lambda x: get_cleaned_dates_period(x)[0])
    # Get the observation period using the date cleaning function
    data["Period"] = data["Date Range of Specimen Collection"].apply(
        lambda x: get_cleaned_dates_period(x)[1])
    # Drop columns that are not needed
    data = data.drop([
        "Date Range of Specimen Collection", "Round",
        "Catchment FIPS Code Description", "Catchment Area Description",
        "Catchment population", "CI Flag [0-17 Years Prevalence]",
        "CI Flag [18-49 Years Prevalence]", "CI Flag [50-64 Years Prevalence]",
        "CI Flag [65+ Years Prevalence]", "CI Flag [Male Prevalence]",
        "CI Flag [Female Prevalence]", "CI Flag [Cumulative Prevalence]",
        "All age-sex strata had at least one positive", "Site Large CI Flag"
    ],
                     axis=1)
    # Rename the columns that are needed with shorter names
    data.columns = [
        "Site", "Count_0_17", "Percent_0_17", "LC_Percent_0_17",
        "UC_Percent_0_17", "Count_18_49", "Percent_18_49", "LC_Percent_18_49",
        "UC_Percent_18_49", "Count_50_64", "Percent_50_64", "LC_Percent_50_64",
        "UC_Percent_50_64", "Count_65", "Percent_65", "LC_Percent_65",
        "UC_Percent_65", "Count_Male", "Percent_Male", "LC_Percent_Male",
        "UC_Percent_Male", "Count_Female", "Percent_Female",
        "LC_Percent_Female", "UC_Percent_Female", "Count_Cumulative",
        "Percent_Cumulative", "LC_Percent_Cumulative", "UC_Percent_Cumulative",
        "Count_Cumulative_Infections", "LC_Count_Cumulative_Infections",
        "UC_Count_Cumulative_Infections", "End_Date", "Period"
    ]
    # Convert the columns with counts from floats to integers
    data["Count_Cumulative_Infections"] = data[
        "Count_Cumulative_Infections"].astype("Int64")
    data["LC_Count_Cumulative_Infections"] = data[
        "LC_Count_Cumulative_Infections"].astype("Int64")
    data["UC_Count_Cumulative_Infections"] = data[
        "UC_Count_Cumulative_Infections"].astype("Int64")
    # Create a list of all the columns with measured percents
    percent_cols = [
        "Percent_0_17", "Percent_18_49", "Percent_50_64", "Percent_65",
        "Percent_Male", "Percent_Female", "Percent_Cumulative"
    ]
    # For each column that has measured percent values, remove all values
    # that equal to 666 or 777. 666 or 777 means that there is no specimen was
    # collected or there was a small cell size.
    for col in percent_cols:
        data[col] = data[col].apply(clean_col_values)
    # Create a list of all the columns with NaN string values
    na_cols = [
        "LC_Percent_0_17", "UC_Percent_0_17", "LC_Percent_18_49",
        "UC_Percent_18_49", "LC_Percent_50_64", "UC_Percent_50_64",
        "LC_Percent_65", "UC_Percent_65", "LC_Percent_Male", "UC_Percent_Male",
        "LC_Percent_Female", "UC_Percent_Female", "LC_Percent_Cumulative",
        "UC_Percent_Cumulative"
    ]
    # Replace NaN values with blank strings
    for col in na_cols:
        data[col] = data[col].fillna("")
    # Output the cleaned csv
    data.to_csv(out_path, index=False)


def main():
    """Main function to generate the cleaned csv file."""
    file_path = sys.argv[1]
    out_path = sys.argv[2]
    clean_data(file_path, out_path)


if __name__ == "__main__":
    main()

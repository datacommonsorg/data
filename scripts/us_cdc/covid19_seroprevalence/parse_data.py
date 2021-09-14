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
Date: 9/13/2021
Description: This script cleans a csv file of COVID-19 seroprevalence
data downloaded from the CDC. census tract, county,
URL: https://data.cdc.gov/api/views/d2tw-32xv/rows.csv?accessType=DOWNLOAD
@input_file         filepath to the original csv that needs to be cleaned
@output_count       filepath to output the data with counts as a csv
@output_percent     filepath to output the data with percents as a csv
python3 parse_data.py input_file output_count output_percent
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

# Mapping of column names in the dataset to StatVar names
COLUMN_MAP = {
    'n [0-17 Years Prevalence]':
        'dcs:Count_Years0To17_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Rate (%) [0-17 Years Prevalence]':
        'dcs:Percent_Years0To17_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Lower CI [0-17 Years Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_Years0To17_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [0-17 Years Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_Years0To17_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [18-49 Years Prevalence]':
        'dcs:Count_Years18To49_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Rate (%) [18-49 Years Prevalence]':
        'dcs:Percent_Years18To49_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Lower CI [18-49 Years Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_Years18To49_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [18-49 Years Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_Years18To49_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [50-64 Years Prevalence]':
        'dcs:Count_Years50To64_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Rate (%) [50-64 Years Prevalence]':
        'dcs:Percent_Years50To64_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Lower CI [50-64 Years Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_Years50To64_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [50-64 Years Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_Years50To64_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [65+ Years Prevalence]':
        'dcs:Count_65OrMoreYears_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Rate (%) [65+ Years Prevalence]':
        'dcs:Percent_65OrMoreYears_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Lower CI [65+ Years Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_65OrMoreYears_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [65+ Years Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_65OrMoreYears_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [Male Prevalence]':
        'dcs:Count_Male_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Rate (%) [Male Prevalence]':
        'dcs:Percent_Male_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Lower CI [Male Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_Male_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [Male Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_Male_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [Female Prevalence]':
        'dcs:Count_Female_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Rate (%) [Female Prevalence]':
        'dcs:Percent_Female_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Lower CI [Female Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_Female_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [Female Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_Female_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'n [Cumulative Prevalence]':
        'dcs:Count_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Rate (%) [Cumulative Prevalence]':
        'dcs:Percent_MedicalConditionIncident_COVID_19_Seroprevalence',
    'Lower CI [Cumulative Prevalence]':
        'dcs:LowerConfidenceIntervalLimit_Percent_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Upper CI [Cumulative Prevalence]':
        'dcs:UpperConfidenceIntervalLimit_Percent_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Estimated cumulative infections count':
        'dcs:EstimatedCumulativeCount_MedicalConditionIncident_COVID_19_'\
        +'Seroprevalence',
    'Estimated cumulative infections lower CI 7':
        'dcs:LowerConfidenceIntervalLimit_EstimatedCumulativeCount_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence',
    'Estimated cumulative infections upper CI 7':
        'dcs:UpperConfidenceIntervalLimit_EstimatedCumulativeCount_'\
        +'MedicalConditionIncident_COVID_19_Seroprevalence'
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
    start_month, start_day, start_year = start_date[0], int(start_date[1]),\
    int(start_date[2])
    # Get the end month, day, and year using the components of the
    # split end date.
    end_month, end_day, end_year = end_date[0], int(end_date[1]),\
    int(end_date[2])
    # Convert the start and end months from month abbreviations to integers
    start_month, end_month = list(calendar.month_abbr).index(start_month),\
    list(calendar.month_abbr).index(end_month)
    # Create cleaned start and end dates by combining the cleaned date
    # components
    cleaned_start_date, cleaned_end_date = (datetime(
        start_year, start_month,
        start_day)).date(), (datetime(end_year, end_month, end_day)).date()
    # Calculate the observation period by finding the difference in days
    # between the end date and the start date
    period = (cleaned_end_date - cleaned_start_date).days
    # If the period is equal to 0 (means the start date and end date
    # are the same), set the period to be 1 day.
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


def clean_data(file_path, output_count, output_percent):
    """
    Args:
        file_path: path to a comma-separated data file to be cleaned
        output_count: path for the cleaned csv of counts
        output_percent: path for the cleaned csv of percents
    Returns:
        2 cleaned csv files
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
    # Rename the columns that are needed with StatVar names
    data.rename(columns=COLUMN_MAP, inplace=True)
    # Convert the columns with counts from floats to integers
    data["dcs:EstimatedCumulativeCount_MedicalConditionIncident_"\
    +"COVID_19_Seroprevalence"] = data[
        "dcs:EstimatedCumulativeCount_MedicalConditionIncident_"\
        +"COVID_19_Seroprevalence"].astype(
            "Int64")
    data["dcs:LowerConfidenceIntervalLimit_EstimatedCumulativeCount_"\
    +"MedicalConditionIncident_"\
    +"COVID_19_Seroprevalence"] = data[
        "dcs:LowerConfidenceIntervalLimit_EstimatedCumulativeCount_"\
        +"MedicalConditionIncident_"\
        +"COVID_19_Seroprevalence"].astype("Int64")
    data["dcs:UpperConfidenceIntervalLimit_EstimatedCumulativeCount_"\
    +"MedicalConditionIncident_"\
    +"COVID_19_Seroprevalence"] = data[
        "dcs:UpperConfidenceIntervalLimit_EstimatedCumulativeCount_"\
        +"MedicalConditionIncident_"\
        +"COVID_19_Seroprevalence"].astype("Int64")
    # For each column that has measured percent values, remove all values
    # that equal to 666 or 777. 666 or 777 means that there is no specimen was
    # collected or there was a small cell size.
    for col in data.columns:
        if "Percent" in col and "ConfidenceIntervalLimit" not in col:
            data[col] = data[col].apply(clean_col_values)
    # Replace NaN values with blank strings
    for col in data.columns:
        if "ConfidenceIntervalLimit" in col and "EstimatedCumulativeCount"\
        not in col:
            data[col] = data[col].fillna("")
    # Combine columns into single StatVar column
    data = pd.melt(data,
                   id_vars=data.columns[[0, 32, 33]],
                   value_vars=data.columns[1:31],
                   var_name='StatVar')
    # Output the cleaned csvs
    data_count = data[(~data['StatVar'].str.contains("Percent"))]
    data_percent = data[((data['StatVar'].str.contains("Percent")))]
    data_count.to_csv(output_count, index=False)
    data_percent.to_csv(output_percent, index=False)


def main():
    """Main function to generate the cleaned csv files."""
    file_path = sys.argv[1]
    output_count = sys.argv[2]
    output_percent = sys.argv[3]
    clean_data(file_path, output_count, output_percent)


if __name__ == "__main__":
    main()

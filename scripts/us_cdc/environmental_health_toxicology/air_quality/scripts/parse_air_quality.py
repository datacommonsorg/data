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
'''
Author: Samantha Piekos @spiekos and Padma Gundapaneni @padma-g
Date: 8/3/21
Description: This script cleans up a csv file on census tract or county level
air quality (ozone or 2.5 PM) data downloaded from the CDC.
URL: https://data.cdc.gov/browse?category=Environmental+Health+%26+Toxicology
@input_file   filepath to the original csv that needs to be cleaned
@output_file  filepath to the csv to which the cleaned data is written
python3 parse_air_quality.py input_file output_file
'''

import sys
import pandas as pd

# Mapping of month abbreviations to month numbers.
MONTH_MAP = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12"
}

def generate_census_tract_dcid(ctfips):
    list_dcids = []
    for index, ctfip in ctfips.items():
        dcid = "dcid:geoId/" + str(ctfip).zfill(11)
        list_dcids.append(dcid)
    return(list_dcids) 

def generate_county_dcid(data):
    list_dcids = []
    for index, row in data.iterrows():
        dcid = "dcid:geoId/" \
            + str(row["statefips"]).zfill(2) \
            + str(row["countyfips"]).zfill(3)
        list_dcids.append(dcid)
    return(list_dcids)

def generate_date(dates):
    list_dates = []
    for index, date in dates.items():
        day = date[:2]
        month = MONTH_MAP[date[2:5]]
        year = date[-4:]
        list_dates.append(year + "-" + month + "-" + day)
    return(list_dates)

def generate_date_county_ozone(data):
    list_dates = []
    for index, row in data.iterrows():
        date = str(row["Year"]) + "-" + MONTH_MAP[row["Month"]] \
         + "-" + str(row["Day"]).zfill(2)
        list_dates.append(date)
    return(list_dates)

def clean_census_tract_data(data):
    data["dcid"] = generate_census_tract_dcid(data["ctfips"])
    print("dcids generated...")
    data["date"] = generate_date(data["date"])
    print("Dates formatted...")
    data = data.drop(labels=["year", "ctfips", "latitude", "longitude"], axis=1)
    return(data)

def clean_county_data(input_file, data):
    data["dcid"] = generate_county_dcid(data)
    print("dcids generated...")
    if "Ozone" in input_file:
        data["date"] = generate_date_county_ozone(data)
        print("Dates formatted...")
        data = data.drop(labels=["Year", "Month", "Day"], axis=1)
    elif "PM2.5" in input_file:
        data["date"] = generate_date(data['date'])
        print("Dates formatted...")
        data = data.drop(labels=["year"], axis=1)
    return(data)

def clean_air_quality_data(input_file, output_file, sep):
    """
    Args:
        input_file: path to a comma-separated CDC air quality data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    print("Cleaning file...")
    data = pd.read_csv(input_file, sep=sep)
    if "Census" in input_file:
        data = clean_census_tract_data(data)
    elif "County" in input_file:
        data = clean_county_data(input_file, data)
    data = data.drop(labels=["statefips", "countyfips"], axis=1)
    print("Writing to output file...")
    data.to_csv(output_file, index=False)
    print("Finished cleaning file!")

def main():
    """Main function to generate the cleaned csv file."""
    sep = ','
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    if len(sys.argv) > 3:
        sep = sys.argv[3].strip('sep=')
    clean_air_quality_data(input_file, output_file, sep)

if __name__ == "__main__":
    main()

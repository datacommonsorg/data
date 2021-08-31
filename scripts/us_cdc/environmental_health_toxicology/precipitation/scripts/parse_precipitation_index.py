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
Date: 8/2/21
Description: This script cleans up a csv file on county level
precipitation data downloaded from the CDC.
URL: https://data.cdc.gov/browse?category=Environmental+Health+%26+Toxicology
@input_file   filepath to the original csv that needs to be cleaned
@output_file  filepath to the csv to which the cleaned data is written
python3 parse_precipitation_index.py input_file output_file
'''

import sys
import pandas as pd

def generate_dcid(fips):
    list_dcids = []
    for index, fip in fips.items():
        fip = 'dcid:geoId/' + str(fip).zfill(5)
        list_dcids.append(fip)
    return(list_dcids)

def clean_spei_file(data):
    data.rename(columns={"spei": "value"}, inplace=True)
    data["dcid"] = generate_dcid(data["fips"])
    data = data.drop(labels=['state', 'county', 'fips'], axis=1)
    return(data)

def clean_pdsi_file(data):
    data.rename(columns={"pdsi": "value"}, inplace=True)
    data["dcid"] = generate_dcid(data["countyfips"])
    data = data.drop(labels=['statefips', 'countyfips'], axis=1)
    return(data)

def clean_spi_file(data):
    data.rename(columns={"spi": "value"}, inplace=True)
    data["dcid"] = generate_dcid(data["countyfips"])
    data = data.drop(labels=['statefips', 'countyfips'], axis=1)
    return(data)

def clean_precipitation_data(input_file, output_file):
    """
    Args:
        input_file: path to a comma-separated CDC precipitation index data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    print("Cleaning file...")
    data = pd.DataFrame(pd.read_csv(input_file))
    month = data["month"].map("{:02}".format).astype(str)
    data["date"] = data["year"].astype(str) + "-" + month
    if "Standardized_Precipitation_Evapotranspiration_Index" in input_file:
        data =  clean_spei_file(data)
    elif "Palmer_Drought_Severity_Index" in input_file:
        data = clean_pdsi_file(data)
    elif "Standardized_Precipitation_Index" in input_file:
        data = clean_spi_file(data)
    data = data.drop(labels=['year', 'month'], axis=1)
    data.to_csv(output_file, index=False)
    print("Finished cleaning file!")

def main():
    """Main function to generate the cleaned csv file."""
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    clean_precipitation_data(input_file, output_file)

if __name__ == "__main__":
    main()

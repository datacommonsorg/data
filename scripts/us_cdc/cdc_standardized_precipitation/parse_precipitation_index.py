# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Description: This script cleans up a csv file on county level
precipitation data downloaded from the CDC.
URL: https://data.cdc.gov/browse?category=Environmental+Health+%26+Toxicology
@input_file     filepath to the original csv that needs to be cleaned
@output_file    filepath to the csv to which the cleaned data is written
python3 parse_precipitation_index.py input_files output_files
"""

import sys
import pandas as pd
from absl import logging
import os

logging.set_verbosity(logging.INFO)


def main():
    """Main function to generate the cleaned csv file."""
    file_path = sys.argv[1]
    output_file = sys.argv[2]
    clean_precipitation_data(file_path, output_file)


def clean_precipitation_data(file_path, output_file):
    """
    Args:
        file_path: path to a comma-separated CDC precipitation index data file
        output_file: path for the cleaned csv to be stored
    Returns:
        a cleaned csv file
    """
    logging.info("Cleaning file...")

    # Extract the directory from the output_file path
    output_dir = os.path.dirname(output_file)
    # If the directory is not empty, create it if it doesn't exist
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Ensured output directory '{output_dir}' exists.")

    data = pd.DataFrame(pd.read_csv(file_path))
    if 'pdsi' in data.columns:
        data['year'] = data['year'].astype(str).str.replace(
            r'\\t', '', regex=True).str.replace(r'""', '"', regex=True)
    data["month"] = data["month"].map("{:02}".format)
    data["date"] = data["year"].astype(str) + "-" + data["month"].astype(str)
    FIPS_TARGET_LENGTH = 5
    if "spei" in data.columns:
        data.rename(columns={
            "spei": "StandardizedPrecipitation" + "EvapotranspirationIndex"
        },
                    inplace=True)

        data["fips"] = data["fips"].astype(str)
        data["fips"] = data["fips"].str.zfill(FIPS_TARGET_LENGTH)
        data = pd.melt(
            data,
            id_vars=['state', 'county', 'fips', 'year', 'month', 'date'],
            value_vars=[
                "StandardizedPrecipitation" + "EvapotranspirationIndex"
            ],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["fips"].astype(str)
    elif "pdsi" in data.columns:
        data.rename(columns={"pdsi": "PalmerDroughtSeverityIndex_Atmosphere"},
                    inplace=True)
        data["countyfips"] = data["countyfips"].astype(str).str.zfill(
            FIPS_TARGET_LENGTH)
        data = pd.melt(
            data,
            id_vars=['year', 'month', 'date', 'statefips', 'countyfips'],
            value_vars=["PalmerDroughtSeverityIndex_Atmosphere"],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["countyfips"].astype(str)
    else:
        data.rename(columns={"spi": "StandardizedPrecipitationIndex"},
                    inplace=True)
        # Use zfill to pad 'countyfips' to 5 digits with leading zeros if shorter.
        # This is the most robust way to handle FIPS codes for all cases.
        data["countyfips"] = data["countyfips"].astype(str).str.zfill(
            FIPS_TARGET_LENGTH)
        data = pd.melt(
            data,
            id_vars=['year', 'month', 'date', 'statefips', 'countyfips'],
            value_vars=["StandardizedPrecipitationIndex"],
            var_name='StatisticalVariable',
            value_name='Value')
        data["dcid"] = "geoId/" + data["countyfips"].astype(str)
    data.to_csv(output_file, index=False)
    logging.info("Finished cleaning file!")


if __name__ == "__main__":
    main()

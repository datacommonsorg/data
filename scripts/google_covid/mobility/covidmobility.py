# Copyright 2022 Google LLC
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

import os
import sys
from absl import app
from absl import flags
from absl import logging
from os import remove, path as ospath
from csv import DictReader, DictWriter
from urllib.request import urlopen

# For finding util
_CODE_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, os.path.join(_CODE_DIR, '../../../'))
import util.name_to_alpha2 as name_to_alpha2
import util.alpha2_to_dcid as alpha2_to_dcid
import util.county_to_dcid as county_to_dcid

# Dictionary that maps a row name in the CSV file is mapped to a Schema place.
# key = CSV's row name
# value = Schema.org place
sys.path.append(os.path.join(_CODE_DIR, '../../'))
from google_covid.mobility.config import PLACE_CATEGORIES

USSTATE_TO_ALPHA2 = name_to_alpha2.USSTATE_MAP
COUNTRY_MAP = alpha2_to_dcid.COUNTRY_MAP
USSTATE_MAP = alpha2_to_dcid.USSTATE_MAP
COUNTY_MAP = county_to_dcid.COUNTY_MAP


def covid_mobility(input_path: str = './input/data.csv',
                   output_path='covid_mobility.csv') -> None:
    """Main method for the covid_mobility script.

    Args:
        path_to_store_data (str): Defaults to 'data.csv'.
        export_to (str): Defaults to 'covid_mobility.csv'.
    """

    # URL to download the data from Google Mobility site.
    url: str = "https://www.gstatic.com/covid19/mobility/" + \
               "Global_Mobility_Report.csv"
    os.makedirs('input', exist_ok=True)

    # Download CSV data from url.
    _download_data(url=url, download_as=input_path)

    # Clean CSV file.
    clean_csv(input_path, output_path)


def clean_csv(input_path: str, output_path: str) -> None:
    """Converts the Mobility data to cleaned CSV

    Args:
        input_path (str): The path to the CSV file containing the data.
        output_path (str): The path to write the output CSV file.
    """

    try:
        visited_dcids: set = set()
        logging.info(
            f"Starting CSV cleaning from '{input_path}' to '{output_path}'")
        # If output file already exists, remove it.
        if ospath.exists(output_path):
            logging.info(f"Removing existing output file: '{output_path}'")
            remove(output_path)

        try:
            f_input = open(input_path, 'r')
            # Output file.
            f_output = open(output_path, 'w')
        except IOError as e:
            logging.error(f"Error opening file: {e}")
            return
        csv_reader: DictReader = DictReader(f_input)
        csv_writer: DictWriter = DictWriter(f_output,
                                            fieldnames=[
                                                'observationAbout',
                                                'variableMeasured',
                                                'observationDate', 'value'
                                            ],
                                            doublequote=False,
                                            escapechar='\\')
        csv_writer.writeheader()
        for row in csv_reader:
            # Get the region names.
            # If the column doesn't exist, skip the row.
            try:
                # metro_area is also considered a sub_region_1.
                # They can not be combined. It's either or.
                sub_region1: str = row['sub_region_1'] or row['metro_area']
                sub_region2: str = row['sub_region_2']
                country_code: str = row['country_region_code']
                date = row['date']
            except KeyError:
                logging.error(
                    f"Missing expected column in row: {e}. Skipping row.")

            # Convert the region name to a dcid/geoId.
            region_dcid: str = _get_region_dcid(sub_region2, sub_region1,
                                                country_code)

            # If no dcid, skip the row.
            if not region_dcid:
                continue

            # If no date, skip the row.
            if not date:
                continue

            # Iterate through all places in the row.
            for place in PLACE_CATEGORIES:
                # Type of place using Schema notation.
                schema_place = PLACE_CATEGORIES[place]

                try:
                    # Get the value for the current place.
                    value = row[place]
                except KeyError:
                    raise Exception(
                        'One of the expected columns is non-existent!')

                if not value:
                    continue

                sv_dcid = 'Covid19MobilityTrend_' + schema_place
                orow = {
                    'observationAbout': 'dcid:' + region_dcid,
                    'variableMeasured': 'dcid:' + sv_dcid,
                    'observationDate': date,
                    'value': value,
                }
                csv_writer.writerow(orow)

        f_input.close()
        f_output.close()
        logging.info(f"CSV cleaning completed.")

    except Exception as e:
        logging.fatal(f"Error while cleaning {e}.")


def _download_data(url: str, download_as: str) -> None:
    """Download the data file from the input url.

    Args:
        url (str): URL of the file.
        download_as (str): path to save the file.
    """
    try:
        logging.info(f"Downloading starts..")
        # Request data from url.
        data: str = urlopen(url).read().decode('utf-8')

        # Store the data as a download_as.
        with open(download_as, 'w+') as input_file:
            input_file.write(data)
    except Exception as e:
        logging.fatal(f"Error while downloading {e}.")


def _get_region_dcid(sub_region_2: str, sub_region_1: str,
                     country_code: str) -> str:
    """Returns the dcid for the region.


    Args:
        sub_region_2 (str): Usually a US County.
        sub_region_1 (str): Usually a US State or a country's province.
        country_code (str): Country Code. Examples: ES, US.

    Returns:
        str: the dcid of the region.
    """

    # Get rid of sub_region_1 whitespaces.
    # Hashmap keys don't contain whitespaces.
    try:
        logging.info(f"Getting region dcid.")
        sub_region_1 = sub_region_1.replace(" ", "")

        if sub_region_1:
            # Only US sub-regions are allowed.
            if country_code != 'US' or sub_region_1 not in USSTATE_TO_ALPHA2:
                return None

            # Convert the State name to Alpha2.
            # Example: Florida->FL.
            sub_region_1_alpha2 = USSTATE_TO_ALPHA2[sub_region_1]

        # If the sub_region_1 is not a key in COUNTY_MAP.
        if sub_region_2 and sub_region_1_alpha2 not in COUNTY_MAP:
            logging.info("sub_region_1_alpha2 not in COUNTY_MAP")
            return None

        # If the sub_region_1_alpha2 is not a key in COUNTY_MAP[State].
        if sub_region_2 and sub_region_2 not in COUNTY_MAP[sub_region_1_alpha2]:
            logging.info(f"The value of sub_region_2 is: {sub_region_2}")
            logging.info(f"sub_region_2 not in COUNTY_MAP[sub_region_1_alpha2]")
            return None

        # If the sub_region_1_alpha2 is not a key in USSATE_MAP.
        if sub_region_1 and sub_region_1_alpha2 not in USSTATE_MAP:
            logging.info(
                f"sub_region_1 and sub_region_1_alpha2 not in USSTATE_MAP")

            return None

        # Counties.
        if sub_region_2:
            dcid = COUNTY_MAP[sub_region_1_alpha2][sub_region_2]
        # States or Provinces.
        elif sub_region_1:
            dcid = USSTATE_MAP[sub_region_1_alpha2]
        # Countries.
        else:
            dcid = COUNTRY_MAP[country_code]
        return dcid
    except Exception as e:
        logging.fatal(f"Error while retrieving DCID {e}.")


if __name__ == '__main__':
    covid_mobility()

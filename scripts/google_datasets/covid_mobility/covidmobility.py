# Copyright 2020 Google LLC
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

from sys import path

module_dir_ = os.path.dirname(os.path.realpath(__file__))
path.insert(1, os.path.join(module_dir_, '../../../'))

from os import remove, path as ospath
from csv import DictReader
from urllib.request import urlopen

import util.name_to_alpha2 as name_to_alpha2
import util.alpha2_to_dcid as alpha2_to_dcid
import util.county_to_dcid as county_to_dcid

# Dictionary that maps a row name in the CSV file is mapped to a Schema place.
# key = CSV's row name
# value = Schema.org place
from .config import PLACE_CATEGORIES

USSTATE_TO_ALPHA2 = name_to_alpha2.USSTATE_MAP
COUNTRY_MAP = alpha2_to_dcid.COUNTRY_MAP
USSTATE_MAP = alpha2_to_dcid.USSTATE_MAP
COUNTY_MAP = county_to_dcid.COUNTY_MAP


def covid_mobility(input_path: str = 'data.csv',
                   output_path='covid_mobility_output.mcf') -> None:
    """Main method for the covid_mobility script.

    Args:
        path_to_store_data (str): Defaults to 'data.csv'.
        export_to (str): Defaults to 'covid_mobility_output.mcf'.
    """

    # URL to download the data from Google Mobility site.
    url: str = "https://www.gstatic.com/covid19/mobility/" + \
               "Global_Mobility_Report.csv"

    # Download CSV data from url.
    _download_data(url=url, download_as=input_path)

    # Convert the CSV data to MCF.
    csv_to_mcf(input_path, output_path)


def csv_to_mcf(input_path: str, output_path: str) -> None:
    """Converts the Mobility data to MCF.

    Args:
        input_path (str): The path to the CSV file containing the data.
        output_path (str): The path to write the output MCF file.
    """

    visited_dcids: set = set()

    # If output file already exists, remove it.
    if ospath.exists(output_path):
        remove(output_path)

    # Input file.
    f_input = open(input_path, 'r')
    # Output file.
    f_output = open(output_path, 'a+')

    csv_reader: DictReader = DictReader(f_input)

    for row in csv_reader:
        # When this script was written, there were 14 columns.
        # If there aren't exactly 14 columns, fail.
        if len(row) != 14:
            raise Exception("Incompatible Google Mobility CSV file. " +
                            "There must be exactly 14 columns in file. " +
                            "Script must be updated!")

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
            continue

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

            population_id = f"{region_dcid}_{schema_place}"
            population_id = convert_to_ascii(population_id)

            observation_id = f"{population_id}_{date}"

            try:
                # Get the value for the current place.
                value = row[place]
            except KeyError:
                continue

            # If this is the first time vieweing this dcid.
            # Write the population node for the place.
            if region_dcid not in visited_dcids:
                f_output.write(f"Node: {population_id}\n"
                               "typeOf: schema:StatisticalPopulation\n"
                               f"location: dcid:{region_dcid}\n"
                               "populationType: dcs:PlaceVisitEvent\n"
                               f"placeCategory: dcs:{schema_place}\n\n")

            # If the value is None, skip the place.
            if not value:
                continue

            # Write observation node for value.
            f_output.write(f"Node: {observation_id}\n"
                           "typeOf: schema:Observation\n"
                           f"observedNode: l:{population_id}\n"
                           f'observationDate: "{date}"\n'
                           "measuredProperty: dcs:covid19MobilityTrend\n"
                           f"measuredValue: {value}\n"
                           "unit: dcs:Percent\n\n")

        # Add dcid to the list of visited.
        visited_dcids.add(region_dcid)

    f_input.close()
    f_output.close()


def _download_data(url: str, download_as: str) -> None:
    """Download the data file from the input url.

    Args:
        url (str): URL of the file.
        download_as (str): path to save the file.
    """

    # Request data from url.
    data: str = urlopen(url).read().decode('utf-8')

    # Store the data as a download_as.
    with open(download_as, 'w+') as input_file:
        input_file.write(data)


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
        print("sub_region_1_alpha2 not in COUNTY_MAP")
        return None

    # If the sub_region_1_alpha2 is not a key in COUNTY_MAP[State].
    if sub_region_2 and sub_region_2 not in COUNTY_MAP[sub_region_1_alpha2]:
        print(sub_region_2)
        print("sub_region_2 not in COUNTY_MAP[sub_region_1_alpha2]")
        return None

    # If the sub_region_1_alpha2 is not a key in USSATE_MAP.
    if sub_region_1 and sub_region_1_alpha2 not in USSTATE_MAP:
        print("sub_region_1 and sub_region_1_alpha2 not in USSTATE_MAP")
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


def convert_to_ascii(string: str) -> str:
    """Given a string, omit any non-ascii characters.
    The knowledge graph only supports ascii.

    Args:
        string (str): the string to convert.

    Returns:
        str: the same string, without any non-ascii characters.
        "ñàlom" would be converted to "lom".
    """

    # Get rid of non-ascii characters.
    # KG only supports ascii characters.
    string_ascii: list = [i if ord(i) < 128 else '' for i in string]
    return ''.join(string_ascii)


if __name__ == '__main__':
    covid_mobility()

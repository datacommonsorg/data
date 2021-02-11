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

from sys import path
# For import util.alpha2_to_dcid
path.insert(1, '../../../')

import csv
import io
import ssl
import urllib.request
import sys
import requests
import re
import os

import pandas as pd
import logging
import geocode_cities
import common_util as cu
import util.alpha2_to_dcid as alpha2_to_dcid

USSTATE_MAP = alpha2_to_dcid.USSTATE_MAP

_FIELDS_IN_STATE_CRIME_FILE = 14
_YEAR_INDEX = 0
_STATE_INDEX = 1
_AREA_INDEX = 2
_LEGACY_RAPE_INDEX = 8

_STATE_CRIME_FIELDS = [
    'Year',
    'State',
    'Area',
    'SubArea',
    'Population',
    # Violent Crimes
    'Violent',
    'ViolentMurderAndNonNegligentManslaughter',
    'ViolentRape',
    'ViolentRobbery',
    'ViolentAggravatedAssault',
    # Property Crimes
    'Property',
    'PropertyBurglary',
    'PropertyLarcenyTheft',
    'PropertyMotorVehicleTheft',
]

GEO_CODE = 'Geocode'
TOTAL = 'Total'

OUTPUT_COLUMNS = [
    'Year', 'GeoId', 'Count_CriminalActivities_ViolentCrime',
    'Count_CriminalActivities_MurderAndNonNegligentManslaughter',
    'Count_CriminalActivities_ForcibleRape',
    'Count_CriminalActivities_Robbery',
    'Count_CriminalActivities_AggravatedAssault',
    'Count_CriminalActivities_PropertyCrime',
    'Count_CriminalActivities_Burglary',
    'Count_CriminalActivities_LarcenyTheft',
    'Count_CriminalActivities_MotorVehicleTheft',
    'Count_CriminalActivities_CombinedCrime'
]

YEAR_TO_URL = {
    '2019':
    'https://ucr.fbi.gov/crime-in-the-u.s/2019/crime-in-the-u.s.-2019/tables/table-5/table-5.xls/output.xls',
    '2018':
    'https://ucr.fbi.gov/crime-in-the-u.s/2018/crime-in-the-u.s.-2018/tables/table-5/table-5.xls/output.xls',
    '2017':
    'https://ucr.fbi.gov/crime-in-the-u.s/2017/crime-in-the-u.s.-2017/tables/table-5/table-5.xls/output.xls',
    '2016':
    'https://ucr.fbi.gov/crime-in-the-u.s/2016/crime-in-the-u.s.-2016/tables/table-3/table-3.xls/output.xls',
    '2015':
    'https://ucr.fbi.gov/crime-in-the-u.s/2015/crime-in-the-u.s.-2015/tables/table-5/table_5_crime_in_the_united_states_by_state_2015.xls/output.xls',
    '2014':
    'https://ucr.fbi.gov/crime-in-the-u.s/2014/crime-in-the-u.s.-2014/tables/table-5/table_5_crime_in_the_united_states_by_state_2014.xls/output.xls',
    '2013':
    'https://ucr.fbi.gov/crime-in-the-u.s/2013/crime-in-the-u.s.-2013/tables/5tabledatadecpdf/table_5_crime_in_the_united_states_by_state_2013.xls/output.xls',
    '2012':
    'https://ucr.fbi.gov/crime-in-the-u.s/2012/crime-in-the-u.s.-2012/tables/5tabledatadecpdf/table_5_crime_in_the_united_states_by_state_2012.xls/output.xls',
    '2011':
    'https://ucr.fbi.gov/crime-in-the-u.s/2011/crime-in-the-u.s.-2011/tables/table-5/output.xls',
    '2010':
    'https://ucr.fbi.gov/crime-in-the-u.s/2010/crime-in-the-u.s.-2010/tables/10tbl05.xls/output.xls',
    '2009': 'https://www2.fbi.gov/ucr/cius2009/data/documents/09tbl05.xls',
    '2008': 'https://www2.fbi.gov/ucr/cius2008/data/documents/08tbl05.xls',
}


def calculate_crimes(r):
    # Return the violent, property & total
    # If a field is empty, it is treated as 0

    # Category 1: Violent Crimes
    violent = cu.int_from_field(r['Violent'])

    murder = cu.int_from_field(r['ViolentMurderAndNonNegligentManslaughter'])
    rape = cu.int_from_field(r['ViolentRape'])
    robbery = cu.int_from_field(r['ViolentRobbery'])
    assault = cu.int_from_field(r['ViolentAggravatedAssault'])

    # Add the values back as ints
    r['ViolentMurderAndNonNegligentManslaughter'] = murder
    r['ViolentRape'] = rape
    r['ViolentRobbery'] = robbery
    r['ViolentAggravatedAssault'] = assault

    violent_computed = murder + rape + robbery + assault
    if violent_computed != violent:
        print('{} {} violent mismatch {} {}'.format(r['Year'], r['State'],
                                                    violent, violent_computed))

    # Category 2: Property Crime
    property = cu.int_from_field(r['Property'])

    burglary = cu.int_from_field(r['PropertyBurglary'])
    theft = cu.int_from_field(r['PropertyLarcenyTheft'])
    motor = cu.int_from_field(r['PropertyMotorVehicleTheft'])

    # Add the property crime values as ints.
    r['PropertyBurglary'] = burglary
    r['PropertyLarcenyTheft'] = theft
    r['PropertyMotorVehicleTheft'] = motor

    # Compute totals
    property_computed = burglary + theft + motor

    if property_computed != property:
        print('{} {} property mismatch {} {}'.format(r['Year'], r['State'],
                                                     property,
                                                     property_computed))

    total = violent_computed + property_computed
    # Write back the totals
    r[TOTAL] = total
    r['Violent'] = violent_computed
    r['Property'] = property_computed


def _clean_crime_file(f_input, f_output):
    """Clean a tsv file of crime statistics.

    The input contains crime statistics, one for every state.

    Remove header and footer lines, and append state column to every line.
    Skip lines that do not contain data.
    Args:
        f_input: file object with crime statistics, one per state.
        f_output: outputstream for writing the cleaned statistics.
    """
    output_line = '{}\n'.format(','.join(_STATE_CRIME_FIELDS))
    f_output.write(output_line)

    state = ''
    count_line = 0
    count_state_total = 0
    count_incomplete_lines = 0
    count_header_footer = 0
    count_comments = 0
    for line in f_input:
        count_line += 1
        if line.startswith('#'):
            count_comments += 1
            continue
        # Split by comma and exclude comma from quotes in split
        # For case like PENNSYLVANIA,"Abington Township, Montgomery County",55476.0,53.0,0.0,6.0,0,15.0,32.0,934.0,32.0,883.0,19.0,2.0
        field = [
            '"{}"'.format(x)
            for x in list(csv.reader([line], delimiter=',', quotechar='"'))[0]
        ]

        # Skip incomplete lines
        if len(field) < _FIELDS_IN_STATE_CRIME_FILE:
            count_incomplete_lines += 1
            logging.info('%s %s', line, len(field))
            continue

        # If field[_STATE_INDEX] is present and not empty, use it as the State.
        if field[_STATE_INDEX] and field[_STATE_INDEX] != '""':
            # Remove numeric values from state names (comes from footnotes)
            state = cu.remove_digits(field[_STATE_INDEX])
        field[_STATE_INDEX] = state

        # Skip if area is not "State Total".
        if (not field[_AREA_INDEX] or field[_AREA_INDEX] != '"State Total"'):
            continue
        count_state_total += 1

        # Replace commas and quotes in fields e.g. "1,234" -> 1234
        # Remove any other leading or trailing whitespace
        for i in range(_FIELDS_IN_STATE_CRIME_FILE):
            field[i] = cu.remove_extra_chars(field[i])

        output_line = '{}\n'.format(','.join(
            field[:_FIELDS_IN_STATE_CRIME_FILE]))
        f_output.write(output_line)

    logging.info('lines: %d, comments: %d, incomplete: %d, header_footer:%d',
                 count_line, count_comments, count_incomplete_lines,
                 count_header_footer)
    logging.info('%d state totals', count_state_total)


def _update_and_calculate_state_crime(crime_csv, writer):
    with open(crime_csv, "r") as crime_f:
        crimes = csv.DictReader(crime_f)

        for crime in crimes:
            try:
                state = geocode_cities.find_crime_state(crime)
                geocode = USSTATE_MAP[state]
            except KeyError:
                assert False, '{} state or its geocode not found'.format(
                    crime['State'])

            crime['Geocode'] = geocode

            calculate_crimes(crime)

            processed_dict = {
                'Year':
                crime['Year'],
                'GeoId':
                "dcid:{}".format(crime[GEO_CODE]),
                'Count_CriminalActivities_ViolentCrime':
                crime['Violent'],
                'Count_CriminalActivities_MurderAndNonNegligentManslaughter':
                crime['ViolentMurderAndNonNegligentManslaughter'],
                'Count_CriminalActivities_ForcibleRape':
                crime['ViolentRape'],
                'Count_CriminalActivities_Robbery':
                crime['ViolentRobbery'],
                'Count_CriminalActivities_AggravatedAssault':
                crime['ViolentAggravatedAssault'],
                'Count_CriminalActivities_PropertyCrime':
                crime['Property'],
                'Count_CriminalActivities_Burglary':
                crime['PropertyBurglary'],
                'Count_CriminalActivities_LarcenyTheft':
                crime['PropertyLarcenyTheft'],
                'Count_CriminalActivities_MotorVehicleTheft':
                crime['PropertyMotorVehicleTheft'],
                'Count_CriminalActivities_CombinedCrime':
                crime[TOTAL],
            }
            writer.writerow(processed_dict)


def create_tmcf_file(tmcf_file_path):
    stat_vars = OUTPUT_COLUMNS[2:]
    with open(tmcf_file_path, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                cu.TEMPLATE_MCF_TEMPLATE.format_map({
                    'index': i,
                    'stat_var': stat_vars[i]
                }))


def create_formatted_csv_file(csv_files, state_output):
    with open(state_output, 'w') as csv_output_f:
        state_writer = csv.DictWriter(csv_output_f, fieldnames=OUTPUT_COLUMNS)
        state_writer.writeheader()

        for csv_file in csv_files:
            with open(csv_file, "r") as f_input:
                cleaned_csv_file = 'cleaned_file.csv'
                with open(cleaned_csv_file, "w") as f_output:
                    logging.info('clean crime file for csv file %s', csv_file)
                    _clean_crime_file(f_input, f_output)

                _update_and_calculate_state_crime(cleaned_csv_file,
                                                  state_writer)

                # Remove intermediate files.
                os.remove(cleaned_csv_file)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    # Script XLS and convert to CSV.
    # Add year as the first column and drop legacy rape column.
    csv_files = []
    for year, url in YEAR_TO_URL.items():
        response = requests.get(url)
        xls_file = year + '.xls'
        csv_file = year + '.csv'
        with open(xls_file, 'wb') as file:
            file.write(response.content)
        # Skip the first three rows which are table titles eg:
        #  Table 5
        #  Crime in the United States
        #  by State, 2009
        read_file = pd.read_excel(xls_file, skiprows=[0, 1, 2])
        read_file.insert(_YEAR_INDEX, 'Year', year)
        # Since the legacy rape column value should not be included in the total count, nor in forcible rape value, we drop it.
        if year in cu.YEARS_WITH_TWO_RAPE_COLUMNS:
            read_file.drop(read_file.columns[[_LEGACY_RAPE_INDEX]],
                           axis=1,
                           inplace=True)
        read_file.to_csv(csv_file, index=None, header=True)
        csv_files.append(csv_file)
        os.remove(xls_file)

    create_formatted_csv_file(csv_files, 'state_crime.csv')

    create_tmcf_file("FBI_state_crime.tmcf")

    # Remove intermediate files.
    for csv_file in csv_files:
        os.remove(csv_file)

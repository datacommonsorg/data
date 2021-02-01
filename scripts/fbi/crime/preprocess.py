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

import csv
import io
import ssl
import urllib.request
import sys
import requests
import re

import pandas as pd
import logging
import geocode_cities

# Years that FBI doesn't public arson data.
# 2019, 2018, 2017
# The FBI does not publish arson data unless it receives data from either the agency or the state for all 12 months of the calendar year.

_FIELDS_IN_CRIME_FILE = 14
_POPULATION_INDEX = 2
_STATE_INDEX = 0
_CITY_INDEX = 1
_DUMMY_RAPE_INDEX = 6

_CRIME_FIELDS = [
    'Year',
    'State',
    'City',
    'Population',
    # Violent Crimes
    'Violent',
    'ViolentMurderAndNonNegligentManslaughter',
    'ViolentRape',
    'Rape2',
    'ViolentRobbery',
    'ViolentAggravatedAssault',
    # Property Crimes
    'Property',
    'PropertyBurglary',
    'PropertyLarcenyTheft',
    'PropertyMotorVehicleTheft',
    # Arson
    'PropertyArson',
]

_CALCULATED_CRIME_FIELDS = _CRIME_FIELDS + ['Total', 'Geocode']

# From 2013-2016, the FBI reported statistics for two different definitions of rape before fully transitioning to the current definition in 2017.
# We add a dummy column after it (so allyears have two Rape columns).
YEARS_WITH_TWO_RAPE_COLUMNS = {'2013', '2014', '2015', '2016'}
YEARS_WITHOUT_POPULATION_COLUMN = {'2016'}

YEAR_TO_URL = {
    '2019':
        'https://ucr.fbi.gov/crime-in-the-u.s/2019/crime-in-the-u.s.-2019/tables/table-8/table-8.xls',
    # TODO(hanlu): un-comment these years after run code agaisnt them and check they are all fine.
    # '2018': 'https://ucr.fbi.gov/crime-in-the-u.s/2018/crime-in-the-u.s.-2018/tables/table-8/table-8.xls',
    # '2017': 'https://ucr.fbi.gov/crime-in-the-u.s/2017/crime-in-the-u.s.-2017/tables/table-8/table-8.xls',
    # '2016': 'https://ucr.fbi.gov/crime-in-the-u.s/2016/crime-in-the-u.s.-2016/tables/table-8/table-8.xls',
    # '2015': 'https://ucr.fbi.gov/crime-in-the-u.s/2015/crime-in-the-u.s.-2015/tables/table-8/table_8_offenses_known_to_law_enforcement_by_state_by_city_2015.xls',
    # '2014': 'https://ucr.fbi.gov/crime-in-the-u.s/2014/crime-in-the-u.s.-2014/tables/table-8/Table_8_Offenses_Known_to_Law_Enforcement_by_State_by_City_2014.xls',
    # '2013': 'https://ucr.fbi.gov/crime-in-the-u.s/2013/crime-in-the-u.s.-2013/tables/table-8/table_8_offenses_known_to_law_enforcement_by_state_by_city_2013.xls',
    # '2012': 'https://ucr.fbi.gov/crime-in-the-u.s/2012/crime-in-the-u.s.-2012/tables/8tabledatadecpdf/table_8_offenses_known_to_law_enforcement_by_state_by_city_2012.xls',
    # '2011': 'https://ucr.fbi.gov/crime-in-the-u.s/2011/crime-in-the-u.s.-2011/tables/table_8_offenses_known_to_law_enforcement_by_state_by_city_2011.xls',
    # '2010': 'https://ucr.fbi.gov/crime-in-the-u.s/2010/crime-in-the-u.s.-2010/tables/10tbl08.xls',
    # '2009': 'https://www2.fbi.gov/ucr/cius2009/data/documents/09tbl08.xls',
    # '2008': 'https://www2.fbi.gov/ucr/cius2008/data/documents/08tbl08.xls',
}


def _remove_extra_chars(c):
    # Remove commas and quotes from string c, and any trailing whitespace.
    # Return the cleaned_string
    return re.sub(r'[,"]', '', c).strip()


def _remove_digits(c):
    # Remove digits from string c
    # Return the cleaned string
    return re.sub(r'[\d]', '', c)


def _is_digit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def _int_from_field(f):
    # Convert a field to int value. If field is empty or non-convertible, return 0.
    # Numeric number was read in as string with ".0" suffix, eg: "12.0". First convert to float, then to int.
    try:
        f = float(f)
        f = int(f)
        return f
    except ValueError as err:
        return 0


# When there is two entries for the same city, skip the one with wrong population data.
def _should_skip_special_line(year, field):
    if year == '2019' and field[_STATE_INDEX] == 'OREGON' and field[
            _CITY_INDEX] == 'Ashland' and field[_POPULATION_INDEX] == '2670.0':
        return True
    if year == '2019' and field[_STATE_INDEX] == 'OREGON' and field[
            _CITY_INDEX] == 'Lebanon' and field[_POPULATION_INDEX] == '25959.0':
        return True
    return False


def calculate_crimes(r):
    # Return the violent, property, arson crimes & total
    # If a field is empty, it is treated as 0

    # Category 1: Violent Crimes
    violent = _int_from_field(r['Violent'])

    murder = _int_from_field(r['ViolentMurderAndNonNegligentManslaughter'])
    rape = _int_from_field(r['ViolentRape'])
    rape2 = _int_from_field(r['Rape2'])
    robbery = _int_from_field(r['ViolentRobbery'])
    assault = _int_from_field(r['ViolentAggravatedAssault'])
    # Fix rape value
    rape += rape2

    # Add the values back as ints
    r['ViolentMurderAndNonNegligentManslaughter'] = murder
    r['ViolentRape'] = rape
    r['Rape2'] = rape2
    r['ViolentRobbery'] = robbery
    r['ViolentAggravatedAssault'] = assault

    violent_computed = murder + rape + robbery + assault
    if violent_computed != violent:
        print('{} {} {} violent mismatch {} {}'.format(r['Year'], r['City'],
                                                       r['State'], violent,
                                                       violent_computed))

    # Category 2: Property Crime
    property = _int_from_field(r['Property'])

    burglary = _int_from_field(r['PropertyBurglary'])
    theft = _int_from_field(r['PropertyLarcenyTheft'])
    motor = _int_from_field(r['PropertyMotorVehicleTheft'])

    # Add the property crime values as ints.
    r['PropertyBurglary'] = burglary
    r['PropertyLarcenyTheft'] = theft
    r['PropertyMotorVehicleTheft'] = motor

    # Compute totals
    property_computed = burglary + theft + motor

    if property_computed != property:
        print('{} {} {} property mismatch {} {}'.format(r['Year'], r['City'],
                                                        r['State'], property,
                                                        property_computed))

    # Category 3: Arson
    arson = int_from_field(r['PropertyArson'])
    r['PropertyArson'] = arson

    total = violent_computed + property_computed + arson
    # Write back the totals
    r['Total'] = total
    r['Violent'] = violent_computed
    r['Property'] = property_computed


def clean_crime_file(f_input, f_output, year):
    """Clean a tsv file of crime statistics.

    The input contains crime statistics, one for every city.

    Remove header and footer lines, and append state column to every line.
    Skip lines that do not contain data.
    Args:
        f_input: file object with crime statistics, one per city.
        f_output: outputstream for writing the cleaned statistics.
        year: year string this input about. 
    """
    state = ''
    count_line = 0
    count_city = 0
    count_state = 0
    count_header_footer = 0
    count_incomplete_lines = 0
    count_comments = 0
    for line in f_input:
        count_line += 1
        if line.startswith('#'):
            count_comments += 1
            continue
        field = line.split(',')
        # Skip incomplete lines
        if len(field) < _FIELDS_IN_CRIME_FILE:
            count_incomplete_lines += 1
            logging.info('%s %s', line, len(field))
            continue

        # Replace commas and quotes in fields e.g. "1,234" -> 1234
        # Remove any other leading or trailing whitespace
        for i in range(_FIELDS_IN_CRIME_FILE):
            field[i] = _remove_extra_chars(field[i])

        # Skip if the line does not contain data or if population is empty.
        if (not field[_POPULATION_INDEX] or
                not _is_digit(field[_POPULATION_INDEX]) or
                field[_POPULATION_INDEX] == '0'):
            count_header_footer += 1
            continue

        # If field[_STATE_INDEX] is present, use it as the State.
        if field[_STATE_INDEX]:
            # Remove numeric values from state names (comes from footnotes)
            state = _remove_digits(field[_STATE_INDEX])
            count_state += 1
        field[_STATE_INDEX] = state
        # Remove any numeric characters from city names.
        field[_CITY_INDEX] = _remove_digits(field[_CITY_INDEX])
        count_city += 1

        # If duplicate lines.
        if _should_skip_special_line(year, field):
            continue

        # Keep the first n fields. Some of the files contain extra empty fields.
        output_line = '{},{}\n'.format(year,
                                       ','.join(field[:_FIELDS_IN_CRIME_FILE]))
        f_output.write(output_line)

    logging.info('lines: %d, comments: %d, incomplete: %d, header_footer:%d',
                 count_line, count_comments, count_incomplete_lines,
                 count_header_footer)
    logging.info('%d cities', count_city)
    logging.info('%d states', count_state)


def update_and_calculate_crime_csv(geo_codes, crime_csv, calculated_csv):
    with open(crime_csv) as crime_f:
        crimes = csv.DictReader(crime_f, fieldnames=_CRIME_FIELDS)
        with open(calculated_csv, 'w') as csv_output_f:
            writer = csv.DictWriter(csv_output_f,
                                    fieldnames=_CALCULATED_CRIME_FIELDS)

            found_set = set()
            cities_not_found_set = set()
            for crime in crimes:
                if geocode_cities.update_crime_geocode(crime, geo_codes,
                                                       found_set,
                                                       cities_not_found_set):
                    calculate_crimes(crime)
                    writer.writerow(crime)

        # Output the cities not_found
        with open('city_not_found.txt', 'w') as cities_not_found_f:
            for s in cities_not_found_set:
                cities_not_found_f.write('{}\n'.format(s))

        print('US src_cities = {}, cities_not_found = {}'.format(
            len(found_set), len(cities_not_found_set)))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    for year, url in YEAR_TO_URL.items():
        response = requests.get(url)
        xls_file = year + '.xls'
        csv_file = year + '.csv'
        cleaned_csv_file = year + '_cleaned.csv'
        with open(xls_file, 'wb') as file:
            file.write(response.content)
        read_file = pd.read_excel(xls_file, skiprows=[0, 1, 2])
        if year in YEARS_WITHOUT_POPULATION_COLUMN:
            read_file.insert(_POPULATION_INDEX, 'Population', 1)
        if year not in YEARS_WITH_TWO_RAPE_COLUMNS:
            read_file.insert(_DUMMY_RAPE_INDEX, 'Dummy', 0)
        read_file.to_csv(csv_file, index=None, header=True)
        with open(csv_file, "r") as f_input:
            with open(cleaned_csv_file, "w") as f_output:
                logging.info('clean crime file for year %s', year)
                clean_crime_file(f_input, f_output, year)

    geo_codes = geocode_cities.read_geocodes()
    # TODO(hanlu): update code logic to iterate over year
    update_and_calculate_crime_csv(geo_codes, '2019_cleaned.csv',
                                   '2019_calculated.csv')

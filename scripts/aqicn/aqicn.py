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
'''Generates cleaned CSVs for the AQICN air quality import.

Usage: python3 aqicn.py
'''
import csv
import io
import os
import urllib.request
from datetime import datetime

module_dir_ = os.path.dirname(__file__)

URL_PREFIX = 'https://aqicn.org/data-platform/covid19/report/37742-68557380/'
OUTPUT_PREFIX = 'output_'

FILES = [
    '2015H1',
    '2016H1',
    '2017H1',
    '2018H1',
    '2019Q1',
    '2019Q2',
    '2019Q3',
    '2019Q4',
    '2020Q1',
    '2020Q2',
    '2020Q3',
    '2020Q4',
    '2021Q1',
    '2021Q2',
    '2021Q3',
    '2021Q4',
    '',  # current
]

# Columns of input CSVs: Date,Country,City,Specie,count,min,max,median,variance
OUTPUT_COLUMNS = [
    'observationDate', 'observationAbout', 'variableMeasured', 'value', 'unit'
]
SPECIES = {
    'aqi': ('AirQualityIndex_AirPollutant', ''),
    'co': ('Concentration_AirPollutant_CO', 'PartsPerMillion'),
    'no2': ('Concentration_AirPollutant_NO2', 'PartsPerBillion'),
    'o3': ('Concentration_AirPollutant_Ozone', 'PartsPerBillion'),
    'pm10': ('Concentration_AirPollutant_PM10', 'MicrogramsPerCubicMeter'),
    'pm25': ('Concentration_AirPollutant_PM2.5', 'MicrogramsPerCubicMeter'),
    'so2': ('Concentration_AirPollutant_SO2', 'PartsPerBillion')
}

CITIES = {}
f = open(os.path.join(module_dir_, 'cities.csv'))
reader = csv.DictReader(f)
for row in reader:
    CITIES[row['name']] = row['dcid']


def datetime_valid(date):
    """Checks whether a string is a valid ISO date.

  Args:
    date: Input string to evaluate.

  Returns:
    Whether date is in valid ISO format.
  """
    try:
        datetime.fromisoformat(date)
    except:
        return False
    return True


def write_csv(csvfile, output, keys):
    """Writes cleaned CSV file.

  Args:
    csvfile: The input CSV file.
    output: The output file.
    keys: Set of keys representing processed observations.
    - Format is Date^Country^City^Specie.

  Returns:
    The updated set of processed observations.
  """
    writer = csv.DictWriter(output,
                            fieldnames=OUTPUT_COLUMNS,
                            lineterminator='\n')
    writer.writeheader()
    for row in csvfile:

        # Skip header
        if not datetime_valid(row[0]):  # Date
            continue
        if len(row) != 9:
            continue

        if row[3] not in SPECIES:  # Specie
            continue

        place = row[2] + ', ' + row[1]  # City, Country
        if place not in CITIES:
            continue

        unit = 'dcs:' + SPECIES[row[3]][1] if len(
            SPECIES[row[3]][1]) > 0 else ''
        new_row = {
            'observationDate': row[0],  # Date
            'observationAbout': 'dcid:' + CITIES[place],
            'unit': unit
        }

        # Remove duplicates :(
        key = '^'.join([row[0], row[1], row[2], row[3]])
        if key in keys:
            continue
        keys.add(key)

        minimum = new_row.copy()
        minimum['variableMeasured'] = 'dcid:Min_' + SPECIES[row[3]][0]
        minimum['value'] = row[5]  # min
        writer.writerow(minimum)

        maximum = new_row.copy()
        maximum['variableMeasured'] = 'dcid:Max_' + SPECIES[row[3]][0]
        maximum['value'] = row[6]  # max
        writer.writerow(maximum)

        median = new_row.copy()
        median['variableMeasured'] = 'dcid:Median_' + SPECIES[row[3]][0]
        median['value'] = row[7]  # median
        writer.writerow(median)

    return keys


if __name__ == '__main__':
    keys = set()
    for file in FILES:
        data = urllib.request.urlopen(URL_PREFIX + file)
        csvfile = csv.reader(io.StringIO(data.read().decode('utf-8')),
                             delimiter=',')
        output = open(OUTPUT_PREFIX + file + '.csv', 'w', newline='')
        keys = write_csv(csvfile, output, keys)

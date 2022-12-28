# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script that takes in thr .csv file and cleans the data, outputting a
new .csv file named "cleaned_output.csv" in a new "output/" folder.
"""
import csv
import pycountry
import os

# Create the output directory if it doesn't already exist.
if not os.path.exists('output'):
    os.makedirs('output')

INPUT_CSV_FILENAME = 'CurrencyFAO.csv'
OUTPUT_CSV_FILENAME = 'output/cleaned_output.csv'

# Variable for representing 'Year' in dataset.
YEAR_CODE = '7021'

# Define order or headers for output via Dictreader.
HEADERS_OUT = [
    'Country', 'Currency', 'YearMonth', 'ObservationPeriod',
    'ExchangeRatePerUSD', 'ExchangeRatePerUSD_Standardized', '# Comments'
]

# Create Dictionary for ISO code transformations.
DISSOLVED_COUNTRIES = {
    "'200": 'CSK',
    "'530": 'NLD',
    "'736": 'SDN',
    "'890": 'YUG'
}

# Open the original .csv file for reading.
with open(INPUT_CSV_FILENAME, 'r', encoding='ISO-8859-1') as csv_in:
    # Open the new .csv file for writing.
    with open(OUTPUT_CSV_FILENAME, 'w') as csv_out:
        # Create a reader and writer object.
        reader = csv.DictReader(csv_in, delimiter=',')
        writer = csv.DictWriter(csv_out, fieldnames=HEADERS_OUT)
        writer.writeheader()
        for row_dict in reader:
            processed_dict = {}
            # Create Currency column.
            processed_dict['Currency'] = row_dict['ISO Currency Code']

            # Create Year-Month column.
            if row_dict['Months Code'] == YEAR_CODE:
                processed_dict['YearMonth'] = row_dict['Year']
            else:
                processed_dict['YearMonth'] = '%s-%s' % (
                    row_dict['Year'], row_dict['Months Code'].replace("70", ""))

            # Transform country into DC readable format of "country/ISO".
            country_iso = "country/"
            if row_dict['Area Code (M49)'] in DISSOLVED_COUNTRIES:
                # Account for dissolved nation needing updated M49.
                country_iso += DISSOLVED_COUNTRIES[row_dict['Area Code (M49)']]
            else:
                pycountry_decoded = pycountry.countries.get(
                    numeric=row_dict['Area Code (M49)'].replace("\'", ""))
                country_iso += pycountry_decoded.alpha_3
            processed_dict['Country'] = country_iso

            # Define ObservationPeriod.
            if row_dict['Months Code'] == YEAR_CODE:
                processed_dict['ObservationPeriod'] = 'P1Y'
            else:
                processed_dict['ObservationPeriod'] = 'P1M'

            # Define value as local or standardized exchange rate per USD.
            if row_dict['Element Code'] == 'LCU':
                processed_dict['ExchangeRatePerUSD'] = row_dict['Value']
            elif row_dict['Element Code'] == 'SLC':
                processed_dict['ExchangeRatePerUSD_Standardized'] = row_dict[
                    'Value']

            # Create a new column called "# Comments" with original row information.
            processed_dict['# Comments'] = "#" + str(
                reader.line_num) + " row original"

            writer.writerow(processed_dict)

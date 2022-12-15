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

import csv
import pycountry

# Open the original .csv file for reading
with open('ExchangeRate_Currency.csv', 'r', encoding='ISO-8859-1') as csv_in:
    # Open the new .csv file for writing
    with open('output.csv', 'w') as csv_out:
        # Create a reader and writer object
        reader = csv.reader(csv_in)
        writer = csv.writer(csv_out)
        headers = next(reader)

        # Define columns for cleaned .csv file
        headers[0] = 'Country'
        headers[1] = 'ISOCurrencyCode'
        headers[2] = 'Currency'
        headers[3] = 'YearMonth'
        headers[4] = 'ObservationPeriod'
        headers[5] = 'ExchangeRatePerUSD'
        headers[6] = 'ExchangeRatePerUSD_Standardized'
        headers[7] = '# Comments'
        headers[8:14] = ''

        writer.writerow(headers)

        # Clean rows in the original file
        for row in reader:
            new_row = []

            #Transform country into DC readable format of "country/ISO"
            country = pycountry.countries.get(numeric=row[1][1:])
            #Account for dissolved nation needing updated M49
            if row[1] == '\'200':
                row[1] = 'CSK'
            elif row[1] == '\'530':
                row[1] = 'NLD'
            elif row[1] == '\'736':
                row[1] = 'SDN'
            elif row[1] == '\'890':
                row[1] = 'YUG'
            elif country:
                row[1] = country.alpha_3
            new_row.append('country/' + row[1])
            new_row.append(row[3])
            new_row.append(row[5])

            # Create Year-Month column
            if row[9] == '7021':
                new_row.append(row[8])
            else:
                new_row.append(row[8] + '-' + row[9][2:])

            # Define ObservationPeriod
            if row[9] == '7021':
                new_row.append('P1Y')
            else:
                new_row.append('P1M')

            # Define value as local or standardized exchange rate per USD
            if row[3] == 'LCU':
                new_row.append(row[12])
            else:
                new_row.append('')
            if row[3] == 'SLC':
                new_row.append(row[12])
            else:
                new_row.append('')

            # Create a new column called "# Comments" with original row information
            new_row.append("#" + str(reader.line_num) + ' row original')

            writer.writerow(new_row)

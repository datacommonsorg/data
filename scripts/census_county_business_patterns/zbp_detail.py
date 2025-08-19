# Copyright 2025 Google LLC
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
import os
import re
from absl import logging


class ZBPDetailProcessor:
    """Processes Zip Business Patterns (ZBP) detail data.

  This class reads ZBP detail data from a file-like object, transforms it, and
  outputs it into CSV and MCF formats.
  """

    def __init__(self, input_file_obj, output_dir, year, is_test_run):
        """Initializes the ZBPDetailProcessor.

    Args:
      input_file_obj: A file-like object containing the ZBP detail data (e.g.,
                      an io.StringIO object from downloaded GCS content).
      output_dir: The local directory path where output CSV and MCF files will be saved.
      year: The four-digit year (e.g., '2022') for which data is being processed.
      is_test_run: A boolean indicating if the script is running in test mode.
                   In test mode, processing might be limited to specific geoIds.
    """
        self.input_file_obj = input_file_obj
        self.output_dir = output_dir
        self.year = year
        self.is_test_run = is_test_run
        self.zip_col = 'zip'
        self.naics_col = 'naics'
        self.est_col = 'est'

    def _lookup_col(self, row, col):
        try:
            return row[col]
        except KeyError:
            return row[col.upper()]

    def process_zbp_detail_data(self):
        """Reads, transforms, and writes ZBP detail data to CSV and MCF files.
    """
        yyyy = self.year

        #CSV and MCF File Creation

        csv_filename = f'zbp_{yyyy}_detail.csv'
        csv_path = os.path.join(self.output_dir, csv_filename)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        logging.info('Writing CSV output to: %s', csv_path)
        # logging.info('Writing MCF output to: %s', mcf_output_path)
        with open(csv_path, 'w', newline='') as csv_f:

            csv_writer = csv.writer(csv_f)
            rows = csv.DictReader(self.input_file_obj)

            # Write the header row for the CSV output file.
            csv_writer.writerow([
                'geoId', 'year', 'NAICS', 'Establishments', 'Employees',
                'Employee Noise Flag', 'Annual Payroll', 'AP Noise Flag'
            ])

            count_rows = 0
            count_zipcodes = 0
            for r in rows:
                logging.debug('Processing row: %s', r)
                try:
                    count_zipcodes += 1

                    # Extracting  data .
                    read_zip = self._lookup_col(r, self.zip_col)
                    read_est = self._lookup_col(r, self.est_col)
                    if str(read_est).strip() == '0':
                        read_est = ''
                    read_naics = self._lookup_col(r, self.naics_col)
                    emp = ''
                    emp_nf = 'D'
                    annual_payroll = ''
                    ap_nf = 'D'
                    geoid = f'zip/{read_zip}'
                    if self.is_test_run:
                        if geoid != 'zip/00501':  # Specific geoId for test filtering
                            continue  # skip to the next row if it's not the test geoId.
                    naics = re.sub('[-/]+$', '', str(read_naics))
                    #write the data into CSV File
                    csv_writer.writerow([
                        geoid, yyyy, naics, read_est, emp, emp_nf,
                        annual_payroll, ap_nf
                    ])
                    count_rows += 1  # Total rows processed

                except Exception as ex:
                    logging.error(
                        'An unexpected error occurred while processing row: %s. Error: %s',
                        r, ex)

        logging.info('Finished processing. %d zipcodes,from %d rows.',
                     count_zipcodes, count_rows)

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
from absl import logging


class ZBPTotalsProcessor:
    """
  This class reads ZBP data from a file-like object, transforms it, and
  outputs it into CSV and MCF formats.
  """

    def __init__(self, input_file_obj, output_dir, year, is_test_run):
        """Initializing  the ZBPProcessor class
    Args:
      input_file_obj: A file-like object containing the ZBP data (files from gcs path).
      output_dir: The local directory path where output CSV and MCF files will be saved.
      year: The four-digit year (e.g., '2022') for which data is being processed.

    """
        self.input_file_obj = input_file_obj
        self.output_dir = output_dir
        self.year = year
        self.is_test_run = is_test_run

        #  class attributes.
        self.zip_col = 'zip'
        self.naics_col = 'naics'
        self.ap_col = 'ap'
        self.est_col = 'est'
        self.emp_col = 'emp'
        self.ap_nf_col = 'ap_nf'
        self.emp_nf_col = 'emp_nf'

    def _lookup_col(self, row, col):
        """Looks up a column in a row, handling potential case differences.

    Args:
      row: A dictionary representing a row from the CSV.
      col: The expected column name (e.g., 'zip').

    Returns:
      The cell value for the given column.
    Raises:
      KeyError: If the column is not found in either its original or uppercase form.
    """
        try:
            return row[col]
        except KeyError:
            return row[col.upper()]

    def process_zbp_data(self):
        """Reads, transforms, and writes ZBP data to CSV and MCF files.
    """
        yyyy = self.year
        csv_filename = f'zbp_{yyyy}_totals.csv'
        csv_path = os.path.join(self.output_dir, csv_filename)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        logging.info('Writing CSV output to: %s', csv_path)

        # Opening  all output files
        with open(csv_path, 'w', newline='') as csv_f:

            csv_writer = csv.writer(csv_f)
            rows = csv.DictReader(self.input_file_obj)

            # Write the header row for the CSV output file.
            csv_writer.writerow([
                'geoId', 'year', 'NAICS', 'Establishments', 'Employees',
                'Employee Noise Flag', 'Annual Payroll', 'AP Noise Flag'
            ])

            count_rows = 0

            for r in rows:
                logging.debug('Processing row: %s', r)
                try:

                    read_zip = self._lookup_col(r, self.zip_col)
                    read_annual_payroll = int(self._lookup_col(
                        r, self.ap_col)) * 1000
                    read_ap_nf = self._lookup_col(r, self.ap_nf_col)
                    read_est = self._lookup_col(r, self.est_col)
                    read_emp = self._lookup_col(r, self.emp_col)
                    read_emp_nf = self._lookup_col(r, self.emp_nf_col)
                    count_rows += 1
                    geoid = f'zip/{read_zip}'
                    if self.is_test_run:
                        if geoid != 'zip/00501':
                            continue  # Skip to the next row if it's not the test geoId.
                    naics = None

                    # Write the data in the CSV File
                    csv_writer.writerow([
                        geoid, yyyy, naics, read_est, read_emp, read_emp_nf,
                        read_annual_payroll, read_ap_nf
                    ])
                except Exception as ex:
                    logging.error(
                        'An unexpected error occurred while processing row: %s. Error: %s',
                        r, ex)

        logging.info('Finished processing. total rows processed %d rows.',
                     count_rows)

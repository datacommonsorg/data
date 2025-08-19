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


class CBPCOProcessor:
    """This class reads CBP CO  data from a file-like object, transforms it, and
  outputs it into CSV and MCF  formats.
  """

    def __init__(self, input_file_obj, output_dir, year, is_test_run):
        """Initializes the CBPCOProcessor.

    Args:
      input_file_obj: A file-like object containing the CBPCO county data ( downloaded GCS content).
      output_dir: The local directory path where output CSV and MCF files will be saved.
      year: The four-digit year (e.g., '2022') for which data is being processed.
      is_test_run: A boolean indicating if the script is running in test mode.
                   In test mode, processing might be limited to specific geoIds.
    """
        self.input_file_obj = input_file_obj
        self.output_dir = output_dir
        self.year = year
        self.is_test_run = is_test_run

        self.fips_state_col = 'fipstate'
        self.fips_cty_col = 'fipscty'
        self.naics_col = 'naics'
        self.ap_col = 'ap'
        self.est_col = 'est'
        self.emp_col = 'emp'
        self.ap_nf_col = 'ap_nf'
        self.emp_nf_col = 'emp_nf'

    def _lookup_col(self, row, col):
        try:
            return row[col]
        except KeyError:
            # Fallback to uppercase if original column name not found, common in some datasets.
            return row[col.upper()]

    def process_co_data(self):
        """Reads, transforms, and writes CBP county data to CSV and MCF files.
    """
        yyyy = self.year

        # Define output filenames based on the year and 'co' for county.
        csv_filename = f'cbp_{yyyy}_co.csv'
        csv_path = os.path.join(self.output_dir, csv_filename)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        logging.info('Writing CSV output to: %s', csv_path)

        # Open all output files
        with open(csv_path, 'w', newline='') as csv_f:

            csv_writer = csv.writer(csv_f)
            rows = csv.DictReader(self.input_file_obj)

            # Write the header row for the CSV output file.
            csv_writer.writerow([
                'geoId', 'year', 'NAICS', 'Establishments', 'Employees',
                'Employee Noise Flag', 'Annual Payroll', 'AP Noise Flag'
            ])

            for r in rows:
                logging.debug('Processing row: %s', r)
                try:
                    # Extract and transform data for each column
                    fips_state = self._lookup_col(r, self.fips_state_col)
                    fips_cty = self._lookup_col(r, self.fips_cty_col)
                    naics = self._lookup_col(r, self.naics_col)
                    annual_payroll = int(self._lookup_col(r,
                                                          self.ap_col)) * 1000
                    est = self._lookup_col(r, self.est_col)
                    emp = self._lookup_col(r, self.emp_col)
                    ap_nf = self._lookup_col(r, self.ap_nf_col)
                    emp_nf = self._lookup_col(r, self.emp_nf_col)

                    # Construct the geoId for the county.
                    geoid = f'geoId/{fips_state}{fips_cty}'

                    if self.is_test_run:
                        if geoid != 'geoId/01001':  # Specific geoId for test filtering
                            continue  # Skip to the next row if it's not the test geoId.
                    naics = re.sub('[-/]+$', '', str(naics))

                    # Write the processed data to the CSV  file.
                    csv_writer.writerow([
                        geoid, yyyy, naics, est, emp, emp_nf, annual_payroll,
                        ap_nf
                    ])
                except Exception as ex:
                    logging.error(
                        'An unexpected error occurred while processing row: %s. Error: %s',
                        r, ex)
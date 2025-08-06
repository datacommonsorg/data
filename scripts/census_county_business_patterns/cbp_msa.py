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
import io
from absl import logging
import write_mcf


class CBPMSAProcessor:
    """This class reads CBP MSA data from a file-like object, transforms it, and
  outputs it into CSV and MCF formats.
  """

    def __init__(self, input_file_obj, output_dir, year, is_test_run=False):
        """
    Initializes the CBPProcessor. All output paths and counters are initialized here.

    Args:
      input_file_obj: A file-like object (downloaded from gcs bucket path).
      output_dir: Base directory to place the local output files (CSV and MCF).
      year: Year to process as a four-digit string (e.g., '2016').
      is_test_run: Boolean, True if running in test mode.
    """
        self.input_file_obj = input_file_obj
        self.output_dir = output_dir
        self.year = year
        self.is_test_run = is_test_run
        #class attributes
        self.MSA_COL = 'msa'
        self.NAICS_COL = 'naics'
        self.AP_COL = 'ap'
        self.EST_COL = 'est'
        self.EMP_COL = 'emp'
        self.AP_NF_COL = 'ap_nf'
        self.EMP_NF_COL = 'emp_nf'

        # Construct CSV file FIle name
        self.csv_output_filename = f'cbp_{self.year}_msa.csv'
        self.csv_output_path = os.path.join(self.output_dir,
                                            self.csv_output_filename)

    def _lookup_col(self, row, col):
        """Looks up a column in a row, handling potential case differences.

    Args:
      row: A dictionary representing a row from the CSV.
      col: The expected column name.

    Returns:
      The cell value for the given column.
    Raises:
      KeyError: If the column is not found in either its original or uppercase form.
    """
        try:
            cell = row[col]
        except KeyError:
            cell = row[col.upper()]
        return cell

    def process_cbp_data(self):
        """
    Reads, transforms, and writes CBP data for the initialized year from the
    provided input_file_obj. File resources are managed here using 'with' statements.
    """
        logging.info('Starting CBP data processing for year: %s', self.year)
        logging.info('Writing CSV to local: %s', self.csv_output_path)
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        try:
            with open(self.csv_output_path, 'w', newline='') as csv_f:
                rows = csv.DictReader(self.input_file_obj)
                csv_writer = csv.writer(csv_f)

                # Write CSV header row
                csv_writer.writerow([
                    'geoId', 'year', 'NAICS', 'Establishments', 'Employees',
                    'Employee Noise Flag', 'Annual Payroll', 'AP Noise Flag'
                ])

                for r in rows:
                    logging.debug('Processing row: %s', r)

                    msa = self._lookup_col(r, self.MSA_COL)
                    naics = self._lookup_col(r, self.NAICS_COL)
                    annual_payroll_raw = self._lookup_col(r, self.AP_COL)
                    est = self._lookup_col(r, self.EST_COL)
                    emp = self._lookup_col(r, self.EMP_COL)
                    ap_nf = self._lookup_col(r, self.AP_NF_COL)
                    emp_nf = self._lookup_col(r, self.EMP_NF_COL)
                    annual_payroll = int(annual_payroll_raw) * 1000
                    geoid = f'geoId/C{msa}'
                    if self.is_test_run:
                        # If running in test mode, process only a specific MSA (e.g., 'C10100')
                        if geoid != 'geoId/C10100':
                            continue  # Skip rows not matching the test geoId
                    naics = re.sub(r'[-/]+$', '', str(naics))

                    # Write data to CSV output file
                    csv_writer.writerow([
                        geoid, self.year, naics, est, emp, emp_nf,
                        annual_payroll, ap_nf
                    ])

            logging.info('CBP data processing complete for year %s.', self.year)

        except Exception as e:
            logging.error('An unexpected error occurred during processing: %s',
                          e)

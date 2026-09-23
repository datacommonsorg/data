# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""CSV and TSV file reader and writer (`CsvFileDictIO`) for `file_dict_io`.

Example:
  from file_dict_io import CsvFileDictIO

  with CsvFileDictIO('people.csv', mode='w', headers=['name', 'age']) as writer:
    writer.write({'name': 'Alice', 'age': '30'})
"""

import csv
from io import UnsupportedOperation
import os
from absl import logging

from file_dict_io.base import FileDictIO
import file_util


def is_csv_file(filename: str) -> bool:
    """Returns True if `filename` refers to a CSV/TSV file or Google Spreadsheet.

    Example:
      from file_dict_io import is_csv_file

      is_csv_file('data/observations.csv')  # Returns True
      is_csv_file('data/nodes.mcf')         # Returns False

    Args:
      filename: Path or URL to check.

    Returns:
      `True` if the filename contains `.csv` or `.tsv` or is a Google
      Spreadsheet URL; `False` otherwise.
    """
    basename = os.path.basename(filename)
    if '.csv' in basename or '.tsv' in basename:
        return True
    if file_util.file_is_google_spreadsheet(filename):
        return True
    return False


@FileDictIO.register
class CsvFileDictIO(FileDictIO):
    """Reads or writes dictionary records from/to a CSV or TSV file.

    Each row in the CSV file is represented as a `dict` keyed by the CSV column
    headers.

    Example:
      from file_dict_io import CsvFileDictIO

      with CsvFileDictIO('people.csv', mode='w', headers=['name', 'age']) as writer:
        writer.write({'name': 'Alice', 'age': '30'})

      with CsvFileDictIO('people.csv', mode='r') as reader:
        for row in reader:
          print(row['name'], row['age'])
    """

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if `filename` is a CSV, TSV, or Google Spreadsheet."""
        return is_csv_file(filename)

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 **kwargs):
        """Initializes a `CsvFileDictIO` reader or writer.

        Args:
          filename: Path to the CSV/TSV file or Google Spreadsheet URL.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of column names for writing. If omitted,
            column headers are inferred from the first record written.
          encoding: Optional text encoding.
          **kwargs: Optional format-specific keyword arguments.
        """
        super().__init__(filename, mode, headers, encoding, **kwargs)
        self._csv_reader = None
        self._csv_writer = None
        self.open()

    def open(self):
        """Opens the CSV file with `csv.DictReader` (read) or `csv.DictWriter` (write)."""
        # Create a file handle for the file.
        super().open()
        if self.is_read_mode():
            # Read the CSV file handle using DictReader and populate headers.
            options = file_util.file_get_csv_reader_options(
                self.filename(), {'delimiter': ','})
            self._csv_reader = csv.DictReader(self.get_file_handle(), **options)
            self.set_headers(self._csv_reader.fieldnames)
            logging.level_debug() and logging.debug(
                f'Opened CSV file {self.filename()} for {self._mode} with options: {options}, headers: {self.headers()}'
            )
        else:
            # Write to the CSV file handle using DictWriter if headers are known.
            if self.headers():
                self._csv_writer = csv.DictWriter(
                    self.get_file_handle(),
                    fieldnames=self.headers(),
                    escapechar='\\',
                    extrasaction='ignore',
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                )
                self.write_header()
                logging.level_debug() and logging.debug(
                    f'Opened CSV file {self.filename()} for {self._mode} with headers: {self.headers()}'
                )
            else:
                logging.info(
                    f'Headers not set for CSV file {self.filename()}. Deferring headers until first record write.'
                )

    def write_header(self):
        """Writes the CSV header row once."""
        if self._csv_writer and not self._header_written:
            self._csv_writer.writeheader()
            self._header_written = True

    def write_record(self, record: dict):
        """Writes one dictionary record as a CSV row.

        If headers were not provided when the file was opened, they are inferred
        from the keys of the first record written.

        Args:
          record: Dictionary mapping column names to row values.

        Returns:
          The return value of `csv.DictWriter.writerow`.

        Raises:
          UnsupportedOperation: If the CSV writer cannot be initialized.
        """
        if not self._csv_writer:
            # This is the first record; initialize the CSV writer from its keys.
            self.set_headers_from_record(record)
            self.open()
            if not self._csv_writer:
                logging.fatal(
                    f'Unable to open CSV file {self.filename()} for write without headers'
                )
        if self._csv_writer:
            self._record_index += 1
            return self._csv_writer.writerow(record)
        raise UnsupportedOperation(
            f'Cannot write record to CSV file {self.filename()} in mode {self._mode} with headers {self.headers()}'
        )

    def next(self) -> dict:
        """Returns the next row from the CSV file as a dictionary.

        Returns:
          A `dict` for the next CSV row, or `None` if the end of the file is
          reached.
        """
        try:
            if self._csv_reader:
                record = next(self._csv_reader)
                self._record_index += 1
                return record
        except StopIteration:
            # Reached end of file.
            return None
        return None

    def headers(self) -> list:
        """Returns the list of column names for the CSV file."""
        if self._csv_reader is not None:
            return self._csv_reader.fieldnames
        return self._headers

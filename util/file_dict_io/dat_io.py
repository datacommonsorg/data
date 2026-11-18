# Copyright 2026 Google LLC
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
"""DAT file reader (`DatFileDictIO`) for `file_dict_io`.

Example:
  # people.dat (pipe-delimited, with a header row):
  #   name|age|city
  #   Alice|30|San Francisco, CA
  #   Bob|07|New York, NY

  from file_dict_io import DatFileDictIO

  with DatFileDictIO('people.dat', mode='r') as reader:
    for row in reader:
      print(row['name'], row['age'], row['city'])
  # Alice 30 San Francisco, CA
  # Bob 07 New York, NY
"""

import csv
from io import UnsupportedOperation

from absl import logging
from file_dict_io.base import FileDictIO
from file_dict_io.base import get_file_extension
from file_dict_io.csv_io import CsvFileDictIO

# Candidate delimiters, in priority order for ties.
_DELIMITER_CANDIDATES = ['|', '\t', ';', ',']


def is_dat_file(filename: str) -> bool:
    """Returns True if `filename` refers to a `.dat` file."""
    return get_file_extension(filename) == '.dat'


def _detect_delimiter(header_line: str) -> str:
    """Returns the candidate character that occurs most often in the header.

    Args:
      header_line: First line of the file.

    Returns:
      The detected delimiter character.

    Raises:
      ValueError: If no candidate delimiter occurs in `header_line`.
    """
    counts = {c: header_line.count(c) for c in _DELIMITER_CANDIDATES}
    delimiter = max(_DELIMITER_CANDIDATES, key=lambda c: counts[c])
    if counts[delimiter] == 0 and header_line.strip():
        logging.warning(
            'No delimiter found in the header row; reading as a single column.')
    return delimiter


@FileDictIO.register
class DatFileDictIO(CsvFileDictIO):
    """Reads dictionary records from a delimited .dat file.

    Each row in the .dat file is represented as a `dict` keyed by the column
    headers. The delimiter is detected from the header row (pipe, tab,
    semicolon or comma) unless `delimiter` is given. Quote characters are
    treated as literal text, and header names are cleaned of a UTF-8 BOM,
    surrounding whitespace and a leading '#'.

    Example:
      from file_dict_io import DatFileDictIO

      with DatFileDictIO('people.dat', mode='r') as reader:
        for row in reader:
          print(row['name'], row['age'])
    """

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if `filename` is a .dat file."""
        return is_dat_file(filename)

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 start_offset: int = 0,
                 end_offset: int = None,
                 delimiter: str = None,
                 **kwargs):
        """Initializes a `DatFileDictIO` reader.

        Args:
          filename: Path to the .dat file.
          mode: File open mode. Only 'r' (read) is supported.
          headers: Optional list of column names, for files without a header
            row.
          encoding: Optional text encoding.
          start_offset: Optional starting byte offset for read mode.
          end_offset: Optional ending byte offset for read mode.
          delimiter: Optional delimiter character. If omitted, it is detected
            from the header row.
          **kwargs: Optional format-specific keyword arguments.
        """
        self._delimiter = delimiter
        super().__init__(filename,
                         mode,
                         headers,
                         encoding,
                         start_offset=start_offset,
                         end_offset=end_offset,
                         **kwargs)

    def open(self):
        """Opens the .dat file for reading using the CSV handler."""
        if not self.is_read_mode():
            raise UnsupportedOperation(
                f'Writing .dat files is not supported: {self.filename()}')
        super().open()

    def _get_reader_options(self, sample: str) -> dict:
        """Returns csv reader options with literal quotes."""
        header_line = sample.split('\n', 1)[0]
        delimiter = self._delimiter or _detect_delimiter(header_line)
        return {'delimiter': delimiter, 'quoting': csv.QUOTE_NONE}

    def _clean_headers(self, headers: list) -> list:
        """Returns header names without BOM, surrounding spaces or a '#'."""
        headers = super()._clean_headers(headers)
        return [h.strip().lstrip('#').strip() for h in headers]

    def write_header(self):
        raise UnsupportedOperation('Writing .dat files is not supported.')

    def write_record(self, record: dict):
        raise UnsupportedOperation('Writing .dat files is not supported.')

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
from absl import logging

from file_dict_io.base import FileDictIO, get_file_extension
import file_util


def is_tsv_file(filename: str) -> bool:
    """Returns True if `filename` refers to a tab-separated (`.tsv`) file."""
    return get_file_extension(filename) == '.tsv'


def is_csv_file(filename: str) -> bool:
    """Returns True if `filename` refers to a CSV/TSV file or Google Spreadsheet.

    Example:
      from file_dict_io import is_csv_file

      is_csv_file('data/observations.csv')  # Returns True
      is_csv_file('data/nodes.mcf')         # Returns False

    Args:
      filename: Path or URL to check.

    Returns:
      `True` if the normalized format extension is `.csv` or `.tsv` or if
      `filename` is a Google Spreadsheet URL; `False` otherwise.
    """
    if not isinstance(filename, str):
        return False
    if get_file_extension(filename) in ('.csv', '.tsv'):
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
                 start_offset: int = 0,
                 end_offset: int = None,
                 **kwargs):
        """Initializes a `CsvFileDictIO` reader or writer.

        Args:
          filename: Path to the CSV/TSV file or Google Spreadsheet URL.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of column names for writing. If omitted,
            column headers are inferred from the first record written.
          encoding: Optional text encoding.
          start_offset: Optional starting byte offset for read mode.
          end_offset: Optional ending byte offset for read mode.
          **kwargs: Optional format-specific keyword arguments.
        """
        self._csv_options = {}
        self._csv_reader = None
        self._csv_writer = None
        self._header_end_pos = 0
        self._reading_row = False
        super().__init__(filename,
                         mode,
                         headers,
                         encoding,
                         start_offset=start_offset,
                         end_offset=end_offset,
                         **kwargs)
        self.open()

    def open(self):
        """Opens the CSV file with `csv.DictReader` (read) or `csv.DictWriter` (write)."""
        # Create a file handle for the file.
        super().open()
        is_tsv = is_tsv_file(self.filename())
        default_delim = '\t' if is_tsv else ','
        if self.is_read_mode():
            # Read the CSV file handle using DictReader and populate headers.
            fp = self.get_file_handle()
            fp.seek(0)
            try:
                sample = fp.read(4096)
            except UnicodeDecodeError:
                if self._encoding is not None:
                    raise
                detected = file_util.file_get_encoding(self.filename())
                if not detected or detected.lower().replace(
                        '_', '-') in ('ascii', 'utf-8', 'utf8'):
                    detected = 'latin-1'
                self.close()
                self._encoding = detected
                super().open()
                fp = self.get_file_handle()
                fp.seek(0)
                sample = fp.read(4096)
            delim_chars = ['\t'] if is_tsv else [',', '\t', ';', '|']
            options = file_util.file_get_csv_reader_options(
                self.filename(),
                {'delimiter': default_delim},
                data=sample,
                delim_chars=delim_chars,
            )
            if is_tsv:
                options['delimiter'] = '\t'
            # Use RFC 4180 doubled quotes: the sniffer sets doublequote=False
            # if its sample has no "" in a field. The sniffed quotechar is
            # kept, so files quoted with ' still read correctly.
            options.update(doublequote=True)
            self._csv_options = options
            fp.seek(0)
            header_reader = csv.reader(iter(fp.readline, ''),
                                       **self._csv_options)
            file_headers = []
            try:
                file_headers = next(header_reader)
                while file_headers == []:
                    file_headers = next(header_reader)
            except StopIteration:
                file_headers = []
            first_row_end = fp.tell()
            if not self._headers:
                self._header_end_pos = first_row_end
                self.set_headers(file_headers)
            elif file_headers == self._headers:
                self._header_end_pos = first_row_end
            else:
                self._header_end_pos = 0
                fp.seek(0)
            if self._start_offset > 0:
                self.seek(self._start_offset)
            else:
                self._next_record_start = self._header_end_pos
                self._reading_row = False
                self._csv_reader = csv.DictReader(self._iter_csv_lines(),
                                                  fieldnames=self.headers(),
                                                  **self._csv_options)
            logging.debug(
                f'Opened CSV file {self.filename()} for {self._mode} with options: {options}, headers: {self.headers()}'
            )
        else:
            # Write to the CSV file handle using DictWriter if headers are known.
            if self.headers():
                self._init_writer()
            else:
                logging.info(
                    f'Headers not set for CSV file {self.filename()}. Deferring headers until first record write.'
                )

    def _init_writer(self):
        """Initializes `self._csv_writer` and writes the header row once."""
        if not self.headers() or self._csv_writer:
            return
        is_tsv = get_file_extension(self._filename) == '.tsv'
        default_delim = '\t' if is_tsv else ','
        # RFC 4180: quote fields only when needed and double any quote
        # inside a field. No escape character, so '\' is written as is.
        self._csv_writer = csv.DictWriter(
            self.get_file_handle(),
            fieldnames=self.headers(),
            delimiter=default_delim,
            extrasaction='ignore',
            quotechar='"',
            doublequote=True,
            quoting=csv.QUOTE_MINIMAL,
        )
        self.write_header()
        logging.debug(
            f'Opened CSV file {self.filename()} for {self._mode} with headers: {self.headers()}'
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
          UnsupportedOperation: If opened in read mode or if the CSV writer
            cannot be initialized (e.g. empty record with no headers).
        """
        if self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot write record to CSV file {self.filename()} opened in read mode {self._mode}'
            )
        if not self._csv_writer:
            # This is the first record; initialize the CSV writer from its keys.
            self.set_headers_from_record(record)
            if self.headers():
                self._init_writer()
        if self._csv_writer:
            self._record_index += 1
            return self._csv_writer.writerow(record)
        raise UnsupportedOperation(
            f'Cannot write record to CSV file {self.filename()} in mode {self._mode} with headers {self.headers()}'
        )

    def seek(self, offset: int) -> int:
        """Seeks to the first complete CSV record starting at or after `offset`.

        Caveats:
          - Multiline Quoted Values: RFC 4180 permits CSV fields to contain raw
            newlines within quotes (e.g. `"line1\nline2"`). If `offset` falls
            inside a multiline quoted field, scanning for the next newline `\n`
            will split the cell across record boundaries and corrupt the first
            read row. Seeking is safe for CSV/TSV files whose field values do not
            contain unescaped raw newlines.
          - Blank Lines: Trailing or empty lines are skipped cleanly.

        Args:
          offset: Byte offset in the file to seek past.

        Returns:
          The actual byte offset where the next CSV record begins.

        Raises:
          UnsupportedOperation: If the file is not opened in read mode.
        """
        if not self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot seek in write mode for CSV file {self.filename()}')
        fp = self.get_file_handle()
        if fp is None:
            return 0
        self._start_offset = offset

        if offset <= self._header_end_pos:
            fp.seek(self._header_end_pos)
            self._next_record_start = self._header_end_pos
        else:
            self._next_record_start = self._seek_to_next_line(offset)

        self._reading_row = False
        self._csv_reader = csv.DictReader(self._iter_csv_lines(),
                                          fieldnames=self.headers(),
                                          **self._csv_options)
        return self._next_record_start

    def _iter_csv_lines(self):
        """Yields CSV lines while enforcing `end_offset` at record boundaries."""
        fp = self.get_file_handle()
        if fp is None:
            return
        if self._end_offset is None:
            yield from iter(fp.readline, '')
            return
        end_offset = self._end_offset
        while True:
            if not self._reading_row:
                pos = fp.tell()
                self._next_record_start = pos
                if pos >= end_offset:
                    return
            line = fp.readline()
            if not line:
                return
            if not self._reading_row and line in ('\n', '\r\n', '\r'):
                continue
            self._reading_row = True
            yield line

    def next(self) -> dict:
        """Returns the next row from the CSV file as a dictionary.

        Returns:
          A `dict` for the next CSV row, or `None` if the end of the file or
          `end_offset` is reached.
        """
        if not self._csv_reader:
            return None
        if self._end_offset is not None and self._next_record_start is not None:
            if self._next_record_start >= self._end_offset:
                return None
        self._reading_row = False
        try:
            row = next(self._csv_reader)
            fp = self.get_file_handle()
            self._next_record_start = fp.tell() if fp else None
            self._record_index += 1
            return row
        except StopIteration:
            return None

    def headers(self) -> list:
        """Returns the list of column names for the CSV file."""
        if self._csv_reader is not None:
            return self._csv_reader.fieldnames
        return self._headers

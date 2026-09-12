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
"""Class to read/write a sequence of dictionary objects from/to file.

The dictionary is written as a csv or MCF node.
"""

import csv
import os
import sys

from absl import logging
from abc import ABC, abstractmethod

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.dirname(_SCRIPT_DIR))
sys.path.append(
    os.path.join(os.path.dirname(_SCRIPT_DIR), "tools", "statvar_importer"))

import file_util
import mcf_file_util


class FileDictIO(ABC):
    """Base class to write record of dictionary to a file."""

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = [],
                 encoding: str = None):
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._headers = headers
        self._fp = None

    def __del__(self):
        self.close()

    def is_read_mode(self):
        """Returns True if the file is set to read mode."""
        return self._mode.startswith('r')

    def open(self):
        """Open file for reading or writing using FileIO.
    Saves the file handle for future writes.
    If there is a header, writes the header at the start of the file."""
        logging.level_debug() and logging.debug(
            f'FileDictIO: Opening {self._filename} for {self._mode}')
        if not self.is_read_mode():
            # Open the file for write, creating the output path as needed.
            file_util.file_makedirs(self._filename)
        self._fp = file_util.FileIO(filename=self._filename,
                                    mode=self._mode,
                                    encoding=self._encoding)

    def close(self):
        """Close an open file."""
        if self._fp is not None:
            # Close the file handle
            del self._fp
        self._fp = None

    def get_file_handle(self):
        """Returns the file handle."""
        return self._fp.get_file_handle()

    def filename(self) -> str:
        """Returns the filename opened."""
        return self._filename

    def headers(self):
        """Returns the file headers.
        For a CSV file, retruns the list of columns.
        For an MCF file, retruns any comments at the top of the file.
        """
        return self._headers

    def set_headers(self, headers: list):
        """Set the headers for a file."""
        self._headers = headers

    def __next__(self):
        """Returns the next record from the file being read."""
        return self.next()

    # Abstract methods overwridden in child classes

    @abstractmethod
    def next(self) -> dict:
        """Returns the next dict record from the file opened for read.
        Returns None if there are no more reacords to read from the file."""
        return None

    @abstractmethod
    def write_header(self):
        """Write the header to the file."""
        pass

    @abstractmethod
    def write_record(self, record: dict):
        """Writes a dict record to the file."""
        pass


class CsvFileDictIO(FileDictIO):
    """Class to read or write records from/to a CSV file.
    Each row in the CSV file is treated as a dict record with the
    csv column headers as the keys.
    """

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = [],
                 encoding: str = None):
        super().__init__(filename, mode, headers, encoding)
        self._csv_reader = None
        self._csv_writer = None
        self.open()

    def open(self):
        """Open CSV file with DictReader or DictWriter."""
        # Create a filehandle for the file
        super().open()
        if self.is_read_mode():
            # Read the CSV filehandle using DictReader
            # Set the headers from the file column headers.
            options = file_util.file_get_csv_reader_options(
                self.filename(), {'delimiter': ','})
            self._csv_reader = csv.DictReader(self.get_file_handle(), **options)
            self.set_headers(self._csv_reader.fieldnames)
            logging.level_debug() and logging.debug(
                f'Opened CSV file {self.filename()} for {self._mode} with options: {options}, headers: {self.headers()}'
            )
        else:
            # Write to the the CSV filehandle using DictWriter
            # Assumes headers are already provided.
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

    def write_header(self):
        """Write the CSV header columns."""
        if self._csv_writer:
            self._csv_writer.writeheader()

    def write_record(self, record: dict):
        """Write one CSV row to the file."""
        if self._csv_writer:
            self._csv_writer.writerow(record)

    def next(self) -> dict:
        """Returns the next records read from the csv file.
        Returns None if there are no more rows to read from the CSV file.
        """
        try:
            if self._csv_reader:
                return next(self._csv_reader)
        except StopIteration:
            # Reached end of file.
            return None
        return None

    def headers(self) -> list:
        """Retruns the list of columns in the file when in read mode."""
        if self._csv_reader is not None:
            return self._csv_reader.fieldnames
        return self._headers

    def __next__(self):
        """Returns the next record from the file being read."""
        return self.next()


class McfFileDictIO(FileDictIO):
    """Class to read/write MCF nodes from a text file."""

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = [],
                 encoding: str = None):
        super().__init__(filename, mode, headers, encoding)
        self._lines = []
        self.open()

    def open(self):
        """Open MCF file to write nodes."""
        # create output file handle for writes
        logging.info(f'Opening MCF file {self._filename} for {self._mode}')
        super().open()
        self.write_header()

    def write_header(self):
        """Write the MCF file headers as comments."""
        if self.is_read_mode():
            return
        headers = self.headers()
        if not headers:
            return
        if isinstance(headers, str):
            headers = [headers]
        for header in headers:
            if header and header[0] != '#':
                header = '#' + header
            if header and header[-1] != '\n':
                header = header + '\n'
            self.get_file_handle().write(header)

    def write_record(self, record: dict):
        """Write one MCF node to the file.
        The record is a dictionary of propety:values."""
        record_str = mcf_file_util.node_dict_to_text(record)
        self.get_file_handle().write(record_str)
        self.get_file_handle().write('\n\n')

    def next(self) -> dict:
        """Returns the next MCF node in the file as a dictionary of property:values.
        Returns None if there are no more MCF nodes in the file to read."""
        fp = self.get_file_handle()
        # Skip empty lines
        seen_node = False
        if not self._lines:
            for line in fp:
                if not line:
                    # End of file.
                    break
                line = line.strip()
                if line != '':
                    # Found the start of the next node.
                    self._lines.append(line.strip())
                    break

        # Read all non-empty lines until the empty line at the end of the record
        lines = self._lines
        for line in lines:
            if line.startswith('Node:'):
                seen_node = True
        for line in fp:
            if not line:
                break
            line = line.strip()
            if line == '':
                self._lines = []
                break
            if line.startswith('Node'):
                if seen_node:
                    # Start of next record without an empty line.
                    self._lines = [line]
                    break
                seen_node = True
            lines.append(line)

        # Parse property:values into a dict.
        if not lines:
            # reached end of file
            return None

        record = {}
        for line in lines:
            if not line:
                continue
            if line.startswith('#'):
                mcf_file_util.add_comment_to_node(line, record)
            else:
                prop, value = mcf_file_util.get_pv_from_line(line)
                mcf_file_util.add_pv_to_node(prop,
                                             value,
                                             record,
                                             normalize=False)

        return record

    def __next__(self):
        """Returns the next record from the file being read."""
        return self.next()


def open_dict_file(filename: str,
                   mode: str,
                   headers: list = None,
                   encoding: str = None) -> FileDictIO:
    """Returns a FileDictIO object for the given filename.
    Retruns a CsvFileDictIO for csv files and McfFileDictIO for MCF files."""
    if is_csv_file(filename):
        return CsvFileDictIO(filename, mode, headers, encoding)
    return McfFileDictIO(filename, mode, headers, encoding)


def is_csv_file(filename: str) -> bool:
    """Returns True if the file is a csv file."""
    basename = os.path.basename(filename)
    if '.csv' in basename or '.tsv' in basename:
        return True
    if file_util.file_is_google_spreadsheet(filename):
        return True
    return False

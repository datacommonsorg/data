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
"""JSON and JSON Lines file reader and writer (`JsonFileDictIO`) for `file_dict_io`.

Example:
  from file_dict_io import JsonFileDictIO

  with JsonFileDictIO('records.jsonl', mode='w') as writer:
    writer.write({'dcid': 'dc/1', 'value': '10'})
"""

from io import UnsupportedOperation
import json
import os
from absl import logging

from file_dict_io.base import FileDictIO


def is_jsonl_file(filename: str) -> bool:
    """Returns True if `filename` refers to a JSON Lines (`.jsonl` or `.ndjson`) file.

    Example:
      from file_dict_io import is_jsonl_file

      is_jsonl_file('data/records.jsonl')  # Returns True
      is_jsonl_file('data/records.json')   # Returns False

    Args:
      filename: Path to check.

    Returns:
      `True` if the filename contains `.jsonl` or `.ndjson`; `False` otherwise.
    """
    basename = os.path.basename(filename)
    if '.jsonl' in basename or '.ndjson' in basename:
        return True
    return False


def is_json_file(filename: str) -> bool:
    """Returns True if `filename` refers to a JSON (`.json`) or JSON Lines (`.jsonl`/`.ndjson`) file.

    Example:
      from file_dict_io import is_json_file

      is_json_file('data/records.json')   # Returns True
      is_json_file('data/records.jsonl')  # Returns True
      is_json_file('data/records.csv')    # Returns False

    Args:
      filename: Path to check.

    Returns:
      `True` if the filename contains `.json`, `.jsonl`, or `.ndjson`; `False`
      otherwise.
    """
    basename = os.path.basename(filename)
    if '.json' in basename or is_jsonl_file(filename):
        return True
    return False


@FileDictIO.register
class JsonFileDictIO(FileDictIO):
    """Reads or writes dictionary records from/to a JSON (`.json`) or JSON Lines (`.jsonl`/`.ndjson`) file.

    In write mode:
      - For `.jsonl` / `.ndjson` files, each record is serialized as a single
        JSON object per line (`JSON Lines` format).
      - For `.json` files, records are streamed out as a formatted JSON array
        (`[\n  {...},\n  {...}\n]`).

    In read mode:
      - Supports reading `.jsonl` / `.ndjson` line-by-line, as well as standard
        `.json` files containing either a JSON array of objects (`[{...}, ...]`),
        a single JSON object (`{...}`), or newline-delimited JSON objects.

    Example:
      from file_dict_io import JsonFileDictIO

      with JsonFileDictIO('records.jsonl', mode='w') as writer:
        writer.write({'dcid': 'dc/1', 'value': '10'})
        writer.write({'dcid': 'dc/2', 'value': '20'})

      with JsonFileDictIO('records.jsonl', mode='r') as reader:
        for row in reader:
          print(row['dcid'], row['value'])
    """

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if `filename` is a JSON (`.json`) or JSON Lines (`.jsonl`/`.ndjson`) file."""
        return is_json_file(filename)

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 **kwargs):
        """Initializes a `JsonFileDictIO` reader or writer.

        Args:
          filename: Path to the `.json`, `.jsonl`, or `.ndjson` file.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional header parameter (unused for JSON/JSONL files).
          encoding: Optional text encoding.
          **kwargs: Optional format-specific keyword arguments.
        """
        self._is_jsonl = is_jsonl_file(filename)
        self._buffer = ''
        self._decoder = json.JSONDecoder()
        super().__init__(filename, mode, headers, encoding, **kwargs)
        self.open()

    def open(self):
        """Opens the JSON or JSONL file for reading or writing."""
        super().open()
        self._buffer = ''
        logging.level_debug() and logging.debug(
            f'Opened JSON file {self.filename()} for {self._mode} (jsonl={self._is_jsonl})'
        )

    def write_header(self):
        """No-op as JSON/JSONL files do not use column headers."""
        pass

    def write_record(self, record: dict):
        """Writes a single dictionary record to the JSON or JSONL file.

        Args:
          record: Dictionary of key-value pairs to write as a JSON object.

        Returns:
          The number of characters written to the underlying file.

        Raises:
          UnsupportedOperation: If the file was opened in read mode.
        """
        if self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot write record to JSON file {self.filename()} opened in read mode {self._mode}'
            )
        fp = self.get_file_handle()
        serialized = json.dumps(record)
        if self._is_jsonl:
            self._record_index += 1
            return fp.write(serialized + '\n')

        # Standard .json array format: stream records inside '[' ... ']'
        if self._record_index == 0:
            prefix = '[\n  '
        else:
            prefix = ',\n  '
        self._record_index += 1
        return fp.write(prefix + serialized)

    def close(self):
        """Finalizes the JSON array (if `.json` write mode) and closes the file."""
        if self._fp is not None and not self.is_read_mode() and not self._is_jsonl:
            fp = self.get_file_handle()
            if fp is not None:
                if self._record_index > 0:
                    fp.write('\n]\n')
                else:
                    fp.write('[]\n')
        self._buffer = ''
        super().close()

    def next(self) -> dict:
        """Reads lines incrementally and parses the next JSON dictionary record upon closing `}`.

        Processes the file one line at a time so arbitrarily large `.json` and
        `.jsonl` files can be streamed without loading the entire file into
        memory.

        Returns:
          A `dict` representing the next JSON object, or `None` at end of file.
        """
        fp = self.get_file_handle()
        if fp is None:
            return None

        while True:
            # Strip leading whitespace, commas, and array brackets between records.
            self._buffer = self._buffer.lstrip(' \t\r\n,[]')
            if '}' in self._buffer:
                try:
                    record, end_idx = self._decoder.raw_decode(self._buffer)
                    self._buffer = self._buffer[end_idx:]
                    if isinstance(record, dict):
                        self._record_index += 1
                        return record
                    continue
                except json.JSONDecodeError:
                    # Incomplete multi-line JSON object; read more lines until next '}'.
                    pass

            # Read lines until a line containing '}' is found or EOF is reached.
            while True:
                line = fp.readline()
                if not line:
                    self._buffer = ''
                    return None
                self._buffer += line
                if '}' in line:
                    break

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
from absl import logging

from file_dict_io.base import FileDictIO, get_file_extension


def is_jsonl_file(filename: str) -> bool:
    """Returns True if `filename` refers to a JSON Lines (`.jsonl` or `.ndjson`) file.

    Example:
      from file_dict_io import is_jsonl_file

      is_jsonl_file('data/records.jsonl')  # Returns True
      is_jsonl_file('data/records.json')   # Returns False

    Args:
      filename: Path to check.

    Returns:
      `True` if the normalized format extension is `.jsonl` or `.ndjson`;
      `False` otherwise.
    """
    return get_file_extension(filename) in ('.jsonl', '.ndjson')


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
      `True` if the normalized format extension is `.json`, `.jsonl`, or
      `.ndjson`; `False` otherwise.
    """
    return get_file_extension(filename) in ('.json', '.jsonl', '.ndjson')


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
                 start_offset: int = 0,
                 end_offset: int = None,
                 **kwargs):
        """Initializes a `JsonFileDictIO` reader or writer.

        Args:
          filename: Path to the `.json`, `.jsonl`, or `.ndjson` file.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional header parameter (unused for JSON/JSONL files).
          encoding: Optional text encoding.
          start_offset: Optional starting byte offset for read mode.
          end_offset: Optional ending byte offset for read mode.
          **kwargs: Optional format-specific keyword arguments.
        """
        self._is_jsonl = is_jsonl_file(filename)
        self._buffer = ''
        self._top_level_indent = None
        self._decoder = json.JSONDecoder()
        super().__init__(filename,
                         mode,
                         headers,
                         encoding,
                         start_offset=start_offset,
                         end_offset=end_offset,
                         **kwargs)
        self.open()

    def open(self):
        """Opens the JSON or JSONL file for reading or writing."""
        super().open()
        self._buffer = ''
        self._next_record_start = 0
        if self.is_read_mode() and self._start_offset > 0:
            self.seek(self._start_offset)
        logging.debug(
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
        if self._fp is not None and not self.is_read_mode(
        ) and not self._is_jsonl:
            fp = self.get_file_handle()
            if fp is not None:
                if self._record_index > 0:
                    fp.write('\n]\n')
                else:
                    fp.write('[]\n')
        self._buffer = ''
        super().close()

    def seek(self, offset: int) -> int:
        """Seeks to the first JSON/JSONL record starting at or after `offset`.

        Caveats:
          - JSON Lines (.jsonl / .ndjson): Seeking is robust, fast, and exact.
            Each line contains a complete JSON record with no unescaped newlines.
            Seeking discards any partial line after `offset` and begins at the
            next line boundary.
          - Standard JSON Array (.json): Standard JSON files are not inherently
            splittable if minified (e.g. `[{"a":1},{"b":2}]`) or if strings
            contain nested brackets/newlines across lines. For formatted JSON
            arrays (where each object starts on a line with '{'), seeking scans
            forward for the next line containing '{'. Using .jsonl is strongly
            recommended for parallel reading.

        Args:
          offset: Byte offset in the file to seek past.

        Returns:
          The actual byte offset where the next record begins.

        Raises:
          UnsupportedOperation: If the file is not opened in read mode.
        """
        if not self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot seek in write mode for JSON file {self.filename()}')
        fp = self.get_file_handle()
        if fp is None:
            return 0
        self._start_offset = offset
        self._buffer = ''
        if offset <= 0:
            fp.seek(0)
            self._next_record_start = 0
            return 0

        if not self._is_jsonl and self._top_level_indent is None:
            fp.seek(0)
            while True:
                first_line = fp.readline()
                if not first_line:
                    break
                no_bom = first_line.lstrip('\ufeff')
                stripped = no_bom.lstrip(' \t,[')
                if stripped.startswith('{'):
                    if no_bom.lstrip(' \t').startswith('['):
                        self._top_level_indent = 0
                    else:
                        self._top_level_indent = len(no_bom) - len(
                            no_bom.lstrip(' \t'))
                    break

        self._next_record_start = self._seek_to_next_line(offset)

        if not self._is_jsonl:
            # For standard formatted JSON arrays, scan for the line starting
            # the next top-level object (matching the top-level indentation so
            # nested objects on their own lines are skipped).
            while True:
                pos = fp.tell()
                line = fp.readline()
                if not line:
                    self._next_record_start = fp.tell()
                    break
                no_bom = line.lstrip('\ufeff')
                indent = len(no_bom) - len(no_bom.lstrip(' \t'))
                stripped = no_bom.lstrip(' \t,[')
                if stripped.startswith('{') and (
                        self._top_level_indent is None or
                        indent == self._top_level_indent or
                        no_bom.lstrip(' \t').startswith('[')):
                    self._next_record_start = pos
                    self._buffer = stripped
                    break

        return self._next_record_start

    def next(self) -> dict:
        """Reads lines incrementally and parses the next JSON dictionary record upon closing `}`.

        Processes the file one line at a time so arbitrarily large `.json` and
        `.jsonl` files can be streamed without loading the entire file into
        memory.

        Returns:
          A `dict` representing the next JSON object, or `None` if end of file
          or `end_offset` is reached.
        """
        fp = self.get_file_handle()
        if fp is None:
            return None

        if self._end_offset is not None and self._next_record_start is not None:
            if self._next_record_start >= self._end_offset:
                return None

        if self._is_jsonl:
            while True:
                if self._end_offset is not None:
                    line_pos = fp.tell()
                    if line_pos >= self._end_offset:
                        self._next_record_start = line_pos
                        return None
                line = fp.readline()
                if not line:
                    self._next_record_start = fp.tell()
                    return None
                line = line.strip()
                if not line:
                    continue
                self._next_record_start = fp.tell()
                self._record_index += 1
                return json.loads(line)

        next_check_size = 4096
        while True:
            # Strip leading whitespace, commas, and array brackets between records.
            self._buffer = self._buffer.lstrip(' \t\r\n,[]')
            if self._buffer and (self._buffer[0] != '{' or '}' in self._buffer
                                 or len(self._buffer) >= next_check_size):
                try:
                    record, end_idx = self._decoder.raw_decode(self._buffer)
                    self._buffer = self._buffer[end_idx:]
                    next_check_size = 4096
                    if isinstance(record, dict):
                        self._record_index += 1
                        return record
                    continue
                except json.JSONDecodeError as err:
                    if err.pos < len(self._buffer.rstrip()):
                        self._buffer = ''
                        raise
                    if len(self._buffer) >= next_check_size:
                        next_check_size = len(self._buffer) * 2

            # Read lines incrementally until closing '}' (for objects) or EOF.
            while True:
                line_pos = fp.tell()
                line = fp.readline()
                if not line:
                    rem = self._buffer.lstrip(' \t\r\n,[]')
                    self._buffer = ''
                    self._next_record_start = fp.tell()
                    if rem:
                        self._decoder.raw_decode(rem)
                    return None
                if not self._buffer:
                    stripped = line.lstrip(' \t\r\n,[]')
                    if not stripped:
                        continue
                    self._next_record_start = line_pos
                    if (self._end_offset is not None and
                            self._next_record_start >= self._end_offset):
                        return None
                    self._buffer = stripped
                    if self._buffer[0] != '{' or '}' in self._buffer:
                        break
                    continue
                self._buffer += line
                if (self._buffer[0] != '{' or '}' in line or
                        len(self._buffer) >= next_check_size):
                    break

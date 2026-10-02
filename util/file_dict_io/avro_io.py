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
"""Apache Avro file reader and writer (`AvroFileDictIO`) for `file_dict_io`.

Example:
  from file_dict_io import AvroFileDictIO

  with AvroFileDictIO('obs.avro', mode='w', headers=['dcid', 'value']) as writer:
    writer.write({'dcid': 'dc/1', 'value': '42'})
"""

from io import UnsupportedOperation
import os
from absl import logging
import fastavro

from file_dict_io.base import FileDictIO


def is_avro_file(filename: str) -> bool:
    """Returns True if `filename` refers to an Apache Avro (`.avro`) file.

    Example:
      from file_dict_io import is_avro_file

      is_avro_file('data/observations.avro')  # Returns True
      is_avro_file('data/observations.csv')   # Returns False

    Args:
      filename: Path to check.

    Returns:
      `True` if the filename contains `.avro`; `False` otherwise.
    """
    basename = os.path.basename(filename)
    if '.avro' in basename:
        return True
    return False


@FileDictIO.register
class AvroFileDictIO(FileDictIO):
    """Reads or writes dictionary records from/to an Apache Avro file.

    By default, when no explicit `schema` is provided, all columns are stored as
    nullable strings (`['string', 'null']`). If a custom Avro `schema` is
    provided, record values are coerced to the corresponding field types before
    writing.

    Example:
      from file_dict_io import AvroFileDictIO

      with AvroFileDictIO('obs.avro', mode='w', headers=['dcid', 'value']) as writer:
        writer.write({'dcid': 'dc/1', 'value': '42'})

      with AvroFileDictIO('obs.avro', mode='r') as reader:
        for record in reader:
          print(record)
    """

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if `filename` is an Apache Avro (`.avro`) file."""
        return is_avro_file(filename)

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 schema: dict = None,
                 encoding: str = None,
                 **kwargs):
        """Initializes an `AvroFileDictIO` reader or writer.

        Args:
          filename: Path to the `.avro` file.
          mode: File open mode ('r'/'rb' for read, 'w'/'wb' for write).
          headers: Optional list of field names. If both `schema` and `headers`
            are omitted in write mode, headers are inferred from the first
            record written.
          schema: Optional Avro schema dictionary.
          encoding: Optional encoding parameter (unused for binary Avro files).
          **kwargs: Optional format-specific keyword arguments.
        """
        # Ensure binary mode for Avro files.
        if 'b' not in mode:
            mode = mode + 'b'
        super().__init__(filename, mode, headers, encoding, **kwargs)
        self._fastavro_reader = None
        self._fastavro_writer = None
        self._avro_schema = dict(schema) if schema else {}
        self.open()

    def open(self):
        """Opens the Avro file with `fastavro.reader` (read) or `fastavro.write.Writer` (write)."""
        # Create a file handle for the file.
        super().open()
        if self.is_read_mode():
            # Read the file handle using fastavro.reader and extract headers from schema.
            self._fastavro_reader = fastavro.reader(self.get_file_handle())
            self._avro_schema = self._fastavro_reader.writer_schema
            self._headers = self._get_headers_from_schema(self._avro_schema)
            logging.level_debug() and logging.debug(
                f'Opened AVRO file {self.filename()} for {self._mode} with headers: {self.headers()}, schema: {self._avro_schema}'
            )
        else:
            # Initialize the Avro writer if a schema or headers are available.
            if not self._avro_schema and self.headers():
                self._avro_schema = self._get_schema_from_headers(
                    self.headers())
            if self._avro_schema:
                self._avro_schema = fastavro.parse_schema(self._avro_schema)
                self._fastavro_writer = fastavro.write.Writer(
                    self.get_file_handle(), self._avro_schema)
                self._header_written = True
                logging.level_debug() and logging.debug(
                    f'Opened AVRO file {self.filename()} for {self._mode} with headers: {self.headers()}, schema: {self._avro_schema}'
                )
            else:
                logging.info(
                    f'Headers not set for AVRO file {self.filename()}. Deferring schema until first record write.'
                )

    def close(self):
        """Flushes any buffered Avro blocks and closes the underlying file."""
        if self._fastavro_writer:
            self._fastavro_writer.flush()
            self._fastavro_writer = None
        self._fastavro_reader = None
        super().close()

    def write_header(self):
        """Marks the Avro header/schema as initialized."""
        self._header_written = True

    def write_record(self, record: dict):
        """Writes one dictionary record to the Avro file.

        If neither `schema` nor `headers` were set prior to the first write, the
        schema is generated automatically from the keys of `record`.

        Args:
          record: Dictionary mapping field names to values.

        Returns:
          The result of `fastavro.write.Writer.write`.

        Raises:
          UnsupportedOperation: If the Avro writer cannot be initialized.
        """
        if not self._fastavro_writer:
            # This is the first record; initialize schema and writer from its keys.
            self.set_headers_from_record(record)
            self.open()
            if not self._fastavro_writer:
                logging.fatal(
                    f'Unable to open AVRO file {self.filename()} for write without headers'
                )
        if self._fastavro_writer:
            self._record_index += 1
            return self._fastavro_writer.write(self.convert_record(record))
        raise UnsupportedOperation(
            f'Cannot write record to AVRO file {self.filename()} in mode {self._mode} with headers {self.headers()}, schema {self._avro_schema}'
        )

    def convert_record(self, record: dict) -> dict:
        """Converts values in `record` to match the types declared in the Avro schema.

        Args:
          record: Input dictionary record.

        Returns:
          A new dictionary with field values converted to their target schema
          types.
        """
        output_record = dict(record)
        for field in self._avro_schema.get('fields', []):
            name = field.get('name')
            if not name:
                continue
            value_type = field.get('type', 'string')
            value = record.get(name)
            if value is not None:
                output_record[name] = self._get_value_type(value_type, value)
        return output_record

    def _get_value_type(self, value_type: str | list, value):
        """Coerces `value` to the Python type corresponding to the Avro `value_type`.

        Args:
          value_type: Avro type name (e.g. `'string'`, `'int'`) or union list
            (e.g. `['string', 'null']`).
          value: Value to convert.

        Returns:
          The converted value matching `value_type`.
        """
        if isinstance(value_type, list):
            non_null_types = [t for t in value_type if t != 'null']
            value_type = non_null_types[0] if non_null_types else 'string'
        match value_type:
            case 'string':
                return str(value)
            case 'int' | 'long':
                return int(value)
            case 'float' | 'double':
                return float(value)
            case 'boolean':
                return bool(value)
            case 'bytes':
                return bytes(value)
        return value

    def next(self) -> dict:
        """Returns the next dictionary record read from the Avro file.

        Keys with `None` values are omitted from the returned dictionary.

        Returns:
          A `dict` representing the next Avro record, or `None` at end of file.
        """
        try:
            if self._fastavro_reader:
                record = next(self._fastavro_reader)
                # Drop any keys with None values.
                output_record = {
                    k: v for k, v in record.items() if v is not None
                }
                self._record_index += 1
                return output_record

        except StopIteration:
            # Reached end of file.
            return None
        return None

    def _get_headers_from_schema(self, schema: dict = None) -> list:
        """Extracts and returns the ordered list of field names from an Avro schema.

        Args:
          schema: Avro schema dictionary. Defaults to `self._avro_schema`.

        Returns:
          List of field names defined in the schema.
        """
        if schema is None:
            schema = self._avro_schema
        headers = []
        for field in schema.get('fields', []):
            name = field.get('name')
            if name is not None:
                headers.append(name)
        return headers

    def _get_schema_from_headers(self, headers: list = None) -> dict:
        """Generates a default Avro record schema where each column is a nullable string.

        Args:
          headers: List of column names. Defaults to `self._headers`.

        Returns:
          An Avro record schema dictionary, or `None` if `headers` is empty.
        """
        if not headers:
            headers = self._headers
        fields = []
        if not headers:
            logging.error(
                f'Unable to generate schema for AVRO file {self.filename()} without headers'
            )
            return None

        for column in headers:
            fields.append({
                'name': column,
                'type': ['string', 'null'],
                'default': None
            })
        schema = {
            'name': 'DictRecord',
            'type': 'record',
            'fields': fields
        }
        return schema

    def headers(self) -> list:
        """Returns the list of field names for the Avro file."""
        if not self._headers:
            if self._fastavro_reader is not None:
                if self._avro_schema:
                    self._headers = self._get_headers_from_schema(
                        self._avro_schema)
        return self._headers

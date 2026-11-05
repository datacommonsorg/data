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
"""Abstract base class and format registry for `FileDictIO` readers and writers.

Example:
  from file_dict_io import open_dict_file

  with open_dict_file('records.csv', 'w') as writer:
    writer.write({'id': '1', 'name': 'Alice'})

  with open_dict_file('records.csv', 'r') as reader:
    for row in reader:
      print(row)
"""

from abc import ABC, abstractmethod
from io import UnsupportedOperation
import os
import re
import sys
from absl import logging

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_UTIL_DIR = os.path.dirname(_PACKAGE_DIR)
_DATA_DIR = os.path.dirname(_UTIL_DIR)
for _path in (
        _UTIL_DIR,
        _DATA_DIR,
        os.path.join(_DATA_DIR, 'tools', 'statvar_importer'),
):
    if _path not in sys.path:
        sys.path.append(_path)

import file_util

_COMPRESSION_EXTS = frozenset({'.gz', '.bz2', '.zst', '.xz', '.zip'})
_SHARD_SUFFIX_RE = re.compile(r'-(?:\d+|\*|\[0-9\]\*)-of-(?:\d+|\*|\[0-9\]\*)$')


def get_file_extension(filename: str) -> str:
    """Returns the normalized lowercase format extension for `filename`.

    Handles shard suffixes (`shards.csv@3`, `output@3.csv`,
    `shards.csv-00000-of-00003`) and compression suffixes (`data.csv.gz`) while
    preserving the final format extension on multi-dot filenames (such as
    `table.csv.mcf` -> `'.mcf'`).
    """
    if not isinstance(filename, str) or not filename:
        return ''
    basename = os.path.basename(filename).lower()
    if '@' in basename:
        prefix, shard_spec = basename.rsplit('@', 1)
        if '.' in shard_spec:
            _, ext_part = shard_spec.split('.', 1)
            basename = f'{prefix}.{ext_part}'
        else:
            basename = prefix
    basename = _SHARD_SUFFIX_RE.sub('', basename)
    root, ext = os.path.splitext(basename)
    while ext in _COMPRESSION_EXTS and root:
        basename = _SHARD_SUFFIX_RE.sub('', root)
        root, ext = os.path.splitext(basename)
    return ext


class FileDictIO(ABC):
    """Abstract base class for reading and writing dictionary records to a file.

    Provides context manager (`with`), iterator (`for row in reader:`), and
    `csv.DictReader` / `csv.DictWriter` compatibility methods (`read()`,
    `write()`, `writerow()`, `writerows()`, `writeheader()`, `fieldnames`,
    and `line_num`), as well as a handler registry for dispatching file formats.
    """

    # Ordered list of registered FileDictIO handler subclasses.
    _registry: list[type['FileDictIO']] = []
    # Fallback handler class used when no registered handler matches `can_handle()`.
    _default_handler: type['FileDictIO'] | None = None

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 start_offset: int = 0,
                 end_offset: int = None,
                 **kwargs):
        """Initializes a FileDictIO instance.

        Args:
          filename: Path to the local or remote (GCS/Spreadsheet) file.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of column names (for CSV/AVRO) or header
            comment lines (for MCF).
          encoding: Optional character encoding for text files.
          start_offset: Optional starting byte offset. If > 0, seeks to the
            first complete record starting at or after this offset.
          end_offset: Optional ending byte offset. If set, reading stops before
            any record whose start offset is >= `end_offset`.
          **kwargs: Optional format-specific keyword arguments.
        """
        if 'seek' in kwargs and not start_offset:
            start_offset = kwargs.pop('seek')
        if 'start_offset' in kwargs and not start_offset:
            start_offset = kwargs.pop('start_offset')
        if 'end_offset' in kwargs and end_offset is None:
            end_offset = kwargs.pop('end_offset')
        del kwargs
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._headers = list(headers) if headers else []
        self._start_offset = int(
            start_offset) if start_offset is not None else 0
        self._end_offset = int(end_offset) if end_offset is not None else None
        self._next_record_start = 0
        self._fp = None
        self._record_index = 0
        self._header_written = False

    @classmethod
    def register(cls,
                 handler_cls: type['FileDictIO'] = None,
                 *,
                 default: bool = False,
                 priority: bool = False):
        """Registers a `FileDictIO` subclass in the format handler registry.

        Can be used either directly as `@FileDictIO.register` or with keyword
        arguments as `@FileDictIO.register(default=True)` or
        `@FileDictIO.register(priority=True)`.

        Example:
          from file_dict_io import FileDictIO

          @FileDictIO.register
          class CustomFileDictIO(FileDictIO):
            @classmethod
            def can_handle(cls, filename: str) -> bool:
              return filename.endswith('.custom')

        Args:
          handler_cls: The `FileDictIO` subclass to register.
          default: If `True`, sets `handler_cls` as the fallback handler when
            no registered handler's `can_handle(filename)` returns `True`.
          priority: If `True`, inserts `handler_cls` at the beginning of the
            registry so it is evaluated before previously registered handlers.

        Returns:
          The registered `handler_cls` (or a decorator function if called with
          keyword arguments).
        """

        def _decorator(subcls: type['FileDictIO']) -> type['FileDictIO']:
            if default:
                cls._default_handler = subcls
            elif subcls not in cls._registry:
                if priority:
                    cls._registry.insert(0, subcls)
                else:
                    cls._registry.append(subcls)
            return subcls

        if handler_cls is not None:
            return _decorator(handler_cls)
        return _decorator

    @classmethod
    def get_registered_handlers(cls) -> list[type['FileDictIO']]:
        """Returns a copy of the registered `FileDictIO` handler classes.

        Returns:
          List of registered `FileDictIO` subclasses in priority order,
          followed by the default fallback handler if one is registered.
        """
        handlers = list(cls._registry)
        if cls._default_handler and cls._default_handler not in handlers:
            handlers.append(cls._default_handler)
        return handlers

    @classmethod
    def get_handler(cls, filename: str) -> type['FileDictIO']:
        """Returns the registered `FileDictIO` subclass that handles `filename`.

        Iterates through registered handlers in registration order and returns
        the first subclass whose `can_handle(filename)` returns `True`. If no
        handler matches, returns the registered default fallback handler.

        Example:
          from file_dict_io import FileDictIO

          handler_cls = FileDictIO.get_handler('data.avro')
          # handler_cls is AvroFileDictIO

        Args:
          filename: Path or URL to the file.

        Returns:
          The matching `FileDictIO` subclass.

        Raises:
          ValueError: If no registered handler matches `filename` and no
            default handler has been registered.
        """
        for handler_cls in cls._registry:
            if handler_cls.can_handle(filename):
                return handler_cls
        if cls._default_handler is not None:
            return cls._default_handler
        raise ValueError(
            f'No registered FileDictIO handler found for file: {filename}')

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if this `FileDictIO` subclass supports `filename`.

        Subclasses should override this method to participate in automatic
        format detection via `FileDictIO.get_handler()` and `open_dict_file()`.

        Args:
          filename: Path or URL to inspect.

        Returns:
          `True` if this class can read/write `filename`; `False` otherwise.
        """
        del filename
        return False

    def __del__(self):
        """Ensures the underlying file handle is closed upon garbage collection."""
        self.close()

    def is_read_mode(self) -> bool:
        """Returns True if the file is opened in read mode."""
        return self._mode.startswith('r')

    def open(self):
        """Opens the underlying file for reading or writing using `FileIO`.

        Saves the file handle for subsequent reads or writes and creates parent
        directories when opening in write mode.
        """
        if self._fp:
            # File is already open.
            return
        logging.level_debug() and logging.debug(
            f'FileDictIO: Opening {self._filename} for {self._mode}')
        if not self.is_read_mode():
            # Open the file for write, creating the output path as needed.
            file_util.file_makedirs(self._filename)
        self._fp = file_util.FileIO(filename=self._filename,
                                    mode=self._mode,
                                    encoding=self._encoding)
        self._record_index = 0
        self._header_written = False

    def close(self):
        """Closes the open file handle and flushes any pending output."""
        if getattr(self, '_fp', None) is not None:
            fp = self._fp
            self._fp = None
            fp.__exit__(None, None, None)

    def get_file_handle(self):
        """Returns the underlying file-like handle from `FileIO`."""
        if self._fp is None:
            return None
        return self._fp.get_file_handle()

    def filename(self) -> str:
        """Returns the filename associated with this instance."""
        return self._filename

    def headers(self) -> list:
        """Returns the file headers.

        Returns:
          For a CSV or AVRO file, the list of column/field names.
          For an MCF file, any header comments configured at the top of the file.
        """
        return self._headers

    def set_headers(self, headers: list):
        """Sets the column headers or MCF header comments for the file.

        Args:
          headers: List of column names or comment strings.
        """
        self._headers = list(headers) if headers else []

    def set_headers_from_record(self, record: dict) -> list:
        """Infers and sets headers from the keys of a dictionary record.

        If headers are already set, the existing headers are preserved and
        returned.

        Args:
          record: Dictionary whose keys will be used as column headers.

        Returns:
          The list of active headers for the file.
        """
        if self._headers:
            # Headers already set; reuse them.
            return self._headers
        headers = list(record.keys())
        if headers:
            logging.info(
                f'Setting headers for {self.filename()} from first record: {headers}'
            )
            self.set_headers(headers)
        return self.headers()

    def current_record_index(self) -> int:
        """Returns the 1-based index of the most recently read or written record."""
        return self._record_index

    def start_offset(self) -> int:
        """Returns the starting byte offset configured for this reader."""
        return self._start_offset

    def end_offset(self) -> int | None:
        """Returns the ending byte offset configured for this reader, or None."""
        return self._end_offset

    def tell(self) -> int:
        """Returns the current byte position in the underlying file."""
        fp = self.get_file_handle()
        if fp is not None and hasattr(fp, 'tell'):
            try:
                return fp.tell()
            except (OSError, IOError):
                return self._next_record_start
        return self._next_record_start

    def _seek_to_next_line(self, offset: int) -> int:
        """Positions the file handle at the first line starting at or after `offset`.

        Uses the underlying binary `fp.buffer` for UTF-8 and single-byte text
        encodings so landing inside a multi-byte UTF-8 character at `offset - 1`
        never raises `UnicodeDecodeError`.

        Args:
          offset: Byte offset in the file to seek past.

        Returns:
          The aligned byte offset where the next line begins (0 if `offset <= 0`).
        """
        fp = self.get_file_handle()
        if fp is None:
            return 0
        if offset <= 0:
            fp.seek(0)
            return 0

        raw_buf = getattr(fp, 'buffer', None)
        enc = (getattr(fp, 'encoding', None) or self._encoding or
               'utf-8').lower().replace('_', '-')
        if raw_buf is not None and not enc.startswith(('utf-16', 'utf-32')):
            raw_buf.seek(offset - 1)
            prev = raw_buf.read(1)
            if prev and prev != b'\n':
                raw_buf.readline()
            target = raw_buf.tell()
            fp.seek(target)
            return target

        fp.seek(offset - 1)
        prev = fp.read(1)
        if prev and prev != '\n':
            fp.readline()
        return fp.tell()

    def seek(self, offset: int) -> int:
        """Seeks to the first complete record starting at or after `offset`.

        Subclasses override this method to provide format-specific record
        boundary scanning and caveat handling.

        Args:
          offset: Byte offset in the file to seek past.

        Returns:
          The actual byte offset where the next record begins.

        Raises:
          UnsupportedOperation: If the file is not opened in read mode.
        """
        if not self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot seek file opened in write mode: {self.filename()}')
        fp = self.get_file_handle()
        if fp is not None and hasattr(fp, 'seek'):
            fp.seek(offset)
            self._start_offset = offset
            self._next_record_start = self.tell()
            return self._next_record_start
        return 0

    @property
    def fieldnames(self) -> list:
        """Returns the list of column names (alias for `csv.DictReader` / `DictWriter`)."""
        return self.headers()

    @property
    def line_num(self) -> int:
        """Returns the number of records read or written (alias for `csv.DictReader.line_num`)."""
        return self.current_record_index()

    def __enter__(self):
        """Enters the runtime context related to this file object."""
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Exits the runtime context and closes the file."""
        self.close()

    def __iter__(self):
        """Returns the iterator object itself for `for row in reader:` loops."""
        return self

    def __next__(self) -> dict:
        """Returns the next dictionary record from the file being read.

        Returns:
          The next record as a `dict`.

        Raises:
          StopIteration: When the end of the file is reached.
        """
        record = self.next()
        if record is None:
            raise StopIteration
        return record

    def read(self) -> dict:
        """Reads and returns a single dictionary record from the file.

        Example:
          from file_dict_io import open_dict_file

          with open_dict_file('data.csv', 'r') as reader:
            first_row = reader.read()

        Returns:
          A `dict` representing the next record, or `None` at end of file.
        """
        return self.next()

    def readlines(self) -> list:
        """Reads and returns all remaining dictionary records from the file.

        Example:
          from file_dict_io import open_dict_file

          with open_dict_file('data.avro', 'r') as reader:
            records = reader.readlines()

        Returns:
          A `list` of `dict` records read from the file.
        """
        return list(self)

    def write(self, record: dict | list):
        """Writes a single dictionary record or a list of dictionary records.

        Example:
          from file_dict_io import open_dict_file

          with open_dict_file('data.csv', 'w') as writer:
            writer.write({'name': 'Alice', 'age': '30'})
            writer.write([{'name': 'Bob', 'age': '25'}])

        Args:
          record: A `dict` record or a `list` of `dict` records to write. If a
            non-dict scalar is provided, it is wrapped as
            `{'key': index, 'value': str(record)}`.

        Returns:
          The result of the underlying `write_record` call (for a single record).
        """
        if isinstance(record, list):
            for row in record:
                self.write(row)
            return
        elif not isinstance(record, dict):
            record = {'key': self._record_index, 'value': str(record)}
        return self.write_record(record)

    def writerow(self, record: dict):
        """Writes a single dictionary record (alias for `csv.DictWriter.writerow`).

        Args:
          record: A `dict` mapping column names to values.
        """
        return self.write(record)

    def writerows(self, records: list):
        """Writes multiple dictionary records (alias for `csv.DictWriter.writerows`).

        Args:
          records: An iterable/list of `dict` records to write.
        """
        return self.write(records)

    def writeheader(self):
        """Writes the file header once (alias for `csv.DictWriter.writeheader`)."""
        return self.write_header()

    # Abstract methods overridden in child classes

    @abstractmethod
    def next(self) -> dict:
        """Returns the next dictionary record from the file opened for reading.

        Returns:
          A `dict` representing the next record, or `None` if there are no more
          records to read.
        """
        return None

    @abstractmethod
    def write_header(self):
        """Writes the header to the file if not already written."""
        pass

    @abstractmethod
    def write_record(self, record: dict):
        """Writes a single dictionary record to the file.

        Args:
          record: A `dict` record to write.
        """
        pass

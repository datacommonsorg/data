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
"""MCF file reader and writer (`McfFileDictIO`) for `file_dict_io`.

Example:
  from file_dict_io import McfFileDictIO

  with McfFileDictIO('nodes.mcf', mode='w') as writer:
    writer.write({'Node': 'dcid:Person1', 'typeOf': 'dcs:Person'})
"""

from io import UnsupportedOperation
from absl import logging

from file_dict_io.base import FileDictIO, get_file_extension
import mcf_file_util


def is_mcf_file(filename: str) -> bool:
    """Returns True if `filename` refers to an MCF (`.mcf` or `.tmcf`) file.

    Example:
      from file_dict_io import is_mcf_file

      is_mcf_file('data/nodes.mcf')  # Returns True
      is_mcf_file('data/nodes.csv')  # Returns False

    Args:
      filename: Path to check.

    Returns:
      `True` if the normalized format extension is `.mcf` or `.tmcf`; `False`
      otherwise.
    """
    return get_file_extension(filename) in ('.mcf', '.tmcf')


# Properties that hold the id of a node, in order of precedence.
NODE_ID_PROPS = ('dcid', 'Node')


def _is_node_line(raw_line: str) -> bool:
    """Returns True if an unindented line starts an MCF `Node:` declaration."""
    line = raw_line.lstrip('\ufeff')
    if not line or line[0] in (' ', '\t'):
        return False
    if not line.startswith('Node'):
        return False
    return line[4:].lstrip(' \t').startswith(':')


def get_record_dcid(record: dict) -> str:
    """Returns the dcid of `record` from its `dcid`, or else from its `Node`.

    Blank values are skipped, so a record with an empty `dcid` falls back to
    its `Node`. Surrounding quotes and a namespace prefix such as `dcid:` are
    removed, so `{'dcid': 'geoId/06'}`, `{'dcid': '"geoId/06"'}` and
    `{'Node': 'dcid:geoId/06'}` all return `'geoId/06'`.

    Example:
      from file_dict_io import get_record_dcid

      get_record_dcid({'dcid': '', 'Node': 'dcid:geoId/06'})  # 'geoId/06'

    Args:
      record: Dictionary of property-value pairs for a node.

    Returns:
      The dcid, or `''` if neither `dcid` nor `Node` has a value.
    """
    if not record:
        return ''
    for prop in NODE_ID_PROPS:
        value = record.get(prop)
        if value is None:
            continue
        dcid = mcf_file_util.strip_namespace(str(value).strip(' "'))
        if dcid:
            return dcid
    return ''


@FileDictIO.register(default=True)
class McfFileDictIO(FileDictIO):
    """Reads or writes MCF nodes as dictionary records from/to a text file.

    Registered as the default fallback `FileDictIO` handler when a file does not
    match another specific format handler.

    Example:
      from file_dict_io import McfFileDictIO

      node = {'Node': 'dcid:Person1', 'typeOf': 'dcs:Person', 'name': '"Alice"'}
      with McfFileDictIO('nodes.mcf', mode='w', headers=['# Generated MCF']) as writer:
        writer.write(node)

      with McfFileDictIO('nodes.mcf', mode='r') as reader:
        for record in reader:
          print(record['Node'])
    """

    @classmethod
    def can_handle(cls, filename: str) -> bool:
        """Returns True if `filename` is an MCF (`.mcf` or `.tmcf`) file."""
        return is_mcf_file(filename)

    def __init__(self,
                 filename: str,
                 mode: str = 'r',
                 headers: list = None,
                 encoding: str = None,
                 start_offset: int = 0,
                 end_offset: int = None,
                 **kwargs):
        """Initializes an `McfFileDictIO` reader or writer.

        Args:
          filename: Path to the MCF file.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of comment strings to write at the top of the
            MCF file.
          encoding: Optional text encoding.
          start_offset: Optional starting byte offset for read mode.
          end_offset: Optional ending byte offset for read mode.
          **kwargs: Optional format-specific keyword arguments.
        """
        super().__init__(filename,
                         mode,
                         headers,
                         encoding,
                         start_offset=start_offset,
                         end_offset=end_offset,
                         **kwargs)
        self._lines = []
        self.open()

    def open(self):
        """Opens the MCF file and writes any configured header comments."""
        logging.info(f'Opening MCF file {self._filename} for {self._mode}')
        super().open()
        self.write_header()
        self._lines = []
        self._next_record_start = 0
        if self.is_read_mode() and self._start_offset > 0:
            self.seek(self._start_offset)

    def write_header(self):
        """Writes the MCF file headers as `#`-prefixed comments once."""
        if self.is_read_mode() or self._header_written:
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
        self._header_written = True

    def write_record(self, record: dict):
        """Writes one MCF node dictionary to the file.

        If `record` has no `Node` (or a blank one) but has a `dcid`, the node
        is written with a `Node: dcid:<dcid>` line. An existing `Node` is
        written as is.

        Args:
          record: Dictionary of MCF property-value pairs for a single node.

        Returns:
          The number of characters written for the node text.

        Raises:
          UnsupportedOperation: If the file was opened in read mode.
        """
        if self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot write record to MCF file {self.filename()} opened in read mode {self._mode}'
            )
        node = {
            k: v for k, v in record.items() if k is not None and v is not None
        }
        node_value = node.get('Node')
        if node_value is None or not str(node_value).strip(' "'):
            dcid = get_record_dcid(node)
            if dcid:
                node['Node'] = f'dcid:{dcid}'
        record_str = mcf_file_util.node_dict_to_text(node)
        ret = self.get_file_handle().write(record_str)
        self.get_file_handle().write('\n\n')
        self._record_index += 1
        return ret

    def seek(self, offset: int) -> int:
        """Seeks to the first MCF node starting at or after `offset`.

        Caveats:
          - Node Demarcation: Seeks forward until an unindented line starting
            with 'Node:' is found. Lines before the first 'Node:' (such as comments
            or blank lines) are skipped.
          - Multiline Property Values: Standard MCF specifies each PV pair on a line.
            If a string property contains embedded newlines with 'Node:', it could be
            mistaken for a node boundary, though standard MCF escapes or wraps strings.
          - Header Comments: Header comments at the top of the file are bypassed
            when seeking to an offset > 0.

        Args:
          offset: Byte offset in the file to seek past.

        Returns:
          The actual byte offset where the next MCF node starts.

        Raises:
          UnsupportedOperation: If the file is not opened in read mode.
        """
        if not self.is_read_mode():
            raise UnsupportedOperation(
                f'Cannot seek in write mode for MCF file {self.filename()}')
        fp = self.get_file_handle()
        if fp is None:
            return 0
        self._start_offset = offset
        self._lines = []
        if offset <= 0:
            fp.seek(0)
            self._next_record_start = 0
            return 0

        self._seek_to_next_line(offset)

        while True:
            line_pos = fp.tell()
            line = fp.readline()
            if not line:
                self._next_record_start = fp.tell()
                return self._next_record_start
            if _is_node_line(line):
                self._lines = [line]
                self._next_record_start = line_pos
                return line_pos

    def next(self) -> dict:
        """Returns the next MCF node in the file as a dictionary.

        Returns:
          A `dict` of property-value pairs for the next MCF node, or `None` if
          there are no more MCF nodes in the file or `end_offset` is reached.
        """
        fp = self.get_file_handle()
        if fp is None:
            return None

        if self._end_offset is not None and self._next_record_start is not None:
            if self._next_record_start >= self._end_offset:
                return None

        # Skip leading empty lines and file comments before the first record.
        seen_node = False
        if not self._lines:
            while True:
                line_pos = fp.tell()
                line = fp.readline()
                if not line:
                    return None
                stripped = line.strip()
                if stripped != '' and not stripped.startswith('#'):
                    if self._start_offset <= 0 or _is_node_line(line):
                        self._lines.append(line)
                        self._next_record_start = line_pos
                        if (self._end_offset is not None and
                                self._next_record_start >= self._end_offset):
                            self._lines = []
                            return None
                        break

        # Read all non-empty lines until the empty line at the end of the record.
        lines = []
        for raw_line in self._lines:
            if _is_node_line(raw_line):
                seen_node = True
            lines.append(raw_line.strip())
        self._lines = []

        next_node_pos = None
        while True:
            line_pos = fp.tell()
            line = fp.readline()
            if not line:
                next_node_pos = fp.tell()
                break
            stripped = line.strip()
            if stripped == '':
                # Node ended by blank line. Find the next node start position.
                while True:
                    cand_pos = fp.tell()
                    next_line = fp.readline()
                    if not next_line:
                        next_node_pos = fp.tell()
                        break
                    next_stripped = next_line.strip()
                    if next_stripped != '' and not next_stripped.startswith(
                            '#'):
                        if self._start_offset <= 0 or _is_node_line(next_line):
                            self._lines = [next_line]
                            next_node_pos = cand_pos
                            break
                break
            if _is_node_line(line):
                if seen_node:
                    # Start of next record without an intervening empty line.
                    self._lines = [line]
                    next_node_pos = line_pos
                    break
                seen_node = True
            lines.append(stripped)

        self._next_record_start = next_node_pos if next_node_pos is not None else fp.tell(
        )

        # Parse property:value lines into a dict.
        if not lines:
            # Reached end of file.
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

        self._record_index += 1
        return record

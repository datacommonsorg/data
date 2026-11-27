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
from file_dict_io.base import FileDictIO
from file_dict_io.base import get_file_extension
import mcf_file_util

_READ_CHUNK_BYTES = 8 * 1024 * 1024  # 8 MiB raw read buffer
_BINARY_SUPPORTED_ENCODINGS = frozenset(
    {'utf-8', 'utf8', 'utf-8-sig', 'ascii', 'latin-1', 'latin1'})
_UTF8_BOM_BYTES = b'\xef\xbb\xbf'


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


def _is_node_line_bytes(raw_line: bytes) -> bool:
    """Returns True if an unindented bytes line starts an MCF `Node:` declaration."""
    line = (raw_line[len(_UTF8_BOM_BYTES):]
            if raw_line.startswith(_UTF8_BOM_BYTES) else raw_line)
    if not line or line[0] in (32, 9):  # ' ', '\t'
        return False
    if not line.startswith(b'Node'):
        return False
    return line[4:].lstrip(b' \t').startswith(b':')


def _add_mcf_line_to_node(line: str, node: dict) -> None:
    """Parses a stripped MCF line and inserts it into `node` without normalization."""
    if not line:
        return
    if line[0] == '#':
        mcf_file_util.add_comment_to_node(line, node)
        return
    colon_idx = line.find(':')
    if colon_idx < 0:
        prop, value = '', line
    else:
        prop = line[:colon_idx].strip()
        value = line[colon_idx + 1:].strip()
    if prop not in node or prop in NODE_ID_PROPS:
        node[prop] = value
    else:
        mcf_file_util.add_pv_to_node(prop, value, node, normalize=False)


def _iter_raw_line_blocks(raw_buf,
                          start_offset: int,
                          chunk_bytes: int = _READ_CHUNK_BYTES):
    """Yields `(block_start_offset, block_end_offset, lines)` from a binary stream."""
    seek_pos = start_offset - 1 if start_offset > 0 else 0
    raw_buf.seek(seek_pos)
    discard_partial = start_offset > 0
    pos = seek_pos
    carryover = b''

    while True:
        chunk = raw_buf.read(chunk_bytes)
        if not chunk:
            break
        if discard_partial:
            nl_idx = chunk.find(b'\n')
            if nl_idx < 0:
                pos += len(chunk)
                continue
            pos += nl_idx + 1
            chunk = chunk[nl_idx + 1:]
            discard_partial = False
            if not chunk:
                continue

        if b'\n' not in chunk:
            carryover += chunk
            continue

        prev_carry_len = len(carryover)
        parts = chunk.split(b'\n')
        if prev_carry_len:
            parts[0] = carryover + parts[0]
        carryover = parts.pop()
        consumed = prev_carry_len + len(chunk) - len(carryover)
        block_start = pos
        pos += consumed
        yield block_start, pos, parts

    if not discard_partial and carryover:
        yield pos, pos + len(carryover), [carryover]


def _iter_binary_mcf_nodes(raw_buf, start_offset: int, end_offset: int | None,
                           decode_enc: str):
    """Streams `(node_start_offset, node_dict)` in deterministic `[B(start), B(end))`.

    `B(offset)` is the first non-blank, non-comment line at position `p >= offset`
    that either starts with `Node:` or follows at least one blank separator line
    at position `s` with `offset <= s < p` (and `B(0) = 0`). This guarantees an
    exact, non-overlapping partition across all MCF nodes—including blank-line
    separated `dcid:`-only nodes and back-to-back `Node:` records—at every
    byte offset without calling `TextIOWrapper.tell()`.
    """
    if end_offset is not None and start_offset >= end_offset:
        return

    skipping = start_offset > 0
    after_sep = False
    past_end = False
    after_sep_since_end = False
    current_node: dict = {}
    current_node_start: int | None = None

    for block_start, block_end, lines in _iter_raw_line_blocks(
            raw_buf, start_offset):
        line_pos = block_start

        # Fast interior loop when we are past the start boundary and the entire
        # block ends at or before `end_offset`.
        if (not skipping and not past_end and
            (end_offset is None or block_end <= end_offset)):
            for raw_line in lines:
                line_offset = line_pos
                line_pos += len(raw_line) + 1
                stripped_b = raw_line.strip()
                if line_offset == 0 and stripped_b.startswith(_UTF8_BOM_BYTES):
                    stripped_b = stripped_b[len(_UTF8_BOM_BYTES):].strip()
                if not stripped_b:
                    if current_node:
                        yield current_node_start, current_node
                        current_node = {}
                        current_node_start = None
                    continue
                if stripped_b[0] == 35 and not current_node:  # '#'
                    continue
                if stripped_b[0] == 78 and _is_node_line_bytes(
                        raw_line) and current_node:  # 'N'
                    yield current_node_start, current_node
                    current_node = {}
                    current_node_start = None
                if not current_node:
                    current_node_start = line_offset
                _add_mcf_line_to_node(stripped_b.decode(decode_enc, 'replace'),
                                      current_node)
            continue

        for raw_line in lines:
            line_offset = line_pos
            line_pos += len(raw_line) + 1
            stripped_b = raw_line.strip()
            if line_offset == 0 and stripped_b.startswith(_UTF8_BOM_BYTES):
                stripped_b = stripped_b[len(_UTF8_BOM_BYTES):].strip()
            is_blank = not stripped_b
            is_comment = (not is_blank) and (stripped_b[0] == 35)
            is_node = ((not is_blank) and (not is_comment) and
                       _is_node_line_bytes(raw_line))

            if skipping:
                if end_offset is not None and line_offset >= end_offset:
                    if is_blank or (not after_sep) or is_node:
                        return
                    if is_comment:
                        continue
                    skipping = False
                    past_end = True
                    after_sep_since_end = False
                else:
                    if is_blank:
                        after_sep = True
                        continue
                    if is_comment:
                        continue
                    if after_sep or is_node:
                        skipping = False
                    else:
                        continue

            if (end_offset is not None and not past_end and
                    line_offset >= end_offset):
                past_end = True
                after_sep_since_end = False

            if is_blank:
                if current_node:
                    yield current_node_start, current_node
                    current_node = {}
                    current_node_start = None
                if past_end:
                    after_sep_since_end = True
                continue

            if is_comment and not current_node:
                continue

            if past_end and (after_sep_since_end or is_node):
                if current_node:
                    yield current_node_start, current_node
                    current_node = {}
                    current_node_start = None
                return

            if is_node and current_node:
                yield current_node_start, current_node
                current_node = {}
                current_node_start = None

            if not current_node:
                current_node_start = line_offset
            _add_mcf_line_to_node(stripped_b.decode(decode_enc, 'replace'),
                                  current_node)

    if current_node:
        yield current_node_start, current_node


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
        self._node_iter = None
        self._peeked_node = None
        self._use_binary_reader = False
        self._decode_enc = 'utf-8'
        self.open()

    def _detect_binary_reader(self) -> None:
        """Configures fast buffered binary reading when the stream supports it."""
        self._use_binary_reader = False
        self._decode_enc = 'utf-8'
        if not self.is_read_mode():
            return
        fp = self.get_file_handle()
        if fp is None:
            return
        raw_buf = getattr(fp, 'buffer', None)
        if raw_buf is None:
            return
        enc = (getattr(fp, 'encoding', None) or self._encoding or
               'utf-8').lower().replace('_', '-')
        if enc in _BINARY_SUPPORTED_ENCODINGS:
            self._use_binary_reader = True
            self._decode_enc = ('latin-1' if enc in ('latin-1',
                                                     'latin1') else 'utf-8')

    def open(self):
        """Opens the MCF file and writes any configured header comments."""
        logging.info(f'Opening MCF file {self._filename} for {self._mode}')
        super().open()
        self.write_header()
        self._lines = []
        self._node_iter = None
        self._peeked_node = None
        self._next_record_start = 0
        self._detect_binary_reader()
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

        Recognizes both `Node:`-delimited records and blank-line-separated
        records (e.g. `dcid:`-only nodes) using deterministic boundary
        alignment `[B(start_offset), B(end_offset))`.

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
        self._node_iter = None
        self._peeked_node = None

        if self._use_binary_reader:
            raw_buf = fp.buffer
            if offset <= 0:
                raw_buf.seek(0)
                self._next_record_start = 0
                return 0
            self._node_iter = _iter_binary_mcf_nodes(
                raw_buf,
                start_offset=offset,
                end_offset=self._end_offset,
                decode_enc=self._decode_enc,
            )
            first = next(self._node_iter, None)
            if first is None:
                self._next_record_start = raw_buf.tell()
                return self._next_record_start
            node_start, node = first
            self._peeked_node = node
            self._next_record_start = node_start
            return node_start

        if offset <= 0:
            fp.seek(0)
            self._next_record_start = 0
            return 0

        self._seek_to_next_line(offset)
        after_sep = False
        while True:
            line_pos = fp.tell()
            line = fp.readline()
            if not line:
                self._next_record_start = fp.tell()
                return self._next_record_start
            stripped = line.strip()
            if not stripped:
                after_sep = True
                continue
            if stripped.startswith('#'):
                continue
            if after_sep or _is_node_line(line):
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

        if self._use_binary_reader:
            if self._peeked_node is not None:
                record = self._peeked_node
                self._peeked_node = None
                self._record_index += 1
                return record
            if self._node_iter is None:
                self._node_iter = _iter_binary_mcf_nodes(
                    fp.buffer,
                    start_offset=self._start_offset,
                    end_offset=self._end_offset,
                    decode_enc=self._decode_enc,
                )
            item = next(self._node_iter, None)
            if item is None:
                return None
            node_start, record = item
            self._next_record_start = node_start
            self._record_index += 1
            return record

        if self._end_offset is not None and self._next_record_start is not None:
            if self._next_record_start >= self._end_offset:
                return None

        # Text-stream fallback for non-UTF-8/non-buffered handles.
        if not self._lines:
            while True:
                line_pos = fp.tell()
                line = fp.readline()
                if not line:
                    return None
                stripped = line.strip()
                if stripped != '' and not stripped.startswith('#'):
                    self._lines.append(line)
                    self._next_record_start = line_pos
                    if (self._end_offset is not None and
                            self._next_record_start >= self._end_offset):
                        self._lines = []
                        return None
                    break

        lines = []
        seen_node = False
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
                while True:
                    cand_pos = fp.tell()
                    next_line = fp.readline()
                    if not next_line:
                        next_node_pos = fp.tell()
                        break
                    next_stripped = next_line.strip()
                    if next_stripped != '' and not next_stripped.startswith(
                            '#'):
                        self._lines = [next_line]
                        next_node_pos = cand_pos
                        break
                break
            if _is_node_line(line):
                if seen_node:
                    self._lines = [line]
                    next_node_pos = line_pos
                    break
                seen_node = True
            lines.append(stripped)

        self._next_record_start = (next_node_pos
                                   if next_node_pos is not None else fp.tell())

        if not lines:
            return None

        record = {}
        for line in lines:
            _add_mcf_line_to_node(line, record)

        self._record_index += 1
        return record

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

import os
from absl import logging

from file_dict_io.base import FileDictIO
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
      `True` if the filename contains `.mcf` or `.tmcf`; `False` otherwise.
    """
    basename = os.path.basename(filename)
    if '.mcf' in basename or '.tmcf' in basename:
        return True
    return False


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
                 **kwargs):
        """Initializes an `McfFileDictIO` reader or writer.

        Args:
          filename: Path to the MCF file.
          mode: File open mode ('r' for read, 'w' for write).
          headers: Optional list of comment strings to write at the top of the
            MCF file.
          encoding: Optional text encoding.
          **kwargs: Optional format-specific keyword arguments.
        """
        super().__init__(filename, mode, headers, encoding, **kwargs)
        self._lines = []
        self.open()

    def open(self):
        """Opens the MCF file and writes any configured header comments."""
        logging.info(f'Opening MCF file {self._filename} for {self._mode}')
        super().open()
        self.write_header()

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

        Args:
          record: Dictionary of MCF property-value pairs for a single node.

        Returns:
          The number of characters written for the node text.
        """
        record_str = mcf_file_util.node_dict_to_text(record)
        ret = self.get_file_handle().write(record_str)
        self.get_file_handle().write('\n\n')
        self._record_index += 1
        return ret

    def next(self) -> dict:
        """Returns the next MCF node in the file as a dictionary.

        Returns:
          A `dict` of property-value pairs for the next MCF node, or `None` if
          there are no more MCF nodes in the file.
        """
        fp = self.get_file_handle()
        # Skip leading empty lines.
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

        # Read all non-empty lines until the empty line at the end of the record.
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
                    # Start of next record without an intervening empty line.
                    self._lines = [line]
                    break
                seen_node = True
            lines.append(line)

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

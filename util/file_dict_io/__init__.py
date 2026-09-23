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
"""Classes and utilities to read and write a sequence of dictionary objects.

Each dictionary record is written as a CSV row, an AVRO record, a JSON/JSONL
object, or an MCF node depending on the file extension (`.csv`/`.tsv`, `.avro`,
`.json`/`.jsonl`/`.ndjson`, or `.mcf`), or sharded across multiple files when
sharding patterns (`@<N>`, `*`, `{column}`) are used.

Format handlers are registered via `@FileDictIO.register` and dispatched
automatically by `open_dict_file()` and `FileDictIO.get_handler()`.

Examples:
  Writing dictionary records to a file (headers inferred from the first record):
    from file_dict_io import open_dict_file

    row = {
        'dcid': 'dc/12345',
        'typeOf': 'StatVarObservation',
        'variableMeasured': 'MyStatVar',
        'observationDate': '2012',
        'value': 123,
    }
    with open_dict_file('test.csv', 'w') as dict_writer:
      dict_writer.write(row)

  Writing dictionary records to sharded Avro files:
    from file_dict_io import open_dict_file

    with open_dict_file('output@3.avro', 'w', shard_key='dcid') as sharded_writer:
      sharded_writer.write(row)

  Reading dictionary records iteratively from a single or sharded file:
    from file_dict_io import open_dict_file

    with open_dict_file('output@3.avro', 'r') as dict_reader:
      for row in dict_reader:
        print(row)
"""

from file_dict_io.avro_io import AvroFileDictIO, is_avro_file
from file_dict_io.base import FileDictIO
from file_dict_io.csv_io import CsvFileDictIO, is_csv_file
from file_dict_io.json_io import JsonFileDictIO, is_json_file, is_jsonl_file
from file_dict_io.mcf_io import McfFileDictIO, is_mcf_file
from file_dict_io.sharded_io import (
    ShardedFileDictIO,
    get_default_shard_config,
    is_sharded_file,
    str_to_int_hash,
)


def open_dict_file(filename: str | list,
                   mode: str = 'r',
                   headers: list = None,
                   encoding: str = None,
                   schema: dict = None,
                   **kwargs) -> FileDictIO:
    """Opens a dictionary record file using the registered `FileDictIO` handler.

    Looks up the appropriate `FileDictIO` subclass via `FileDictIO.get_handler(filename)`:
      - `ShardedFileDictIO` for sharded patterns (`output@10.csv`, `data*.avro`, etc.)
      - `CsvFileDictIO` for `.csv`/`.tsv`/Spreadsheet files
      - `AvroFileDictIO` for `.avro` files
      - `JsonFileDictIO` for `.json`/`.jsonl`/`.ndjson` files
      - `McfFileDictIO` for `.mcf` (or any other fallback) files

    Examples:
      from file_dict_io import open_dict_file

      # Write records to CSV, AVRO, JSON, JSONL, MCF, or sharded files:
      with open_dict_file('output.jsonl', 'w', headers=['dcid', 'value']) as writer:
        writer.writerow({'dcid': 'dc/1', 'value': '100'})

      # Read records iteratively using a for-loop:
      with open_dict_file('output.jsonl', 'r') as reader:
        for row in reader:
          print(row)

    Args:
      filename: Path, sharded pattern, or URL to the file(s) to open.
      mode: File open mode ('r' for read, 'w' for write).
      headers: Optional list of column headers (for CSV/AVRO) or comment lines
        (for MCF). If omitted in write mode, headers are inferred from the
        first record written.
      encoding: Optional character encoding for text-based formats.
      schema: Optional Avro schema dictionary (used only for `.avro` files).
      **kwargs: Additional keyword arguments (including sharding options such
        as `shard_key`, `shard_count`, `shard_skip_duplicates`, `config`, etc.)
        passed to the handler constructor.

    Returns:
      An initialized `FileDictIO` subclass instance matching `filename`.
    """
    handler_cls = FileDictIO.get_handler(filename)
    if schema is not None:
        kwargs['schema'] = schema
    return handler_cls(filename,
                       mode=mode,
                       headers=headers,
                       encoding=encoding,
                       **kwargs)


__all__ = [
    'FileDictIO',
    'CsvFileDictIO',
    'McfFileDictIO',
    'AvroFileDictIO',
    'JsonFileDictIO',
    'ShardedFileDictIO',
    'open_dict_file',
    'is_csv_file',
    'is_avro_file',
    'is_json_file',
    'is_jsonl_file',
    'is_mcf_file',
    'is_sharded_file',
    'get_default_shard_config',
    'str_to_int_hash',
]

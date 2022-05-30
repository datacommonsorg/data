# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A script to clean CDC Wonder Natality files."""

import os
import re

from absl import app
from absl import flags

flags.DEFINE_string('input_path', None, 'Path to directory with files to clean')
flags.DEFINE_string(
    'output_path', None,
    'Path to output directory. If empty, files are overwritten')

_FLAGS = flags.FLAGS

# Regex to identify "Notes" in the header file
_HEADER_REGEX = re.compile(r'"Notes"')

# Regex to identify tabs at the start of the line
_STARTING_TAB_REGEX = re.compile(r'^\t+')

# Regex to identify tab delimiters
_TAB_DELIMITER_REGEX = re.compile(r'\t+')


def clean_file(f_handle, w_handle=None):
    """Clean CDC Data file.

    Removes '"Notes"' from header.
    Removes lines that start with '"Total"'.
    All lines after first occurance of '"---"' are removed.

    Args:
        f_handle: File handle of file to clean.
        w_handle: File to write to. If None, attempts to overwrite f_handle.
    """
    lines = f_handle.readlines()
    if not w_handle:
        w_handle = f_handle
        w_handle.truncate(0)

    for line in lines:
        if line.startswith('"---"'):  # Start of metadata
            break

        elif line.startswith('"Notes"'):  # header line
            # Removing "Notes"
            cleaned_header = _HEADER_REGEX.sub('', line)

            # Tabs at start of the line are removed
            cleaned_header = _STARTING_TAB_REGEX.sub('', cleaned_header)

            # Tab delimiter replaced with ,
            cleaned_header = _TAB_DELIMITER_REGEX.sub(',', cleaned_header)

            w_handle.write(cleaned_header)

        elif not line.startswith('"Total"'):  # Line should not start with total
            # Tabs at start of the line are removed
            cleaned_line = _STARTING_TAB_REGEX.sub('', line)

            # Tab delimiter replaced with ,
            cleaned_line = _TAB_DELIMITER_REGEX.sub(',', cleaned_line)

            w_handle.write(cleaned_line)


def main(argv):
    for file_name in os.listdir(_FLAGS.input_path):
        input_file_path = os.path.join(_FLAGS.input_path, file_name)
        with open(input_file_path, 'r+', encoding='utf-8') as input_f:
            if _FLAGS.output_path:
                output_file_path = os.path.join(_FLAGS.output_path, file_name)
                with open(output_file_path, 'w', encoding='utf-8') as output_f:
                    clean_file(input_f, output_f)
            else:
                clean_file(input_f)


if __name__ == "__main__":
    flags.mark_flags_as_required(['input_path'])
    app.run(main)

# Copyright 2025 Google LLC
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
"""This script converts financial incentive data from textproto format to CSV format."""
import csv

from absl import app
from absl import flags
from google.protobuf import text_format

import sustainable_financial_incentives_pb2

FLAGS = flags.FLAGS

flags.DEFINE_string('textproto_path', 'testdata/sample_incentives.textproto',
                    'Local path to the textproto file.')
flags.DEFINE_string('csv_path', 'output.csv',
                    'Local path to write the CSV file.')


def _flatten_message(message, prefix=''):
    """Recursively flattens a protobuf message."""
    row = {}
    for field, value in message.ListFields():
        if field.type == field.TYPE_MESSAGE:
            row.update(_flatten_message(value, prefix=f'{prefix}{field.name}.'))
        elif field.type == field.TYPE_ENUM:
            row[f'{prefix}{field.name}'] = field.enum_type.values_by_number[
                value].name
        else:
            row[f'{prefix}{field.name}'] = value
    return row


def convert_textproto_to_csv(textproto_path: str, csv_path: str) -> None:
    """Converts a textproto file to a CSV file with a flattened, dot-notation header.

    Args:
        textproto_path: The local path to the input textproto file.
        csv_path: The local path to write the output CSV file to.
    """
    with open(textproto_path, 'r', encoding='utf-8') as f:
        incentive_summaries = text_format.Parse(
            f.read(),
            sustainable_financial_incentives_pb2.IncentiveSummaries()  # pylint: disable=no-member
        )

    # Dynamically generate the header by iterating through all summaries
    header_fields = set()
    all_rows = []
    for summary in incentive_summaries.incentive_summaries:
        row = _flatten_message(summary)
        header_fields.update(row.keys())
        all_rows.append(row)
    header = sorted(list(header_fields))

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(all_rows)


def main(argv):
    """Converts a textproto file to a CSV file."""
    del argv  # Unused
    print(f'Converting {FLAGS.textproto_path} to {FLAGS.csv_path}...')
    convert_textproto_to_csv(FLAGS.textproto_path, FLAGS.csv_path)
    print('Conversion complete.')


if __name__ == '__main__':
    app.run(main)

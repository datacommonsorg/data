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
"""A script to download EPH Tracking data."""

import os
import csv
from bs4 import BeautifulSoup

from absl import app
from absl import flags

flags.DEFINE_string('input_path', None,
                    'Path to directory containing html files')
flags.DEFINE_string('output_path', None,
                    'Path to directory where data will be written')
_FLAGS = flags.FLAGS


def table_to_csv(html, csv_path: str):
    """Downloads a HTML table as a CSV file."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.select_one("table")
    headers = [th.text for th in table.select("tr th")]

    with open(csv_path, "w", encoding='utf-8') as csv_f:
        writer = csv.writer(csv_f)
        writer.writerow(headers)
        writer.writerows([[td.text
                           for td in row.find_all("td")]
                          for row in table.select("tr + tr")])


def main(argv):
    if _FLAGS.output_path is None:
        _FLAGS.output_path = os.path.dirname(os.path.abspath(__file__))

    for file_name in os.listdir(_FLAGS.input_path):
        if file_name.endswith('.html'):  # If file is a html file
            file_path = os.path.join(_FLAGS.input_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                cleaned_csv_path = os.path.join(_FLAGS.output_path,
                                                file_name[:-5] + '.csv')
                table_to_csv(f.read(), cleaned_csv_path)


if __name__ == "__main__":
    flags.mark_flags_as_required(['input_path'])
    app.run(main)

# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Script to download all the WHO GHO raw data."""

import requests
import json
from absl import flags
from absl import app

FLAGS = flags.FLAGS
flags.DEFINE_string('output_folder',
                    '',
                    'path to folder to keep the downloaded data in',
                    short_name="output")


def download_data(output_destination):
    indicator_list = requests.get(
        "https://ghoapi.azureedge.net/api/Indicator").json().get("value", [])
    for indicator in indicator_list:
        code = indicator.get("IndicatorCode", "")
        indicator_data = requests.get(
            f"https://ghoapi.azureedge.net/api/{code}").json()
        f = open(f"{output_destination}{code}.json", "w+")
        f.write(json.dumps(indicator_data))


def main(args):
    download_data(FLAGS.output_folder)


if __name__ == '__main__':
    app.run(main)

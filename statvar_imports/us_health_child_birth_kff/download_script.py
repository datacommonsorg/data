# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import csv
import re
import json
from absl import app
from absl import logging
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "output_file",
    "kff_birth_data_all_timeframes.csv",
    "The path to write the output CSV file.",
)

logging.set_verbosity(logging.INFO)
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

def extract_data_from_url(url):
    """Extracts child birth data from a KFF URL.

    Args:
        url: The URL to fetch and extract data from.

    Returns:
        A list representing the parsed JSON data, or None if an error occurs.
    """
    headers = {
        'User-Agent': _USER_AGENT
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Error fetching URL {url}: {e}")
        raise RuntimeError(e)
        return None

    match = re.search(r'"gdocsObject":(\[\[.*?\]\]),"postBody"', response.text)
    if not match:
        logging.fatal(f"Could not find gdocsObject in {url}.")
        raise RuntimeError(e)
        return None
    try:
        child_birth_str = match.group(1)
        child_birth_data = json.loads(child_birth_str)
        return child_birth_data
    except (json.JSONDecodeError, KeyError) as e:
        logging.fatal(f"Failed to parse gdocsObject from {url}: {e}")
        raise RuntimeError(e)
        return None

def main(_):
    """Downloads child birth data for all timeframes and saves it to a CSV file."""

    output_file = FLAGS.output_file
    base_url = "https://www.kff.org/state-health-policy-data/state-indicator/number-of-births/?currentTimeframe={i}&selectedRows=%7B%22states%22:%7B%22all%22:%7B%7D%7D,%22wrapups%22:%7B%22united-states%22:%7B%7D%7D%7D&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D"

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header_written = False
        # This dynamic loop automatically fetches all existing and future timeframe data published by KFF without requiring code updates
        for i in range(16):
            url = base_url.format(i=i)
            logging.info(f"Fetching data for timeframe {i} from {url}")
            child_birth_data = extract_data_from_url(url)

            if child_birth_data:
                try:
                    if not header_written:
                        first_year_data = child_birth_data[0][1]
                        header = ["Year", "Location", first_year_data[0][1]]
                        writer.writerow(header)
                        header_written = True

                    for year_data in child_birth_data:
                        if year_data[0] == "Notes":
                            continue
                        year = year_data[0]
                        if len(year_data[1]) < 3:
                            logging.warning(f"Skipping year {year}: Inner data list is too short to contain state data.")
                            continue
                        data_rows = year_data[1][2:] 
                        for row in data_rows:
                            writer.writerow([year] + row)
                except (IndexError) as e:
                    logging.fatal(f"Error processing data from {url}: {e}")
                    raise RuntimeError(e)

    logging.info(f"Data downloaded and saved to {output_file}")

if __name__ == '__main__':
    app.run(main)
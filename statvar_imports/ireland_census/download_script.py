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

import os
import config
import requests
from absl import app, logging
from pathlib import Path
from retry import retry

base_url = config.base_url
DATA_CONFIG = {
    "suicides_with_aa1_aa2.csv": "VSD30",
    "suicides.csv": "VSD31",
    "life_expectancy.csv": "VSA30",
    "deaths.csv": "VSA09",
    "deaths_from_external_causes.csv": "VSD24",
    "births.csv": "VSA03",
    "population_by_gender.csv": "FY003B",
    "population_at_each_census.csv": "FY001",
    "population_by_religion.csv": "FY031",
    "population_by_age_gender.csv": "FY002",
    "population_by_employment.csv": "CNA22"
}

INPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

def download_csv():
    logging.info("Starting download...")
    try:
        for filename, table in DATA_CONFIG.items():
            output_path = os.path.join(INPUT_DIR, filename)
            logging.info(f"Downloading {filename} from table {table}")
            response = retry_method(base_url.format(table))
            with open(output_path, "wb") as f:
                f.write(response.content)
            logging.info(f"Successfully downloaded {filename} to {output_path}")
        logging.info(f"All files downloaded to {INPUT_DIR}")

    except Exception as e:
        logging.fatal(f"Failed to download Ireland Census data: {e}")


def main(argv):
    download_csv()

if __name__ == "__main__":
    app.run(main)


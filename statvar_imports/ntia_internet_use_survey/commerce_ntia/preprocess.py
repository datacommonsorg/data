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

import os, sys, time
import pandas as pd
import requests
import urllib3
from absl import app, logging
from pathlib import Path
import config

# Suppress InsecureRequestWarning when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

script_dir = os.path.dirname(os.path.abspath(__file__))

Commerce_NTIA_URL = config.Commerce_NTIA_URL

INPUT_DIR = os.path.join(script_dir, "input_files")
Path(INPUT_DIR).mkdir(parents=True, exist_ok=True)


COMMON_COLUMNS = ["dataset", "variable", "description", "universe"]
AGE_COLUMNS = ["age314Count", "age1524Count", "age2544Count", "age4564Count", "age65pCount"]
INPUT_FILE = os.path.join(INPUT_DIR, "ntia-analyze-table.csv")
INPUT_FILE_1 = os.path.join(INPUT_DIR, "ntia-data-age-only.csv")
INPUT_FILE_2 = os.path.join(INPUT_DIR, "ntia-data.csv")

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def download_dataset(url: str,
                     output_file: str,
                     tries: int = 3,
                     delay: int = 5,
                     backoff: int = 2) -> bool:
    """Downloads dataset with browser headers, SSL verification disabled, and retries."""
    current_delay = delay
    for attempt in range(1, tries + 1):
        try:
            logging.info(
                f"Attempt {attempt}/{tries}: Downloading from {url} (verify=False)"
            )
            response = requests.get(
                url,
                headers=HEADERS,
                verify=False,
                timeout=60,
                stream=True,
            )
            response.raise_for_status()
            with open(output_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Successfully downloaded dataset to {output_file}")
            return True
        except Exception as e:
            logging.warning(f"Download attempt {attempt} failed: {e}")
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except OSError:
                    pass
            if attempt < tries:
                time.sleep(current_delay)
                current_delay *= backoff
    logging.error(f"All {tries} download attempts failed for {url}")
    return False


def move_column_left(df, column_to_move, target_column):
    """Moves the universe column to the left of variable column."""
    cols = df.columns.tolist()
    if column_to_move in cols and target_column in cols:
        cols.remove(column_to_move)
        target_index = cols.index(target_column)
        new_cols = cols[:target_index] + [column_to_move] + cols[target_index:]
        return df[new_cols]
    return df


def preprocess_data():
    try:
        org_df = pd.read_csv(INPUT_FILE)
    
        df1 = org_df[COMMON_COLUMNS + AGE_COLUMNS].copy()
        df1['universeAgeResol'] = df1['universe'].apply(
            lambda x: 'CivilPerson' if x == 'isPerson' else ('Adult' if x == 'isAdult' else None)
        )
        df1['variableAgeResol'] = df1['variable'].apply(
            lambda x: 'CivilPerson' if x == 'isPerson' else ('Adult' if x == 'isAdult' else None)
        )
        df1_moved = move_column_left(df1, 'universe', 'variable')
        df1_moved.to_csv(INPUT_FILE_1, index=False)

        df2_cols_to_keep = [col for col in org_df.columns if not col.startswith('age')]
        df2 = org_df[df2_cols_to_keep].copy()
        df2['universeAgeResol'] = df2['universe'].apply(
            lambda x: 'CivilPerson' if x == 'isPerson' else ('Adult' if x == 'isAdult' else None)
        )
        df2['variableAgeResol'] = df2['variable'].apply(
            lambda x: 'CivilPerson' if x == 'isPerson' else ('Adult' if x == 'isAdult' else None)
        )
        df2_moved = move_column_left(df2, 'universe', 'variable')
        df2_moved.to_csv(INPUT_FILE_2, index=False)

    except Exception as e:
        logging.fatal(f"An error occurred while preprocessing the input data: {e}")
        return None

def main(argv):
    try:
        success = download_dataset(
            url=Commerce_NTIA_URL,
            output_file=INPUT_FILE,
            tries=3,
            delay=5,
            backoff=2,
        )
        if not success or not os.path.exists(INPUT_FILE):
            logging.fatal("Failed to download Commerce_NTIA file.")
            sys.exit(1)
    except Exception as e:
        logging.fatal(f"Failed to download Commerce_NTIA file: {e}")
        sys.exit(1)
    preprocess_data()

if __name__ == "__main__":
    app.run(main)

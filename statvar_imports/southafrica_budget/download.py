# Copyright 2025 Google LLC
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
import os
import shutil
import tempfile
import pandas as pd
from absl import logging, app
import subprocess
"""
Code to download inout files from GitHub Repo
python3 download.py
"""

# GitHub repo details
REPO_URL = "https://github.com/dsfsi/data-commons-data.git"
CSV_RELATIVE_PATH = "data/budget data/csv"

# Output path inside current repo
OUTPUT_BASE_PATH = "./input_files"

def clone_repo(repo_url, temp_dir):
    """Clones the input repo into a temporary directory."""
    try:
        subprocess.run(["git", "clone", repo_url, temp_dir], check=True)
        logging.info(f"Cloned repo to: {temp_dir}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git clone failed: {e}")
        raise

def process_budget_csvs(argv):
    logging.set_verbosity(logging.INFO)
    logging.info("Starting budget data import and processing script.")

    with tempfile.TemporaryDirectory() as tmpdir:
        logging.info("Created temporary directory for cloning input repo.")
        
        try:
            clone_repo(REPO_URL, tmpdir)
        except Exception as e:
            logging.error(f"Could not clone repository: {e}")
            return

        input_path = os.path.join(tmpdir, CSV_RELATIVE_PATH)
        if not os.path.exists(input_path):
            logging.error(f"Expected CSV path not found: {input_path}")
            return

        try:
            cities = os.listdir(input_path)
        except Exception as e:
            logging.error(f"Failed to list directories in {input_path}: {e}")
            return

        for city in cities:
            city_path = os.path.join(input_path, city)

            if not os.path.isdir(city_path):
                logging.warning(f"Skipping non-directory entry: {city_path}")
                continue

            try:
                files = os.listdir(city_path)
            except Exception as e:
                logging.error(f"Failed to list files in {city_path}: {e}")
                continue

            for filename in files:
                if not filename.endswith(".csv"):
                    logging.debug(f"Skipping non-CSV file: {filename}")
                    continue

                year = filename.replace(".csv", "")
                input_csv_path = os.path.join(city_path, filename)

                try:
                    df = pd.read_csv(input_csv_path)
                    df["Year"] = year
                except Exception as e:
                    logging.error(f"Error reading or processing {input_csv_path}: {e}")
                    continue

                output_city_path = os.path.join(OUTPUT_BASE_PATH, city)
                os.makedirs(output_city_path, exist_ok=True)
                output_file_path = os.path.join(output_city_path, filename)

                try:
                    df.to_csv(output_file_path, index=False)
                    logging.info(f"Processed and saved: {output_file_path}")
                except Exception as e:
                    logging.error(f"Failed to write file: {output_file_path}: {e}")

    logging.info("Finished processing all budget CSV files.")

if __name__ == "__main__":
    app.run(process_budget_csvs)

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pandas as pd
import re
from absl import app, logging


# --- Path Configuration ---
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(_SCRIPT_PATH, "input_files")

# Regex pattern to extract year from filenames like ef2010d_rv.csv or ef2024d.csv
pattern = re.compile(r"ef(\d{4})d(?:_rv)?", re.IGNORECASE)

def process_files():
    try:
        if not os.path.exists(input_folder):
            logging.fatal("FATAL ERROR: Input folder '%s' does not exist.", input_folder)

        # Group files by extracted year
        year_files = {}
        for filename in os.listdir(input_folder):
            # Skip hidden files and lock files (e.g. .~lock.ef2024d.csv#)
            if filename.startswith(".") or filename.startswith("~"):
                continue

            file_path = os.path.join(input_folder, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                logging.info("Skipping (not a file): %s", filename)
                continue

            match = pattern.search(filename)
            if not match:
                logging.info("Skipping %s: No year found.", filename)
                continue

            year = match.group(1)
            year_files.setdefault(year, []).append((filename, file_path))

        if not year_files:
            logging.fatal("FATAL ERROR: No valid input files found in '%s'.", input_folder)

        # Process each year
        for year, files in year_files.items():
            # Prefer _rv file if available
            selected_filename, selected_file_path = None, None
            for fname, fpath in files:
                if "_rv" in fname.lower():
                    selected_filename, selected_file_path = fname, fpath
                    break
            if not selected_file_path:
                selected_filename, selected_file_path = files[0]

            # Remove any redundant files for the same year
            for fname, fpath in files:
                if fpath != selected_file_path and os.path.exists(fpath):
                    os.remove(fpath)
                    logging.info("Removed redundant file for year %s: %s", year, fname)

            new_filename = f"student_faculty_ratio_data_{year}.csv"
            new_file_path = os.path.join(input_folder, new_filename)

            try:
                if selected_file_path != new_file_path:
                    os.rename(selected_file_path, new_file_path)
                    logging.info("Renamed: %s → %s", selected_filename, new_filename)

            except Exception as e:
                logging.fatal("Error renaming file %s: %s", selected_filename, e)

            try:
                # Load CSV
                df = pd.read_csv(new_file_path)

                # Clean column headers
                df.columns = df.columns.str.strip()

                # Add or update Year column in the second position
                if "Year" not in df.columns:
                    df.insert(1, "Year", int(year))
                else:
                    df["Year"] = int(year)

                # Check if the source dataset is provisional (lacks '_rv' suffix)
                is_provisional = "_rv" not in selected_filename.lower()
                if is_provisional:
                    df["measurementMethod"] = "NCES_ProvisionalEstimate"
                    logging.info("Added 'measurementMethod' = 'NCES_ProvisionalEstimate' to provisional file %s", new_filename)
                else:
                    df["measurementMethod"] = ""
                    logging.info("Set empty 'measurementMethod' for revised file %s", new_filename)

                # Save updated CSV
                df.to_csv(new_file_path, index=False)
                logging.info("Updated: Successfully preprocessed %s", new_filename)

            except Exception as e:
                logging.fatal("Error processing CSV %s: %s", new_filename, e)

    except Exception as e:
        logging.fatal("Unexpected error: %s", e)

def main(_):
    process_files()

if __name__ == "__main__":
    app.run(main)

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
from absl import logging


# Set verbosity level to 2
logging.set_verbosity(2)

# Folder containing input files
input_folder = "input_files"

# Regex pattern to extract year from filenames like ef2010d_rv.csv or ef2024d.csv
pattern = re.compile(r"ef(\d{4})d(?:_rv)?", re.IGNORECASE)

def process_files():
    try:
        if not os.path.exists(input_folder):
            logging.info(f"Input folder '{input_folder}' does not exist.")
            return

        # Group files by extracted year
        year_files = {}
        for filename in os.listdir(input_folder):
            # Skip hidden files and lock files (e.g. .~lock.ef2024d.csv#)
            if filename.startswith(".") or filename.startswith("~"):
                continue

            file_path = os.path.join(input_folder, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                logging.info(f"Skipping (not a file): {filename}")
                continue

            match = pattern.search(filename)
            if not match:
                logging.info(f"Skipping {filename}: No year found.")
                continue

            year = match.group(1)
            year_files.setdefault(year, []).append((filename, file_path))

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
                    logging.info(f"Removed redundant file for year {year}: {fname}")

            new_filename = f"student_faculty_ratio_data_{year}.csv"
            new_file_path = os.path.join(input_folder, new_filename)

            try:
                if selected_file_path != new_file_path:
                    os.rename(selected_file_path, new_file_path)
                    logging.info(f"Renamed: {selected_filename} → {new_filename}")

            except Exception as e:
                logging.fatal(f"Error renaming file {selected_filename}: {e}")
                continue

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
                    logging.info(f"Added 'measurementMethod' = 'NCES_ProvisionalEstimate' to provisional file {new_filename}")
                else:
                    if "measurementMethod" in df.columns:
                        df.drop(columns=["measurementMethod"], inplace=True)
                        logging.info(f"Removed 'measurementMethod' column from revised file {new_filename}")

                # Save updated CSV
                df.to_csv(new_file_path, index=False)
                logging.info(f"Updated: Successfully preprocessed {new_filename}")

            except Exception as e:
                logging.fatal(f"Error processing CSV {new_filename}: {e}")

    except Exception as e:
        logging.fatal(f"Unexpected error: {e}")

if __name__ == "__main__":
    process_files()


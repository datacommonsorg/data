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

# Regex pattern to extract year from filenames like ef2010d_rv.csv
pattern = re.compile(r"ef(\d{4})d_rv", re.IGNORECASE)

def process_files():
    try:
        for filename in os.listdir(input_folder):
            file_path = os.path.join(input_folder, filename)

            # Skip if not a file
            if not os.path.isfile(file_path):
                logging.info(f"Skipping (not a file): {filename}")
                continue

            try:
                # Extract year
                match = pattern.search(filename)
                if not match:
                    logging.info(f"Skipping {filename}: No year found.")
                    continue

                year = match.group(1)

                # New filename
                new_filename = f"student_faculty_ratio_data_{year}.csv"
                new_file_path = os.path.join(input_folder, new_filename)

                # Rename file
                os.rename(file_path, new_file_path)
                logging.info(f"Renamed: {filename} → {new_filename}")

            except Exception as e:
                logging.fatal(f"Error renaming file {filename}: {e}")
                continue

            try:
                # Load CSV
                df = pd.read_csv(new_file_path)

                # Add Year column in the second position
                df.insert(1, "Year", int(year))

                # Save updated CSV
                df.to_csv(new_file_path, index=False)
                logging.info(f"Updated: Added 'Year' column to {new_filename}")

            except Exception as e:
                logging.fatal(f"Error processing CSV {new_filename}: {e}")

    except Exception as e:
        logging.fatal(f"Unexpected error: {e}")

if __name__ == "__main__":
    process_files()

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

import os, shutil, re
from absl import logging, app

def move_latest_files(input_dir, latest_dir):
    """
    Identifies the latest male and female data files, and moves them to a
    separate directory for processing.
    """
    os.makedirs(latest_dir, exist_ok=True)
    logging.info(f"Created or found latest files directory: {latest_dir}")

    # Use a regex for robust parsing of filenames like 'table_40_13.xlsx'
    file_pattern = re.compile(r"table_(?P<gender_code>40|50)_(?P<num>\d+)\.xlsx")

    male_files = []
    female_files = []

    #Categorize all files in a single pass
    for filename in os.listdir(input_dir):
        match = file_pattern.match(filename)
        if not match:
            logging.warning(f"Skipping file with unexpected name: {filename}")
            continue

        data = match.groupdict()
        file_info = {
            "path": os.path.join(input_dir, filename),
            "num": int(data["num"]),
            "filename": filename
        }

        if data["gender_code"] == "40":
            male_files.append(file_info)
        else: # gender_code == "50"
            female_files.append(file_info)

    #Sort the lists to find the latest file easily
    male_files.sort(key=lambda f: f["num"])
    female_files.sort(key=lambda f: f["num"])

    #Move the latest file for each gender, if they exist
    if male_files:
        latest_male = male_files[-1]
        dest_path = os.path.join(latest_dir, latest_male["filename"])
        shutil.move(latest_male["path"], dest_path)
        logging.info(f"Moved latest male file: {latest_male['filename']}")

    if female_files:
        latest_female = female_files[-1]
        dest_path = os.path.join(latest_dir, latest_female["filename"])
        shutil.move(latest_female["path"], dest_path)
        logging.info(f"Moved latest female file: {latest_female['filename']}")

def main(_):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, "input_files")
    input_dir_latest = os.path.join(script_dir, "input_files_latest")
    try:
        move_latest_files(input_dir,input_dir_latest)
    except Exception as e:
        logging.fatal(f"A critical error prevented pre process the data from  completing: {e}")

if __name__ == "__main__":
   app.run(main)


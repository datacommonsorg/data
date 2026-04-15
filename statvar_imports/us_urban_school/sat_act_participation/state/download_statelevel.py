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
import sys
from absl import app
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(_SCRIPT_PATH, '../../../../util/'))

from download_util_script import download_file

logging.set_verbosity(logging.INFO)

data_sources = [
    {
        "year":
            "2021",
        "url":
            "https://docs.google.com/spreadsheets/d/1ovFJ2T0ZIpIcOZCUutE-aXiqGnXNgF1a/export?format=xlsx",
    },
    {
        "year":
            "2018",
        "url":
            "https://civilrightsdata.ed.gov/assets/downloads/2017-2018/College-Prepatory-Exams/SAT-ACT/SAT-or-ACT-Participation-by-state.xlsx",
    },
    {
        "year":
            "2016",
        "url":
            "https://civilrightsdata.ed.gov/assets/downloads/2015-2016/SAT-or-ACT-Participation-by-State.xlsx",
    },
    {
        "year":
            "2014",
        "url":
            "https://civilrightsdata.ed.gov/assets/downloads/2013-2014/SAT-or-ACT-Participation-by-state.xlsx",
    },
    {
        "year":
            "2012",
        "url":
            "https://civilrightsdata.ed.gov/assets/downloads/2011-2012/SAT%20or%20ACT/SAT-or-ACT-Participation-by-state.xlsx",
    },
]

BASE_DOWNLOAD_DIR = "input_files_state"


def main(_):
    """
    Iterates through the list of data sources and downloads each file
    to a unique subfolder.
    """
    logging.info(f"Starting download process for {len(data_sources)} files...")

    if not os.path.exists(BASE_DOWNLOAD_DIR):
        os.makedirs(BASE_DOWNLOAD_DIR)

    for item in data_sources:
        # Create a unique subfolder for each download to isolate the downloaded file
        unique_folder = os.path.join(BASE_DOWNLOAD_DIR, item["year"])
        if not os.path.exists(unique_folder):
            os.makedirs(unique_folder)

        file_name = f"{item['year']}_sat_act_participation.xlsx"

        logging.info(
            f"Attempting download for {item['year']} data into '{unique_folder}'..."
        )

        download_file(url=item["url"], output_folder=unique_folder, unzip=False)

        # Identify the downloaded file and rename it
        downloaded_files = os.listdir(unique_folder)
        if len(downloaded_files) == 1:
            downloaded_file_name = downloaded_files[0]
            downloaded_file_path = os.path.join(unique_folder,
                                                downloaded_file_name)
            renamed_file_path = os.path.join(BASE_DOWNLOAD_DIR, file_name)
            os.rename(downloaded_file_path, renamed_file_path)
            os.rmdir(unique_folder)  # Clean up the temporary unique folder
        else:
            logging.error(
                f"Could not determine the downloaded file for year {item['year']}. "
                f"Expected 1 file, but found {len(downloaded_files)} in '{unique_folder}'."
            )

    logging.info("Download process complete.")


if __name__ == "__main__":
    app.run(main)
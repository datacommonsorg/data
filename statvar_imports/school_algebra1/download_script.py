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
"""Downloads raw CRDC Algebra 1 data archives across survey years."""

import datetime
import glob
import os
import re
import shutil
import sys
from absl import app
from absl import logging

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(_SCRIPT_PATH, '../../util/'))

from download_util_script import download_file

logging.set_verbosity(logging.INFO)

_BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/{year_range}-crdc-data.zip"
_OUTPUT_DIRECTORY = os.path.join(_SCRIPT_PATH, "input_files")
_START_YEAR = 2009
_CURRENT_YEAR = datetime.datetime.now().year


def get_survey_years():
    """Returns the list of CRDC survey start years to check dynamically."""
    # CRDC followed odd-year reporting up to 2017, then 2020 onward annually/biennially
    odd_years = list(range(_START_YEAR, 2018, 2))
    recent_years = list(range(2020, _CURRENT_YEAR + 1, 1))
    return odd_years + recent_years


def download_crdc_files():
    """Downloads and extracts CRDC Algebra 1 raw files into input_files/."""
    os.makedirs(_OUTPUT_DIRECTORY, exist_ok=True)
    logging.info(
        f"Base output directory '{_OUTPUT_DIRECTORY}' ensured to exist.")

    years_to_try = get_survey_years()

    for year in years_to_try:
        end_year = year + 1
        year_range = f"{year}-{str(end_year)[-2:]}"

        # If data for this year is already downloaded, skip re-downloading
        existing_files = glob.glob(
            os.path.join(_OUTPUT_DIRECTORY, f"crdc_{year_range}_*"))
        if existing_files:
            logging.info(f"Data files for {year_range} already exist in "
                         f"'{_OUTPUT_DIRECTORY}'. Skipping download.")
            continue

        url = _BASE_URL.format(year_range=year_range)

        # Download to a temporary sub-folder
        temp_output_dir = os.path.join(_OUTPUT_DIRECTORY, f"temp_{year_range}")
        os.makedirs(temp_output_dir, exist_ok=True)

        success = download_file(url=url,
                                output_folder=temp_output_dir,
                                unzip=True)

        if not success:
            logging.info(
                f"Data for {year_range} is not available at {url}. Skipping.")
            shutil.rmtree(temp_output_dir, ignore_errors=True)
            continue

        logging.info(
            f"Successfully downloaded and extracted data for {year_range}.")

        search_pattern = os.path.join(temp_output_dir, '**', '*')
        category_name = "Algebra"

        for item_path in glob.glob(search_pattern, recursive=True):
            if not os.path.isfile(item_path):
                continue

            filename = os.path.basename(item_path)
            base, extension = os.path.splitext(filename)
            extension = extension.lower()

            if (extension in ['.csv', '.xlsx'] and
                (category_name.lower() in base.lower() or
                 (year == 2015 and "CRDC 2015-16 School Data" in base and
                  "layout" not in base.lower()))):
                if re.search(r'(^|[_\W])lea([_\W]|$)', base, re.IGNORECASE):
                    continue

                clean_base = re.sub(r'[^a-zA-Z0-9]+', '_', base).lower()
                if "enrollment" in clean_base or "algebra_ii" in clean_base:
                    continue

                new_filename = f"crdc_{year_range}_{clean_base}{extension}"
                new_filepath = os.path.join(_OUTPUT_DIRECTORY, new_filename)

                logging.info(
                    f"Moving raw file '{item_path}' to '{new_filepath}'")
                shutil.move(item_path, new_filepath)

        shutil.rmtree(temp_output_dir, ignore_errors=True)

    downloaded_files = (glob.glob(os.path.join(_OUTPUT_DIRECTORY, '*.csv')) +
                        glob.glob(os.path.join(_OUTPUT_DIRECTORY, '*.xlsx')))
    if not downloaded_files:
        raise RuntimeError(
            f"No CRDC Algebra 1 files found or downloaded in {_OUTPUT_DIRECTORY}"
        )

    logging.info("Download script finished.")


def main(argv):
    """Main entry point for downloading CRDC Algebra 1 files."""
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")
    try:
        download_crdc_files()
    except Exception as e:
        logging.fatal(f"Download script failed: {e}", exc_info=True)


if __name__ == '__main__':
    app.run(main)

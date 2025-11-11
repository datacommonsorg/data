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

"""
This script downloads SAIPE School District Estimates for 2003 to current year.
URL: https://www.census.gov/programs-surveys/saipe/data/datasets.html
"""
import sys
import datetime
from pathlib import Path
from typing import List

from absl import app
from absl import logging
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(_SCRIPT_DIR.joinpath('../../../util/').resolve()))
from download_util_script import download_file

URL_TEMPLATE = "https://www2.census.gov/programs-surveys/saipe/datasets/{year}/{year}-school-districts/ussd{yy}.xls"
_OUTPUT_DIR = _SCRIPT_DIR.joinpath("input_files")


def _find_header_row(df: pd.DataFrame) -> int:
    """Finds the header row index in a DataFrame by looking for a specific string."""
    for i, row in df.iterrows():
        if 'State FIPS Code' in row.astype(str).values:
            return i
    return -1


def _process_xls(filepath: Path, year: int) -> None:
    """
    Processes a downloaded XLS file, extracts data, adds a year column,
    and saves it as an XLSX file.
    """
    try:
        df = pd.read_excel(filepath, header=None)
        header_row_index = _find_header_row(df)

        if header_row_index != -1:
            # Set the found row as header and get data from the next row onwards
            df.columns = df.iloc[header_row_index]
            df = df.iloc[header_row_index + 1:]
            df['Year'] = year

            new_filepath = filepath.with_suffix(".xlsx")
            df.to_excel(new_filepath, index=False)
            filepath.unlink()  # Remove the original .xls file
            logging.info(f"Processed {filepath} and saved as {new_filepath}")
        else:
            logging.warning(f"Header not found in {filepath}")
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}")


def main(_: List[str]) -> None:
    """Main function to download and process data for all years."""
    _OUTPUT_DIR.mkdir(exist_ok=True)

    current_year = datetime.datetime.now().year
    # Data is usually not available for the current year immediately.
    # We iterate up to the current year, and the download failure for an
    # unavailable year will gracefully stop the script.
    for year in range(2003, current_year + 1):
        yy = str(year)[-2:]
        url = URL_TEMPLATE.format(year=year, yy=yy)
        logging.info(f"Downloading data for year {year} from {url}")

        success = download_file(url=url,
                                output_folder=str(_OUTPUT_DIR),
                                unzip=False)

        if success:
            file_path = _OUTPUT_DIR.joinpath(f"ussd{yy}.xls")
            _process_xls(file_path, year)
        else:
            logging.warning(
                f"Failed to download data for year {year}. This may be because "
                "the data is not yet available. Stopping.")
            break

    logging.info("Script processing completed.")


if __name__ == "__main__":
    app.run(main)

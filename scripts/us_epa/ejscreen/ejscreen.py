# Copyright 2023 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import zipfile
import requests
import pandas as pd
import json
from absl import logging, flags, app
import sys
import time
from retry import retry
import requests
import shutil
from pathlib import Path

# Setup path for import from data/util
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
_DATA_DIR = _SCRIPT_DIR.split('/data/')[0]
sys.path.append(os.path.join(_DATA_DIR, 'data/util'))
import file_util

logging.set_verbosity(logging.INFO)

_FLAGS = flags.FLAGS

flags.DEFINE_string('config_path',
                    'gs://unresolved_mcf/epa/ejscreen/download_config.json',
                    'Path to config file')
flags.DEFINE_string(
    'mode', '',
    'Mode of operation: "download" to only download, "process" to only process, leave empty for both.'
)

# Define the  path for output files.

OUTPUT_DIR = "input_files"
OUTPUT_DIR_FINAL = "output_files"


@retry(requests.exceptions.RequestException, tries=3, delay=10)
def download_and_extract_ejdata(year, config):
    """
    Downloads the yearly files from the Zenodo-like source (Multi-level ZIP extraction),
    extracts the final CSV data, and writes it to GCS.
    
    Modified to stream to a temporary file to avoid IncompleteRead errors.
    """
    output_path = f"{OUTPUT_DIR}/{year}.csv"

    if file_util.file_get_matching(output_path):
        logging.info(
            f"Final CSV file for year {year} already exists in GCS. Skipping download."
        )
        return

    logging.info(f"Starting download for Year {year}")
    max_retries = 3

    files_to_process = config["FILES_TO_PROCESS"]
    source_info = files_to_process.get(year)

    if not source_info:
        logging.fatal(
            f"No file information found in config for year {year}. Skipping.")
        return

    #  DOWNLOAD LOGIC
    base_url = config["BASE_ZENODO_URL"]
    url_suffix = source_info["url_suffix"]
    internal_zip_name = source_info["internal_zip_name"]
    main_url = base_url + url_suffix

    # Define temporary file paths
    temp_main_zip = Path(f"/tmp/main_zip_{year}.zip")
    temp_internal_zip = Path(f"/tmp/internal_zip_{year}.zip")

    for attempt in range(max_retries):
        logging.info(
            f"Downloading main ZIP from source: {main_url} (Attempt {attempt + 1}/{max_retries})"
        )
        try:
            # Use stream=True to handle large files without loading into memory
            with requests.get(main_url, stream=True, timeout=300) as response:
                response.raise_for_status()

                # Write the streamed content directly to a temporary file
                with temp_main_zip.open("wb") as f_out:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f_out.write(chunk)

            logging.info(
                f"Successfully downloaded main ZIP to temporary file for {year}."
            )

            # Now, open the temporary file for extraction
            with zipfile.ZipFile(temp_main_zip, 'r') as main_zip:
                logging.info(f"Successfully opened main ZIP for {year}.")

                if internal_zip_name not in main_zip.namelist():
                    basename = os.path.basename(internal_zip_name)
                    internal_zip_name = next(
                        (name for name in main_zip.namelist()
                         if basename in name), None)
                    if not internal_zip_name:
                        logging.fatal(
                            f"Error: Internal file matching '{basename}' not found in the main {year} ZIP."
                        )
                        # Clean up temp files before returning
                        temp_main_zip.unlink(missing_ok=True)
                        temp_internal_zip.unlink(missing_ok=True)
                        return

                logging.info(
                    f"Found internal ZIP: '{internal_zip_name}'. Reading content..."
                )

                # Check if the internal file is a CSV or another ZIP
                if internal_zip_name.lower().endswith(".zip"):
                    # This is the original logic for nested ZIP files
                    logging.info(
                        f"Found nested ZIP file. Extracting from '{internal_zip_name}'."
                    )

                    # Extract the inner zip directly to a temporary file
                    with main_zip.open(internal_zip_name,
                                       'r') as inner_zip_file:
                        with temp_internal_zip.open("wb") as f_out:
                            shutil.copyfileobj(inner_zip_file, f_out)

                    with zipfile.ZipFile(temp_internal_zip,
                                         'r') as internal_zip:
                        csv_files = [
                            name for name in internal_zip.namelist()
                            if name.lower().endswith(".csv")
                        ]

                        if not csv_files:
                            logging.fatal(
                                f"Warning: No CSV files found inside the inner ZIP for {year}. List: {internal_zip.namelist()}"
                            )
                            # Clean up temp files before returning
                            temp_main_zip.unlink(missing_ok=True)
                            temp_internal_zip.unlink(missing_ok=True)
                            return
                        source_file_content = internal_zip.read(csv_files[0])
                elif internal_zip_name.lower().endswith(".csv"):
                    # This is the new logic for a direct CSV file
                    logging.info(
                        f"Internal file is a CSV. Reading directly from '{internal_zip_name}'."
                    )
                    source_file_content = main_zip.read(internal_zip_name)

                else:
                    logging.fatal(
                        f"Error: Internal file '{internal_zip_name}' is not a .zip or .csv. Skipping."
                    )
                    return
                with file_util.FileIO(output_path, "wb") as target:
                    target.write(source_file_content)

                logging.info(f"  -> Extracted and saved to GCS: {output_path}")

                # Clean up temporary files on success
                temp_main_zip.unlink(missing_ok=True)
                temp_internal_zip.unlink(missing_ok=True)

                return  # Success, break out of retry loop

        except (requests.exceptions.RequestException, zipfile.BadZipFile,
                OSError) as e:
            logging.error(
                f"An error occurred during download/extraction for year {year} (Attempt {attempt + 1}): {e}"
            )
            # Clean up temp files on failure
            temp_main_zip.unlink(missing_ok=True)
            temp_internal_zip.unlink(missing_ok=True)

            if attempt < max_retries - 1:
                logging.info("Retrying in 10 seconds...")
                time.sleep(10)
            else:
                logging.fatal("Max retries exceeded. Skipping this year.")
                return


def write_csv(data, outfilename):
    """
    Concatenates dataframes and writes the final CSV to GCS.
    """
    full_df = pd.DataFrame()
    for curr_year, one_year_df in data.items():
        one_year_df['year'] = curr_year
        full_df = pd.concat([full_df, one_year_df], ignore_index=True)

    full_df = full_df.rename(columns={'ID': 'FIPS'})
    full_df = full_df.sort_values(by=['FIPS'], ignore_index=True)
    full_df['FIPS'] = 'dcid:geoId/' + (
        full_df['FIPS'].astype(str).str.zfill(12))
    full_df = full_df.fillna('')
    full_df = full_df.replace('None', '')

    with file_util.FileIO(outfilename, 'w') as f_out:
        full_df.to_csv(f_out, index=False)


def write_tmcf(outfilename, TEMPLATE_MCF):
    """
    Writes a list of dictionaries (representing MCF nodes) to a file in GCS.
    """
    mcf_content = []
    if isinstance(TEMPLATE_MCF, list):
        for node in TEMPLATE_MCF:
            if isinstance(node, dict):
                lines = []
                for key, value in node.items():
                    if isinstance(value, list):
                        value_str = "\n".join(f"  {v}" for v in value)
                        lines.append(f"{key}:\n{value_str}")
                    else:
                        lines.append(f"{key}: {value}")
                mcf_content.append("\n".join(lines))
    else:
        if isinstance(TEMPLATE_MCF, dict):
            lines = [f"{key}: {value}" for key, value in TEMPLATE_MCF.items()]
            mcf_content.append("\n".join(lines))
        else:
            mcf_content.append(str(TEMPLATE_MCF))

    template_content = "\n\n".join(mcf_content)

    with file_util.FileIO(outfilename, 'w') as f_out:
        f_out.write(template_content)


def main(_):
    try:
        with file_util.FileIO(_FLAGS.config_path, 'r') as f:
            config = json.load(f)

        YEARS = config.get("YEARS", [])
        NORM_CSV_COLUMNS = config.get("NORM_CSV_COLUMNS", [])
        NORM_CSV_COLUMNS1 = config.get("NORM_CSV_COLUMNS1", [])
        CSV_COLUMNS_BY_YEAR = config.get("CSV_COLUMNS_BY_YEAR", {})
        TEMPLATE_MCF = config.get("TEMPLATE_MCF", [])
        RENAME_COLUMNS_YEARS = config.get("RENAME_COLUMNS_YEARS", [])

        files_to_process_from_config = config.get("FILES_TO_PROCESS", {})

        if "BASE_ZENODO_URL" not in config or not files_to_process_from_config:
            logging.fatal(
                "Mandatory configuration keys (BASE_ZENODO_URL or FILES_TO_PROCESS) are missing from config file."
            )
            raise KeyError("Missing mandatory configuration keys.")

        dfs = {}

        if _FLAGS.mode == "" or _FLAGS.mode == "download":
            for year in YEARS:
                if year in files_to_process_from_config:
                    download_and_extract_ejdata(year, config)
                else:
                    logging.warning(
                        f"No download config found for year {year}. Skipping.")

        if _FLAGS.mode == "" or _FLAGS.mode == "process":
            for year in YEARS:
                try:
                    logging.info(f"Processing data for year {year}")
                    columns = CSV_COLUMNS_BY_YEAR.get(year)

                    if not columns:
                        logging.warning(
                            f"No column mapping found for year {year}. Skipping processing."
                        )
                        continue

                    file_path = f"{OUTPUT_DIR}/{year}.csv"

                    if not file_util.file_get_matching(file_path):
                        logging.error(
                            f"Required file for year {year} not found at {file_path}. Skipping processing."
                        )
                        continue

                    # Fix: Add the 'encoding' parameter to handle non-UTF-8 characters
                    dfs[year] = pd.read_csv(file_path,
                                            sep=',',
                                            usecols=columns,
                                            encoding='latin1')
                    logging.info(f"File processed for {year} successfully")

                    if year in RENAME_COLUMNS_YEARS:
                        cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS1))
                    else:
                        cols_renamed = dict(zip(columns, NORM_CSV_COLUMNS))

                    dfs[year] = dfs[year].rename(columns=cols_renamed)
                    logging.info(f"Columns renamed for {year} successfully")

                except Exception as e:
                    logging.fatal(f"Error processing data for year {year}: {e}")
                    continue

            logging.info("Writing data to CSV")
            write_csv(dfs, f"{OUTPUT_DIR_FINAL}/ejscreen_airpollutants.csv")

            logging.info("Writing template to TMCF")
            write_tmcf(f"{OUTPUT_DIR_FINAL}/ejscreen.tmcf", TEMPLATE_MCF)

            logging.info("Process completed successfully")

    except Exception as e:
        logging.fatal(f"Unexpected error in the main process: {e}")
        raise RuntimeError(f"Unexpected error in the main process: {e}")


if __name__ == '__main__':
    app.run(main)

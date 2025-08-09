# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import functools
import io
import json
import os
import shutil
import sys
import time
import zipfile
from absl import app
from absl import flags
from absl import logging
from bs4 import BeautifulSoup
import requests
import fetch_ncid
from download_config import COLUMNS_SELECTOR_URL
from download_config import COLUMNS_SELECTOR
from download_config import COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL
from download_config import COMPRESS_FILE_URL
from download_config import COMPRESS_FILE
from download_config import DOWNLOAD_URL
from download_config import HEADERS
from download_config import MAX_RETRIES
from download_config import NCES_DOWNLOAD_URL
from download_config import RETRY_SLEEP_SECS
from download_config import YEAR_PAYLOAD, YEAR_URL
from download_files_details import DEFAULT_COLUMNS_SELECTED
from download_files_details import DISTRICT_COLUMNS
from download_files_details import KEY_COLUMNS_DISTRICT
from download_files_details import KEY_COLUMNS_PRIVATE
from download_files_details import KEY_COLUMNS_PUBLIC
from download_files_details import PRIVATE_COLUMNS
from download_files_details import PUBLIC_COLUMNS

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
import file_util

_FLAGS = flags.FLAGS

flags.DEFINE_enum("import_name", None,
                  ["PublicSchool", "PrivateSchool", "District"],
                  "Import name for which input files to be downloaded")
flags.DEFINE_list("years_to_download", None,
                  "Years for which file has to be downloaded")
flags.mark_flag_as_required("import_name")
flags.DEFINE_string(
    'config_file',
    'gs://datcom-prod-imports/scripts/us_nces/demographics/school_id_list.json',
    'Path to config file')


def _call_export_csv_api(school: str, year: str, columns: list) -> str:
    """
    Calls the CSV export API to generate a CSV file.

    Args:
        school: The school name.
        year: The year.
        columns: A list of columns to be included in the CSV.

    Returns:
        The source file name of the exported CSV.

    Raises:
        requests.exceptions.HTTPError: If the API call returns a non-200 status code.
        KeyError: If the JSON response is not in the expected format.
    """
    COLUMNS_SELECTOR["lColumnsSelected"] = DEFAULT_COLUMNS_SELECTED + columns
    COLUMNS_SELECTOR["sLevel"] = school
    COLUMNS_SELECTOR["lYearsSelected"] = [year]

    try:
        response = requests.post(url=COLUMNS_SELECTOR_URL,
                                 json=COLUMNS_SELECTOR,
                                 headers=HEADERS)
        # This will raise an HTTPError for 4xx or 5xx status codes
        response.raise_for_status()

        src_file_name = response.json()['d']
        logging.info(
            f"CSV export successful for {school} - {year} - {src_file_name}")
        return src_file_name

    except requests.exceptions.RequestException as e:
        logging.error(f"CSV export API call failed for {school}-{year}: {e}")
        raise RuntimeError(
            f"CSV export API call failed for {school}-{year}") from e

    except (json.JSONDecodeError, KeyError) as e:
        logging.error(
            f"Failed to parse CSV export API response for {school}-{year}: {e}")
        logging.debug(f"Response content: {response.text}")
        raise RuntimeError(
            f"Unexpected response from CSV export API for {school}-{year}"
        ) from e


def retry(f):
    """Wrap a function so that the function is retried automatically."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        attempt = 1
        while attempt <= MAX_RETRIES:
            try:
                return f(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt <= MAX_RETRIES:
                    logging.warning(
                        f'Retrying in {RETRY_SLEEP_SECS} seconds: attempt {attempt} of {MAX_RETRIES}. Error: {e}'
                    )
                    time.sleep(RETRY_SLEEP_SECS)
                else:
                    logging.fatal(
                        f'Execution failed after {MAX_RETRIES} retries for {args}. Last error: {e}'
                    )
                    raise

    return wrapped


def _call_compress_api(file_name: str) -> str:
    """
    Calls the compression API to compress a file.

    Args:
        file_name: The name of the file to be compressed.

    Returns:
        The source file name of the compressed file.

    Raises:
        requests.exceptions.HTTPError: If the API call returns a non-200 status code.
        KeyError: If the JSON response is not in the expected format.
    """
    COMPRESS_FILE["sFileName"] = file_name

    try:
        response = requests.post(url=COMPRESS_FILE_URL,
                                 json=COMPRESS_FILE,
                                 headers=HEADERS)
        # This will raise an HTTPError for 4xx or 5xx status codes
        response.raise_for_status()

        compressed_src_file = response.json()['d'][0]
        logging.info(f"File compression successful: {compressed_src_file}")
        return compressed_src_file

    except requests.exceptions.RequestException as e:
        logging.error(
            f"File compression API call failed for '{file_name}': {e}")
        raise RuntimeError(
            f"File compression API call failed for '{file_name}'") from e

    except (json.JSONDecodeError, KeyError) as e:
        logging.error(
            f"Failed to parse compression API response for '{file_name}': {e}")
        logging.debug(f"Response content: {response.text}")
        raise RuntimeError(
            f"Unexpected response from compression API for '{file_name}'"
        ) from e


def _call_download_api(compressed_src_file: str, year: str) -> int:
    """
    Calls the download API to download a compressed file, extracts it to the
    original specified locations (now with year subfolders), and then copies
    these extracted files to the corresponding year-specific subfolders within
    the local _GCS_OUTPUT_DIR.

    Args:
        compressed_src_file: The identifier of the compressed file to download.
        year: The year associated with the file.

    Returns:
        0 if successful, 1 otherwise.
    """
    res = requests.get(url=DOWNLOAD_URL.format(
        compressed_src_file=compressed_src_file))

    if res.status_code == 200:
        logging.info(f"API success for downloading file for year {year}")

        base_extract_parent_dir = ""
        if _FLAGS.import_name == "PrivateSchool":
            base_extract_parent_dir = "private_school/input_files"
        elif _FLAGS.import_name == "District":
            base_extract_parent_dir = "school_district/input_files"
        elif _FLAGS.import_name == "PublicSchool":
            base_extract_parent_dir = "public_school/input_files"
        else:
            logging.warning(
                f"Unknown _FLAGS.import_name: {_FLAGS.import_name}. Extracting to current directory."
            )
        base_extract_path_original = os.path.join(base_extract_parent_dir, year)
        # checking the  target extraction paths existance
        os.makedirs(base_extract_path_original, exist_ok=True)

        try:
            with zipfile.ZipFile(io.BytesIO(res.content)) as zipfileout:
                # extracting to the original location
                zipfileout.extractall(base_extract_path_original)
                logging.info(
                    f"Files extracted to original location: {os.path.abspath(base_extract_path_original)}"
                )
            return 0

        except zipfile.BadZipFile:
            logging.error(
                f"Downloaded file for year {year} is not a valid zip file.")
            return 1
        except Exception as e:
            logging.error(
                f"An unexpected error occurred during file extraction or copying: {e}"
            )
            return 1
    else:
        logging.error(
            f"Download failed with status code: {res.status_code} for year {year}"
        )
        return 1


def get_year_list(school):
    YEAR_PAYLOAD["sLevel"] = school
    response = requests.post(YEAR_URL,
                             headers=HEADERS,
                             data=json.dumps(YEAR_PAYLOAD))
    years_to_download = []
    if response.status_code == 200:
        data = response.json()
        html_content = f"""{data}"""
        soup = BeautifulSoup(html_content, 'html.parser')
        for input_tag in soup.find_all('input', {'type': 'checkbox'}):
            year = input_tag['value']
            years_to_download.append(year)
    else:
        logging.fatal(
            f"Failed to retrieve years with status code: {response.status_code}"
        )
    if school == "PublicSchool" or school == "District":
        years_to_download = [y for y in years_to_download if int(y) >= 2010]
    return years_to_download


def main(_):
    logging.info(f'Loading config: {_FLAGS.config_file}')

    logging.info(f"Downloading files for import {_FLAGS.import_name}")
    school = _FLAGS.import_name

    if _FLAGS.years_to_download:
        years_to_process = _FLAGS.years_to_download
    else:
        years_to_process = get_year_list(school)

    if school == "PublicSchool":
        primary_key = KEY_COLUMNS_PUBLIC
        column_names = PUBLIC_COLUMNS
    elif school == "PrivateSchool":
        primary_key = KEY_COLUMNS_PRIVATE
        column_names = PRIVATE_COLUMNS
    elif school == "District":
        primary_key = KEY_COLUMNS_DISTRICT
        column_names = DISTRICT_COLUMNS

    data = {}
    try:
        with file_util.FileIO(_FLAGS.config_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logging.warning(
            f"Could not load config file, starting with empty data: {e}")
        data = {school: {}}

    if school not in data:
        data[school] = {}

    for year in years_to_process:
        logging.info(f"Processing download for {school} - {year}")
        if year in data[school]:
            id_list = data[school][year]
        else:
            id_list = fetch_ncid.fetch_school_ncid(school, year, column_names,
                                                   NCES_DOWNLOAD_URL)
            data[school][year] = id_list
            with file_util.FileIO(_FLAGS.config_file, 'w') as f:
                json.dump(data, f, indent=4)

        index_columns_selected = 0
        COLUMNS_TO_DOWNLOAD = id_list
        total_columns_to_download = len(COLUMNS_TO_DOWNLOAD)
        while index_columns_selected < total_columns_to_download:
            start_idx = index_columns_selected
            remaining_columns_to_select = total_columns_to_download - index_columns_selected
            end_idx = index_columns_selected + min(
                remaining_columns_to_select,
                COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)
            curr_columns_selected = COLUMNS_TO_DOWNLOAD[start_idx:end_idx]
            if primary_key[0] not in curr_columns_selected:
                curr_columns_selected.append(primary_key[0])
            index_columns_selected += min(
                remaining_columns_to_select,
                COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)

            logging.info(
                f"{school} - {year} - {index_columns_selected} columns out of {total_columns_to_download}"
            )

            try:
                nces_elsi_file_download(school, year, curr_columns_selected)
            except Exception as e:
                logging.fatal(
                    f"An error occurred during download for {school} - {year}: {e}"
                )
                break
        logging.info(f"Download complete for year {year}")


@retry
def nces_elsi_file_download(school, year, curr_columns_selected):
    file_name = _call_export_csv_api(school, year, curr_columns_selected)
    if file_name is None:
        raise Exception(f"Export to CSV failed for {school} - {year}")
    else:
        logging.info(f"Compressing output CSV: {file_name}")
        compressed_file_path = _call_compress_api(file_name)
        if compressed_file_path is None:
            raise Exception(f"Compress file failed for {file_name}")
        else:
            logging.info(f"Downloading the compressed file for {year}")
            download_ret = _call_download_api(compressed_file_path, year)
            if download_ret != 0:
                raise Exception(f"Download failed for {file_name}")


if __name__ == "__main__":
    app.run(main)

import functools
import io
import json
from absl import logging
import zipfile
import requests
import time
from absl import app, flags
from bs4 import BeautifulSoup
from download_config import COLUMNS_SELECTOR_URL
from download_config import COMPRESS_FILE_URL
from download_config import DOWNLOAD_URL
from download_config import COLUMNS_SELECTOR
from download_config import COMPRESS_FILE
from download_config import HEADERS
from download_config import COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL
from download_config import MAX_RETRIES
from download_config import RETRY_SLEEP_SECS
from download_config import YEAR_PAYLOAD, YEAR_URL
from download_files_details import DEFAULT_COLUMNS_SELECTED
from download_files_details import KEY_COLUMNS_PUBLIC, PUBLIC_COLUMNS
from download_files_details import KEY_COLUMNS_PRIVATE, PRIVATE_COLUMNS
from download_files_details import KEY_COLUMNS_DISTRICT, DISTRICT_COLUMNS
import fetch_ncid

import os
import sys

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_MODULE_DIR, '../../../util/'))
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
    'gs://unresolved_mcf/us_nces/demographics/school_id_list.json',
    'Path to config file')


def _call_export_csv_api(school: str, year: str, columns: list) -> str:
    COLUMNS_SELECTOR["lColumnsSelected"] = DEFAULT_COLUMNS_SELECTED + columns
    COLUMNS_SELECTOR["sLevel"] = school
    COLUMNS_SELECTOR["lYearsSelected"] = [year]
    json_value = COLUMNS_SELECTOR
    response = requests.post(url=COLUMNS_SELECTOR_URL,
                             json=COLUMNS_SELECTOR,
                             headers=HEADERS)
    if response.status_code == 200:
        src_file_name = json.loads(response.text)['d']
        logging.info(
            f"CSV export successful for {school} - {year} - {src_file_name}")
        return src_file_name
    else:
        logging.error(
            f"CSV export failed with status code: {response.status_code}")
        return None


def retry(f):
    """Wrap a function so that the function is retried automatically."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        attempt = 1
        while attempt <= MAX_RETRIES:
            try:
                return f(*args, **kwargs)
            except Exception:
                attempt += 1
                if attempt <= MAX_RETRIES:
                    logging.warning(
                        f'Retrying in {RETRY_SLEEP_SECS} seconds: attempt {attempt} of {MAX_RETRIES}'
                    )
                    time.sleep(RETRY_SLEEP_SECS)
                else:
                    logging.error(
                        f'Execution failed after {MAX_RETRIES} retries for {args}'
                    )
                    raise

    return wrapped


def _call_compress_api(file_name: str) -> str:
    COMPRESS_FILE["sFileName"] = file_name
    response = requests.post(url=COMPRESS_FILE_URL,
                             json=COMPRESS_FILE,
                             headers=HEADERS)
    if response.status_code == 200:
        compressed_src_file = json.loads(response.text)['d'][0]
        logging.info(f"File compression successful: {compressed_src_file}")
        return compressed_src_file
    else:
        logging.error(
            f"File compression failed with status code: {response.status_code}")
        return None


def _call_download_api(compressed_src_file: str, year: str) -> int:
    res = requests.get(url=DOWNLOAD_URL.format(
        compressed_src_file=compressed_src_file))
    if res.status_code == 200:
        logging.info(f"API success for downloading file for year {year}")
        with zipfile.ZipFile(io.BytesIO(res.content)) as zipfileout:
            if _FLAGS.import_name == "PrivateSchool":
                zipfileout.extractall(f"private_school/input_files")
            elif _FLAGS.import_name == "District":
                zipfileout.extractall(f"school_district/input_files")
            elif _FLAGS.import_name == "PublicSchool":
                zipfileout.extractall(f"public_school/input_files")
        return 0
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
        logging.error(
            f"Failed to retrieve years with status code: {response.status_code}"
        )
    if school == "PublicSchool" or school == "District":
        years_to_download = [y for y in years_to_download if int(y) >= 2010]
    return years_to_download


def main(_):
    logging.info(f'Loading config: {_FLAGS.config_file}')

    logging.info(f"Downloading files for import {_FLAGS.import_name}")
    school = _FLAGS.import_name
    years_to_download = get_year_list(school)
    if school == "PublicSchool":
        primary_key = KEY_COLUMNS_PUBLIC
        column_names = PUBLIC_COLUMNS
    elif school == "PrivateSchool":
        primary_key = KEY_COLUMNS_PRIVATE
        column_names = PRIVATE_COLUMNS
    elif school == "District":
        primary_key = KEY_COLUMNS_DISTRICT
        column_names = DISTRICT_COLUMNS

    with file_util.FileIO(_FLAGS.config_file, 'r') as f:
        data = json.load(f)
    for year in years_to_download:
        if school in data and year in data[school]:
            id_list = data[school][year]
            print(f"Year {year} exists for {school} in the JSON file.")
        else:
            id_list = fetch_ncid.fetch_school_ncid(school, year, column_names)
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

            nces_elsi_file_download(school, year, curr_columns_selected)
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

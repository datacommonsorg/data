import functools
import io
import json
import logging
import zipfile
import requests
import time
from absl import app, flags

from download_config import COLUMNS_SELECTOR_URL
from download_config import COMPRESS_FILE_URL
from download_config import DOWNLOAD_URL
from download_config import COLUMNS_SELECTOR
from download_config import COMPRESS_FILE
from download_config import HEADERS
from download_config import COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL
from download_config import MAX_RETRIES
from download_config import RETRY_SLEEP_SECS

from download_files_details import DEFAULT_COLUMNS_SELECTED
from download_files_details import COLUMNS_TO_DOWNLOAD_PUBLIC, COLUMNS_TO_DOWNLOAD_PRIVATE, COLUMNS_TO_DOWNLOAD_DISTRICT
from download_files_details import SCHOOL
from download_files_details import YEARS_SELECTED
from download_files_details import KEY_COLUMNS_PRIVATE
from download_files_details import KEY_COLUMNS_PUBLIC
from download_files_details import KEY_COLUMNS_DISTRICT

_FLAGS = flags.FLAGS
flags.DEFINE_enum("import_name", None,
                  ["PublicSchool", "PrivateSchool", "District"],
                  "Import name for which input files to be downloaded")
flags.DEFINE_list("years_to_download", None,
                  "Years for which file has to be downloaded")
flags.mark_flag_as_required("import_name")


def _call_export_csv_api(school: str, year: str, columns: list) -> str:

    COLUMNS_SELECTOR["lColumnsSelected"] = DEFAULT_COLUMNS_SELECTED + columns
    COLUMNS_SELECTOR["sLevel"] = school
    COLUMNS_SELECTOR["lYearsSelected"] = [year]

    response = requests.post(url=COLUMNS_SELECTOR_URL,
                             json=COLUMNS_SELECTOR,
                             headers=HEADERS)
    if response.status_code == 200:
        src_file_name = json.loads(response.text)['d']
        return src_file_name
    else:
        print(f"Non success return code : {response.status_code}")
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
                    logging.exception(
                        f'Retrying in {RETRY_SLEEP_SECS} seconds : attempt {attempt} out of {MAX_RETRIES}'
                    )
                    time.sleep(RETRY_SLEEP_SECS)
                else:
                    logging.exception(
                        f'Execution failed even after retry for {args}')

    return wrapped


def _call_compress_api(file_name: str) -> str:

    COMPRESS_FILE["sFileName"] = file_name
    response = requests.post(url=COMPRESS_FILE_URL,
                             json=COMPRESS_FILE,
                             headers=HEADERS)
    if response.status_code == 200:

        compressed_src_file = json.loads(response.text)
        compressed_src_file = json.loads(response.text)['d'][0]
        return compressed_src_file
    else:
        return None


def _call_download_api(compressed_src_file: str, year: str) -> int:

    res = requests.get(url=DOWNLOAD_URL.format(
        compressed_src_file=compressed_src_file))
    if res.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(res.content)) as zipfileout:
            zipfileout.extractall(f"scripts/us_nces/input_files/{year}")
        return 0
    else:
        return 1


def main(_):
    print(f"Downloading files for import {_FLAGS.import_name}")
    school = _FLAGS.import_name
    if school == "PublicSchool":
        columns_to_download_list = COLUMNS_TO_DOWNLOAD_PUBLIC
        primary_key = KEY_COLUMNS_PUBLIC
    elif school == "PrivateSchool":
        columns_to_download_list = COLUMNS_TO_DOWNLOAD_PRIVATE
        primary_key = KEY_COLUMNS_PRIVATE
    elif school == "District":
        columns_to_download_list = COLUMNS_TO_DOWNLOAD_DISTRICT
        primary_key = KEY_COLUMNS_DISTRICT

    if _FLAGS.years_to_download is None:
        years_to_download = columns_to_download_list.keys()
    else:
        years_to_download = _FLAGS.years_to_download
    for year in years_to_download:
        index_columns_selected = 0
        COLUMNS_TO_DOWNLOAD = columns_to_download_list[year]
        total_columns_to_download = len(COLUMNS_TO_DOWNLOAD)
        while (index_columns_selected < total_columns_to_download):
            start_idx = index_columns_selected

            remaining_columns_to_select = total_columns_to_download - index_columns_selected

            end_idx = index_columns_selected + min(
                remaining_columns_to_select,
                COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)

            curr_columns_selected = COLUMNS_TO_DOWNLOAD[
                start_idx:end_idx] + primary_key

            index_columns_selected = index_columns_selected + min(
                remaining_columns_to_select,
                COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)
            print("--------------------------------------------")
            print(
                f" {school} - {year} - {index_columns_selected} columns out of {total_columns_to_download}"
            )
            print("********************************************")

            nces_elsi_file_download(school, year, curr_columns_selected)
        print(f"Dowloand complete for year {year}")


@retry
def nces_elsi_file_download(school, year, curr_columns_selected):

    file_name = _call_export_csv_api(school, year, curr_columns_selected)
    if file_name is None:
        raise Exception("Export to csv Failure")
    else:
        print(f"compress ouput csv {file_name}")
        compressed_file_path = _call_compress_api(file_name)

        if compressed_file_path is None:
            raise Exception("Compress file Failure")
        else:
            print("Download the compressed file")
            download_ret = _call_download_api(compressed_file_path, year)
            if download_ret != 0:
                raise Exception("Download Failure")


#if __name__ == '__main__':
#    download()

if __name__ == "__main__":
    app.run(main)
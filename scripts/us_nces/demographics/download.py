import functools
import io
import json
import logging
import zipfile
import requests

from download_config import COLUMNS_SELECTOR_URL
from download_config import COMPRESS_FILE_URL
from download_config import DOWNLOAD_URL
from download_config import COLUMNS_SELECTOR
from download_config import COMPRESS_FILE
from download_config import HEADERS
from download_config import COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL

from download_files_details import DEFAULT_COLUMNS_SELECTED
from download_files_details import COLUMNS_TO_DOWNLOAD_PUBLIC, COLUMNS_TO_DOWNLOAD_PRIVATE, COLUMNS_TO_DOWNLOAD_DISTRICT
from download_files_details import SCHOOL
from download_files_details import YEARS_SELECTED


def _call_export_csv_api(school: str, year: str, columns: list) -> str:

    COLUMNS_SELECTOR["lColumnsSelected"] = DEFAULT_COLUMNS_SELECTED + columns
    COLUMNS_SELECTOR["sLevel"] = school
    COLUMNS_SELECTOR["lYearsSelected"] = [year]

    response = requests.post(url=COLUMNS_SELECTOR_URL,
                             json=COLUMNS_SELECTOR,
                             headers=HEADERS)

    src_file_name = json.loads(response.text)['d']

    return src_file_name


def retry(f):
    """Wrap a function so that the function is retried automatically."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except Exception:
                logging.exception('retrying %s', args)

    return wrapped


def _call_compress_api(file_name: str) -> str:

    COMPRESS_FILE["sFileName"] = file_name
    response = requests.post(url=COMPRESS_FILE_URL,
                             json=COMPRESS_FILE,
                             headers=HEADERS)

    compressed_src_file = json.loads(response.text)
    compressed_src_file = json.loads(response.text)['d'][0]

    return compressed_src_file


def _call_download_api(compressed_src_file: str) -> None:

    res = requests.get(url=DOWNLOAD_URL.format(
        compressed_src_file=compressed_src_file))
    with zipfile.ZipFile(io.BytesIO(res.content)) as zipfileout:
        zipfileout.extractall("scripts/us_nces/input_files")


def download():
    print("inside download")
    print("Working")
    print("WORK")
    for school in SCHOOL:
        for year in YEARS_SELECTED:
            columns_selected = 0
            if school == "PublicSchool":
                COLUMNS_TO_DOWNLOAD = COLUMNS_TO_DOWNLOAD_PUBLIC[year]
            elif school == "PrivateSchool":
                COLUMNS_TO_DOWNLOAD = COLUMNS_TO_DOWNLOAD_PRIVATE[year]
            elif school == "District":
                COLUMNS_TO_DOWNLOAD = COLUMNS_TO_DOWNLOAD_DISTRICT[year]
            TOTAL_COLUMNS_TO_DOWNLOAD = len(COLUMNS_TO_DOWNLOAD)
            while (columns_selected < len(COLUMNS_TO_DOWNLOAD)):
                print("--------------------------------------------")
                print(school)
                print(year)
                print("********************************************")
                start_idx = columns_selected

                remaining_columns_to_select = TOTAL_COLUMNS_TO_DOWNLOAD - columns_selected

                end_idx = columns_selected + min(
                    remaining_columns_to_select,
                    COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)

                curr_columns_selected = COLUMNS_TO_DOWNLOAD[start_idx:end_idx]

                columns_selected = columns_selected + min(
                    remaining_columns_to_select,
                    COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL)
                test_func(school, year, curr_columns_selected)
                print("exit dowloand")


@retry
def test_func(school, year, curr_columns_selected):

    file_name = _call_export_csv_api(school, year, curr_columns_selected)

    compressed_file_path = _call_compress_api(file_name)

    _call_download_api(compressed_file_path)


if __name__ == '__main__':
    download()
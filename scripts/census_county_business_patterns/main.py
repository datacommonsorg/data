# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import io
import re
from absl import app
from absl import flags
from absl import logging
from google.cloud import storage

# Import your MSAProcessor class
from cbp_co import CBPCOProcessor
from cbp_msa import CBPMSAProcessor
from zbp import ZBPTotalsProcessor
from zbp_detail import ZBPDetailProcessor

FLAGS = flags.FLAGS
from datetime import datetime
from retry import retry
import requests
import zipfile

# Define flags for paths and year
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
if not os.path.exists(_GCS_OUTPUT_DIR):
    os.makedirs(_GCS_OUTPUT_DIR, exist_ok=True)

_LOCAL_OUTPUT_PATH = os.path.join(_GCS_OUTPUT_DIR, 'source_files')
if not os.path.exists(_LOCAL_OUTPUT_PATH):
    os.makedirs(_LOCAL_OUTPUT_PATH, exist_ok=True)

_OUTPUT_DIR = os.path.join(_GCS_OUTPUT_DIR, 'input_files')
if not os.path.exists(_OUTPUT_DIR):
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

flags.DEFINE_string('output_dir', _OUTPUT_DIR,
                    'Base directory to place the local output files.')
flags.DEFINE_string('gcs_folder_path',
                    'gs://unresolved_mcf/CensusCountyBusinessPatterns',
                    'Input directory where config files downloaded.')
# flags.DEFINE_string('year', '2021', 'YYYY to generate stats for.')
flags.DEFINE_bool('test', False, 'Run in test mode.')

flags.DEFINE_integer('data_start_year', os.getenv('START_YEAR', '2016'),
                     'Process data starting from this year.')
flags.DEFINE_integer('data_end_year', os.getenv('END_YEAR',
                                                datetime.now().year),
                     'Process data till current year')

FILE_TYPES_CONFIG = [
    {
        "name":
            "cbp{}co.zip",  # This name will be used for subfolders
        "url_template":
            "https://www2.census.gov/programs-surveys/cbp/datasets/{}/cbp{}co.zip"  # <<< REPLACE THIS URL TEMPLATE
    },
    {
        "name":
            "cbp{}msa.zip",  # Another file type
        "url_template":
            "https://www2.census.gov/programs-surveys/cbp/datasets/{}/cbp{}msa.zip"  # <<< REPLACE THIS URL TEMPLATE
    },
    {
        "name":
            "zbp{}totals.zip",  # And so on
        "url_template":
            "https://www2.census.gov/programs-surveys/cbp/datasets/{}/zbp{}totals.zip"  # <<< REPLACE THIS URL TEMPLATE
    },
    {
        "name":
            "zbp{}detail.zip",  # Fourth type
        "url_template":
            "https://www2.census.gov/programs-surveys/cbp/datasets/{}/zbp{}detail.zip"  # <<< REPLACE THIS URL TEMPLATE
    }
]


@retry(tries=3,
       delay=5,
       backoff=2,
       exceptions=requests.exceptions.ConnectionError)
def retry_method(url, headers=None):
    response = requests.get(url, stream=True, headers=headers, timeout=30)
    response.raise_for_status()
    return response


def download_files():
    start_year = FLAGS.data_start_year
    end_year = FLAGS.data_end_year

    for year in range(start_year, end_year - 1):
        last_two_digits_formatted = f"{year % 100:02d}"
        for filetype in FILE_TYPES_CONFIG:
            name_template = filetype['name']
            url_template = filetype['url_template']
            filename = name_template.format(last_two_digits_formatted)
            url = url_template.format(year, last_two_digits_formatted)
            logging.info(f"downloading url: {url}")
            response = retry_method(url)
            zip_content_stream = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_content_stream, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if not member.endswith('/') and member.lower().endswith(
                            '.txt'):
                        extract_path = os.path.join(_LOCAL_OUTPUT_PATH,
                                                    os.path.basename(member))
                        abs_extract_path = os.path.abspath(extract_path)
                        abs_target_dir = os.path.abspath(_LOCAL_OUTPUT_PATH)
                        if not abs_extract_path.startswith(abs_target_dir):
                            logging.info(
                                f"    WARNING: Path traversal attempt detected for '{member}'. Skipping."
                            )
                            continue  # Skip this member to prevent security risk

                            # Read the file content from the in-memory zip and write it to disk
                        with open(extract_path, 'wb') as outfile:
                            outfile.write(zip_ref.read(member))
                        extracted_any_txt = True
                    else:
                        logging.info(
                            f"Skipping non-txt file/folder in zip: '{member}'")


def main(argv):
    download_files()
    try:
        found_files = False
        for root, _, files in os.walk(_LOCAL_OUTPUT_PATH):
            for filename in files:
                # We only care about .txt files
                if filename.lower().endswith('.txt'):
                    logging.info("processing the file:{filename}")
                    full_local_path = os.path.join(root, filename)
                    found_files = True
                    logging.info(
                        'Found local .txt file: %s. Attempting to process.',
                        filename)
                    with open(full_local_path, 'r', encoding='latin-1') as f:
                        local_file_content = f.read()

                    # Use io.StringIO to treat the string content as a file-like object
                    # This maintains compatibility with your existing processor classes
                    input_file_obj = io.StringIO(local_file_content)
                    logging.info(
                        'Successfully loaded %s into in-memory object.',
                        filename)

                    year_match = re.search(
                        r'(\d{2})(?:co|msa|totals|detail)\.txt$',
                        filename.lower())
                    # processing_year = FLAGS.year
                    if year_match:
                        two_digit_year = year_match.group(1)
                        processing_year = '20' + two_digit_year

                    else:
                        logging.warning(
                            f"Could not extract 2-digit year from filename '{filename}'"
                        )

                    if 'msa' in filename.lower() and filename.lower().endswith(
                            '.txt'):  # Explicitly check for .txt extension
                        logging.info(
                            'Detected CBPMSA .txt file: %s. Initiating CBP MSA processing.',
                            filename)
                        processor = CBPMSAProcessor(
                            input_file_obj=input_file_obj,
                            output_dir=FLAGS.output_dir,
                            year=processing_year,
                            is_test_run=FLAGS.test)
                        processor.process_cbp_data()
                        logging.info("process completed for cbp msa import")
                    elif 'co' in filename.lower() and filename.lower().endswith(
                            '.txt'):  # Explicitly check for .txt extension
                        logging.info(
                            'Detected CBP CO .txt file: %s. Initiating CBP CO processing.',
                            filename)
                        processor = CBPCOProcessor(
                            input_file_obj=input_file_obj,
                            output_dir=FLAGS.output_dir,
                            year=processing_year,
                            is_test_run=FLAGS.test)
                        processor.process_co_data()
                        logging.info("process completed for co import")
                    elif 'totals' in filename.lower() and filename.lower(
                    ).endswith('.txt'):  # Explicitly check for .txt extension
                        logging.info(
                            'Detected ZPB TOTALS .txt file: %s. Initiating ZPB TOTALS processing.',
                            filename)
                        processor = ZBPTotalsProcessor(
                            input_file_obj=input_file_obj,
                            output_dir=FLAGS.output_dir,
                            year=processing_year,
                            is_test_run=FLAGS.test)
                        processor.process_zbp_data()
                        logging.info("process completed for zbp  import")

                    elif 'detail' in filename.lower() and filename.lower(
                    ).endswith('.txt'):  # Explicitly check for .txt extension
                        logging.info(
                            'Detected ZBP DETAILS .txt file: %s. Initiating ZBP DETAILS processing.',
                            filename)
                        processor = ZBPDetailProcessor(
                            input_file_obj=input_file_obj,
                            output_dir=FLAGS.output_dir,
                            year=processing_year,
                            is_test_run=FLAGS.test)
                        processor.process_zbp_detail_data()
                        logging.info("process completed for co import")

            if not found_files:
                logging.warning("No .txt files found in the specified folder")

    except Exception as e:
        logging.fatal('An unexpected error occurred during file processing: %s',
                      e)


if __name__ == '__main__':
    app.run(main)

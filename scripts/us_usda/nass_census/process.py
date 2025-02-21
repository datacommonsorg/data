# Copyright 2021 Google LLC
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
"""Import USDA Census of Agriculture."""

import csv
import io
import os
import sys
import requests
import gzip
import shutil
from datetime import datetime
from absl import app, flags, logging
from retry import retry

# Define flags
_FLAGS = flags.FLAGS
flags.DEFINE_string('output', 'output/agriculture.csv', 'Output CSV file')
flags.DEFINE_string('mode', '', 'Mode to run: "download", "process", or both')

# Constants
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_SCRIPT_DIR)
sys.path.append(os.path.join(_SCRIPT_DIR.split('/scripts')[0], 'util'))

import file_util

CSV_COLUMNS = [
    'variableMeasured', 'observationAbout', 'value', 'unit', 'observationDate'
]

SKIPPED_VALUES = [
    '(D)',
    '(Z)',
]


def check_url_status(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.fatal(f"Error checking URL {url}: {e}")
        return False


@retry(tries=3, delay=2, backoff=2, exceptions=(requests.RequestException,))
def download_file(url, output_path):
    """
    Download a file from the specified URL with retry logic.

    Args:
        url (str): URL of the file to download.
        output_path (str): Local path to save the downloaded file.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
        logging.info(f"Downloaded file: {output_path}")
    except requests.RequestException as e:
        logging.fatal(f"Error downloading file from {url}: {e}")
        raise


def unzip_file(input_path, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir,
            os.path.basename(input_path).replace('.gz', ''))
        with gzip.open(input_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        logging.info(f"Unzipped file to: {output_path}")
        return output_path
    except Exception as e:
        logging.fatal(f"Error unzipping file {input_path}: {e}")


def get_statvars(filename):
    d = {}
    with open(filename) as f:
        lines = f.readlines()
    for l in lines:
        l = l.strip()
        p = l.split('^')
        d[p[0]] = tuple(p[1:])
    return d


def write_csv(reader, out, d):
    try:
        writer = csv.DictWriter(out,
                                fieldnames=CSV_COLUMNS,
                                lineterminator='\n')
        writer.writeheader()
        for r in reader:
            key = r['SHORT_DESC']
            if r['DOMAINCAT_DESC']:
                key += '%%' + r['DOMAINCAT_DESC']
            if key not in d:
                continue
            if r['VALUE'] in SKIPPED_VALUES:
                continue
            value = d[key]
            if r['AGG_LEVEL_DESC'] == 'NATIONAL':
                observationAbout = 'dcid:country/USA'
            elif r['AGG_LEVEL_DESC'] == 'STATE':
                observationAbout = 'dcid:geoId/' + r['STATE_FIPS_CODE']
            elif r['AGG_LEVEL_DESC'] == 'COUNTY':
                observationAbout = 'dcid:geoId/' + r['STATE_FIPS_CODE'] + r[
                    'COUNTY_CODE']
            else:
                continue  # Skip if AGG_LEVEL_DESC is unrecognized
            # Parse observationDate and VALUE
            observationDate = r.get('YEAR', '')
            row = {
                'variableMeasured': 'dcs:' + value[0],
                'observationAbout': observationAbout,
                'value': int(r['VALUE'].replace(',', '')),
                'observationDate': observationDate,
            }
            if len(value) > 1:
                row['unit'] = 'dcs:' + value[1]
            writer.writerow(row)

        logging.info(
            f"Output file: {out.name} has been successfully generated.")

    except Exception as e:
        logging.fatal(f"The write_csv method failed due to the error: {e}")


def merge_csv_files(output_file, input_files):
    with open(output_file, 'w', newline='') as out_f:
        writer = None
        for input_file in input_files:
            with open(input_file, 'r') as in_f:
                reader = csv.DictReader(in_f)
                if writer is None:
                    writer = csv.DictWriter(out_f, fieldnames=reader.fieldnames)
                    writer.writeheader()
                for row in reader:
                    writer.writerow(row)
        logging.info(f"Merged output written to: {output_file}")


def download_and_process_data(year, d):
    url = f"https://www.nass.usda.gov/datasets/qs.census{year}.txt.gz"
    input_dir = "input"
    output_dir = "output"  # Define the output directory
    os.makedirs(input_dir, exist_ok=True)  # Ensure input directory exists
    os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

    if check_url_status(url):
        gz_file_path = os.path.join(input_dir, f"qs.census{year}.txt.gz")
        download_file(url, gz_file_path)  # Download the .gz file
        txt_file_path = unzip_file(gz_file_path,
                                   input_dir)  # Unzip to input directory

        # Set the output file path inside the output directory
        output_file = os.path.join(output_dir, f"agriculture_{year}.csv")

        # Process the file and write the results to the output directory
        with file_util.FileIO(txt_file_path, 'r') as input_f:
            reader = csv.DictReader(input_f, delimiter='\t')
            with file_util.FileIO(output_file, 'w', newline='') as out_f:
                write_csv(reader, out_f, d)

        logging.info(f"Processed file saved to: {output_file}")
        return output_file
    else:
        logging.fatal(f"URL not accessible: {url}")
        return None


def main(_):
    # Ensure the output folder exists
    output_dir = os.path.dirname(_FLAGS.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created missing output directory: {output_dir}")

    #flag 'mode' to do the operations download and process together and individually
    d = get_statvars('statvars')
    mode = _FLAGS.mode
    if mode == 'download' or mode == '':
        files = []
        for year in range(2002, 2048, 5):
            if year <= datetime.now().year:
                file = download_and_process_data(year, d)
                if file:
                    files.append(file)
        if mode == '':
            merge_csv_files(_FLAGS.output, files)
    elif mode == 'process':
        if not os.path.exists('input'):
            logging.fatal(
                "Input directory does not exist. Run with --mode=download first."
            )
            return
        txt_files = [
            os.path.join('input', f)
            for f in os.listdir('input')
            if f.endswith('.txt')
        ]
        output_files = []
        for txt_file in txt_files:
            year = os.path.basename(txt_file).split('qs.census')[-1].split(
                '.txt')[0]
            output_file = f"agriculture_{year}.csv"
            with file_util.FileIO(txt_file, 'r') as input_f:
                reader = csv.DictReader(input_f, delimiter='\t')
                with file_util.FileIO(output_file, 'w', newline='') as out_f:
                    write_csv(reader, out_f, d)
            output_files.append(output_file)
        merge_csv_files(_FLAGS.output, output_files)


if __name__ == '__main__':
    app.run(main)

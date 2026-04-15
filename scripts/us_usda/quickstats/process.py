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
"""Import USDA Agriculture Survey data.

To run this script, specify a USDA api key as follows:

You can request an API key here: https://quickstats.nass.usda.gov/api/

If the key is not specified as above, it falls back to using a key specified
in a GCS config file. However, that file is available to DC team members only.

"""

import json
import requests
import sys
import csv
import multiprocessing
from itertools import repeat
import os
import datetime
from google.cloud import storage
from retry import retry
from absl import app
from absl import flags
from absl import logging
from collections import deque
import time

_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
import file_util

API_BASE = 'https://quickstats.nass.usda.gov/api'
CSV_COLUMNS = [
    'variableMeasured',
    'observationDate',
    'observationAbout',
    'value',
    'unit',
]

SKIPPED_VALUES = {'(D)', '(Z)'}

SKIPPED_COUNTY_CODES = set([
    '998',  # "OTHER" county code
])

_FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')
flags.DEFINE_integer('start_year', 2024, 'start_year')
flags.DEFINE_string('api_key',
                    'gs://unresolved_mcf/us_usda/ag_survey/api_key.json',
                    'directory where api key exists')


def process_survey_data(year, svs, input_dir, out_dir):
    """
    Processes survey data for the given year and saves the results.

    Args:
        year: The year of the survey data.
        svs: A list of survey variables to process.
        input_dir: The output directory to save the processed data.

    Returns:
        None
    """
    start = datetime.datetime.now()
    logging.info(f'Start, {year}, =, {start}')
    try:
        logging.info(f"start processing data for the year : {year}")
        if _FLAGS.mode == "" or _FLAGS.mode == "download":
            os.makedirs(get_parts_dir(input_dir, year), exist_ok=True)
            os.makedirs(get_response_dir(input_dir, year), exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            logging.info('Getting county names')
            county_names = get_param_values('county_name')
            logging.info(f'# counties =, {len(county_names)}')

            pool_size = 2

            with multiprocessing.Pool(pool_size) as pool:
                pool.starmap(
                    fetch_and_write,
                    zip(county_names, repeat(year), repeat(svs),
                        repeat(input_dir)))

        if _FLAGS.mode == "" or _FLAGS.mode == "process":
            write_aggregate_csv(year, input_dir, out_dir)

        end = datetime.datetime.now()
        logging.info(f'End, {year}, =, {end}')
        logging.info(f'Duration, {year}, =, {str(end - start)}')
    except Exception as e:
        logging.fatal(f"Error while processing the data for year: {e}")
        raise RuntimeError(
            f"Failed to process data for year due to: {e}") from e


def get_parts_dir(input_dir, year):
    return f'{input_dir}/parts/{year}'


def get_response_dir(input_dir, year):
    return f"{input_dir}/response/{year}"


def get_response_file_path(input_dir, year, county):
    return f"{get_response_dir(input_dir, year)}/{county}.json"


def write_aggregate_csv(year, input_dir, out_dir):
    """
    Writes aggregated data to a CSV file.

    Args:
        year: The year of the data to aggregate.
        input_dir: The directory where the CSV file should be saved.

    This function likely performs the following steps:

    1. **Load data:** Reads the necessary data files for the given year. 
    2. **Aggregate data:** Performs the aggregation logic (e.g., summing, averaging, grouping) on the loaded data.
    3. **Write to CSV:** Writes the aggregated data to a CSV file within the specified output directory. 

    The specific implementation will depend on the nature of the data and the desired aggregation.
    """
    logging.info(f"Aggregation starts for the year: {year}")
    try:
        parts_dir = get_parts_dir(input_dir, year)
        part_files = os.listdir(parts_dir)
        out_file = f"{out_dir}/ag-{year}.csv"

        logging.info(f'Writing aggregate CSV, {out_file}')

        with open(out_file, 'w', newline='') as out:
            csv_writer = csv.DictWriter(out,
                                        fieldnames=CSV_COLUMNS,
                                        lineterminator='\n')
            csv_writer.writeheader()
            for part_file in part_files:
                if part_file.endswith(".csv"):
                    with open(f"{parts_dir}/{part_file}", 'r') as part:
                        csv_writer.writerows(csv.DictReader(part))
    except Exception as e:
        logging.fatal(f"Error in write_aggregate_csv for year {year}: {e}")


def fetch_and_write(county_name, year, svs, input_dir):
    """
    Fetches survey data for a given county and writes it to a CSV file.
    Args:
        county_name: The name of the county.
        year: The year of the survey data.
        svs: A list of survey variables to include in the output.
        input_dir: The output directory for the CSV file.

    Raises:
        Exception: If any error occurs during the data fetching or writing process.
    """
    logging.info(f"Fetching data for county: {county_name}")
    try:
        out_file = f"{get_parts_dir(input_dir, year)}/{county_name.replace('[^a-zA-Z0-9]', '')}.csv"
        api_data = get_survey_county_data(year, county_name, input_dir)
        county_csv_rows = to_csv_rows(api_data, svs)
        if county_csv_rows:
            logging.info(
                f"Writing {len(county_csv_rows)} rows for county {county_name} to file {out_file}"
            )
            with open(out_file, 'w', newline='') as out:
                write_csv(out, county_csv_rows)
        else:
            logging.info(
                f"No data to write for county {county_name}. Skipping file creation."
            )
    except Exception as e:
        logging.fatal(
            f"Error processing data for county: {county_name}. Error: {e}")


def get_survey_county_data(year, county, input_dir):
    """
    Fetches survey data for a given county and year.
    Args:
        year: The year of the survey data.
        county: The name of the county.
        input_dir: The output directory to save the response file.
    Returns:
        The downloaded survey data.
    Raises:
        Exception: If an error occurs during data fetching or writing.
    """

    logging.info(f"Fetching survey data for county: {county} and year: {year}")

    response_file = get_response_file_path(input_dir, year, county)
    if _FLAGS.mode == "process":
        try:
            if os.path.exists(response_file):
                logging.info(f"Reading response from file: {response_file}")
                with open(response_file, 'r') as f:
                    response = json.load(f)
            else:
                logging.warning(f"Response file not found: {response_file}")
                return {'data': []}
        except Exception as e:
            logging.warning(
                f"Error while reading response file: {response_file}. Error: {e}"
            )
            return {'data': []}

    if _FLAGS.mode == "" or _FLAGS.mode == "download":

        params = {
            'key': get_usda_api_key(),
            'source_desc': "SURVEY",
            'year': year,
            'county_name': county
        }
        try:
            response = get_data(params)
            if response is None:
                logging.error(
                    f"get_data() returned None. Check logs for details.")
                logging.warning(f"No data found for: {county}")
                return {'data': []}

            with open(response_file, 'w') as f:
                logging.info(f"Writing response to file: {response_file}")
                json.dump(response, f, indent=2)

            if 'data' not in response:
                logging.info(f"No api records found for county: {county}")
                return {'data': []}

            # Return the valid response here
            return response

        except Exception as e:
            logging.fatal(
                f"Error while fetching data for county: {county} - {e}")
            # Return a default value in case of any exception
            return {'data': []}


MAX_REQUESTS_PER_WINDOW = 2  # Maximum requests per window (1 request)
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)
request_times = deque()
FIVE_MINUTES_IN_SECONDS = 300  # 5 minutes in seconds


def is_rate_limited():
    current_time = time.time()
    while request_times and request_times[0] <= current_time - RATE_LIMIT_WINDOW:
        request_times.popleft()
    return len(request_times) >= MAX_REQUESTS_PER_WINDOW


@retry(tries=3,
       delay=2,
       backoff=2,
       exceptions=requests.exceptions.RequestException
      )  # Retry only for request exceptions
def get_data(params):
    """
    Download data from the API with retry, rate limiting, and status code handling.

    Args:
        params (dict): Parameters for the API request.
    """
    while is_rate_limited():
        time_until_reset = RATE_LIMIT_WINDOW - (time.time() - request_times[0])
        logging.info(f"Rate limit hit. Waiting {time_until_reset:.1f} seconds.")
        time.sleep(time_until_reset)

    logging.info(f"Fetching data from API: {params}")

    try:
        response = requests.get(f'{API_BASE}/api_GET', params=params)
        response.raise_for_status()

        if response.status_code != 200:
            logging.warning(
                f"API returned non-200 status code: {response.status_code}. Retrying..."
            )
            raise requests.exceptions.RequestException(
                f"Non-200 status code: {response.status_code}")

        request_times.append(time.time())
        return response.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")


def get_param_values(param):
    """
    Retrieves possible values for a given parameter from the API.

    Args:
        param: The name of the parameter to retrieve values for.

    Returns:
        A list of possible values for the given parameter, or an empty list if 
        no values are found or an error occurs. 

    Raises:
        Exception: If an error occurs during the API request.
    """
    params = {'key': get_usda_api_key(), 'param': param}
    try:
        response = requests.get(f'{API_BASE}/get_param_values',
                                params=params).json()

        # Check if the expected parameter key exists in the response
        if param in response:
            return response[param]
        else:
            logging.warning(
                f"Parameter '{param}' not found in API response. Response: {response}"
            )
            return []

    except requests.exceptions.RequestException as e:
        # Handle network-related errors gracefully
        logging.error(
            f"Network error while fetching parameter values for '{param}': {e}")
        return []
    except json.JSONDecodeError as e:
        # Handle cases where the response is not valid JSON
        logging.error(f"JSON decode error for '{param}': {e}")
        return []
    except Exception as e:
        # Catch any other unexpected exceptions
        logging.error(
            f"An unexpected error occurred while fetching '{param}': {e}")
        return []


'''Converts a quickstats data row to a DC CSV row.

data = quickstats data row
svs = {name: {name: ..., sv: ..., unit: ...}}

returns = {variableMeasured: ..., observationAbout: ..., value: ..., unit: ...}
'''


def to_csv_row(data_row, svs):
    name = data_row['short_desc']
    if data_row['domaincat_desc'] and data_row[
            'domaincat_desc'] != 'NOT SPECIFIED':
        name = f"{name}%%{data_row['domaincat_desc']}"

    if name not in svs:
        eprint('SKIPPED, No SV mapped for', name)
        return None

    county_code = data_row['county_code']
    if county_code in SKIPPED_COUNTY_CODES:
        eprint('SKIPPED, Unsupported county code', county_code)
        return None

    value = (data_row['value'] if 'value' in data_row else
             data_row['Value']).strip().replace(',', '')
    if value in SKIPPED_VALUES:
        eprint('SKIPPED, Invalid value', f"'{value}'", 'for', name)
        return None
    value = int(value)
    observation_about = f"dcid:geoId/{data_row['state_fips_code']}{county_code}" if data_row[
        'state_fips_code'] else 'dcid:country/USA'
    sv = svs[name]

    return {
        'variableMeasured': sv['sv'],
        'observationDate': data_row['year'],
        'observationAbout': observation_about,
        'value': value,
        'unit': sv['unit'],
    }


def to_csv_rows(api_data, svs):
    csv_rows = []

    if api_data and 'data' in api_data:
        for data_row in api_data['data']:
            csv_row = to_csv_row(data_row, svs)
            if csv_row:
                csv_rows.append(csv_row)
    return csv_rows


def load_svs():
    svs = {}
    with open("sv.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            svs[row['name']] = row
    return svs


def write_csv(out, rows):
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_multiple_years():
    start = datetime.datetime.now()
    logging.info(f'Start, {start}')
    svs = load_svs()
    start_year = _FLAGS.start_year
    for year in range(start_year, datetime.datetime.now().year + 1):
        process_survey_data(year, svs, "input", "output")
    end = datetime.datetime.now()
    logging.info(f'End, {end}')
    logging.info(f'Duration, {str(end - start)}')


def load_usda_api_key():
    """
    Sets the API key to be used.
    Since we are reading from a config file, this function simply
    ensures the key is available.
    """
    api_key = get_usda_api_key()
    if not api_key:
        raise ValueError("USDA API key not found in bucket path.")
    return api_key


def get_usda_api_key():
    """Reads the USDA API key from the bucket path."""
    # This function now correctly returns the key from the config module.
    file_config = file_util.file_load_py_dict(_FLAGS.api_key)
    api_key = file_config.get('api_key')
    return api_key


def main(_):
    load_usda_api_key()
    logging.info('USDA API key successfully loaded.')
    get_multiple_years()


if __name__ == '__main__':
    app.run(main)

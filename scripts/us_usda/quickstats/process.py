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

from collections import deque
import csv
import datetime
from itertools import repeat
import json
import multiprocessing
import os
import re
import sys
import time

from absl import app
from absl import flags
from absl import logging
import requests
from retry import retry

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

SKIPPED_VALUES = {'(D)', '(Z)', '(NA)', '(S)', '(X)', '(L)', '(H)'}

SKIPPED_COUNTY_CODES = set([
    '998',  # "OTHER" county code
])

QUICKSTATS_ROW_LIMIT = 50000
REQUEST_TIMEOUT = (15, 90)
RETRY_TRIES = 5
RETRY_DELAY = 10
RETRY_BACKOFF = 2
RETRY_MAX_DELAY = 120
RETRY_JITTER = (1, 5)
SECOND_PASS_COOLDOWN_SECONDS = 300
POOL_SIZE = 2

_CACHED_API_KEY = None
_HTTP_SESSION = None
_HTTP_SESSION_PID = None

_FLAGS = flags.FLAGS


def _define_api_key_flag():
    if 'api_key' not in _FLAGS:
        flags.DEFINE_string(
            'api_key', 'gs://unresolved_mcf/us_usda/ag_survey/api_key.json',
            'directory where api key exists')


def _define_flags():
    if 'mode' not in _FLAGS:
        flags.DEFINE_string('mode', '', 'Options: download or process')
    if 'start_year' not in _FLAGS:
        flags.DEFINE_integer('start_year', 2024, 'start_year')
    _define_api_key_flag()


_define_api_key_flag()


class QueryLimitExceededError(Exception):
    """Raised when a QuickStats query exceeds the 50,000-row API limit."""


def _get_mode():
    if _FLAGS.is_parsed() and 'mode' in _FLAGS:
        return _FLAGS.mode
    return ""


def _get_start_year():
    if _FLAGS.is_parsed() and 'start_year' in _FLAGS:
        return _FLAGS.start_year
    return 2024


def _get_api_key_path():
    if _FLAGS.is_parsed() and 'api_key' in _FLAGS:
        return _FLAGS.api_key
    return 'gs://unresolved_mcf/us_usda/ag_survey/api_key.json'


def _sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', str(name)).strip('_') or 'part'


def _redact_params(params):
    if not isinstance(params, dict):
        return params
    return {
        k: ('[REDACTED]' if str(k).lower() in ('key', 'api_key') else v)
        for k, v in params.items()
    }


def _redact_secrets(text):
    if text is None:
        return ''
    redacted = str(text)
    if _CACHED_API_KEY:
        redacted = redacted.replace(_CACHED_API_KEY, '[REDACTED]')
    redacted = re.sub(
        r'(?i)(api_?key|key)([\'\"\s:=]+)[A-Za-z0-9_%-]{4,}',
        r'\1\2[REDACTED]',
        redacted,
    )
    return redacted


def _get_http_session():
    """Returns a fork-safe, per-process requests.Session for connection reuse."""
    global _HTTP_SESSION, _HTTP_SESSION_PID
    pid = os.getpid()
    if _HTTP_SESSION is None or _HTTP_SESSION_PID != pid:
        _HTTP_SESSION = requests.Session()
        _HTTP_SESSION_PID = pid
    return _HTTP_SESSION


def _is_empty_query_400(err_text):
    """Returns True only for benign QuickStats 400 empty-result responses."""
    lowered = str(err_text or '').lower()
    if any(tok in lowered for tok in (
            'key',
            'auth',
            'unauthorized',
            'exceed',
            'limit',
            'too many',
            'missing',
            'token',
    )):
        return False
    return any(tok in lowered for tok in (
        'no data found',
        'invalid query',
        'unsupported query',
    ))


def _write_json_atomic(file_path, payload):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    tmp_path = f'{file_path}.{os.getpid()}.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp_path, file_path)


def _init_worker(cached_api_key):
    """Propagates parent's cached API key to spawned worker processes."""
    global _CACHED_API_KEY
    if cached_api_key and not _CACHED_API_KEY:
        _CACHED_API_KEY = cached_api_key


def _run_partition_task(partition_name, year, svs, input_dir, reuse_existing,
                        mode):
    """Fault-isolated pool worker so one failure never aborts a starmap chunk."""
    try:
        fetch_state_and_write(partition_name,
                              year,
                              svs,
                              input_dir,
                              reuse_existing=reuse_existing,
                              mode=mode)
        return (partition_name, True, '')
    except Exception as e:
        err_msg = _redact_secrets(e)
        logging.error(
            f'Partition {partition_name} failed for year {year}: {err_msg}')
        return (partition_name, False, err_msg)


def _execute_partition_batch(partitions, year, svs, input_dir, reuse_existing,
                             mode):
    if not partitions:
        return []
    worker_count = min(POOL_SIZE, len(partitions))
    if worker_count <= 1:
        return [
            _run_partition_task(p, year, svs, input_dir, reuse_existing, mode)
            for p in partitions
        ]
    with multiprocessing.Pool(worker_count,
                              initializer=_init_worker,
                              initargs=(_CACHED_API_KEY,)) as pool:
        return pool.starmap(
            _run_partition_task,
            zip(
                partitions,
                repeat(year),
                repeat(svs),
                repeat(input_dir),
                repeat(reuse_existing),
                repeat(mode),
            ),
            chunksize=1,
        )


def process_survey_data(year, svs, input_dir, out_dir, states=None, mode=None):
    """
    Processes survey data for the given year and saves the results.

    Args:
        year: The year of the survey data.
        svs: A list of survey variables to process.
        input_dir: The output directory to save the processed data.
        out_dir: Directory where aggregated yearly CSV files are written.
        states: Optional pre-fetched list of state_alpha codes.
        mode: Optional execution mode ('', 'download', or 'process').

    Returns:
        None
    """
    start = datetime.datetime.now()
    logging.info(f'Start, {year}, =, {start}')
    try:
        logging.info(f"start processing data for the year : {year}")
        parts_dir = get_parts_dir(input_dir, year)
        if os.path.exists(parts_dir):
            for fname in os.listdir(parts_dir):
                if fname.endswith('.csv') or fname.endswith('.tmp'):
                    os.remove(os.path.join(parts_dir, fname))
        os.makedirs(parts_dir, exist_ok=True)
        os.makedirs(get_response_dir(input_dir, year), exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        if mode is None:
            mode = _get_mode()
        if mode in ("", "download", "process"):
            response_dir = get_response_dir(input_dir, year)
            if mode == "process":
                if os.path.exists(response_dir):
                    partitions = sorted(
                        os.path.splitext(f)[0]
                        for f in os.listdir(response_dir)
                        if f.endswith('.json'))
                else:
                    partitions = []
            else:
                if states is not None:
                    partitions = list(states)
                else:
                    logging.info('Getting state_alpha values')
                    partitions = get_param_values('state_alpha')

            logging.info(f'# partitions =, {len(partitions)}')

            if partitions:
                results = _execute_partition_batch(partitions,
                                                   year,
                                                   svs,
                                                   input_dir,
                                                   reuse_existing=False,
                                                   mode=mode)
                failed = [(name, err) for name, ok, err in results if not ok]

                if failed and mode != "process":
                    failed_names = [name for name, _ in failed]
                    logging.warning(
                        f'{len(failed_names)} partitions failed in pass 1 for '
                        f'year {year} ({failed_names}); waiting '
                        f'{SECOND_PASS_COOLDOWN_SECONDS}s before retry pass.')
                    time.sleep(SECOND_PASS_COOLDOWN_SECONDS)
                    retry_results = _execute_partition_batch(
                        failed_names,
                        year,
                        svs,
                        input_dir,
                        reuse_existing=True,
                        mode=mode)
                    failed = [
                        (name, err) for name, ok, err in retry_results if not ok
                    ]

                if failed:
                    summary = '; '.join(
                        f'{name}: {err}' for name, err in failed[:5])
                    raise RuntimeError(
                        f'{len(failed)} partition(s) failed for year {year}: '
                        f'{summary}')

        if mode == "" or mode == "process":
            write_aggregate_csv(year, input_dir, out_dir)

        end = datetime.datetime.now()
        logging.info(f'End, {year}, =, {end}')
        logging.info(f'Duration, {year}, =, {str(end - start)}')
    except Exception as e:
        redacted_err = _redact_secrets(e)
        logging.error(
            f"Error while processing the data for year: {redacted_err}")
        raise RuntimeError(
            f"Failed to process data for year {year} due to: {redacted_err}"
        ) from e


def get_parts_dir(input_dir, year):
    return f'{input_dir}/parts/{year}'


def get_response_dir(input_dir, year):
    return f"{input_dir}/response/{year}"


def get_response_file_path(input_dir, year, county):
    return f"{get_response_dir(input_dir, year)}/{_sanitize_filename(county)}.json"


def write_aggregate_csv(year, input_dir, out_dir):
    """Deduplicates, sorts, and atomically writes the yearly aggregate CSV."""
    logging.info(f"Aggregation starts for the year: {year}")
    try:
        parts_dir = get_parts_dir(input_dir, year)
        if not os.path.exists(parts_dir):
            logging.warning(
                f"Parts directory {parts_dir} does not exist. Skipping aggregation."
            )
            return
        part_files = sorted(
            f for f in os.listdir(parts_dir) if f.endswith(".csv"))
        os.makedirs(out_dir, exist_ok=True)
        out_file = f"{out_dir}/ag-{year}.csv"
        tmp_file = f"{out_file}.{os.getpid()}.tmp"

        logging.info(f'Writing aggregate CSV, {out_file}')

        seen = set()
        rows = []
        for part_file in part_files:
            with open(f"{parts_dir}/{part_file}", 'r', newline='') as part:
                for row in csv.DictReader(part):
                    dedup_key = tuple(row[col] for col in CSV_COLUMNS)
                    if dedup_key not in seen:
                        seen.add(dedup_key)
                        rows.append(row)

        rows.sort(key=lambda r: (
            r['variableMeasured'],
            r['observationAbout'],
            str(r['observationDate']),
        ))

        with open(tmp_file, 'w', newline='') as out:
            csv_writer = csv.DictWriter(out,
                                        fieldnames=CSV_COLUMNS,
                                        lineterminator='\n')
            csv_writer.writeheader()
            csv_writer.writerows(rows)
        os.replace(tmp_file, out_file)
    except Exception as e:
        logging.error(f"Error in write_aggregate_csv for year {year}: {e}")
        raise


def fetch_state_and_write(state_alpha,
                          year,
                          svs,
                          input_dir,
                          reuse_existing=False,
                          mode=None):
    """Fetches county-level survey data for a state (with county fallback) and writes part CSV."""
    logging.info(f"Fetching data for state: {state_alpha} (year: {year})")
    out_file = f"{get_parts_dir(input_dir, year)}/{_sanitize_filename(state_alpha)}.csv"
    api_data = get_survey_state_data(year,
                                     state_alpha,
                                     input_dir,
                                     reuse_existing=reuse_existing,
                                     mode=mode)
    state_csv_rows = to_csv_rows(api_data, svs)
    if state_csv_rows:
        logging.info(
            f"Writing {len(state_csv_rows)} rows for state {state_alpha} to file {out_file}"
        )
        tmp_file = f"{out_file}.{os.getpid()}.tmp"
        with open(tmp_file, 'w', newline='') as out:
            write_csv(out, state_csv_rows)
        os.replace(tmp_file, out_file)
    else:
        if os.path.exists(out_file):
            os.remove(out_file)
        logging.info(
            f"No data to write for state {state_alpha}. Skipping file creation."
        )


def get_survey_state_data(year,
                          state_alpha,
                          input_dir,
                          reuse_existing=False,
                          mode=None):
    """Fetches county-level survey data for a given state and year, splitting by county if needed."""
    response_file = get_response_file_path(input_dir, year, state_alpha)
    if mode is None:
        mode = _get_mode()

    if mode == "process":
        if not os.path.exists(response_file):
            logging.warning(f"Response file not found: {response_file}")
            return {'data': []}
        logging.info(f"Reading response from file: {response_file}")
        with open(response_file, 'r') as f:
            response = json.load(f)
        return response if isinstance(response,
                                      dict) and 'data' in response else {
                                          'data': []
                                      }

    if mode in ("", "download"):
        if reuse_existing and os.path.exists(response_file):
            try:
                with open(response_file, 'r') as f:
                    cached = json.load(f)
                if isinstance(cached, dict):
                    return cached if 'data' in cached else {'data': []}
            except Exception:
                pass

        params = {
            'key': get_usda_api_key(),
            'source_desc': 'SURVEY',
            'agg_level_desc': 'COUNTY',
            'year': year,
            'state_alpha': state_alpha,
        }
        try:
            response = get_data(params)
            if response is None:
                raise RuntimeError(
                    f"get_data() returned None for state: {state_alpha}")
            if len(response.get('data', [])) >= QUICKSTATS_ROW_LIMIT:
                raise QueryLimitExceededError(
                    f"State {state_alpha} returned {len(response['data'])} rows "
                    f"(>= {QUICKSTATS_ROW_LIMIT}).")

            logging.info(f"Writing response to file: {response_file}")
            _write_json_atomic(response_file, response)

            if 'data' not in response:
                return {'data': []}
            return response

        except QueryLimitExceededError as limit_err:
            logging.warning(
                f"{limit_err} Falling back to county-level queries for state {state_alpha}."
            )
            return _fetch_state_by_counties(year,
                                            state_alpha,
                                            input_dir,
                                            reuse_existing=reuse_existing)
        except Exception as e:
            redacted = _redact_secrets(e)
            logging.error(
                f"Error while fetching data for state: {state_alpha} - {redacted}"
            )
            raise RuntimeError(
                f"Error while fetching data for state {state_alpha}: {redacted}"
            ) from e

    return {'data': []}


def _fetch_state_by_counties(year,
                             state_alpha,
                             input_dir,
                             reuse_existing=False):
    """Fallback when a single state's COUNTY survey rows exceed QuickStats' 50,000-row cap."""
    counties = get_param_values('county_name',
                                state_alpha=state_alpha,
                                agg_level_desc='COUNTY')
    if not counties:
        raise RuntimeError(
            f"County fallback returned no counties for state {state_alpha} (year {year})."
        )

    combined_rows = []
    failed_counties = []
    for county in counties:
        partition_key = f"{state_alpha}_{_sanitize_filename(county)}"
        county_file = get_response_file_path(input_dir, year, partition_key)
        if reuse_existing and os.path.exists(county_file):
            try:
                with open(county_file, 'r') as f:
                    cached = json.load(f)
                if isinstance(cached, dict):
                    combined_rows.extend(cached.get('data', []))
                    continue
            except Exception:
                pass

        params = {
            'key': get_usda_api_key(),
            'source_desc': 'SURVEY',
            'agg_level_desc': 'COUNTY',
            'year': year,
            'state_alpha': state_alpha,
            'county_name': county,
        }
        try:
            resp = get_data(params)
            if resp is None:
                raise RuntimeError(
                    f"get_data() returned None for {state_alpha}/{county}")
            _write_json_atomic(county_file, resp)
            combined_rows.extend(resp.get('data', []))
        except Exception as e:
            failed_counties.append((county, _redact_secrets(e)))

    if failed_counties:
        sample = ', '.join(f"{c} ({err})" for c, err in failed_counties[:3])
        raise RuntimeError(
            f"Failed {len(failed_counties)}/{len(counties)} counties in state "
            f"{state_alpha}: {sample}")

    return {'data': combined_rows}


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
    if _get_mode() == "process":
        try:
            if os.path.exists(response_file):
                logging.info(f"Reading response from file: {response_file}")
                with open(response_file, 'r') as f:
                    response = json.load(f)
                return response
            else:
                logging.warning(f"Response file not found: {response_file}")
                return {'data': []}
        except Exception as e:
            logging.warning(
                f"Error while reading response file: {response_file}. Error: {e}"
            )
            return {'data': []}

    if _get_mode() == "" or _get_mode() == "download":

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
                    f"get_data() returned None for county: {county}. Raising error to prevent silent data loss."
                )
                raise RuntimeError(
                    f"get_data() returned None for county: {county}")

            _write_json_atomic(response_file, response)
            logging.info(f"Writing response to file: {response_file}")

            if 'data' not in response:
                logging.info(f"No api records found for county: {county}")
                return {'data': []}

            # Return the valid response here
            return response

        except Exception as e:
            logging.error(
                f"Error while fetching data for county: {county} - {_redact_secrets(e)}"
            )
            raise


MAX_REQUESTS_PER_WINDOW = 2  # Maximum requests per window (1 request)
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)
request_times = deque()
FIVE_MINUTES_IN_SECONDS = 300  # 5 minutes in seconds


def is_rate_limited():
    current_time = time.time()
    while request_times and request_times[0] <= current_time - RATE_LIMIT_WINDOW:
        request_times.popleft()
    return len(request_times) >= MAX_REQUESTS_PER_WINDOW


@retry(
    tries=RETRY_TRIES,
    delay=RETRY_DELAY,
    backoff=RETRY_BACKOFF,
    max_delay=RETRY_MAX_DELAY,
    jitter=RETRY_JITTER,
    exceptions=requests.exceptions.RequestException,
)  # Retry only for request exceptions
def get_data(params):
    """
    Download data from the API with retry, rate limiting, and status code handling.

    Args:
        params (dict): Parameters for the API request.
    """
    while is_rate_limited():
        time_until_reset = max(
            0.0, RATE_LIMIT_WINDOW - (time.time() - request_times[0]))
        logging.info(f"Rate limit hit. Waiting {time_until_reset:.1f} seconds.")
        time.sleep(time_until_reset)

    safe_params = _redact_params(params)
    url = f'{API_BASE}/api_GET'
    logging.info(f"Outbound request: GET {url} params={safe_params}")

    try:
        response = _get_http_session().get(url,
                                           params=params,
                                           timeout=REQUEST_TIMEOUT)
        if response.status_code == 413:
            raise QueryLimitExceededError(
                f"API returned 413 Payload Too Large for query: {safe_params}")

        if response.status_code == 400:
            err_text = ''
            try:
                err_json = response.json()
                err_text = str(err_json.get("error", "")).lower()
            except Exception:
                err_text = str(response.text or "").lower()

            if ("exceed" in err_text or "limit" in err_text or
                    "too many" in err_text):
                raise QueryLimitExceededError(
                    f"Query exceeded QuickStats limit for {safe_params}: "
                    f"{_redact_secrets(response.text)}")

            if _is_empty_query_400(err_text):
                logging.info(f"No records found for query: {safe_params}")
                request_times.append(time.time())
                return {'data': []}

            redacted_body = _redact_secrets(response.text)
            logging.warning(
                f"API returned 400 status code with error: {redacted_body}")
            raise requests.exceptions.RequestException(
                f"Status 400 error: {redacted_body}")

        response.raise_for_status()

        if response.status_code != 200:
            logging.warning(
                f"API returned non-200 status code: {response.status_code}. Retrying..."
            )
            raise requests.exceptions.RequestException(
                f"Non-200 status code: {response.status_code}")

        request_times.append(time.time())
        return response.json()

    except QueryLimitExceededError:
        raise
    except requests.exceptions.RequestException as e:
        redacted_err = _redact_secrets(e)
        logging.error(f"Error fetching data for {safe_params}: {redacted_err}")
        raise requests.exceptions.RequestException(redacted_err) from None


@retry(
    tries=RETRY_TRIES,
    delay=RETRY_DELAY,
    backoff=RETRY_BACKOFF,
    max_delay=RETRY_MAX_DELAY,
    jitter=RETRY_JITTER,
    exceptions=requests.exceptions.RequestException,
)
def _fetch_param_values_json(params):
    while is_rate_limited():
        time_until_reset = max(
            0.0, RATE_LIMIT_WINDOW - (time.time() - request_times[0]))
        logging.info(f"Rate limit hit. Waiting {time_until_reset:.1f} seconds.")
        time.sleep(time_until_reset)

    safe_params = _redact_params(params)
    url = f'{API_BASE}/get_param_values'
    logging.info(f"Outbound request: GET {url} params={safe_params}")
    try:
        resp = _get_http_session().get(url,
                                       params=params,
                                       timeout=REQUEST_TIMEOUT)
        if resp.status_code == 400:
            err_text = ''
            try:
                err_json = resp.json()
                err_text = str(err_json.get("error", "")).lower()
            except Exception:
                err_text = str(resp.text or "").lower()
            if _is_empty_query_400(err_text):
                request_times.append(time.time())
                return {}
        resp.raise_for_status()
        request_times.append(time.time())
        return resp.json()
    except requests.exceptions.RequestException as e:
        redacted_err = _redact_secrets(e)
        logging.error(
            f"Error fetching param values for {safe_params}: {redacted_err}")
        raise requests.exceptions.RequestException(redacted_err) from None


def get_param_values(param, **extra_filters):
    """
    Retrieves possible values for a given parameter from the API.

    Args:
        param: The name of the parameter to retrieve values for.
        **extra_filters: Optional QuickStats filter parameters (e.g. state_alpha).

    Returns:
        A non-empty list of parameter values (or [] if scoped filter has no matches).

    Raises:
        RuntimeError: If the API request fails, returns invalid JSON, or returns
            no values for an unscoped parameter lookup.
    """
    params = {'key': get_usda_api_key(), 'param': param}
    params.update(extra_filters)
    try:
        response = _fetch_param_values_json(params)
        if not response and extra_filters:
            return []
        if isinstance(response, dict) and param in response and response[param]:
            return response[param]
        if extra_filters and isinstance(response, dict) and param in response:
            return response[param]
        raise RuntimeError(
            f"Parameter '{param}' missing or empty in API response for "
            f"{_redact_params(params)}")
    except Exception as e:
        redacted_err = _redact_secrets(e)
        logging.error(
            f"Failed to retrieve parameter values for '{param}': {redacted_err}"
        )
        raise RuntimeError(
            f"Failed to retrieve parameter values for '{param}': {redacted_err}"
        ) from e


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

    county_code = str(data_row.get('county_code', '')).strip()
    if not county_code or county_code in SKIPPED_COUNTY_CODES:
        eprint('SKIPPED, Unsupported county code', county_code)
        return None

    value = (data_row['value'] if 'value' in data_row else
             data_row['Value']).strip().replace(',', '')
    if not value or value in SKIPPED_VALUES or value.startswith('('):
        eprint('SKIPPED, Invalid value', f"'{value}'", 'for', name)
        return None
    value = int(value)
    state_fips = str(data_row.get('state_fips_code', '')).strip()
    observation_about = (f"dcid:geoId/{state_fips}{county_code}"
                         if state_fips else 'dcid:country/USA')
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
    sv_path = os.path.join(_SCRIPT_PATH, "sv.csv")
    with open(sv_path, newline='') as csvfile:
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
    start_year = _get_start_year()
    input_dir = os.path.join(_SCRIPT_PATH, 'input')
    out_dir = os.path.join(_SCRIPT_PATH, 'output')
    states = None
    mode = _get_mode()
    if mode != 'process':
        logging.info('Getting state_alpha values once for all years')
        states = get_param_values('state_alpha')
    for year in range(start_year, datetime.datetime.now().year + 1):
        process_survey_data(year,
                            svs,
                            input_dir,
                            out_dir,
                            states=states,
                            mode=mode)
    end = datetime.datetime.now()
    logging.info(f'End, {end}')
    logging.info(f'Duration, {str(end - start)}')


def load_usda_api_key():
    """
    Sets the API key to be used.
    Since we are reading from a config file, this function simply
    ensures the key is available.
    """
    global _CACHED_API_KEY
    if _get_mode() == "process":
        _CACHED_API_KEY = "mock-key-for-process-mode"
        return _CACHED_API_KEY
    api_key = get_usda_api_key()
    if not api_key:
        raise ValueError("USDA API key not found in bucket path.")
    return api_key


def get_usda_api_key():
    """Reads the USDA API key from the bucket path and caches it in memory."""
    global _CACHED_API_KEY
    if _CACHED_API_KEY:
        return _CACHED_API_KEY
    # This function now correctly returns the key from the config module.
    file_config = file_util.file_load_py_dict(_get_api_key_path())
    api_key = file_config.get('api_key')
    if api_key:
        _CACHED_API_KEY = api_key
    return api_key


def main(_):
    load_usda_api_key()
    logging.info('USDA API key successfully loaded.')
    get_multiple_years()


if __name__ == '__main__':
    _define_flags()
    app.run(main)

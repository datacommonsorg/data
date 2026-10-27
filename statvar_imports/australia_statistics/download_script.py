#!/usr/bin/env python3
# Copyright 2026 Google LLC
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
"""Downloads Australia Bureau of Statistics (ABS) datasets live as-is to input_files/."""

import concurrent.futures
import os
import socket
import tempfile
import threading
import time

from absl import app
from absl import flags
from absl import logging
import requests
from requests.adapters import HTTPAdapter
import urllib3.util.connection
from urllib3.util.retry import Retry

# Force IPv4 resolution because data.api.abs.gov.au has broken IPv6 routing
# from some cloud environments, causing IPv6 connection timeouts before fallback.
urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'output_dir',
    os.path.join(_MODULE_DIR, 'input_files'),
    'Output directory for raw downloaded ABS files.',
)
flags.DEFINE_integer(
    'max_workers',
    5,
    'Maximum number of concurrent dataset download workers.',
)

_THREAD_LOCAL = threading.local()

# ABS SDMX API endpoints
ABS_LF_SDMX_URL = ('https://data.api.abs.gov.au/rest/data/ABS,LF,1.0.0/'
                   'M3+M6+M13.1+2+3.1599.10.AUS+1+2+3+4+5+6+7+8.M'
                   '?startPeriod=1978-02&format=csv')
ABS_ERP_Q_SDMX_URL = (
    'https://data.api.abs.gov.au/rest/data/ABS,ERP_Q,1.0.0/'
    '1.1+2+3.A04+A59+A10+A15+A20+A25+A30+A35+A40+A45+A50+A55+A60+A65+A70+A75+A80+8599+TOT.'
    'AUS+1+2+3+4+5+6+7+8.Q?startPeriod=2017-Q2&format=csv')

# Direct ABS publication workbook URLs
ABS_CENSUS_POP_2021_URL = (
    'https://www.abs.gov.au/statistics/people/population/population-census/'
    '2021/Population%20data%20summary.xlsx')
ABS_HIST_POP_URL = (
    'https://www.abs.gov.au/statistics/people/population/historical-population/'
    '2016/3105065001ds0002_2019.xls')
ABS_HIST_LIFE_EXP_URL = (
    'https://www.abs.gov.au/statistics/people/population/historical-population/'
    '2016/3105065001ds0006_2019.xls')
ABS_LIFE_EXP_BASE_URL = (
    'https://www.abs.gov.au/statistics/people/population/life-expectancy')
ABS_HEALTH_2021_URL = (
    'https://www.abs.gov.au/statistics/health/health-conditions-and-risks/'
    'health-census/2021/'
    'Health%20data%20summary%20-%20first%20and%20second%20release.xlsx')
ABS_INCOME_URL = (
    'https://www.abs.gov.au/statistics/economy/finance/'
    'household-income-and-wealth-australia/2019-20/'
    '1.%20Household%20income%20and%20income%20distribution%2C%20Australia.xlsx'
)

STATIC_DATASETS: dict[str, str] = {
    'abs_lf_sdmx.csv': ABS_LF_SDMX_URL,
    'abs_erp_q_sdmx.csv': ABS_ERP_Q_SDMX_URL,
    'population_data_summary_2021.xlsx': ABS_CENSUS_POP_2021_URL,
    'historical_population_2016.xls': ABS_HIST_POP_URL,
    'historical_life_expectancy_2016.xls': ABS_HIST_LIFE_EXP_URL,
    'health_data_summary_2021.xlsx': ABS_HEALTH_2021_URL,
    'household_income_2019_20.xlsx': ABS_INCOME_URL,
}


def _get_session() -> requests.Session:
    """Returns a thread-local HTTP session with retry logic for transient errors."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
        session = requests.Session()
        retry = Retry(
            total=5,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=('HEAD', 'GET'),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.headers.update(
            {'User-Agent': 'DataCommons-AustraliaStatistics-Importer/1.0'})
        _THREAD_LOCAL.session = session
    return session


def _fetch_bytes(url: str, timeout: int = 60) -> bytes:
    """Downloads raw bytes from a URL with retry logic."""
    session = _get_session()
    for attempt in range(10):
        try:
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            if not resp.content:
                raise RuntimeError(f'Empty response body from {url}')
            return resp.content
        except requests.exceptions.RequestException as e:
            if attempt == 9:
                raise RuntimeError(f'Failed to download {url}: {e}') from e
            time.sleep(2**attempt)
    raise RuntimeError(f'Unreachable download failure for {url}')


def _write_bytes_atomically(output_filepath: str, data: bytes) -> None:
    """Writes raw bytes atomically to output_filepath and verifies non-empty output."""
    if not data:
        raise RuntimeError(
            f'Refusing to write empty payload to {output_filepath}')
    output_dir = os.path.dirname(output_filepath)
    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix='.tmp_aus_',
        suffix=os.path.splitext(output_filepath)[1],
        dir=output_dir,
    )
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        if not (os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0):
            raise RuntimeError(
                f'Atomic write failed: {tmp_path} is empty or missing.')
        os.replace(tmp_path, output_filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _download_static_file(filename: str, url: str,
                          output_dir: str) -> dict[str, int]:
    """Downloads a single raw source file as-is into output_dir."""
    logging.info('Downloading %s from %s...', filename, url)
    content = _fetch_bytes(url)
    if filename.endswith('.csv'):
        text_head = content[:256].decode('utf-8-sig', errors='ignore').lstrip()
        if not text_head.startswith('DATAFLOW,'):
            raise RuntimeError(
                f'Invalid SDMX CSV payload from {url}: {text_head[:100]!r}')
    out_path = os.path.join(output_dir, filename)
    _write_bytes_atomically(out_path, content)
    return {filename: len(content)}


def _download_recent_life_expectancy_workbooks(
    output_dir: str, ) -> dict[str, int]:
    """Downloads ABS 3-year period Life Tables workbooks as-is (2016-2018+)."""
    session = _get_session()
    current_year = time.gmtime().tm_year
    downloaded: dict[str, int] = {}

    for start_yr in range(2016, current_year):
        end_yr = str(start_yr + 2)
        period = f'{start_yr}-{end_yr}'
        period_nodash = f'{start_yr}{end_yr}'
        for ext in ('xlsx', 'xls'):
            url = (f'{ABS_LIFE_EXP_BASE_URL}/{period}/'
                   f'3302055001DO001_{period_nodash}.{ext}')
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            if not resp.content:
                raise RuntimeError(f'Empty response body from {url}')
            fname = f'life_expectancy_{period_nodash}.{ext}'
            out_path = os.path.join(output_dir, fname)
            _write_bytes_atomically(out_path, resp.content)
            downloaded[fname] = len(resp.content)
            logging.info(
                'Downloaded ABS Life Expectancy workbook %s (%d bytes)',
                fname,
                len(resp.content),
            )
            break

    if not downloaded:
        raise RuntimeError(
            'Failed to download any recent ABS Life Expectancy workbooks (2016-2018+).'
        )
    return downloaded


def _cleanup_stale_files(output_dir: str, expected_files: set[str]) -> None:
    """Removes any files in output_dir that are not in expected_files."""
    if not os.path.isdir(output_dir):
        return
    for fname in os.listdir(output_dir):
        if fname.startswith('.'):
            continue
        fpath = os.path.join(output_dir, fname)
        if os.path.isfile(fpath) and fname not in expected_files:
            logging.info('Removing stale file in output_dir: %s', fpath)
            os.remove(fpath)


def download_all(
    output_dir: str,
    max_workers: int = 5,
) -> dict[str, int]:
    """Downloads all raw ABS datasets concurrently into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    summary: dict[str, int] = {}

    if max_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(max_workers,
                                len(STATIC_DATASETS) + 1)) as executor:
            futures = [
                executor.submit(_download_static_file, fname, url, output_dir)
                for fname, url in STATIC_DATASETS.items()
            ]
            futures.append(
                executor.submit(_download_recent_life_expectancy_workbooks,
                                output_dir))
            for fut in concurrent.futures.as_completed(futures):
                summary.update(fut.result())
    else:
        for fname, url in STATIC_DATASETS.items():
            summary.update(_download_static_file(fname, url, output_dir))
        summary.update(_download_recent_life_expectancy_workbooks(output_dir))

    _cleanup_stale_files(output_dir, set(summary.keys()))

    total_bytes = sum(summary.values())
    logging.info(
        'Successfully downloaded %d raw ABS source files (%d total bytes) in %s',
        len(summary),
        total_bytes,
        output_dir,
    )
    return summary


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    output_dir = (_FLAGS.output_dir if os.path.isabs(_FLAGS.output_dir) else
                  os.path.join(_MODULE_DIR, _FLAGS.output_dir))
    try:
        download_all(
            output_dir=output_dir,
            max_workers=_FLAGS.max_workers,
        )
    except Exception as e:
        logging.fatal('%s', e, exc_info=True)


if __name__ == '__main__':
    app.run(main)

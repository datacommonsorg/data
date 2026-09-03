# Copyright 2026 Google LLC
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
"""Programmatically downloads CDC WONDER NNDSS Annual Summary data via API.

Queries CDC WONDER (dataset D130) for Notifiable Infectious Diseases Annual
Summary data across demographic and geographic breakdowns (age, sex, race,
ethnicity, region, region_state) and formats the output into CSVs ready for
downstream processing with stat_var_processor.py.
"""

import csv
import datetime
import os
import re
import tempfile
import time
import xml.etree.ElementTree as ET

from absl import app
from absl import flags
from absl import logging
import requests

# CDC WONDER Endpoint and Database Constants
CDC_WONDER_ENDPOINT = "https://wonder.cdc.gov/controller/datarequest/D130"
DATASET_CODE = "D130"
MIN_REQUEST_INTERVAL_SECONDS = 16.0  # CDC WONDER requires >= 15s between requests

# Flags configuration
FLAGS = flags.FLAGS

flags.DEFINE_string(
    'verticals',
    'all',
    'Comma-separated list of verticals (age,sex,race,ethnicity,region,region_state) or "all"'
)
flags.DEFINE_string(
    'years',
    'all',
    'Comma-separated list of years (e.g. "2016,2017,2018,2019,2020,2021,2022,2023") or single year'
)
flags.DEFINE_string(
    'output_dir',
    './input_files',
    'Output directory to save downloaded CSV files'
)

# Vertical breakdown configurations
VERTICAL_CONFIGS = {
    'age': {
        'b3': 'D130.V8',
        'table_var': 'D130.V8',
        'filter_var': 'V_D130.V8',
        'header_label': 'Age',
        'header_code': 'Age Code',
    },
    'sex': {
        'b3': 'D130.V4',
        'table_var': 'D130.V4',
        'filter_var': 'V_D130.V4',
        'header_label': 'Sex',
        'header_code': 'Sex Code',
    },
    'race': {
        'b3': 'D130.V5',
        'table_var': 'D130.V5',
        'filter_var': 'V_D130.V5',
        'header_label': 'Race',
        'header_code': 'Race Code',
    },
    'ethnicity': {
        'b3': 'D130.V7',
        'table_var': 'D130.V7',
        'filter_var': 'V_D130.V7',
        'header_label': 'Ethnicity',
        'header_code': 'Ethnicity Code',
    },
    'region': {
        'b3': 'D130.V10',
        'table_var': 'D130.V10',
        'filter_var': 'V_D130.V10',
        'header_label': 'Regions',
        'header_code': 'Regions Code',
    },
    'region_state': {
        'b3': 'D130.V6',
        'table_var': 'D130.V6',
        'filter_var': 'V_D130.V6',
        'header_label': 'Regions/States',
        'header_code': 'Regions/States Code',
    },
}

_last_request_time = 0.0
_session = None


def get_session() -> requests.Session:
    """Returns a shared requests.Session instance for connection pooling."""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session


def _rate_limit_wait():
    """Enforces mandatory delay between consecutive CDC WONDER API requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL_SECONDS:
        wait_time = MIN_REQUEST_INTERVAL_SECONDS - elapsed
        logging.info(f"Rate limiting: waiting {wait_time:.1f}s before next query...")
        time.sleep(wait_time)
    _last_request_time = time.time()


def _normalize_label(label: str) -> str:
    """Normalizes whitespace in labels for consistent dictionary lookup."""
    if not label:
        return ""
    return re.sub(r'\s+', ' ', label.strip())


def build_request_xml(vertical: str, year: str) -> str:
    """Builds the CDC WONDER XML request payload for a given vertical and year."""
    cfg = VERTICAL_CONFIGS[vertical]
    b3 = cfg['b3']
    table_var = cfg['table_var']
    filter_var = cfg['filter_var']

    xml_parameters = f"""<request-parameters>
  <parameter><name>B_1</name><value>D130.V3</value></parameter>
  <parameter><name>B_2</name><value>D130.V1</value></parameter>
  <parameter><name>B_3</name><value>{b3}</value></parameter>
  <parameter><name>O_tables</name><value>{table_var}</value></parameter>
  <parameter><name>M_1</name><value>D130.M1</value></parameter>
  <parameter><name>V_D130.V1</name><value>{year}</value></parameter>
  <parameter><name>V_D130.V3</name><value>*All*</value></parameter>
  <parameter><name>{filter_var}</name><value>*All*</value></parameter>
  <parameter><name>O_javascript</name><value>on</value></parameter>
  <parameter><name>O_show_totals</name><value>true</value></parameter>
  <parameter><name>O_show_zeros</name><value>true</value></parameter>
  <parameter><name>O_precision</name><value>0</value></parameter>
  <parameter><name>O_timeout</name><value>300</value></parameter>
  <parameter><name>O_rate_per</name><value>100000</value></parameter>
  <parameter><name>action-Send</name><value>Send</value></parameter>
</request-parameters>"""
    return xml_parameters


class YearUnavailableError(Exception):
    """Raised when CDC WONDER indicates that the requested year is unavailable."""


def query_cdc_wonder(xml_payload: str, max_retries: int = 3, session: requests.Session = None) -> str:
    """Sends an HTTP POST query to CDC WONDER API with retry handling."""
    if session is None:
        session = get_session()
    data = {
        'request_xml': xml_payload,
        'accept_datause_restrictions': 'true',
    }
    for attempt in range(1, max_retries + 1):
        _rate_limit_wait()
        try:
            logging.info(f"Sending HTTP POST request to {CDC_WONDER_ENDPOINT} (attempt {attempt}/{max_retries})...")
            resp = session.post(CDC_WONDER_ENDPOINT, data=data, timeout=300)
            res = resp.text
            if '<title>Processing Error</title>' in res:
                if 'rate exceeded' in res.lower():
                    logging.warning(f"Rate limit hit on POST {CDC_WONDER_ENDPOINT} (attempt {attempt}/{max_retries}), backing off 25s...")
                    time.sleep(25)
                    continue

                msg_match = re.search(r'<message>(.*?)</message>', res, re.DOTALL | re.IGNORECASE)
                err_msg = msg_match.group(1).strip() if msg_match else res
                if 'd130.v1' in res.lower() or ('year' in err_msg.lower() and ('valid' in err_msg.lower() or 'unavailable' in err_msg.lower())):
                    raise YearUnavailableError(f"Year is unavailable in CDC WONDER: {err_msg}")

                logging.error(f"CDC WONDER Processing Error on POST {CDC_WONDER_ENDPOINT}: {res}")
                raise RuntimeError(f"CDC WONDER processing error: {res}")
            resp.raise_for_status()
            logging.info(f"Received HTTP {resp.status_code} from POST {CDC_WONDER_ENDPOINT}")
            if '<data-table' not in res and '<message>' in res:
                msg_match = re.search(r'<message>(.*?)</message>', res, re.DOTALL | re.IGNORECASE)
                if msg_match and ('dataset or year is currently unavailable' in msg_match.group(1).lower() or ('year' in msg_match.group(1).lower() and 'unavailable' in msg_match.group(1).lower())):
                    raise YearUnavailableError(f"Year is unavailable in CDC WONDER: {msg_match.group(1).strip()}")
            return res
        except requests.RequestException as e:
            logging.warning(f"Network error on POST {CDC_WONDER_ENDPOINT} (attempt {attempt}/{max_retries}): {e}")
            time.sleep(10 * attempt)
    logging.error("Failed to fetch data from CDC WONDER after maximum retries.")
    raise RuntimeError("Failed to fetch data from CDC WONDER after maximum retries.")


def parse_xml_to_csv_rows(xml_response: str, vertical: str) -> list:
    """Parses CDC WONDER XML table response into tabular CSV rows."""
    cfg = VERTICAL_CONFIGS[vertical]
    b3 = cfg['b3']
    root = ET.fromstring(xml_response)

    # 1. Extract variable lookup tables for codes
    label_to_code = {}
    for var in root.findall('.//variable'):
        code = var.attrib.get('code')
        if not code:
            continue
        values = var.findall('value')
        if not values:
            continue
        if code not in label_to_code:
            label_to_code[code] = {}
        for v in values:
            v_code = v.attrib.get('code')
            v_label = v.attrib.get('label')
            if v_code and v_label:
                label_to_code[code][_normalize_label(v_label)] = v_code.strip()

    disease_codes = label_to_code.get('D130.V3', {})
    year_codes = label_to_code.get('D130.V1', {})
    breakdown_codes = label_to_code.get(b3, {})

    table = root.find('.//data-table')
    if table is None:
        messages = [m.text for m in root.findall('.//message') if m.text]
        raise ValueError(f"No data-table found in response: {messages}")

    header = [
        'Notes', 'Disease', 'Disease Code', 'Year', 'Year Code',
        cfg['header_label'], cfg['header_code'], 'Case Count'
    ]
    rows = [header]

    curr_disease = None
    curr_year = None

    for r in table:
        cells = list(r)
        if not cells:
            continue

        c0 = cells[0].attrib
        # Handle total rows
        if 'c' in c0:
            colspan = int(c0.get('c', '1'))
            val = cells[1].attrib.get('dt', '0') if len(cells) > 1 else '0'
            d_code = disease_codes.get(_normalize_label(curr_disease), '')
            y_code = year_codes.get(_normalize_label(curr_year), curr_year or '')
            if colspan == 1:
                # Subtotal for year
                rows.append(['Total', curr_disease, d_code, curr_year, y_code, '', '', val])
            elif colspan == 2:
                # Subtotal for disease
                rows.append(['Total', curr_disease, d_code, '', '', '', '', val])
            continue

        # Handle data rows
        if len(cells) == 4:
            curr_disease = cells[0].attrib.get('l', '')
            curr_year = cells[1].attrib.get('l', '')
            b_label = cells[2].attrib.get('l', '')
            val = cells[3].attrib.get('v', '0')
        elif len(cells) == 2:
            b_label = cells[0].attrib.get('l', '')
            val = cells[1].attrib.get('v', '0')
        else:
            continue

        d_code = disease_codes.get(_normalize_label(curr_disease), '')
        y_code = year_codes.get(_normalize_label(curr_year), curr_year)
        b_code = breakdown_codes.get(_normalize_label(b_label), '')
        rows.append(['', curr_disease, d_code, curr_year, y_code, b_label, b_code, val])

    return rows


def download_vertical_year(vertical: str, year: str, output_dir: str, session: requests.Session = None) -> bool:
    """Downloads and writes CSV for a specific vertical breakdown and year.

    Returns:
        True if download succeeded and CSV was written, False if data was unavailable.
    """
    logging.info(f"Downloading vertical '{vertical}' for year {year}...")
    try:
        xml_payload = build_request_xml(vertical, year)
        xml_response = query_cdc_wonder(xml_payload, session=session)
    except YearUnavailableError as e:
        logging.warning(
            f"Data unavailable for vertical '{vertical}' and year {year}: {e}. "
            f"Skipping download."
        )
        return False

    rows = parse_xml_to_csv_rows(xml_response, vertical)

    target_dir = os.path.join(output_dir, vertical)
    os.makedirs(target_dir, exist_ok=True)
    target_csv = os.path.join(target_dir, f"NNDSS_Annual_Summary_Data_{year}.csv")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', dir=target_dir, delete=False, newline='', encoding='utf-8') as f:
            temp_path = f.name
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for r in rows:
                # Match CDC WONDER quote format: quote non-empty string fields
                writer.writerow(r)
        os.replace(temp_path, target_csv)
        temp_path = None
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    logging.info(f"Saved {len(rows)-1} records to {target_csv}")
    return True


def download_all(verticals: list, years: list, output_dir: str, session: requests.Session = None):
    """Downloads all requested verticals and years sequentially."""
    if session is None:
        session = get_session()
    total_tasks = len(verticals) * len(years)
    idx = 1
    successful_downloads = 0
    unavailable_downloads = 0
    unavailable_years = set()
    for v in verticals:
        for y in years:
            str_y = str(y)
            logging.info(f"[{idx}/{total_tasks}] Processing {v} ({str_y})...")
            if str_y in unavailable_years:
                logging.info(
                    f"Skipping {v} ({str_y}) because year {str_y} was previously determined to be unavailable."
                )
                unavailable_downloads += 1
                idx += 1
                continue
            if download_vertical_year(v, str_y, output_dir, session=session):
                successful_downloads += 1
            else:
                unavailable_years.add(str_y)
                unavailable_downloads += 1
            idx += 1
    logging.info(
        f"All downloads finished: {successful_downloads} successful, "
        f"{unavailable_downloads} unavailable."
    )
    if successful_downloads == 0:
        logging.fatal("Zero downloads succeeded from CDC WONDER API.")


def main(argv):
    del argv  # Unused.

    if FLAGS.verticals.lower() == 'all':
        selected_verticals = list(VERTICAL_CONFIGS.keys())
    else:
        selected_verticals = [v.strip() for v in FLAGS.verticals.split(',') if v.strip()]

    if FLAGS.years.lower() == 'all':
        # Inclusive of published years up to datetime.date.today().year - 1
        selected_years = [str(y) for y in range(2016, datetime.date.today().year)]
    else:
        selected_years = [y.strip() for y in FLAGS.years.split(',') if y.strip()]

    logging.info(f"Starting download for verticals={selected_verticals}, years={selected_years}")
    logging.info(f"Output directory: {FLAGS.output_dir}")
    download_all(selected_verticals, selected_years, FLAGS.output_dir)


if __name__ == '__main__':
    app.run(main)

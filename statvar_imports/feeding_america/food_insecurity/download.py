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
"""Downloads Feeding America Food Insecurity data (2022+) and merges with 2019-2021 baseline."""

import argparse
import csv
import html
import http.cookiejar
import json
import logging
import os
import re
import sys
import tempfile
import time

import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
_UTIL_DIR = os.path.join(_REPO_ROOT, 'util')
if _UTIL_DIR not in sys.path:
    sys.path.append(_UTIL_DIR)

import file_util  # pylint: disable=wrong-import-position

MAP_HOME_URL = 'https://map.feedingamerica.org/'
MAPDATA_URL = 'https://map.feedingamerica.org/mapdata'
BASELINE_GCS_PATH = (
    'gs://unresolved_mcf/feeding_america/food_insecurity/'
    'input_files/FeedingAmerica_FoodInsecurity_baseline_2019_2021.csv')
OUTPUT_INPUT_CSV = os.path.join(
    _SCRIPT_DIR,
    'input_files',
    'feedingamerica_foodinsecurity_input.csv',
)
DEFAULT_YEARS = ['2022', '2023', '2024']
MIN_API_YEAR = 2022
MAX_RETRIES = 5
REQUEST_TIMEOUT_SECS = 60
HOME_TIMEOUT_SECS = 30
TRANSIENT_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
WEEKS_IN_7_MONTHS = 52.0 * 7.0 / 12.0

MAPTYPES = ('county', 'district')
DEMOGRAPHIC_TYPES = ('overall', 'child', 'black', 'hispanic', 'white')

FIELDNAMES = [
    'dcid',
    'observationDate',
    'Count_Person_FoodInsecure_AsAFractionOf_Count_Person',
    'Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_Black_AsAFractionOf_Count_Person_Black',
    'Count_Person_HispanicOrLatino_FoodInSecure_AsAFractionOf_Count_Person_HispanicOrLatino',
    'Count_Person_NotHispanicOrLatino_FoodInSecure_White_AsAFractionOf_Count_Person_NotHispanicOrLatino_White',
    'Count_Person_FoodInsecure_HouseholdIncomeAtOrBelowStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThresholdAndBelowOrEqualStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure',
    'Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure',
    'Count_Child_FoodInsecure_AsAFractionOf_Count_Child',
    'Count_Child_FoodInsecure',
    'Count_Child_FoodInsecure_HouseholdIncomeBelow185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure',
    'Count_Child_FoodInsecure_HouseholdIncomeAbove185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure',
    'Mean_CostPerMeal_Person_FoodInSecure',
    'Weekly_WeightedFoodSpendAmount_Person_FoodInSecure',
    'Annual_WeightedBudgetShortfall_Food',
]
STATVAR_FIELDS = FIELDNAMES[2:]


def build_session():
    """Creates a stateless requests.Session for Feeding America endpoints.

    Disables cookie storage because sending Laravel's session/XSRF cookies from
    the homepage back to /mapdata triggers HTTP 500 responses from the server.
    """
    session = requests.Session()
    session.cookies.set_policy(
        http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (DataCommons Import)',
    })
    return session


def fetch_json(url, params=None, session=None, max_retries=MAX_RETRIES):
    """Fetches JSON from url with exponential backoff on transient HTTP/network errors."""
    http = session or build_session()
    headers = {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
    }
    last_err = None
    for attempt in range(max_retries):
        logging.info('GET %s params=%s (attempt %d/%d)', url, params,
                     attempt + 1, max_retries)
        try:
            resp = http.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECS,
            )
            if resp.status_code in TRANSIENT_STATUS_CODES:
                raise requests.HTTPError(
                    f'Transient HTTP {resp.status_code} for {resp.url}',
                    response=resp,
                )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError(
                    f'Expected JSON object from {resp.url}, got {type(data).__name__}'
                )
            return data
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status is not None and status not in TRANSIENT_STATUS_CODES:
                raise RuntimeError(
                    f'Permanent HTTP {status} fetching {url} params={params}: {e}'
                ) from e
            last_err = e
        except (requests.RequestException, ValueError) as e:
            last_err = e

        if attempt + 1 < max_retries:
            wait_secs = 2**attempt
            logging.warning(
                'Request to %s params=%s failed (attempt %d/%d: %s); retrying in %ds',
                url,
                params,
                attempt + 1,
                max_retries,
                last_err,
                wait_secs,
            )
            time.sleep(wait_secs)

    raise RuntimeError(
        f'Failed to fetch {url} params={params} after {max_retries} attempts: {last_err}'
    ) from last_err


def discover_years(session=None, max_retries=3):
    """Discovers available years >= MIN_API_YEAR from the Inertia app payload."""
    years = set(DEFAULT_YEARS)
    http = session or build_session()
    last_err = None
    for attempt in range(max_retries):
        try:
            logging.info(
                'GET %s (discovering available years, attempt %d/%d)',
                MAP_HOME_URL,
                attempt + 1,
                max_retries,
            )
            resp = http.get(MAP_HOME_URL, timeout=HOME_TIMEOUT_SECS)
            if resp.status_code in TRANSIENT_STATUS_CODES:
                raise requests.HTTPError(
                    f'Transient HTTP {resp.status_code} for {resp.url}',
                    response=resp,
                )
            resp.raise_for_status()
            page = resp.text
            match = re.search(
                r'data-page="app"\s+type="application/json">(.*?)</script>',
                page,
                re.S,
            )
            if match:
                payload = json.loads(match.group(1))
            else:
                attr_match = re.search(r'data-page="([^"]+)"', page)
                if not attr_match:
                    logging.warning(
                        'No Inertia data-page payload found on %s; falling back to defaults',
                        MAP_HOME_URL,
                    )
                    return sorted(years)
                payload = json.loads(html.unescape(attr_match.group(1)))
            if not isinstance(payload, dict):
                raise ValueError(
                    f'Expected JSON object for Inertia data-page, got {type(payload).__name__}'
                )
            props = payload.get('props')
            filters = props.get('filters') if isinstance(props, dict) else None
            raw_years = (filters.get('years')
                         if isinstance(filters, dict) else None)
            if not isinstance(raw_years, list):
                logging.warning(
                    'Missing or invalid props.filters.years in Inertia payload on %s; falling back to defaults',
                    MAP_HOME_URL,
                )
                return sorted(years)
            discovered = set()
            for item in raw_years:
                if not isinstance(item, dict):
                    continue
                yr = str(item.get('year', '')).strip()
                if yr.isdigit() and int(yr) >= MIN_API_YEAR:
                    discovered.add(yr)
            if not discovered:
                logging.warning(
                    'No years >= %d found in Inertia payload on %s; falling back to defaults',
                    MIN_API_YEAR,
                    MAP_HOME_URL,
                )
            years.update(discovered)
            return sorted(years)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status is not None and status not in TRANSIENT_STATUS_CODES:
                logging.warning(
                    'Permanent HTTP %s during year discovery; falling back to defaults (%s)',
                    status,
                    e,
                )
                return sorted(years)
            last_err = e
        except (ValueError, KeyError, TypeError) as e:
            logging.warning(
                'Year discovery payload parse failed; falling back to defaults (%s)',
                e,
            )
            return sorted(years)
        except requests.RequestException as e:
            last_err = e

        if attempt + 1 < max_retries:
            wait_secs = 2**attempt
            logging.warning(
                'Year discovery failed (attempt %d/%d: %s); retrying in %ds',
                attempt + 1,
                max_retries,
                last_err,
                wait_secs,
            )
            time.sleep(wait_secs)
    logging.warning('Dynamic year discovery fallback to defaults (%s)',
                    last_err)
    return sorted(years)


def resolve_bands(low_band, mid_band, high_band):
    """Restores 0.0 when complementary band(s) sum to 100% (1.0) and API serialized 0% as null."""
    if high_band is None and low_band is not None:
        if round(float(low_band) + float(mid_band or 0.0), 4) >= 0.999:
            high_band = 0.0
    if low_band is None and high_band is not None:
        if round(float(high_band) + float(mid_band or 0.0), 4) >= 0.999:
            low_band = 0.0
    return low_band, mid_band, high_band


def to_pct(val):
    """Converts a 0-1 proportion to a 0-100 percentage rounded to 4 decimals."""
    return '' if val is None else round(float(val) * 100.0, 4)


def format_dcid(level, fips):
    """Formats a Feeding America FIPS code into a canonical Data Commons geoId DCID."""
    if fips is None or not str(fips).strip().isdigit():
        return None
    code = int(str(fips).strip())
    if level == 'state':
        return f'dcid:geoId/{code:02d}'
    if level == 'county':
        return f'dcid:geoId/{code:05d}'
    if level == 'district':
        return f'dcid:geoId/{code:04d}'
    return None


def load_baseline(baseline_path):
    """Loads the immutable 2019-2021 historical baseline CSV from GCS or local disk."""
    matching = file_util.file_get_matching(baseline_path)
    if not matching:
        raise FileNotFoundError(
            f'Missing historical baseline CSV: {baseline_path}')
    rows_by_key = {}
    with file_util.FileIO(matching[0], 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            dcid = row['dcid'].strip()
            if not dcid.startswith('dcid:'):
                dcid = f'dcid:{dcid}'
            year = row['observationDate'].strip()
            normalized = {k: row.get(k, '') for k in FIELDNAMES}
            normalized['dcid'] = dcid
            normalized['observationDate'] = year
            rows_by_key[(dcid, year)] = normalized
    if not rows_by_key:
        raise ValueError(f'Historical baseline CSV is empty: {baseline_path}')
    logging.info('Loaded %d historical baseline rows from %s', len(rows_by_key),
                 matching[0])
    return rows_by_key


def build_row_from_api(level, dcid, year, ov, ch, bl, hi, wh):
    """Builds one wide CSV row for (dcid, year) from the 5 demographic API records."""
    ov_pop = ov.get('population')
    ch_pop = ch.get('population')
    ov_low, ov_mid, ov_high = resolve_bands(
        ov.get('low_band'),
        ov.get('mid_band'),
        ov.get('high_band'),
    )
    ch_low, _, ch_high = resolve_bands(
        ch.get('low_band'),
        None,
        ch.get('high_band'),
    )

    if ov_mid is not None:
        btwn_pct = to_pct(ov_mid)
        above_high_pct = to_pct(ov_high)
        above_low_pct = ('' if ov_low is None else round(
            (1.0 - float(ov_low)) * 100.0, 4))
    else:
        btwn_pct = ''
        above_high_pct = ''
        above_low_pct = to_pct(ov_high)

    cost_meal = ''
    weekly_spend = ''
    annual_shortfall = ''
    if level in ('state', 'county'):
        if ov.get('cost_per_meal') is not None:
            cost_meal = round(float(ov['cost_per_meal']), 2)
        if ov.get('money_needed') is not None:
            annual_shortfall = ov['money_needed']
        if ov.get('money_needed') is not None and ov_pop:
            weekly_spend = round(
                float(ov['money_needed']) / (float(ov_pop) * WEEKS_IN_7_MONTHS),
                2,
            )

    row = {
        'dcid':
            dcid,
        'observationDate':
            year,
        'Count_Person_FoodInsecure_AsAFractionOf_Count_Person':
            to_pct(ov.get('insecurity')),
        'Count_Person_FoodInsecure':
            '' if ov_pop is None else ov_pop,
        'Count_Person_FoodInsecure_Black_AsAFractionOf_Count_Person_Black':
            to_pct(bl.get('insecurity')),
        'Count_Person_HispanicOrLatino_FoodInSecure_AsAFractionOf_Count_Person_HispanicOrLatino':
            to_pct(hi.get('insecurity')),
        'Count_Person_NotHispanicOrLatino_FoodInSecure_White_AsAFractionOf_Count_Person_NotHispanicOrLatino_White':
            to_pct(wh.get('insecurity')),
        'Count_Person_FoodInsecure_HouseholdIncomeAtOrBelowStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure':
            to_pct(ov_low),
        'Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThresholdAndBelowOrEqualStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure':
            btwn_pct,
        'Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure':
            above_high_pct,
        'Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure':
            above_low_pct,
        'Count_Child_FoodInsecure_AsAFractionOf_Count_Child':
            to_pct(ch.get('insecurity')),
        'Count_Child_FoodInsecure':
            '' if ch_pop is None else ch_pop,
        'Count_Child_FoodInsecure_HouseholdIncomeBelow185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure':
            to_pct(ch_low),
        'Count_Child_FoodInsecure_HouseholdIncomeAbove185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure':
            to_pct(ch_high),
        'Mean_CostPerMeal_Person_FoodInSecure':
            cost_meal,
        'Weekly_WeightedFoodSpendAmount_Person_FoodInSecure':
            weekly_spend,
        'Annual_WeightedBudgetShortfall_Food':
            annual_shortfall,
    }
    if not any(row[col] != '' for col in STATVAR_FIELDS):
        return None
    return row


def write_csv_atomic(output_path, rows_by_key):
    """Atomically writes sorted merged rows to output_path."""
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
                mode='w',
                newline='',
                encoding='utf-8',
                dir=out_dir,
                prefix='.tmp_feedingamerica_',
                suffix='.csv',
                delete=False,
        ) as tmp_fp:
            tmp_path = tmp_fp.name
            writer = csv.DictWriter(tmp_fp, fieldnames=FIELDNAMES)
            writer.writeheader()
            for _, row in sorted(rows_by_key.items()):
                writer.writerow(row)
        os.replace(tmp_path, output_path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def parse_args(argv=None):
    """Parses optional CLI arguments for baseline and output CSV paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--baseline_path',
        default=BASELINE_GCS_PATH,
        help='GCS URI or local path to the 2019-2021 historical baseline CSV.',
    )
    parser.add_argument(
        '--output_csv',
        default=OUTPUT_INPUT_CSV,
        help='Destination path for the merged wide input CSV.',
    )
    return parser.parse_args(argv if argv is not None else [])


def main(argv=None):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )
    args = parse_args(argv)
    rows_by_key = load_baseline(args.baseline_path)

    with build_session() as session:
        years = discover_years(session=session)
        logging.info('Fetching live API data for years: %s', years)

        for year in years:
            payloads = {}
            for mtype in MAPTYPES:
                for dtype in DEMOGRAPHIC_TYPES:
                    payloads[(mtype, dtype)] = fetch_json(
                        MAPDATA_URL,
                        params={
                            'maptype': mtype,
                            'year': year,
                            'type': dtype,
                        },
                        session=session,
                    )

            for level, mtype in (
                ('state', 'county'),
                ('county', 'county'),
                ('district', 'district'),
            ):
                if not payloads[(mtype, 'overall')].get(level):
                    raise RuntimeError(
                        f'Empty "{level}" records for year={year} maptype={mtype} type=overall'
                    )
                by_dtype = {}
                for dtype in DEMOGRAPHIC_TYPES:
                    by_dtype[dtype] = {
                        str(item.get('fips')).strip(): item
                        for item in payloads[(mtype, dtype)].get(level, [])
                        if item.get('fips') is not None and
                        str(item.get('fips')).strip()
                    }
                all_fips = sorted(
                    set().union(*(d.keys() for d in by_dtype.values())),
                    key=lambda x: (0, int(x)) if x.isdigit() else (1, x),
                )
                added_for_level = 0
                for fips in all_fips:
                    dcid = format_dcid(level, fips)
                    if not dcid:
                        continue
                    row = build_row_from_api(
                        level=level,
                        dcid=dcid,
                        year=year,
                        ov=by_dtype['overall'].get(fips, {}),
                        ch=by_dtype['child'].get(fips, {}),
                        bl=by_dtype['black'].get(fips, {}),
                        hi=by_dtype['hispanic'].get(fips, {}),
                        wh=by_dtype['white'].get(fips, {}),
                    )
                    if row is not None:
                        rows_by_key[(dcid, year)] = row
                        added_for_level += 1
                logging.info('Year %s level=%s: merged %d rows', year, level,
                             added_for_level)

    write_csv_atomic(args.output_csv, rows_by_key)
    logging.info('Wrote %d rows to %s', len(rows_by_key), args.output_csv)


if __name__ == '__main__':
    main(sys.argv[1:])

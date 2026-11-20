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
"""Downloads and normalizes OECD Air and GHG emissions datasets via SDMX."""

import csv
from dataclasses import dataclass
import logging as py_logging
import math
import os
from pathlib import Path
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
import sdmx

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_FLAGS = flags.FLAGS

SDMX_ENDPOINT = 'https://sdmx.oecd.org/public/rest/'
SDMX_AGENCY_ID = 'OECD.ENV.EPI'
DEFAULT_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) DataCommons/1.0'
TRANSIENT_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504})

HISTORICAL_GCS_BUCKET = 'unresolved_mcf'
HISTORICAL_GCS_BLOB = ('oecd/oecd_air_and_ghg_emissions/'
                       'AirandGHGEmissions-latest - processed_csv.csv')
HISTORICAL_RAW_FILENAME = 'historical_baseline_2024.csv'
STAGING_CSV_FILENAME = 'oecd_air_ghg_emissions_input.csv'

OUTPUT_COLUMNS = [
    'LOCATION',
    'SUBJECT',
    'MEASURE',
    'FREQUENCY',
    'TIME',
    'Value',
]


@dataclass(frozen=True)
class SdmxFeedSpec:
    """Configuration for a single OECD SDMX dataflow query."""

    name: str
    dataflow_id: str
    raw_filename: str
    key: dict[str, str]
    params: dict[str, str]
    expected_series: frozenset[tuple[str, str]]


SDMX_FEEDS: tuple[SdmxFeedSpec, ...] = (
    SdmxFeedSpec(
        name='ghg',
        dataflow_id='DSD_AIR_GHG@DF_AIR_GHG',
        raw_filename='oecd_air_ghg_raw.xml',
        key={
            'FREQ': 'A',
            'POLLUTANT': 'GHG',
            'MEASURE': '_T',
            'UNIT_MEASURE': 'T_CO2E+KG_CO2E_PS',
        },
        params={},
        expected_series=frozenset({
            ('GHG', 'THND_TONNECO2'),
            ('GHG', 'TONNE_CAP'),
        }),
    ),
    SdmxFeedSpec(
        name='air_emissions',
        dataflow_id='DSD_AIR_EMISSIONS@DF_AIR_EMISSIONS',
        raw_filename='oecd_air_emissions_raw.xml',
        key={
            'FREQ': 'A',
            'POLLUTANT': 'CO+NOX+SOX+NMVOC',
            'MEASURE': 'T_EM_MM',
            'UNIT_MEASURE': 'T+KG_PS',
        },
        params={},
        expected_series=frozenset({
            ('CO', 'THND_TONNE'),
            ('CO', 'KG_CAP'),
            ('NOX', 'THND_TONNE'),
            ('NOX', 'KG_CAP'),
            ('SOX', 'THND_TONNE'),
            ('SOX', 'KG_CAP'),
            ('VOC', 'THND_TONNE'),
            ('VOC', 'KG_CAP'),
        }),
    ),
    SdmxFeedSpec(
        name='green_growth_co2',
        dataflow_id='DSD_GG@DF_GREEN_GROWTH',
        raw_filename='oecd_green_growth_co2_raw.xml',
        key={
            'FREQ': 'A',
            'MEASURE': 'CO2_PBEM+CO2_PBEMCAP+CO2_PBPROD',
            'UNIT_MEASURE': 'T+T_CO2E_PS+USD_CO2',
            'ACTIVITY': '_T',
        },
        params={},
        expected_series=frozenset({
            ('CO2', 'MLN_TONNE'),
            ('CO2', 'TONNE_CAP'),
            ('CO2_PBPROD', 'USD_CO2'),
        }),
    ),
)

POLLUTANT_TO_SUBJECT: dict[str, str] = {
    'GHG': 'GHG',
    'CO': 'CO',
    'NOX': 'NOX',
    'SOX': 'SOX',
    'NMVOC': 'VOC',
}

# Maps the 12 existing physical-mass Emissions StatVars to (SUBJECT, MEASURE,
# divisor) for pre-SDMX historical backfill. CO2_PBPROD (USD_CO2) is ingested
# solely from live DSD_GG@DF_GREEN_GROWTH under a dedicated productivity StatVar
# so constant-2020 PPP USD observations are not mixed with legacy 2015-base rows.
HISTORICAL_SV_MAP: dict[str, tuple[str, str, float]] = {
    'dcid:Annual_Amount_Emissions_CarbonDioxide': (
        'CO2',
        'MLN_TONNE',
        1_000_000.0,
    ),
    'dcid:Annual_Amount_Emissions_CarbonDioxide_AsAFractionOf_Count_Person': (
        'CO2',
        'TONNE_CAP',
        1.0,
    ),
    'dcid:Annual_Emissions_GreenhouseGas': ('GHG', 'THND_TONNECO2', 1_000.0),
    'dcid:Annual_Amount_Emissions_GreenhouseGas_AsAFractionOf_Count_Person': (
        'GHG',
        'TONNE_CAP',
        1.0,
    ),
    'dcid:Annual_Amount_Emissions_CarbonMonoxide': (
        'CO',
        'THND_TONNE',
        1_000.0,
    ),
    'dcid:Annual_Amount_Emissions_CarbonMonoxide_AsAFractionOf_Count_Person': (
        'CO',
        'KG_CAP',
        1.0,
    ),
    'dcid:Annual_Amount_Emissions_OxidesOfNitrogen': (
        'NOX',
        'THND_TONNE',
        1_000.0,
    ),
    'dcid:Annual_Amount_Emissions_OxidesOfNitrogen_AsAFractionOf_Count_Person':
        (
            'NOX',
            'KG_CAP',
            1.0,
        ),
    'dcid:Annual_Amount_Emissions_OxidesOfSulfur': (
        'SOX',
        'THND_TONNE',
        1_000.0,
    ),
    'dcid:Annual_Amount_Emissions_OxidesOfSulfur_AsAFractionOf_Count_Person': (
        'SOX',
        'KG_CAP',
        1.0,
    ),
    'dcid:Annual_Amount_Emissions_VolatileOrganicCompound': (
        'VOC',
        'THND_TONNE',
        1_000.0,
    ),
    'dcid:Annual_Amount_Emissions_VolatileOrganicCompound_AsAFractionOf_Count_Person':
        (
            'VOC',
            'KG_CAP',
            1.0,
        ),
}


class _TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter enforcing a default socket timeout on all requests."""

    def __init__(self, timeout: int = 120, *args: Any, **kwargs: Any) -> None:
        self._timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request: requests.PreparedRequest, **kwargs: Any) -> Any:
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self._timeout
        return super().send(request, **kwargs)


def _define_flags(flag_values: flags.FlagValues = _FLAGS) -> None:
    """Defines command-line flags when invoked as an executable script."""
    flags.DEFINE_string(
        'output_dir',
        os.path.join(_MODULE_DIR, 'input_files'),
        'Directory path to write the normalized staging CSV.',
        flag_values=flag_values,
    )
    flags.DEFINE_string(
        'raw_dir',
        os.path.join(_MODULE_DIR, 'raw_files'),
        'Directory path to archive raw SDMX and GCS baseline files.',
        flag_values=flag_values,
    )
    flags.DEFINE_string(
        'places_resolved_csv',
        os.path.join(_MODULE_DIR, 'oecd_air_ghg_emissions_places_resolved.csv'),
        'Path to the resolved places CSV mapping OECD location codes to DCIDs.',
        flag_values=flag_values,
    )
    flags.DEFINE_string(
        'gcs_bucket',
        HISTORICAL_GCS_BUCKET,
        'GCS bucket hosting the historical 2024 baseline CSV.',
        flag_values=flag_values,
    )
    flags.DEFINE_string(
        'gcs_blob',
        HISTORICAL_GCS_BLOB,
        'GCS blob path to the historical 2024 baseline CSV.',
        flag_values=flag_values,
    )


def load_resolved_places(places_csv_path: str) -> dict[str, str]:
    """Loads valid OECD place codes to Data Commons DCIDs from CSV."""
    path = Path(places_csv_path)
    if not path.is_file():
        raise FileNotFoundError(
            f'Resolved places CSV not found at {places_csv_path}')
    places: dict[str, str] = {}
    with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if (not reader.fieldnames or 'place_name' not in reader.fieldnames or
                'dcid' not in reader.fieldnames):
            raise ValueError(
                f'Invalid header in {places_csv_path}: expected place_name,dcid'
            )
        for row in reader:
            code = (row.get('place_name') or '').strip()
            dcid = (row.get('dcid') or '').strip()
            if code and dcid:
                places[code] = dcid
    if not places:
        raise ValueError(f'No valid place mappings found in {places_csv_path}')
    return places


def _create_sdmx_client(
    endpoint: str = SDMX_ENDPOINT,
    agency_id: str = SDMX_AGENCY_ID,
    timeout: int = 120,
) -> sdmx.Client:
    """Creates a configured sdmx.Client with bounded timeouts and headers."""
    py_logging.getLogger('sdmx').setLevel(py_logging.WARNING)
    sdmx.add_source(
        {
            'id': agency_id,
            'url': endpoint,
            'name': f'OECD SDMX ({agency_id})',
        },
        override=True,
    )
    client = sdmx.Client(agency_id)
    client.session.headers.update({
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept-Encoding': 'gzip, deflate',
    })
    adapter = _TimeoutHTTPAdapter(timeout=timeout)
    client.session.mount('https://', adapter)
    client.session.mount('http://', adapter)
    return client


def _validate_sdmx_xml_file(file_path: Path, dataflow_id: str) -> None:
    """Verifies that a downloaded SDMX file is non-empty XML."""
    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise RuntimeError(
            f'SDMX download produced an empty raw file for {dataflow_id} at '
            f'{file_path}')
    with open(file_path, 'rb') as f:
        head = f.read(256).lstrip()
    if not head.startswith((b'<?xml', b'<message:', b'<GenericData')):
        raise RuntimeError(
            f'Invalid SDMX-ML XML payload for {dataflow_id}: {head[:100]!r}')


def fetch_sdmx_dataframe(
    client: sdmx.Client,
    spec: SdmxFeedSpec,
    raw_dir: str,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> pd.DataFrame:
    """Downloads an SDMX dataflow, archives the raw payload, and returns a DataFrame."""
    os.makedirs(raw_dir, exist_ok=True)
    raw_dest = Path(raw_dir) / spec.raw_filename
    temp_raw = Path(f'{raw_dest}.tmp')
    target_url = f'{SDMX_ENDPOINT.rstrip("/")}/data/{spec.dataflow_id}'

    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(
                'Outbound SDMX request [attempt %d/%d]: method=GET '
                'url=%s key=%s params=%s body=None',
                attempt,
                max_retries,
                target_url,
                spec.key,
                spec.params,
            )
            with open(temp_raw, mode='w+b') as raw_fp:
                msg = client.data(
                    spec.dataflow_id,
                    key=spec.key,
                    params=spec.params,
                    tofile=raw_fp,
                )
                raw_fp.flush()
            _validate_sdmx_xml_file(temp_raw, spec.dataflow_id)
            parsed = sdmx.to_pandas(msg, attributes='osgd')
            if isinstance(parsed, pd.Series):
                df = parsed.reset_index(name='value')
            elif isinstance(parsed, pd.DataFrame):
                df = parsed.reset_index()
            else:
                raise ValueError(
                    f'Unexpected sdmx.to_pandas output type '
                    f'{type(parsed).__name__} for {spec.dataflow_id}')
            if df.empty:
                raise ValueError(
                    f'Parsed SDMX DataFrame is empty for {spec.dataflow_id}')
            os.replace(temp_raw, raw_dest)
            response_url = getattr(getattr(msg, 'response', None), 'url', '')
            logging.info(
                'Received SDMX response for %s from %s (%d bytes archived to %s)',
                spec.dataflow_id,
                response_url or target_url,
                raw_dest.stat().st_size,
                raw_dest,
            )
            return df
        except requests.exceptions.HTTPError as err:
            last_err = err
            if temp_raw.exists():
                temp_raw.unlink()
            status_code = (err.response.status_code
                           if err.response is not None else None)
            if (status_code is not None and
                    status_code not in TRANSIENT_HTTP_STATUSES):
                raise RuntimeError(
                    f'Permanent HTTP {status_code} error fetching SDMX '
                    f'{spec.dataflow_id} (url={target_url}, key={spec.key}): '
                    f'{err}') from err
            logging.warning(
                'Transient HTTP error (%s) fetching %s (attempt %d/%d): %s',
                status_code,
                spec.dataflow_id,
                attempt,
                max_retries,
                err,
            )
        except (requests.exceptions.RequestException, OSError) as err:
            last_err = err
            if temp_raw.exists():
                temp_raw.unlink()
            logging.warning(
                'Network/IO error fetching %s (attempt %d/%d): %s',
                spec.dataflow_id,
                attempt,
                max_retries,
                err,
            )
        except Exception:
            if temp_raw.exists():
                temp_raw.unlink()
            raise

        if attempt < max_retries:
            sleep_secs = retry_delay * (2**(attempt - 1))
            time.sleep(sleep_secs)

    raise RuntimeError(
        f'Failed to download SDMX dataflow {spec.dataflow_id} after '
        f'{max_retries} attempts: {last_err}') from last_err


def _parse_unit_mult(raw_mult: Any) -> int:
    """Parses SDMX UNIT_MULT attribute into an integer power-of-10 exponent."""
    if raw_mult is None or isinstance(raw_mult, bool):
        return 0
    if isinstance(raw_mult, float) and math.isnan(raw_mult):
        return 0
    text = str(raw_mult).strip()
    if not text or text.lower() == 'nan':
        return 0
    return int(float(text))


def _parse_float(raw_val: Any) -> float | None:
    """Parses a numeric observation value, returning None for missing/NaN."""
    if raw_val is None or isinstance(raw_val, bool):
        return None
    if isinstance(raw_val, (int, float)):
        if math.isnan(raw_val) or math.isinf(raw_val):
            return None
        return float(raw_val)
    text = str(raw_val).strip()
    if not text or text.lower() in ('nan', 'na', '..', '-'):
        return None
    val = float(text)
    if math.isnan(val) or math.isinf(val):
        return None
    return val


def _canonicalize_location(code: str) -> str:
    """Normalizes World codes ('WLD' -> 'W') to prevent duplicate Earth rows."""
    cleaned = code.strip().upper()
    if cleaned == 'WLD':
        return 'W'
    return cleaned


def _format_number(value: float) -> str:
    """Formats floats cleanly without scientific notation or trailing zeros."""
    formatted = f'{value:.8f}'.rstrip('0').rstrip('.')
    return '0' if formatted in ('', '-0') else formatted


def normalize_sdmx_feed(
    feed_name: str,
    df: pd.DataFrame,
    valid_places: dict[str, str],
    expected_series: frozenset[tuple[str, str]] | None = None,
) -> dict[tuple[str, str, str, str], str]:
    """Transforms an SDMX DataFrame into keyed (LOCATION, SUBJECT, MEASURE, TIME) -> Value."""
    records: dict[tuple[str, str, str, str], str] = {}
    records_list = df.to_dict(orient='records')

    for row in records_list:
        raw_loc = str(row.get('REF_AREA', '')).strip()
        loc = _canonicalize_location(raw_loc)
        if loc not in valid_places:
            continue

        freq = str(row.get('FREQ', 'A')).strip().upper()
        if freq != 'A':
            continue

        year = str(row.get('TIME_PERIOD', '')).strip()
        if not year.isdigit() or len(year) != 4:
            continue

        obs_val = _parse_float(row.get('value'))
        if obs_val is None:
            continue

        unit_mult = _parse_unit_mult(row.get('UNIT_MULT'))
        unit_measure = str(row.get('UNIT_MEASURE', '')).strip().upper()
        measure_code = str(row.get('MEASURE', '')).strip().upper()

        subject = ''
        target_measure = ''
        scaled_val: float | None = None

        if feed_name == 'ghg':
            pollutant = str(row.get('POLLUTANT', '')).strip().upper()
            if pollutant != 'GHG' or measure_code != '_T':
                continue
            subject = 'GHG'
            if unit_measure == 'T_CO2E':
                target_measure = 'THND_TONNECO2'
                scaled_val = obs_val * (10.0**(unit_mult - 3))
            elif unit_measure == 'KG_CO2E_PS':
                # 10^3 kg CO2e/person == 1 MetricTon CO2e/person (TONNE_CAP).
                target_measure = 'TONNE_CAP'
                scaled_val = obs_val * (10.0**(unit_mult - 3))
        elif feed_name == 'air_emissions':
            pollutant = str(row.get('POLLUTANT', '')).strip().upper()
            if pollutant not in POLLUTANT_TO_SUBJECT or measure_code != 'T_EM_MM':
                continue
            subject = POLLUTANT_TO_SUBJECT[pollutant]
            if unit_measure == 'T':
                target_measure = 'THND_TONNE'
                scaled_val = obs_val * (10.0**(unit_mult - 3))
            elif unit_measure == 'KG_PS':
                target_measure = 'KG_CAP'
                scaled_val = obs_val * (10.0**unit_mult)
        elif feed_name == 'green_growth_co2':
            activity = str(row.get('ACTIVITY', '_T')).strip().upper()
            if activity != '_T':
                continue
            if measure_code == 'CO2_PBEM' and unit_measure == 'T':
                subject = 'CO2'
                target_measure = 'MLN_TONNE'
                scaled_val = obs_val * (10.0**(unit_mult - 6))
            elif measure_code == 'CO2_PBEMCAP' and unit_measure == 'T_CO2E_PS':
                subject = 'CO2'
                target_measure = 'TONNE_CAP'
                scaled_val = obs_val * (10.0**unit_mult)
            elif measure_code == 'CO2_PBPROD' and unit_measure == 'USD_CO2':
                subject = 'CO2_PBPROD'
                target_measure = 'USD_CO2'
                scaled_val = obs_val * (10.0**unit_mult)
        else:
            raise ValueError(f'Unsupported SDMX feed name: {feed_name}')

        if not subject or not target_measure or scaled_val is None:
            continue

        record_key = (loc, subject, target_measure, year)
        formatted_val = _format_number(scaled_val)
        existing_val = records.get(record_key)
        if existing_val is not None and existing_val != formatted_val:
            raise ValueError(
                f'Conflicting SDMX values in feed {feed_name} for key '
                f'{record_key}: {existing_val} vs {formatted_val}')
        records[record_key] = formatted_val

    if not records:
        raise RuntimeError(
            f'Zero valid observation rows extracted from SDMX feed {feed_name}')
    if expected_series is not None:
        observed_series = {(k[1], k[2]) for k in records}
        missing_series = expected_series - observed_series
        if missing_series:
            raise RuntimeError(
                f'SDMX feed {feed_name} is missing expected (SUBJECT, MEASURE) '
                f'series: {sorted(missing_series)}')
    return records


def download_historical_baseline_from_gcs(
    gcs_bucket: str,
    gcs_blob: str,
    raw_dir: str,
) -> str:
    """Downloads the static 2024 historical baseline CSV from GCS atomically."""
    os.makedirs(raw_dir, exist_ok=True)
    dest_path = Path(raw_dir) / HISTORICAL_RAW_FILENAME
    temp_path = Path(f'{dest_path}.tmp')

    logging.info(
        'Outbound GCS request: method=GET uri=gs://%s/%s params=None body=None '
        'dest=%s',
        gcs_bucket,
        gcs_blob,
        dest_path,
    )
    try:
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        blob = bucket.blob(gcs_blob)
        blob.download_to_filename(str(temp_path), timeout=300)
        if not temp_path.is_file() or temp_path.stat().st_size == 0:
            raise ValueError(
                f'Downloaded GCS baseline gs://{gcs_bucket}/{gcs_blob} is empty'
            )
        os.replace(temp_path, dest_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    return str(dest_path)


def parse_historical_baseline_csv(
    csv_path: str,
    valid_places: dict[str, str],
) -> dict[tuple[str, str, str, str], str]:
    """Parses the 2024 processed CSV into normalized (LOCATION, SUBJECT, MEASURE, TIME) rows."""
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(
            f'Historical baseline CSV not found at {csv_path}')

    records: dict[tuple[str, str, str, str], str] = {}
    precedence: dict[tuple[str, str, str, str], int] = {}
    with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {
            'observationAbout',
            'observationDate',
            'value',
            'variableMeasured',
        }
        if not reader.fieldnames or not required.issubset(set(
                reader.fieldnames)):
            raise ValueError(f'Invalid columns in historical CSV {csv_path}: '
                             f'{reader.fieldnames}')
        for row in reader:
            raw_place = (row.get('observationAbout') or '').strip()
            row_prec = 2
            if raw_place.startswith('dcid:country/'):
                raw_code = raw_place[len('dcid:country/'):]
                if raw_code.strip().upper() == 'WLD':
                    row_prec = 1
            elif raw_place.startswith('country/'):
                raw_code = raw_place[len('country/'):]
                if raw_code.strip().upper() == 'WLD':
                    row_prec = 1
            elif raw_place in ('dcid:Earth', 'Earth'):
                raw_code = 'W'
                row_prec = 2
            else:
                continue

            loc = _canonicalize_location(raw_code)
            if loc not in valid_places:
                continue

            sv = (row.get('variableMeasured') or '').strip()
            if not sv.startswith('dcid:'):
                sv = f'dcid:{sv}'
            if sv not in HISTORICAL_SV_MAP:
                continue

            year = (row.get('observationDate') or '').strip()
            if not year.isdigit() or len(year) != 4:
                continue

            obs_val = _parse_float(row.get('value'))
            if obs_val is None:
                continue

            subject, measure, divisor = HISTORICAL_SV_MAP[sv]
            record_key = (loc, subject, measure, year)
            formatted_val = _format_number(obs_val / divisor)
            existing_prec = precedence.get(record_key, 0)
            if row_prec < existing_prec:
                continue
            if (row_prec == existing_prec and
                    records[record_key] != formatted_val):
                raise ValueError(
                    f'Conflicting historical baseline values in {csv_path} for '
                    f'key {record_key}: {records[record_key]} vs {formatted_val}'
                )
            records[record_key] = formatted_val
            precedence[record_key] = row_prec

    if not records:
        raise ValueError(
            f'No valid historical baseline observations parsed from {csv_path}')
    return records


def merge_observations(
    live_records: dict[tuple[str, str, str, str], str],
    historical_records: dict[tuple[str, str, str, str], str],
) -> tuple[list[dict[str, str]], int]:
    """Merges live SDMX records with non-overlapping historical baseline records."""
    merged = dict(historical_records)
    retained_count = sum(1 for k in historical_records if k not in live_records)
    merged.update(live_records)

    rows: list[dict[str, str]] = []
    for (loc, subject, measure, year) in sorted(merged.keys()):
        rows.append({
            'LOCATION': loc,
            'SUBJECT': subject,
            'MEASURE': measure,
            'FREQUENCY': 'A',
            'TIME': year,
            'Value': merged[(loc, subject, measure, year)],
        })
    return rows, retained_count


def write_staging_csv_atomic(
    output_dir: str,
    rows: list[dict[str, str]],
) -> str:
    """Purges stale staging CSVs and atomically writes the unified input CSV."""
    if not rows:
        raise ValueError('Cannot write empty staging CSV')

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest_path = out_dir / STAGING_CSV_FILENAME
    temp_path = out_dir / f'{STAGING_CSV_FILENAME}.tmp'

    for existing_csv in out_dir.glob('*.csv'):
        if existing_csv != dest_path:
            existing_csv.unlink()

    try:
        with open(temp_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_path, dest_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    return str(dest_path)


def _cleanup_stale_files(directory: str, expected_files: set[str]) -> None:
    """Removes regular files in directory that are not in expected_files."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return
    for entry in dir_path.iterdir():
        if entry.name.startswith('.'):
            continue
        if entry.is_file() and entry.name not in expected_files:
            logging.info('Removing stale file: %s', entry)
            entry.unlink()


def _resolve_module_path(path_str: str) -> str:
    """Resolves relative paths against the script directory."""
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(_MODULE_DIR, path_str)


def download_and_process(
    output_dir: str,
    raw_dir: str,
    places_resolved_csv: str,
    gcs_bucket: str = HISTORICAL_GCS_BUCKET,
    gcs_blob: str = HISTORICAL_GCS_BLOB,
) -> str:
    """Runs end-to-end SDMX download, GCS baseline backfill, and staging CSV generation."""
    valid_places = load_resolved_places(places_resolved_csv)
    logging.info('Loaded %d resolved place mappings.', len(valid_places))

    sdmx_client = _create_sdmx_client()
    live_records: dict[tuple[str, str, str, str], str] = {}
    expected_raw_files: set[str] = {HISTORICAL_RAW_FILENAME}
    for spec in SDMX_FEEDS:
        expected_raw_files.add(spec.raw_filename)
        df = fetch_sdmx_dataframe(
            client=sdmx_client,
            spec=spec,
            raw_dir=raw_dir,
        )
        feed_records = normalize_sdmx_feed(
            spec.name,
            df,
            valid_places,
            expected_series=spec.expected_series,
        )
        logging.info(
            'Normalized %d observations from SDMX feed %s (%s).',
            len(feed_records),
            spec.name,
            spec.dataflow_id,
        )
        live_records.update(feed_records)

    hist_csv_path = download_historical_baseline_from_gcs(
        gcs_bucket=gcs_bucket,
        gcs_blob=gcs_blob,
        raw_dir=raw_dir,
    )
    _cleanup_stale_files(raw_dir, expected_raw_files)

    historical_records = parse_historical_baseline_csv(
        csv_path=hist_csv_path,
        valid_places=valid_places,
    )
    logging.info(
        'Parsed %d valid observations from historical baseline.',
        len(historical_records),
    )

    merged_rows, retained_count = merge_observations(
        live_records=live_records,
        historical_records=historical_records,
    )
    staging_path = write_staging_csv_atomic(output_dir, merged_rows)
    logging.info(
        'Wrote %d total observations (%d live SDMX + %d retained historical) '
        'to %s',
        len(merged_rows),
        len(live_records),
        retained_count,
        staging_path,
    )
    return staging_path


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise ValueError(f'Unexpected positional arguments: {argv[1:]}')
    download_and_process(
        output_dir=_resolve_module_path(_FLAGS.output_dir),
        raw_dir=_resolve_module_path(_FLAGS.raw_dir),
        places_resolved_csv=_resolve_module_path(_FLAGS.places_resolved_csv),
        gcs_bucket=_FLAGS.gcs_bucket,
        gcs_blob=_FLAGS.gcs_blob,
    )


if __name__ == '__main__':
    _define_flags()
    app.run(main)

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
"""Downloads and merges MoSPI eSankhyiki National Accounts Statistics (NAS) data.

Queries the official unauthenticated MoSPI NAS JSON REST API
(https://api.mospi.gov.in/api/nas/getNasData) across annual national GDP (ic=5),
national sectoral GVA (ic=1), state-level GSDP (ic=23), and state-level GSDP
growth rate (ic=26), saves unmodified raw JSON responses to raw_source/, loads
the 9 unmodified legacy 2026-02-02 production CSVs staged in GCS (repairing the
GSDP_CONSTANT.csv Ladakh/Puducherry misattribution bug in memory and preserving
Assam, Haryana, Ladakh, and Nagaland omitted by ic=23/ic=26), merges live API
records on top, and atomically writes the 5 tidy input CSVs under input_files/
for stat_var_processor.py.
"""

from decimal import Decimal
from decimal import InvalidOperation
import io
import json
import os
import ssl
import tempfile
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
from google.api_core import exceptions as gcs_exceptions
from google.cloud import storage
import pandas as pd
import requests
from requests.adapters import HTTPAdapter

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_API_URL = 'https://api.mospi.gov.in/api/nas/getNasData'
DEFAULT_GCS_BASELINE_DIR = 'gs://unresolved_mcf/india_mospi/economy/baseline'
DEFAULT_PLACES_CSV = os.path.join(_SCRIPT_DIR, 'india_nas_places.csv')
DEFAULT_RAW_SOURCE_DIR = os.path.join(_SCRIPT_DIR, 'raw_source')
DEFAULT_INPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')

CRORE_SCALE = Decimal('10000000')
LADAKH_DCID = 'wikidataId/Q200667'
PUDUCHERRY_DCID = 'wikidataId/Q66743'

_GCS_CLIENT: storage.Client | None = None

MAX_PAGE_SIZE = 200
BASE_YEAR_2011_12 = '2011-12'
FREQUENCY_ANNUAL = 1
SERIES_CURRENT = 'Current'

INDICATOR_GVA = 1
INDICATOR_GDP = 5
INDICATOR_GSDP = 23
INDICATOR_GSDP_GROWTH = 26

GDP_COLUMNS = [
    'base_year',
    'series',
    'year',
    'indicator',
    'frequency',
    'revision',
    'current_price',
    'constant_price',
    'unit',
]
GDP_KEY_COLUMNS = ['base_year', 'series', 'year', 'revision']

GVA_COLUMNS = [
    'base_year',
    'series',
    'year',
    'indicator',
    'frequency',
    'revision',
    'industry',
    'current_price',
    'constant_price',
    'unit',
]
GVA_KEY_COLUMNS = ['base_year', 'series', 'year', 'revision', 'industry']

GSDP_COLUMNS = [
    'base_year',
    'series',
    'year',
    'indicator',
    'frequency',
    'state',
    'current_price',
    'constant_price',
    'unit',
]
GSDP_KEY_COLUMNS = ['base_year', 'series', 'year', 'indicator', 'state']

VALUE_COLUMNS = ('current_price', 'constant_price')

# Revisions matching existing MeasurementMethodEnum values in production schema.
GDP_ALLOWED_REVISIONS = frozenset({
    'First Advance Estimates',
    'Second Revised Estimates',
})
GVA_STANDARD_REVISIONS = frozenset({
    'First Advance Estimates',
    'Second Advance Estimates',
    'Provisional Estimates',
    'Second Revised Estimates',
})
GVA_THIRD_REVISED_REVISION = 'Third Revised Estimates'

_NON_NUMERIC_PLACEHOLDERS = frozenset({'', 'na', 'n/a', 'null', 'none', '-'})
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

METHOD_TO_REVISION = {
    'MOSPIFirstAdvanceEstimates': 'First Advance Estimates',
    'MOSPISecondAdvanceEstimates': 'Second Advance Estimates',
    'MOSPIProvisionalEstimates': 'Provisional Estimates',
    'MOSPISecondRevisedEstimates': 'Second Revised Estimates',
    'MOSPIThirdRevisedEstimates': 'Third Revised Estimates',
}

HEADLINE_METHODS = frozenset({
    'MOSPIFirstAdvanceEstimates',
    'MOSPISecondAdvanceEstimates',
    'MOSPIProvisionalEstimates',
})

# Maps legacy prod StatVar DCID (without leading 'dcid:') to (price_col, industry).
# FinanceService and PublicAdministrationAndDefenceOrMOSPIOtherService depend on
# measurementMethod and are resolved via _resolve_gva_statvar().
_GVA_STATVAR_BASE_MAP: dict[str, tuple[str, str]] = {
    'Nominal_Amount_EconomicActivity_GrossValueAdded':
        ('current_price', 'Total Gross Value Added'),
    'Amount_EconomicActivity_GrossValueAdded_RealValue':
        ('constant_price', 'Total Gross Value Added'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_AgricultureForestryFishingSector':
        ('current_price', 'Agriculture, Livestock, Forestry and Fishing'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_AgricultureForestryFishingSector':
        ('constant_price', 'Agriculture, Livestock, Forestry and Fishing'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_MiningQuarrying':
        ('current_price', 'Mining and Quarrying'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_MiningQuarrying':
        ('constant_price', 'Mining and Quarrying'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_ManufacturingSector':
        ('current_price', 'Manufacturing'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_ManufacturingSector':
        ('constant_price', 'Manufacturing'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_ElectricityGasSteamAirConditionSupply':
        ('current_price',
         'Electricity, Gas, Water Supply & Other Utility Services'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_ElectricityGasSteamAirConditionSupply':
        ('constant_price',
         'Electricity, Gas, Water Supply & Other Utility Services'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_ConstructionSector':
        ('current_price', 'Construction'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_ConstructionSector':
        ('constant_price', 'Construction'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_TradeSectorOrTransportStorageSectorOrPublishingBroadcastingInformationActivities':
        ('current_price',
         'Trade, Hotels, Transport, Communication & Services Related to Broadcasting'
        ),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_TradeSectorOrTransportStorageSectorOrPublishingBroadcastingInformationActivities':
        ('constant_price',
         'Trade, Hotels, Transport, Communication & Services Related to Broadcasting'
        ),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_TradeSector':
        ('current_price', 'Trade, Repair, Hotels and Restaurants'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_TradeSector':
        ('constant_price', 'Trade, Repair, Hotels and Restaurants'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_TradeSectorOrMaintenanceAndRepairOrRestaurantAndHotels':
        ('current_price', 'Trade, Repair, Hotels and Restaurants'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_TradeSectorOrMaintenanceAndRepairOrRestaurantAndHotels':
        ('constant_price', 'Trade, Repair, Hotels and Restaurants'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_TransportStorageSectorOrPublishingBroadcastingInformationActivities':
        ('current_price',
         'Transport, Storage, Communication & Services Related to Broadcasting'
        ),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_TransportStorageSectorOrPublishingBroadcastingInformationActivities':
        ('constant_price',
         'Transport, Storage, Communication & Services Related to Broadcasting'
        ),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_RealEstateOrDwellingRelatedServicesOrProfessionalServices':
        ('current_price',
         'Real Estate, Ownership of Dwelling & Professional Services'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_RealEstateOrDwellingRelatedServicesOrProfessionalServices':
        ('constant_price',
         'Real Estate, Ownership of Dwelling & Professional Services'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_PublicAdministrationAndDefence':
        ('current_price', 'Public Administration and Defence'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_PublicAdministrationAndDefence':
        ('constant_price', 'Public Administration and Defence'),
    'Nominal_Amount_EconomicActivity_GrossValueAdded_MOSPIOtherService':
        ('current_price', 'Other Services'),
    'RealValue_Amount_EconomicActivity_GrossValueAdded_MOSPIOtherService':
        ('constant_price', 'Other Services'),
}

FLAGS = flags.FLAGS


def _define_flags() -> None:
    """Defines command-line flags for this download script."""
    flags.DEFINE_string(
        'nas_api_url',
        DEFAULT_API_URL,
        'MoSPI eSankhyiki NAS getNasData REST API endpoint.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'nas_gcs_baseline_dir',
        DEFAULT_GCS_BASELINE_DIR,
        'GCS URI (or local directory) containing the 9 unmodified 20260202 legacy baseline CSVs.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'nas_places_csv',
        DEFAULT_PLACES_CSV,
        'Path to india_nas_places.csv mapping place names to Wikidata DCIDs.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'nas_raw_source_dir',
        DEFAULT_RAW_SOURCE_DIR,
        'Directory where unmodified raw API JSON payloads are written.',
        allow_override=True,
    )
    flags.DEFINE_string(
        'nas_input_dir',
        DEFAULT_INPUT_DIR,
        'Destination directory for merged tidy input CSVs.',
        allow_override=True,
    )
    flags.DEFINE_integer(
        'nas_page_size',
        MAX_PAGE_SIZE,
        'Records per API page (MoSPI enforces <= 200).',
        allow_override=True,
    )
    flags.DEFINE_integer(
        'nas_timeout_seconds',
        30,
        'Per-request HTTP timeout in seconds.',
        allow_override=True,
    )
    flags.DEFINE_integer(
        'nas_max_retries',
        3,
        'Maximum retry attempts for transient HTTP/network errors.',
        allow_override=True,
    )
    flags.DEFINE_float(
        'nas_retry_delay_seconds',
        5.0,
        'Initial backoff delay in seconds between retries.',
        allow_override=True,
    )
    flags.DEFINE_float(
        'nas_retry_backoff',
        2.0,
        'Exponential backoff multiplier between retry attempts.',
        allow_override=True,
    )
    flags.DEFINE_bool(
        'nas_skip_live_api',
        False,
        'If true, skip live MoSPI API calls and write staged baselines only.',
        allow_override=True,
    )
    flags.DEFINE_bool(
        'nas_skip_baseline',
        False,
        'If true, skip loading GCS baselines (local debugging only; drops '
        'states omitted by ic=23/ic=26 such as Assam, Haryana, Ladakh, Nagaland).',
        allow_override=True,
    )


class _LegacyTLSAdapter(HTTPAdapter):
    """HTTPS adapter enabling OpenSSL OP_LEGACY_SERVER_CONNECT for api.mospi.gov.in.

    Keeps full certificate and hostname verification enabled while allowing
    legacy TLS renegotiation required by MoSPI's upstream TLS terminator.
    """

    @staticmethod
    def _build_ssl_context() -> ssl.SSLContext:
        ctx = ssl.create_default_context()
        ctx.options |= getattr(ssl, 'OP_LEGACY_SERVER_CONNECT', 0x4)
        return ctx

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self._build_ssl_context()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args: Any, **kwargs: Any) -> Any:
        kwargs['ssl_context'] = self._build_ssl_context()
        return super().proxy_manager_for(*args, **kwargs)


def create_session() -> requests.Session:
    """Creates a requests.Session configured for MoSPI eSankhyiki HTTPS calls."""
    session = requests.Session()
    session.mount('https://', _LegacyTLSAdapter())
    return session


def _clean_str(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def _clean_numeric_str(value: Any) -> str:
    text = _clean_str(value)
    if text.lower() in _NON_NUMERIC_PLACEHOLDERS:
        return ''
    return text


def _fetch_page(
    session: requests.Session,
    api_url: str,
    params: dict[str, Any],
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
) -> dict[str, Any]:
    """Fetches one JSON page from MoSPI NAS API with bounded retries."""
    delay = retry_delay_seconds
    for attempt in range(1, max_retries + 1):
        logging.info('GET %s params=%s (attempt %d/%d)', api_url, params,
                     attempt, max_retries)
        try:
            response = session.get(api_url,
                                   params=params,
                                   timeout=timeout_seconds)
            logging.info('GET %s params=%s -> HTTP %d', api_url, params,
                         response.status_code)
            if response.status_code in _RETRYABLE_STATUS_CODES:
                raise requests.HTTPError(
                    f'Retryable HTTP {response.status_code} from {api_url} '
                    f'params={params}',
                    response=response,
                )
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError(
                    f'Non-JSON response (possible soft 404/error page) from '
                    f'{api_url} params={params}: {response.text[:200]!r}'
                ) from exc
            if not isinstance(payload, dict):
                raise ValueError(
                    f'Expected JSON object from {api_url} params={params}, '
                    f'got {type(payload).__name__}')
            if payload.get('statusCode') is False:
                raise RuntimeError(
                    f'MoSPI NAS API returned statusCode=False for {api_url} '
                    f"params={params}: {payload.get('msg')}")
            return payload
        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt >= max_retries:
                raise RuntimeError(
                    f'Exhausted {max_retries} attempts fetching {api_url} '
                    f'params={params}') from exc
            logging.warning(
                'Transient network error on GET %s params=%s (%s); '
                'retrying in %.1fs', api_url, params, exc, delay)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in _RETRYABLE_STATUS_CODES or attempt >= max_retries:
                raise
            logging.warning(
                'Transient HTTP %s on GET %s params=%s; retrying in %.1fs',
                status, api_url, params, delay)
        time.sleep(delay)
        delay *= retry_backoff
    raise RuntimeError(f'Unreachable retry state for {api_url} params={params}')


def fetch_paginated_indicator(
    session: requests.Session,
    api_url: str,
    query_params: dict[str, Any],
    page_size: int = MAX_PAGE_SIZE,
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetches all pages for one MoSPI NAS indicator query.

    Returns:
        Tuple of (all_records, raw_page_payloads).
    """
    if page_size <= 0 or page_size > MAX_PAGE_SIZE:
        raise ValueError(
            f'page_size must be in 1..{MAX_PAGE_SIZE}, got {page_size}')

    all_records: list[dict[str, Any]] = []
    raw_pages: list[dict[str, Any]] = []
    page = 1
    total_pages = 1
    expected_total_records: int | None = None

    while page <= total_pages:
        params = dict(query_params)
        params.update({
            'Format': 'JSON',
            'limit': page_size,
            'page': page,
        })
        payload = _fetch_page(
            session=session,
            api_url=api_url,
            params=params,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            retry_backoff=retry_backoff,
        )
        raw_pages.append(payload)

        records = payload.get('data')
        meta = payload.get('meta_data')
        if not isinstance(records, list) or not isinstance(meta, dict):
            raise RuntimeError(
                f'Malformed MoSPI NAS payload for {query_params} page {page}: '
                'missing data or meta_data')

        if expected_total_records is None:
            expected_total_records = int(meta.get('totalRecords', 0))
            total_pages = int(meta.get('totalPages', 0))
            if expected_total_records <= 0 or total_pages <= 0:
                raise RuntimeError(
                    f'MoSPI NAS API returned zero records for {query_params}: '
                    f'meta_data={meta}')
            logging.info(
                'MoSPI NAS API query=%s reported totalRecords=%d across %d pages',
                query_params, expected_total_records, total_pages)

        if not records:
            raise RuntimeError(
                f'MoSPI NAS API returned empty data list for {query_params} '
                f'on page {page}/{total_pages}')

        all_records.extend(records)
        page += 1

    if expected_total_records is not None and len(
            all_records) != expected_total_records:
        raise RuntimeError(
            f'Fetched record count ({len(all_records)}) does not match '
            f'meta_data.totalRecords ({expected_total_records}) for '
            f'query={query_params}')

    logging.info('Fetched %d records across %d pages for query=%s',
                 len(all_records), len(raw_pages), query_params)
    return all_records, raw_pages


def _require_fields(item: dict[str, Any], required: tuple[str, ...],
                    context: str) -> None:
    missing = [col for col in required if col not in item]
    if missing:
        raise RuntimeError(
            f'MoSPI NAS {context} record missing required fields {missing}: '
            f'{item}')


def normalize_gdp_records(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Filters and normalizes annual national GDP records (ic=5)."""
    required = ('base_year', 'series', 'year', 'indicator', 'frequency',
                'revision', 'current_price', 'constant_price', 'unit')
    rows: list[dict[str, str]] = []
    for item in records:
        _require_fields(item, required, 'GDP')
        revision = _clean_str(item.get('revision'))
        if revision not in GDP_ALLOWED_REVISIONS:
            continue
        cur = _clean_numeric_str(item.get('current_price'))
        const = _clean_numeric_str(item.get('constant_price'))
        if not cur and not const:
            continue
        rows.append({
            'base_year': _clean_str(item.get('base_year')),
            'series': _clean_str(item.get('series')),
            'year': _clean_str(item.get('year')),
            'indicator': _clean_str(item.get('indicator')),
            'frequency': _clean_str(item.get('frequency')),
            'revision': revision,
            'current_price': cur,
            'constant_price': const,
            'unit': _clean_str(item.get('unit')),
        })
    return pd.DataFrame(rows, columns=GDP_COLUMNS, dtype=str)


def normalize_gva_records(
    records: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filters and splits annual GVA records (ic=1) into standard & ThirdRevised.

    Explicitly excludes sub-industry rows (subindustry != null) and
    institutional-sector breakdown rows (institutional_sector != null) to avoid
    duplicate observations against top-level industry rows.
    """
    required = ('base_year', 'series', 'year', 'indicator', 'frequency',
                'revision', 'industry', 'current_price', 'constant_price',
                'unit')
    standard_rows: list[dict[str, str]] = []
    third_revised_rows: list[dict[str, str]] = []

    for item in records:
        _require_fields(item, required, 'GVA')
        industry = _clean_str(item.get('industry'))
        subindustry = _clean_str(item.get('subindustry'))
        institutional_sector = _clean_str(item.get('institutional_sector'))
        if not industry or subindustry or institutional_sector:
            continue

        revision = _clean_str(item.get('revision'))
        cur = _clean_numeric_str(item.get('current_price'))
        const = _clean_numeric_str(item.get('constant_price'))
        if not cur and not const:
            continue

        row = {
            'base_year': _clean_str(item.get('base_year')),
            'series': _clean_str(item.get('series')),
            'year': _clean_str(item.get('year')),
            'indicator': _clean_str(item.get('indicator')),
            'frequency': _clean_str(item.get('frequency')),
            'revision': revision,
            'industry': industry,
            'current_price': cur,
            'constant_price': const,
            'unit': _clean_str(item.get('unit')),
        }
        if revision in GVA_STANDARD_REVISIONS:
            standard_rows.append(row)
        elif revision == GVA_THIRD_REVISED_REVISION:
            third_revised_rows.append(row)

    return (
        pd.DataFrame(standard_rows, columns=GVA_COLUMNS, dtype=str),
        pd.DataFrame(third_revised_rows, columns=GVA_COLUMNS, dtype=str),
    )


def normalize_gsdp_records(records: list[dict[str, Any]],
                           context: str) -> pd.DataFrame:
    """Normalizes state-level GSDP (ic=23) or GSDP Growth Rate (ic=26) rows."""
    required = ('base_year', 'series', 'year', 'indicator', 'frequency',
                'state', 'current_price', 'constant_price', 'unit')
    rows: list[dict[str, str]] = []
    for item in records:
        _require_fields(item, required, context)
        if _clean_str(item.get('base_year')) != BASE_YEAR_2011_12:
            continue
        state = _clean_str(item.get('state'))
        if not state:
            continue
        cur = _clean_numeric_str(item.get('current_price'))
        const = _clean_numeric_str(item.get('constant_price'))
        if not cur and not const:
            continue
        rows.append({
            'base_year': _clean_str(item.get('base_year')),
            'series': _clean_str(item.get('series')),
            'year': _clean_str(item.get('year')),
            'indicator': _clean_str(item.get('indicator')),
            'frequency': _clean_str(item.get('frequency')),
            'state': state,
            'current_price': cur,
            'constant_price': const,
            'unit': _clean_str(item.get('unit')),
        })
    return pd.DataFrame(rows, columns=GSDP_COLUMNS, dtype=str)


def _strip_dcid_prefix(value: str) -> str:
    text = value.strip()
    if text.startswith('dcid:'):
        return text[5:]
    if text.startswith('dcs:'):
        return text[4:]
    return text


def end_year_to_fiscal_year(obs_date: str) -> str:
    """Converts ending calendar year YYYY (e.g. '2026') to fiscal year '2025-26'."""
    text = obs_date.strip()
    if not text.isdigit() or len(text) != 4:
        raise ValueError(f'Expected 4-digit year observationDate, got {obs_date!r}')
    end_year = int(text)
    return f'{end_year - 1}-{str(end_year)[-2:]}'


def inr_to_crore_str(value_str: str) -> str:
    """Divides an INR string by 1e7 back to Crore without float drift."""
    text = value_str.strip()
    if not text:
        return ''
    try:
        crore = Decimal(text) / CRORE_SCALE
    except InvalidOperation as exc:
        raise ValueError(f'Invalid numeric INR value: {value_str!r}') from exc
    normalized = format(crore.normalize(), 'f')
    if '.' in normalized:
        normalized = normalized.rstrip('0').rstrip('.')
    return normalized


def load_dcid_to_place_name(places_csv: str) -> dict[str, str]:
    """Loads canonical DCID -> state/UT name map (preferring non-alias rows)."""
    df = pd.read_csv(places_csv, dtype=str, keep_default_na=False)
    dcid_to_name: dict[str, str] = {}
    for _, row in df.iterrows():
        name = row['place_name'].strip()
        dcid = _strip_dcid_prefix(row['dcid'])
        if not name or not dcid:
            continue
        if dcid not in dcid_to_name:
            dcid_to_name[dcid] = name
    return dcid_to_name


def _resolve_gva_statvar(statvar: str, method: str) -> tuple[str, str]:
    """Maps a legacy GVA StatVar DCID and measurementMethod to (price_col, industry)."""
    sv = _strip_dcid_prefix(statvar)
    if sv in _GVA_STATVAR_BASE_MAP:
        return _GVA_STATVAR_BASE_MAP[sv]
    if sv == 'Nominal_Amount_EconomicActivity_GrossValueAdded_FinanceService':
        industry = ('Financial, Real Estate & Professional Services'
                    if method in HEADLINE_METHODS else 'Financial Services')
        return ('current_price', industry)
    if sv == 'RealValue_Amount_EconomicActivity_GrossValueAdded_FinanceService':
        industry = ('Financial, Real Estate & Professional Services'
                    if method in HEADLINE_METHODS else 'Financial Services')
        return ('constant_price', industry)
    if sv == 'Nominal_Amount_EconomicActivity_GrossValueAdded_PublicAdministrationAndDefenceOrMOSPIOtherService':
        industry = ('Public Administration, Defence & Other Services'
                    if method in HEADLINE_METHODS else
                    'Public Administration and Defence')
        return ('current_price', industry)
    if sv == 'RealValue_Amount_EconomicActivity_GrossValueAdded_PublicAdministrationAndDefenceOrMOSPIOtherService':
        industry = ('Public Administration, Defence & Other Services'
                    if method in HEADLINE_METHODS else
                    'Public Administration and Defence')
        return ('constant_price', industry)
    raise ValueError(
        f'Unrecognized GVA StatVar {statvar!r} for measurementMethod {method!r}'
    )


def _get_gcs_client() -> storage.Client:
    """Lazily initializes a shared GCS client."""
    global _GCS_CLIENT
    if _GCS_CLIENT is None:
        _GCS_CLIENT = storage.Client()
    return _GCS_CLIENT


def _read_csv_if_exists(path: str) -> pd.DataFrame | None:
    """Reads a CSV from GCS (object-level read) or local disk; returns None if absent."""
    if path.startswith('gs://'):
        bucket_name, blob_name = path[5:].split('/', 1)
        client = _get_gcs_client()
        blob = client.bucket(bucket_name).blob(blob_name)
        try:
            raw_bytes = blob.download_as_bytes()
        except gcs_exceptions.NotFound:
            return None
        return pd.read_csv(io.BytesIO(raw_bytes),
                           dtype=str,
                           keep_default_na=False)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _read_first_existing_csv(source_dir: str,
                             candidates: tuple[str, ...]) -> pd.DataFrame:
    """Reads the first existing candidate CSV from a GCS or local directory."""
    base = source_dir.rstrip('/')
    for name in candidates:
        path = f'{base}/{name}'
        df = _read_csv_if_exists(path)
        if df is not None:
            logging.info('Loaded legacy baseline CSV %s (%d rows)', path,
                         len(df))
            return df
    raise FileNotFoundError(
        f'None of {candidates} found in baseline directory {source_dir}')


def convert_gdp_prod_dfs(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Converts legacy prod GDP_ANNUAL + GDP_India_FirstAdvanced CSVs to tidy schema."""
    by_key: dict[tuple[str, str], dict[str, str]] = {}
    for df in dfs:
        for _, row in df.iterrows():
            method = _strip_dcid_prefix(row['measurementMethod'])
            if method not in METHOD_TO_REVISION:
                raise ValueError(f'Unknown GDP measurementMethod: {method!r}')
            revision = METHOD_TO_REVISION[method]
            fy = end_year_to_fiscal_year(row['observationDate'])
            sv = _strip_dcid_prefix(row['variableMeasured'])
            if sv == 'Amount_EconomicActivity_GrossDomesticProduction_Nominal':
                price_col = 'current_price'
            elif sv == 'Amount_EconomicActivity_GrossDomesticProduction_RealValue':
                price_col = 'constant_price'
            else:
                raise ValueError(f'Unknown GDP StatVar: {sv!r}')

            key = (fy, revision)
            rec = by_key.setdefault(
                key, {
                    'base_year': BASE_YEAR_2011_12,
                    'series': SERIES_CURRENT,
                    'year': fy,
                    'indicator': 'Gross Domestic Product',
                    'frequency': 'Annual',
                    'revision': revision,
                    'current_price': '',
                    'constant_price': '',
                    'unit': '₹ Crore',
                })
            rec[price_col] = inr_to_crore_str(row['value'])

    rows = [by_key[k] for k in sorted(by_key, reverse=True)]
    return pd.DataFrame(rows, columns=GDP_COLUMNS, dtype=str)


def convert_gva_prod_dfs(
    dfs: list[pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Converts legacy prod GVA CSVs into (standard_gva_df, third_revised_gva_df)."""
    standard_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    third_by_key: dict[tuple[str, str, str], dict[str, str]] = {}

    for df in dfs:
        for _, row in df.iterrows():
            method = _strip_dcid_prefix(row['measurementMethod'])
            if method not in METHOD_TO_REVISION:
                raise ValueError(f'Unknown GVA measurementMethod: {method!r}')
            revision = METHOD_TO_REVISION[method]
            fy = end_year_to_fiscal_year(row['observationDate'])
            price_col, industry = _resolve_gva_statvar(row['variableMeasured'],
                                                       method)
            target = (third_by_key
                      if method == 'MOSPIThirdRevisedEstimates' else
                      standard_by_key)
            key = (fy, revision, industry)
            rec = target.setdefault(
                key, {
                    'base_year': BASE_YEAR_2011_12,
                    'series': SERIES_CURRENT,
                    'year': fy,
                    'indicator': 'Gross Value Added',
                    'frequency': 'Annual',
                    'revision': revision,
                    'industry': industry,
                    'current_price': '',
                    'constant_price': '',
                    'unit': '₹ Crore',
                })
            rec[price_col] = inr_to_crore_str(row['value'])

    std_rows = [standard_by_key[k] for k in sorted(standard_by_key, reverse=True)]
    third_rows = [third_by_key[k] for k in sorted(third_by_key, reverse=True)]
    return (
        pd.DataFrame(std_rows, columns=GVA_COLUMNS, dtype=str),
        pd.DataFrame(third_rows, columns=GVA_COLUMNS, dtype=str),
    )


def repair_gsdp_constant_ladakh_bug(df: pd.DataFrame) -> pd.DataFrame:
    """Repairs Puducherry rows misattributed to Ladakh in legacy GSDP_CONSTANT.csv.

    In the 2026-02-02 manual export, an empty Ladakh row immediately preceded
    Puducherry, causing all 27 constant-price observations for Puducherry
    (wikidataId/Q66743) to be emitted under Ladakh (wikidataId/Q200667) while
    Puducherry had zero constant-price rows.
    """
    fixed = df.copy()
    places = {_strip_dcid_prefix(p) for p in fixed['observationAbout']}
    if PUDUCHERRY_DCID not in places and LADAKH_DCID in places:
        mask = fixed['observationAbout'].map(_strip_dcid_prefix) == LADAKH_DCID
        repaired_count = int(mask.sum())
        logging.warning(
            'Repairing GSDP_CONSTANT.csv Ladakh/Puducherry bug: reassigning '
            '%d rows from %s to %s', repaired_count, LADAKH_DCID,
            PUDUCHERRY_DCID)
        fixed.loc[mask, 'observationAbout'] = PUDUCHERRY_DCID
    return fixed


def convert_gsdp_prod_dfs(
    gsdp_constant_df: pd.DataFrame,
    gsdp_current_df: pd.DataFrame,
    dcid_to_place: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Converts legacy prod GSDP_CONSTANT + GSDP_CURRENT CSVs into tidy GSDP + Growth."""
    fixed_constant_df = repair_gsdp_constant_ladakh_bug(gsdp_constant_df)
    gsdp_by_key: dict[tuple[str, str], dict[str, str]] = {}
    growth_by_key: dict[tuple[str, str], dict[str, str]] = {}

    for df in (fixed_constant_df, gsdp_current_df):
        for _, row in df.iterrows():
            place_dcid = _strip_dcid_prefix(row['observationAbout'])
            if place_dcid not in dcid_to_place:
                raise ValueError(
                    f'Unmapped GSDP observationAbout DCID: {place_dcid!r}')
            state_name = dcid_to_place[place_dcid]
            fy = end_year_to_fiscal_year(row['observationDate'])
            sv = _strip_dcid_prefix(row['variableMeasured'])

            if sv == 'Amount_EconomicActivity_GrossDomesticProduction_Nominal':
                target, price_col, val = (gsdp_by_key, 'current_price',
                                          inr_to_crore_str(row['value']))
                indicator, unit = 'Gross State Domestic Product', '₹ Crore'
            elif sv == 'Amount_EconomicActivity_GrossDomesticProduction_RealValue':
                target, price_col, val = (gsdp_by_key, 'constant_price',
                                          inr_to_crore_str(row['value']))
                indicator, unit = 'Gross State Domestic Product', '₹ Crore'
            elif sv == 'Nominal_GrowthRate_Amount_EconomicActivity_GrossDomesticProduction':
                target, price_col, val = (growth_by_key, 'current_price',
                                          row['value'].strip())
                indicator, unit = 'GSDP Growth Rate', '%'
            elif sv == 'RealValue_GrowthRate_Amount_EconomicActivity_GrossDomesticProduction':
                target, price_col, val = (growth_by_key, 'constant_price',
                                          row['value'].strip())
                indicator, unit = 'GSDP Growth Rate', '%'
            else:
                raise ValueError(f'Unknown GSDP StatVar: {sv!r}')

            key = (fy, state_name)
            rec = target.setdefault(
                key, {
                    'base_year': BASE_YEAR_2011_12,
                    'series': SERIES_CURRENT,
                    'year': fy,
                    'indicator': indicator,
                    'frequency': 'Annual',
                    'state': state_name,
                    'current_price': '',
                    'constant_price': '',
                    'unit': unit,
                })
            rec[price_col] = val

    gsdp_rows = [gsdp_by_key[k] for k in sorted(gsdp_by_key, reverse=True)]
    growth_rows = [
        growth_by_key[k] for k in sorted(growth_by_key, reverse=True)
    ]
    return (
        pd.DataFrame(gsdp_rows, columns=GSDP_COLUMNS, dtype=str),
        pd.DataFrame(growth_rows, columns=GSDP_COLUMNS, dtype=str),
    )


def load_legacy_baselines(
    baseline_dir: str,
    places_csv: str = DEFAULT_PLACES_CSV,
) -> dict[str, pd.DataFrame]:
    """Loads the 9 unmodified 20260202 legacy CSVs from GCS or local disk."""
    dcid_to_place = load_dcid_to_place_name(places_csv)
    gdp_dfs = [
        _read_first_existing_csv(baseline_dir, ('GDP_ANNUAL.csv',)),
        _read_first_existing_csv(baseline_dir,
                                 ('GDP_India_FirstAdvanced.csv',)),
    ]
    gva_dfs = [
        _read_first_existing_csv(
            baseline_dir,
            ('GVA_FristAdvanceEstimates_output.csv',
             'GVA_FirstAdvanceEstimates_output.csv'),
        ),
        _read_first_existing_csv(
            baseline_dir,
            ('GVA_AdvancedEstimates_output.csv',
             'GVA_SecondAdvanceEstimates_output.csv'),
        ),
        _read_first_existing_csv(baseline_dir,
                                 ('GVA_ProvisionalEstimates_output.csv',)),
        _read_first_existing_csv(baseline_dir,
                                 ('GVA_SecondRevisedEstimates_output.csv',)),
        _read_first_existing_csv(baseline_dir,
                                 ('GVA_ThirdRevisedEstimates_output.csv',)),
    ]
    gsdp_constant_df = _read_first_existing_csv(baseline_dir,
                                                ('GSDP_CONSTANT.csv',))
    gsdp_current_df = _read_first_existing_csv(baseline_dir,
                                               ('GSDP_CURRENT.csv',))

    gdp_df = convert_gdp_prod_dfs(gdp_dfs)
    gva_df, gva_third_df = convert_gva_prod_dfs(gva_dfs)
    gsdp_df, gsdp_growth_df = convert_gsdp_prod_dfs(gsdp_constant_df,
                                                    gsdp_current_df,
                                                    dcid_to_place)
    return {
        'india_nas_gdp.csv': gdp_df,
        'india_nas_gva.csv': gva_df,
        'india_nas_gva_third_revised.csv': gva_third_df,
        'india_nas_gsdp.csv': gsdp_df,
        'india_nas_gsdp_growth.csv': gsdp_growth_df,
    }


def merge_records(
    baseline_df: pd.DataFrame | None,
    live_df: pd.DataFrame | None,
    columns: list[str],
    key_columns: list[str],
) -> pd.DataFrame:
    """Merges live MoSPI rows over baseline without losing keys or overwriting with blanks.

    For each unique key tuple:
      - Baseline rows absent from live_df (e.g. Assam, Haryana, Ladakh, Nagaland)
        are preserved intact.
      - Live non-empty values in current_price / constant_price update the
        corresponding baseline cells.
      - Empty/null live cells never overwrite populated baseline values.
      - Rows where both current_price and constant_price are empty are omitted.
    """
    merged_by_key: dict[tuple[str, ...], dict[str, str]] = {}

    if baseline_df is not None and not baseline_df.empty:
        for _, row in baseline_df[columns].iterrows():
            rec = {col: _clean_str(row[col]) for col in columns}
            for vcol in VALUE_COLUMNS:
                rec[vcol] = _clean_numeric_str(rec[vcol])
            key = tuple(rec[k] for k in key_columns)
            merged_by_key[key] = rec

    if live_df is not None and not live_df.empty:
        for _, row in live_df[columns].iterrows():
            rec = {col: _clean_str(row[col]) for col in columns}
            for vcol in VALUE_COLUMNS:
                rec[vcol] = _clean_numeric_str(rec[vcol])
            key = tuple(rec[k] for k in key_columns)
            if key not in merged_by_key:
                merged_by_key[key] = rec
            else:
                existing = merged_by_key[key]
                for col in columns:
                    if col in VALUE_COLUMNS:
                        if rec[col]:
                            existing[col] = rec[col]
                    elif rec[col]:
                        existing[col] = rec[col]

    final_rows = [
        merged_by_key[k]
        for k in sorted(merged_by_key, reverse=True)
        if any(merged_by_key[k][vcol] for vcol in VALUE_COLUMNS)
    ]
    return pd.DataFrame(final_rows, columns=columns, dtype=str)


def write_text_atomically(content: str, output_file: str,
                          prefix: str = '.nas_tmp_') -> None:
    """Writes UTF-8 text content atomically via temp file + os.replace."""
    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',
                                         encoding='utf-8',
                                         newline='',
                                         dir=output_dir,
                                         prefix=prefix,
                                         delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(content)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, output_file)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def write_csv_atomically(df: pd.DataFrame, output_file: str) -> None:
    """Writes DataFrame to output_file atomically via temp file + os.replace."""
    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w',
                                         encoding='utf-8',
                                         newline='',
                                         dir=output_dir,
                                         prefix='.nas_csv_tmp_',
                                         suffix='.csv',
                                         delete=False) as tmp_file:
            tmp_path = tmp_file.name
            df.to_csv(tmp_file, index=False)
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, output_file)
        logging.info('Wrote %d merged rows atomically to %s', len(df),
                     output_file)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _save_raw_json(raw_source_dir: str, filename: str, api_url: str,
                   query_params: dict[str, Any],
                   raw_pages: list[dict[str, Any]]) -> None:
    """Persists unmodified API JSON page responses for audit and attribution."""
    envelope = {
        'endpoint': api_url,
        'query_params': query_params,
        'pages': raw_pages,
    }
    output_file = os.path.join(raw_source_dir, filename)
    write_text_atomically(
        json.dumps(envelope, ensure_ascii=False, indent=2),
        output_file,
        prefix='.nas_raw_tmp_',
    )
    logging.info('Saved raw API JSON (%d pages) to %s', len(raw_pages),
                 output_file)


def run_download(
    api_url: str = DEFAULT_API_URL,
    gcs_baseline_dir: str = DEFAULT_GCS_BASELINE_DIR,
    places_csv: str = DEFAULT_PLACES_CSV,
    raw_source_dir: str = DEFAULT_RAW_SOURCE_DIR,
    input_dir: str = DEFAULT_INPUT_DIR,
    page_size: int = MAX_PAGE_SIZE,
    timeout_seconds: int = 30,
    max_retries: int = 3,
    retry_delay_seconds: float = 5.0,
    retry_backoff: float = 2.0,
    skip_live_api: bool = False,
    skip_baseline: bool = False,
) -> dict[str, pd.DataFrame]:
    """Executes legacy baseline load, live MoSPI NAS API fetch, merge, and atomic writes."""
    if skip_live_api and skip_baseline:
        raise ValueError(
            'Cannot skip both live API and baseline; at least one source is required.'
        )

    stream_specs: list[tuple[str, list[str], list[str]]] = [
        ('india_nas_gdp.csv', GDP_COLUMNS, GDP_KEY_COLUMNS),
        ('india_nas_gva.csv', GVA_COLUMNS, GVA_KEY_COLUMNS),
        ('india_nas_gva_third_revised.csv', GVA_COLUMNS, GVA_KEY_COLUMNS),
        ('india_nas_gsdp.csv', GSDP_COLUMNS, GSDP_KEY_COLUMNS),
        ('india_nas_gsdp_growth.csv', GSDP_COLUMNS, GSDP_KEY_COLUMNS),
    ]

    if skip_baseline:
        baselines: dict[str, pd.DataFrame | None] = {
            filename: None for filename, _, _ in stream_specs
        }
    else:
        baselines = dict(load_legacy_baselines(gcs_baseline_dir, places_csv))

    live_dfs: dict[str, pd.DataFrame | None] = {
        filename: None for filename, _, _ in stream_specs
    }

    if not skip_live_api:
        with create_session() as session:
            gdp_query = {
                'series': SERIES_CURRENT,
                'base_year': BASE_YEAR_2011_12,
                'frequency_code': FREQUENCY_ANNUAL,
                'indicator_code': INDICATOR_GDP,
            }
            gdp_records, gdp_pages = fetch_paginated_indicator(
                session=session,
                api_url=api_url,
                query_params=gdp_query,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                retry_backoff=retry_backoff,
            )
            _save_raw_json(raw_source_dir, 'nas_gdp_2011_12.json', api_url,
                           gdp_query, gdp_pages)
            live_dfs['india_nas_gdp.csv'] = normalize_gdp_records(gdp_records)

            gva_query = {
                'series': SERIES_CURRENT,
                'base_year': BASE_YEAR_2011_12,
                'frequency_code': FREQUENCY_ANNUAL,
                'indicator_code': INDICATOR_GVA,
            }
            gva_records, gva_pages = fetch_paginated_indicator(
                session=session,
                api_url=api_url,
                query_params=gva_query,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                retry_backoff=retry_backoff,
            )
            _save_raw_json(raw_source_dir, 'nas_gva_2011_12.json', api_url,
                           gva_query, gva_pages)
            gva_std_df, gva_third_df = normalize_gva_records(gva_records)
            live_dfs['india_nas_gva.csv'] = gva_std_df
            live_dfs['india_nas_gva_third_revised.csv'] = gva_third_df

            gsdp_query = {
                'series': SERIES_CURRENT,
                'base_year': BASE_YEAR_2011_12,
                'frequency_code': FREQUENCY_ANNUAL,
                'indicator_code': INDICATOR_GSDP,
            }
            gsdp_records, gsdp_pages = fetch_paginated_indicator(
                session=session,
                api_url=api_url,
                query_params=gsdp_query,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                retry_backoff=retry_backoff,
            )
            _save_raw_json(raw_source_dir, 'nas_gsdp_2011_12.json', api_url,
                           gsdp_query, gsdp_pages)
            live_dfs['india_nas_gsdp.csv'] = normalize_gsdp_records(
                gsdp_records, 'GSDP')

            gsdp_growth_query = {
                'series': SERIES_CURRENT,
                'base_year': BASE_YEAR_2011_12,
                'frequency_code': FREQUENCY_ANNUAL,
                'indicator_code': INDICATOR_GSDP_GROWTH,
            }
            gsdp_growth_records, gsdp_growth_pages = fetch_paginated_indicator(
                session=session,
                api_url=api_url,
                query_params=gsdp_growth_query,
                page_size=page_size,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
                retry_delay_seconds=retry_delay_seconds,
                retry_backoff=retry_backoff,
            )
            _save_raw_json(raw_source_dir, 'nas_gsdp_growth_2011_12.json',
                           api_url, gsdp_growth_query, gsdp_growth_pages)
            live_dfs['india_nas_gsdp_growth.csv'] = normalize_gsdp_records(
                gsdp_growth_records, 'GSDP Growth Rate')

    results: dict[str, pd.DataFrame] = {}
    for filename, cols, key_cols in stream_specs:
        merged = merge_records(
            baseline_df=baselines[filename],
            live_df=live_dfs[filename],
            columns=cols,
            key_columns=key_cols,
        )
        if merged.empty:
            raise RuntimeError(
                f'Merged output for {filename} is empty after baseline/API merge.'
            )
        write_csv_atomically(merged, os.path.join(input_dir, filename))
        results[filename] = merged

    return results


def main(argv: list[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError(f'Unexpected positional arguments: {argv[1:]}')
    run_download(
        api_url=FLAGS.nas_api_url,
        gcs_baseline_dir=FLAGS.nas_gcs_baseline_dir,
        places_csv=FLAGS.nas_places_csv,
        raw_source_dir=FLAGS.nas_raw_source_dir,
        input_dir=FLAGS.nas_input_dir,
        page_size=FLAGS.nas_page_size,
        timeout_seconds=FLAGS.nas_timeout_seconds,
        max_retries=FLAGS.nas_max_retries,
        retry_delay_seconds=FLAGS.nas_retry_delay_seconds,
        retry_backoff=FLAGS.nas_retry_backoff,
        skip_live_api=FLAGS.nas_skip_live_api,
        skip_baseline=FLAGS.nas_skip_baseline,
    )


if __name__ == '__main__':
    _define_flags()
    app.run(main)

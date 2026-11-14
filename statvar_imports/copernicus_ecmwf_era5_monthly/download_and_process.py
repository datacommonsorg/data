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
"""Downloads and preprocesses Copernicus ECMWF ERA5 Monthly data.

Pipeline stages:
1. Syncs historical baseline `.celsius.csv` files (`1979-01..2020-06`) from GCS
   (`gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/`)
   into a separate `history_files/` directory using shared utilities from
   `util/download_util_script.py` and `util/file_util.py`.
2. Fetches monthly observations for `2020-07..latest` from Google Earth Engine
   (`ECMWF/ERA5_LAND/MONTHLY_AGGR`), mapping ERA5-Land band names to canonical
   ERA5 column names, and converts Kelvin temperature columns to Celsius
   matching `kelvin2celsius.sh` (`%.6g` formatting) into `input_files/`.
3. `manifest.json` then executes `tools/statvar_importer/stat_var_processor.py`
   over `history_files/*.celsius.csv,input_files/*.celsius.csv` to emit
   `output/era5_monthly.csv` and `output/era5_monthly.tmcf`.
"""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import csv
import datetime
import glob
import math
import os
import sys
import tempfile
import threading
import time
from typing import Dict, List, Optional, Tuple

from absl import app
from absl import flags
from absl import logging
import requests

try:
    import ee
except ImportError:
    ee = None

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
_UTIL_DIR = os.path.join(_REPO_ROOT, 'util')
for _path in (_REPO_ROOT, _UTIL_DIR):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import download_util_script
import file_util

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'gcs_baseline_prefix',
    'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/',
    'GCS URI prefix containing cached historical .celsius.csv files.',
)
flags.DEFINE_string(
    'history_dir',
    os.path.join(_SCRIPT_DIR, 'history_files'),
    'Directory containing historical baseline .celsius.csv files (1979-01..2020-06).',
)
flags.DEFINE_string(
    'raw_dir',
    os.path.join(_SCRIPT_DIR, 'raw_files'),
    'Directory containing raw Kelvin CSV files from Earth Engine.',
)
flags.DEFINE_string(
    'input_dir',
    os.path.join(_SCRIPT_DIR, 'input_files'),
    'Directory containing newly fetched Kelvin-to-Celsius converted .celsius.csv files.',
)
flags.DEFINE_string(
    'ee_dataset',
    'ECMWF/ERA5_LAND/MONTHLY_AGGR',
    'Earth Engine ImageCollection asset ID for post-2020-06 monthly data.',
)
flags.DEFINE_string(
    'ee_start_date',
    '2020-07',
    'Start year-month (YYYY-MM) for Earth Engine extraction.',
)
flags.DEFINE_string(
    'ee_end_date',
    '',
    'End year-month (YYYY-MM) inclusive for Earth Engine extraction. '
    'Defaults to the previous calendar month.',
)
_DEFAULT_EE_PROJECT = os.environ.get('EE_PROJECT',
                                     'datcom-import-automation-prod')
_DEFAULT_EE_PLACE_ASSETS = [
    asset.strip() for asset in os.environ.get(
        'EE_PLACE_ASSETS',
        f'projects/{_DEFAULT_EE_PROJECT}/assets/all_administrativearea1,'
        f'projects/{_DEFAULT_EE_PROJECT}/assets/all_administrativearea2',
    ).split(',') if asset.strip()
]

flags.DEFINE_string(
    'ee_project',
    _DEFAULT_EE_PROJECT,
    'GCP project ID with Earth Engine API enabled (or set EE_PROJECT env var).',
)
flags.DEFINE_list(
    'ee_place_assets',
    _DEFAULT_EE_PLACE_ASSETS,
    'Earth Engine FeatureCollection assets containing place geometries and dcid '
    '(or set EE_PLACE_ASSETS env var).',
)
flags.DEFINE_integer(
    'reduce_region_scale',
    1000,
    'Scale in meters for ee.Image.reduceRegion().',
)
flags.DEFINE_bool(
    'skip_gcs_baseline',
    False,
    'If True, skip syncing baseline .celsius.csv files (1979-01..2020-06) from GCS.',
)
flags.DEFINE_bool(
    'skip_ee_fetch',
    False,
    'If True, skip fetching new months from Earth Engine.',
)
flags.DEFINE_bool(
    'strict_ee',
    True,
    'If True, fail the run if Earth Engine initialization, fetch, or post-2020-06 '
    'extraction returns empty.',
)
flags.DEFINE_integer(
    'parallelism',
    min(16,
        os.cpu_count() or 4),
    'Number of parallel worker threads for baseline download.',
)
flags.DEFINE_integer(
    'ee_parallelism',
    12,
    'Number of parallel worker threads for Earth Engine monthly fetches.',
)

# Kelvin to Celsius offset matching kelvin2celsius.sh
KELVIN_OFFSET = 273.15

# Maximum number of pixels to consider while reducing each region in Earth Engine.
REDUCE_REGION_MAX_PIXELS = int(1e9)

# Maximum valid area (in sq m) for an AA1/AA2 place; filters broken/inverted/unbounded
# geometries (Earth land area is ~1.49e14 m^2; inverted-winding polygons evaluate to ~5.10e14 m^2).
WORLD_AREA_THRESHOLD = 1.0e14

# Page size for ee.data.computeFeatures pagination to keep per-RPC runtime well below
# Earth Engine's 300s synchronous computeFeatures timeout.
EE_COMPUTE_FEATURES_PAGE_SIZE = 500

# Adaptive reduceRegion scale threshold: ERA5-Land native resolution is ~11.1 km (0.1 deg),
# so regions > 100 km^2 (1e8 m^2) reduce cleanly at 10 km while smaller regions keep --reduce_region_scale.
ADAPTIVE_SCALE_AREA_THRESHOLD = 1e8
ADAPTIVE_LARGE_REGION_SCALE = 10000

# Mapping from ECMWF/ERA5_LAND/MONTHLY_AGGR band names to canonical
# ECMWF/ERA5/MONTHLY column names used in the PVMap and baseline CSVs.
ERA5_LAND_BAND_MAP: Dict[str, str] = OrderedDict([
    ('dewpoint_temperature_2m', 'dewpoint_2m_temperature'),
    ('temperature_2m_max', 'maximum_2m_air_temperature'),
    ('temperature_2m', 'mean_2m_air_temperature'),
    ('temperature_2m_min', 'minimum_2m_air_temperature'),
    ('surface_pressure', 'surface_pressure'),
    ('total_precipitation_sum', 'total_precipitation'),
    ('u_component_of_wind_10m', 'u_component_of_wind_10m'),
    ('v_component_of_wind_10m', 'v_component_of_wind_10m'),
])

ERA5_LAND_MIN_BANDS: List[Tuple[str, str]] = [
    ('temperature_2m_min', 'minimum_2m_air_temperature'),
]

ERA5_LAND_MAX_BANDS: List[Tuple[str, str]] = [
    ('temperature_2m_max', 'maximum_2m_air_temperature'),
]

ERA5_LAND_MEAN_BANDS: List[Tuple[str, str]] = [
    ('dewpoint_temperature_2m', 'dewpoint_2m_temperature'),
    ('temperature_2m', 'mean_2m_air_temperature'),
    ('surface_pressure', 'surface_pressure'),
    ('total_precipitation_sum', 'total_precipitation'),
    ('u_component_of_wind_10m', 'u_component_of_wind_10m'),
    ('v_component_of_wind_10m', 'v_component_of_wind_10m'),
]

CANONICAL_CSV_COLUMNS: List[str] = [
    'system:index',
    'date',
    'dcid',
    'dewpoint_2m_temperature',
    'maximum_2m_air_temperature',
    'mean_2m_air_temperature',
    'minimum_2m_air_temperature',
    'surface_pressure',
    'total_precipitation',
    'u_component_of_wind_10m',
    'v_component_of_wind_10m',
    '.geo',
]


def map_era5_land_columns(columns: List[str]) -> List[str]:
    """Maps ERA5-Land band names in a CSV header to canonical ERA5 column names."""
    return [ERA5_LAND_BAND_MAP.get(col.strip(), col.strip()) for col in columns]


def convert_kelvin_to_celsius_value(value_str: str) -> str:
    """Converts a single Kelvin numeric string to Celsius matching awk's %.6g.

    Matches `kelvin2celsius.sh`: only positive numeric values (`$i > 0`) are
    decremented by 273.15 and formatted with 6 significant digits (`%.6g`).

    Args:
        value_str: Raw string value from a temperature column.

    Returns:
        Converted Celsius string if `value_str` is a float > 0, else `value_str`.
    """
    if not value_str:
        return value_str
    stripped = value_str.strip()
    if not stripped:
        return value_str
    try:
        val = float(stripped)
    except ValueError:
        return value_str
    if math.isfinite(val) and val > 0:
        return f'{val - KELVIN_OFFSET:.6g}'
    return value_str


def convert_kelvin_to_celsius_csv(in_csv_path: str, out_csv_path: str) -> str:
    """Converts temperature columns in `in_csv_path` from Kelvin to Celsius.

    Also normalizes any `ECMWF/ERA5_LAND/MONTHLY_AGGR` band names in the header
    to canonical `ECMWF/ERA5/MONTHLY` column names. Writes atomically via a
    temporary file in the target directory.

    Args:
        in_csv_path: Path to input CSV file with Kelvin temperatures.
        out_csv_path: Destination path for converted `.celsius.csv` file.

    Returns:
        The `out_csv_path` written.
    """
    out_dir = os.path.dirname(os.path.abspath(out_csv_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f'.{os.path.basename(out_csv_path)}.', dir=out_dir)
    os.close(fd)
    try:
        with open(in_csv_path, mode='r', encoding='utf-8',
                  newline='') as in_file, open(tmp_path,
                                               mode='w',
                                               encoding='utf-8',
                                               newline='') as out_file:
            reader = csv.reader(in_file)
            writer = csv.writer(out_file, lineterminator='\n')
            try:
                raw_header = next(reader)
                header = map_era5_land_columns(raw_header)
                writer.writerow(header)
                temp_col_indices = [
                    idx for idx, col_name in enumerate(header)
                    if 'temperature' in col_name
                ]
                for row in reader:
                    for idx in temp_col_indices:
                        if idx < len(row) and row[idx]:
                            row[idx] = convert_kelvin_to_celsius_value(row[idx])
                    writer.writerow(row)
            except StopIteration:
                pass
        os.replace(tmp_path, out_csv_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return out_csv_path


def convert_directory_kelvin_to_celsius(in_dir: str, out_dir: str) -> List[str]:
    """Converts all raw `.csv` files in `in_dir` into `.celsius.csv` in `out_dir`."""
    if not os.path.isdir(in_dir):
        return []
    os.makedirs(out_dir, exist_ok=True)
    converted_files = []
    for entry in sorted(os.listdir(in_dir)):
        if not entry.endswith('.csv') or entry.endswith('.celsius.csv'):
            continue
        in_path = os.path.join(in_dir, entry)
        if not os.path.isfile(in_path):
            continue
        stem = entry[:-4]
        out_path = os.path.join(out_dir, f'{stem}.celsius.csv')
        logging.info('Converting %s -> %s', in_path, out_path)
        convert_kelvin_to_celsius_csv(in_path, out_path)
        converted_files.append(out_path)
    return converted_files


def _parse_gcs_uri(gcs_uri: str) -> Tuple[str, str]:
    """Splits `gs://bucket/prefix` into `(bucket_name, blob_prefix)`."""
    if not gcs_uri.startswith('gs://'):
        raise ValueError(
            f'Invalid GCS URI (must start with gs://): {gcs_uri!r}')
    without_scheme = gcs_uri[len('gs://'):]
    parts = without_scheme.split('/', 1)
    bucket_name = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    if not bucket_name:
        raise ValueError(f'Missing bucket name in GCS URI: {gcs_uri!r}')
    return bucket_name, prefix


def _gcs_uri_to_https_url(gcs_uri: str) -> str:
    """Converts `gs://bucket/path` to `https://storage.googleapis.com/bucket/path`."""
    bucket_name, blob_path = _parse_gcs_uri(gcs_uri)
    return f'https://storage.googleapis.com/{bucket_name}/{blob_path}'


def _download_gcs_file_via_util(
    gcs_uri: str,
    dest_dir: str,
    session: Optional[requests.Session] = None,
    tries: int = 3,
    delay: int = 1,
    backoff: int = 2,
) -> str:
    """Downloads a single GCS URI into `dest_dir` using shared `util/` helpers."""
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(gcs_uri))
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return dest_path
    https_url = _gcs_uri_to_https_url(gcs_uri)
    if download_util_script.download_file(
            url=https_url,
            output_folder=dest_dir,
            unzip=False,
            tries=tries,
            delay=delay,
            backoff=backoff,
            session=session,
    ) and os.path.exists(dest_path):
        return dest_path

    # Fallback to file_util.file_copy for authenticated GCS buckets.
    file_util.file_copy(gcs_uri, dest_path)
    if not os.path.exists(dest_path):
        raise RuntimeError(f'Failed to download {gcs_uri} into {dest_dir}')
    return dest_path


def sync_baseline_from_gcs(
    gcs_prefix: str,
    dest_dir: str,
    max_workers: int = 16,
) -> List[str]:
    """Syncs cached `.celsius.csv` baseline files from GCS into `dest_dir`.

    Uses `file_util.file_get_matching` to discover `.celsius.csv` blobs and
    `download_util_script.download_file` (with `file_util.file_copy` fallback)
    to download them into `dest_dir` (`history_files/`).
    """
    _parse_gcs_uri(gcs_prefix)
    os.makedirs(dest_dir, exist_ok=True)
    gcs_pattern = f"{gcs_prefix.rstrip('/')}/*.celsius.csv"
    logging.info('Listing baseline .celsius.csv files matching %s', gcs_pattern)
    celsius_uris = [
        uri for uri in file_util.file_get_matching(gcs_pattern)
        if uri.endswith('.celsius.csv')
    ]
    if not celsius_uris:
        raise RuntimeError(
            f'No .celsius.csv baseline files found under {gcs_prefix}')

    logging.info('Found %d baseline .celsius.csv files in GCS; syncing to %s',
                 len(celsius_uris), dest_dir)
    downloaded_paths: List[str] = []
    with requests.Session() as session:
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers,
            pool_maxsize=max_workers,
        )
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_uri = {
                executor.submit(
                    _download_gcs_file_via_util,
                    gcs_uri,
                    dest_dir,
                    session,
                ):
                    gcs_uri for gcs_uri in celsius_uris
            }
            for future in as_completed(future_to_uri):
                downloaded_paths.append(future.result())

    downloaded_paths.sort()
    logging.info('Synced %d baseline .celsius.csv files to %s',
                 len(downloaded_paths), dest_dir)
    return downloaded_paths


def generate_year_months(start_ym: str, end_ym: str) -> List[str]:
    """Generates `YYYY-MM` strings from `start_ym` to `end_ym` inclusive."""
    start_dt = datetime.datetime.strptime(start_ym, '%Y-%m')
    end_dt = datetime.datetime.strptime(end_ym, '%Y-%m')
    if start_dt > end_dt:
        return []
    months: List[str] = []
    year, month = start_dt.year, start_dt.month
    while (year, month) <= (end_dt.year, end_dt.month):
        months.append(f'{year:04d}-{month:02d}')
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
    return months


def _next_year_month(ym: str) -> str:
    """Returns the `YYYY-MM` string immediately following `ym`."""
    dt = datetime.datetime.strptime(ym, '%Y-%m')
    if dt.month == 12:
        return f'{dt.year + 1:04d}-01'
    return f'{dt.year:04d}-{dt.month + 1:02d}'


# Trailing calendar-month lag tolerated when --strict_ee=true encounters an
# unpublished latest month in Earth Engine; validation_config.json enforces SLA.
_TRAILING_FRESHNESS_MONTHS = 3


def _subtract_months(year: int, month: int,
                     delta_months: int) -> Tuple[int, int]:
    total_months = year * 12 + (month - 1) - delta_months
    return total_months // 12, total_months % 12 + 1


def _is_within_freshness_window(
    ym: str,
    lag_months: int = _TRAILING_FRESHNESS_MONTHS,
    today: Optional[datetime.date] = None,
) -> bool:
    """Returns True if `ym` is strictly newer than `(today - lag_months)` (`%Y-%m`)."""
    if today is None:
        today = datetime.date.today()
    cutoff_year, cutoff_month = _subtract_months(today.year, today.month,
                                                 lag_months)
    cutoff_ym = f'{cutoff_year:04d}-{cutoff_month:02d}'
    return ym > cutoff_ym


def _default_end_year_month(today: Optional[datetime.date] = None) -> str:
    """Returns the previous calendar month in `YYYY-MM` format."""
    if today is None:
        today = datetime.date.today()
    first_of_month = today.replace(day=1)
    prev_month_last_day = first_of_month - datetime.timedelta(days=1)
    return prev_month_last_day.strftime('%Y-%m')


def _fetch_ee_feature_collection(
    flattened,
    page_size: int = EE_COMPUTE_FEATURES_PAGE_SIZE,
) -> Optional[dict]:
    """Fetches all features from an `ee.FeatureCollection`, paginating if supported.

    `FeatureCollection.getInfo()` calls `ee.data.computeValue`, which aborts at
    5,000 elements (`all_administrativearea2` has 5,574+ features). When
    `ee.data.computeFeatures` is available, this paginates with `nextPageToken`
    and explicit `pageSize` to retrieve all features without hitting element or
    synchronous timeout limits.
    """
    if ee is not None and hasattr(ee, 'data') and hasattr(
            ee.data, 'computeFeatures'):
        features = []
        page_token = None
        while True:
            params = {'expression': flattened, 'pageSize': page_size}
            if page_token:
                params['pageToken'] = page_token
            page = ee.data.computeFeatures(params)
            if not isinstance(page, dict):
                return flattened.getInfo()
            features.extend(page.get('features', []))
            page_token = page.get('nextPageToken')
            if not page_token:
                break
        return {'type': 'FeatureCollection', 'features': features}
    return flattened.getInfo()


def _compute_ee_monthly_features(
    dataset_asset: str,
    geo_locations_asset: str,
    year_month: str,
    reduce_region_scale: int,
) -> Optional[dict]:
    """Computes ERA5-Land monthly aggregations in Earth Engine for one month."""
    if ee is None:
        raise RuntimeError('earthengine-api (ee) is not installed.')

    start_date = f'{year_month}-01'
    end_date = f'{_next_year_month(year_month)}-01'
    dataset = ee.ImageCollection(dataset_asset).filterDate(start_date, end_date)
    first_image_info = dataset.first().getInfo()
    if not first_image_info:
        logging.warning('No image found in %s for %s', dataset_asset,
                        year_month)
        return None

    places = ee.FeatureCollection(geo_locations_asset)
    if not places.first().getInfo():
        raise FileNotFoundError(
            f'Earth Engine FeatureCollection not found: {geo_locations_asset}')

    world_area_threshold = ee.Number(WORLD_AREA_THRESHOLD)
    min_src = [src for src, _ in ERA5_LAND_MIN_BANDS]
    min_dst = [dst for _, dst in ERA5_LAND_MIN_BANDS]
    max_src = [src for src, _ in ERA5_LAND_MAX_BANDS]
    max_dst = [dst for _, dst in ERA5_LAND_MAX_BANDS]
    mean_src = [src for src, _ in ERA5_LAND_MEAN_BANDS]
    mean_dst = [dst for _, dst in ERA5_LAND_MEAN_BANDS]

    def _handle_place(place):
        geom = place.geometry()
        area = geom.area(maxError=1000)
        is_oversized = area.lte(0).Or(area.gt(world_area_threshold))
        effective_scale = ee.Algorithms.If(
            area.gt(ADAPTIVE_SCALE_AREA_THRESHOLD),
            max(reduce_region_scale, ADAPTIVE_LARGE_REGION_SCALE),
            reduce_region_scale,
        )

        def _handle_image(image):
            result = ee.Feature(
                None,
                {
                    'dcid': place.get('dcid'),
                    'date': image.date().format('YYYY-MM'),
                },
            )
            # Use unweighted mean so it selects the exact same pixel-center set as
            # min/max reducers, preventing small/coastal places from getting mean
            # values without min/max (which fails NUM_PLACES_CONSISTENT).
            for src_bands, dst_bands, reducer in [
                (min_src, min_dst, ee.Reducer.min()),
                (max_src, max_dst, ee.Reducer.max()),
                (mean_src, mean_dst, ee.Reducer.mean().unweighted()),
            ]:
                aggr = ee.Algorithms.If(
                    is_oversized,
                    ee.Dictionary(),
                    image.select(src_bands, dst_bands).reduceRegion(
                        reducer=reducer,
                        geometry=geom,
                        scale=effective_scale,
                        maxPixels=REDUCE_REGION_MAX_PIXELS,
                    ),
                )
                result = result.copyProperties(ee.Feature(None, aggr))
            return result

        return dataset.map(_handle_image)

    flattened = places.map(_handle_place).flatten()
    return _fetch_ee_feature_collection(flattened)


def _is_permission_or_auth_error(exc: Exception) -> bool:
    """Returns True if `exc` indicates a permanent IAM permission or auth failure."""
    text = str(exc).lower()
    return any(token in text for token in (
        '403',
        '401',
        'permission',
        'forbidden',
        'denied',
        'not authorized',
        'unauthenticated',
    ))


def _compute_ee_monthly_features_with_retry(
    dataset_asset: str,
    geo_locations_asset: str,
    year_month: str,
    reduce_region_scale: int,
    max_attempts: int = 3,
    initial_delay_secs: float = 2.0,
) -> Optional[dict]:
    """Computes ERA5-Land monthly features in Earth Engine with exponential backoff."""
    delay = initial_delay_secs
    for attempt in range(1, max_attempts + 1):
        try:
            return _compute_ee_monthly_features(
                dataset_asset=dataset_asset,
                geo_locations_asset=geo_locations_asset,
                year_month=year_month,
                reduce_region_scale=reduce_region_scale,
            )
        except FileNotFoundError:
            raise
        except Exception as exc:
            if attempt == max_attempts or _is_permission_or_auth_error(exc):
                raise
            logging.warning(
                'Transient Earth Engine error for asset=%s month=%s '
                '(attempt %d/%d): %s; retrying in %.1fs',
                geo_locations_asset,
                year_month,
                attempt,
                max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)
            delay *= 2.0
    return None


def write_ee_feature_collection_to_csv(
    fc_info: dict,
    out_csv_path: str,
) -> int:
    """Writes an Earth Engine FeatureCollection dict to a canonical Kelvin CSV."""
    features = fc_info.get('features', []) if fc_info else []
    out_dir = os.path.dirname(os.path.abspath(out_csv_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f'.{os.path.basename(out_csv_path)}.', dir=out_dir)
    os.close(fd)
    try:
        with open(tmp_path, mode='w', encoding='utf-8', newline='') as out_file:
            writer = csv.DictWriter(
                out_file,
                fieldnames=CANONICAL_CSV_COLUMNS,
                extrasaction='ignore',
                lineterminator='\n',
            )
            writer.writeheader()
            for feature in features:
                props = dict(feature.get('properties', {}))
                # Normalize any ERA5-Land band names if present in properties.
                normalized_row = {
                    'system:index': feature.get('id', ''),
                    '.geo': '{"type":"MultiPoint","coordinates":[]}',
                }
                for key, val in props.items():
                    canonical_key = ERA5_LAND_BAND_MAP.get(key, key)
                    normalized_row[canonical_key] = '' if val is None else val
                writer.writerow(normalized_row)
        os.replace(tmp_path, out_csv_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return len(features)


def _fetch_single_ee_month(
    dataset_asset: str,
    place_asset: str,
    ym: str,
    raw_path: str,
    celsius_path: str,
    ee_project: str,
    reduce_region_scale: int,
    strict: bool,
    auth_failed_event: threading.Event,
) -> Optional[str]:
    """Fetches and converts one `(place_asset, ym)` pair from Earth Engine."""
    if auth_failed_event.is_set():
        return None
    try:
        logging.info(
            'Computing Earth Engine ERA5-Land stats for asset=%s month=%s',
            place_asset,
            ym,
        )
        fc_info = _compute_ee_monthly_features_with_retry(
            dataset_asset=dataset_asset,
            geo_locations_asset=place_asset,
            year_month=ym,
            reduce_region_scale=reduce_region_scale,
        )
        if not fc_info or not fc_info.get('features'):
            msg = f'No features returned for asset={place_asset} month={ym}'
            if strict and not _is_within_freshness_window(ym):
                raise RuntimeError(msg)
            logging.warning('%s', msg)
            return None
        write_ee_feature_collection_to_csv(fc_info, raw_path)
        convert_kelvin_to_celsius_csv(raw_path, celsius_path)
        return celsius_path
    except Exception as exc:
        if strict:
            raise
        if _is_permission_or_auth_error(exc):
            auth_failed_event.set()
            logging.warning(
                'Earth Engine permission/authentication error for project %r '
                '(asset=%s month=%s): %s; skipping remaining Earth Engine '
                'fetches and continuing with cached/existing files.',
                ee_project,
                place_asset,
                ym,
                exc,
            )
            return None
        logging.warning(
            'Failed fetching Earth Engine asset=%s month=%s: %s',
            place_asset,
            ym,
            exc,
        )
        return None


def fetch_era5_land_from_ee(
    dataset_asset: str,
    place_assets: List[str],
    start_ym: str,
    end_ym: str,
    raw_dir: str,
    input_dir: str,
    ee_project: str,
    reduce_region_scale: int,
    strict: bool = False,
    ee_parallelism: int = 12,
) -> List[str]:
    """Fetches `start_ym..end_ym` from Earth Engine and converts to `.celsius.csv`."""
    if not end_ym:
        end_ym = _default_end_year_month()
    year_months = generate_year_months(start_ym, end_ym)
    if not year_months or not place_assets:
        logging.info('No Earth Engine months/assets to fetch for range %s..%s',
                     start_ym, end_ym)
        return []

    if ee is None:
        msg = (
            'earthengine-api is not available; skipping live Earth Engine fetch '
            f'for {start_ym}..{end_ym}.')
        if strict:
            raise RuntimeError(msg)
        logging.warning(msg)
        return []

    try:
        ee.Initialize(project=ee_project)
    except Exception:
        try:
            import google.auth
            credentials, _ = google.auth.default(scopes=[
                'https://www.googleapis.com/auth/earthengine',
                'https://www.googleapis.com/auth/cloud-platform',
            ])
            ee.Initialize(credentials=credentials, project=ee_project)
        except Exception as exc:
            msg = (
                f'Unable to initialize Earth Engine for project {ee_project!r}: {exc}'
            )
            if strict:
                raise RuntimeError(msg) from exc
            logging.warning('%s; continuing with cached/existing files.', msg)
            return []

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)
    generated_celsius_files: List[str] = []
    pending_tasks: List[Tuple[str, str, str, str]] = []

    for place_asset in place_assets:
        asset_name = os.path.basename(place_asset.rstrip('/'))
        for ym in year_months:
            celsius_filename = f'{asset_name}_{ym}.ee.celsius.csv'
            celsius_path = os.path.join(input_dir, celsius_filename)
            if os.path.exists(celsius_path) and os.path.getsize(
                    celsius_path) > 0:
                logging.info('Skipping already-fetched %s', celsius_path)
                generated_celsius_files.append(celsius_path)
                continue

            raw_filename = f'{asset_name}_{ym}.ee.csv'
            raw_path = os.path.join(raw_dir, raw_filename)
            pending_tasks.append((place_asset, ym, raw_path, celsius_path))

    if not pending_tasks:
        return sorted(generated_celsius_files)

    auth_failed_event = threading.Event()
    # Execute the first pending task upfront to fail fast on permission/auth errors.
    first_asset, first_ym, first_raw, first_celsius = pending_tasks[0]
    first_result = _fetch_single_ee_month(
        dataset_asset=dataset_asset,
        place_asset=first_asset,
        ym=first_ym,
        raw_path=first_raw,
        celsius_path=first_celsius,
        ee_project=ee_project,
        reduce_region_scale=reduce_region_scale,
        strict=strict,
        auth_failed_event=auth_failed_event,
    )
    if first_result:
        generated_celsius_files.append(first_result)

    remaining_tasks = pending_tasks[1:]
    if remaining_tasks and not auth_failed_event.is_set():
        workers = max(1, min(ee_parallelism, len(remaining_tasks)))
        if workers == 1:
            for place_asset, ym, raw_path, celsius_path in remaining_tasks:
                res = _fetch_single_ee_month(
                    dataset_asset=dataset_asset,
                    place_asset=place_asset,
                    ym=ym,
                    raw_path=raw_path,
                    celsius_path=celsius_path,
                    ee_project=ee_project,
                    reduce_region_scale=reduce_region_scale,
                    strict=strict,
                    auth_failed_event=auth_failed_event,
                )
                if res:
                    generated_celsius_files.append(res)
                if auth_failed_event.is_set():
                    break
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        _fetch_single_ee_month,
                        dataset_asset,
                        place_asset,
                        ym,
                        raw_path,
                        celsius_path,
                        ee_project,
                        reduce_region_scale,
                        strict,
                        auth_failed_event,
                    ) for place_asset, ym, raw_path, celsius_path in
                    remaining_tasks
                ]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        generated_celsius_files.append(res)

    if strict and not generated_celsius_files:
        raise RuntimeError(
            f'No Earth Engine data fetched for range {start_ym}..{end_ym} '
            f'(project={ee_project!r}).')

    return sorted(generated_celsius_files)


def run_pipeline(
    gcs_baseline_prefix: str,
    history_dir: str,
    raw_dir: str,
    input_dir: str,
    ee_dataset: str,
    ee_place_assets: List[str],
    ee_start_date: str,
    ee_end_date: str,
    ee_project: str,
    reduce_region_scale: int,
    skip_gcs_baseline: bool,
    skip_ee_fetch: bool,
    strict_ee: bool,
    parallelism: int,
    ee_parallelism: int = 12,
) -> Tuple[List[str], List[str]]:
    """Runs baseline download into `history_dir` and EE fetch/conversion into `input_dir`.

    Returns:
        Tuple of `(history_celsius_files, input_celsius_files)`.
    """
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)

    if not skip_gcs_baseline:
        sync_baseline_from_gcs(
            gcs_prefix=gcs_baseline_prefix,
            dest_dir=history_dir,
            max_workers=max(4, parallelism),
        )

    # Convert any pre-staged raw Kelvin CSVs in raw_dir into input_dir.
    if os.path.isdir(raw_dir):
        convert_directory_kelvin_to_celsius(raw_dir, input_dir)

    if not skip_ee_fetch:
        fetch_era5_land_from_ee(
            dataset_asset=ee_dataset,
            place_assets=ee_place_assets,
            start_ym=ee_start_date,
            end_ym=ee_end_date,
            raw_dir=raw_dir,
            input_dir=input_dir,
            ee_project=ee_project,
            reduce_region_scale=reduce_region_scale,
            strict=strict_ee,
            ee_parallelism=ee_parallelism,
        )

    history_files = sorted(glob.glob(os.path.join(history_dir,
                                                  '*.celsius.csv')))
    input_files = sorted(glob.glob(os.path.join(input_dir, '*.celsius.csv')))
    if not history_files and not input_files:
        raise RuntimeError(
            f'No .celsius.csv files found in {history_dir} or {input_dir}')

    logging.info(
        'Prepared %d historical .celsius.csv files in %s and %d new .celsius.csv files in %s',
        len(history_files),
        history_dir,
        len(input_files),
        input_dir,
    )
    return history_files, input_files


def main(_):
    ee_place_assets = FLAGS.ee_place_assets
    if (not FLAGS['ee_place_assets'].present and
            not os.environ.get('EE_PLACE_ASSETS')):
        ee_place_assets = [
            f'projects/{FLAGS.ee_project}/assets/all_administrativearea1',
            f'projects/{FLAGS.ee_project}/assets/all_administrativearea2',
        ]
    run_pipeline(
        gcs_baseline_prefix=FLAGS.gcs_baseline_prefix,
        history_dir=FLAGS.history_dir,
        raw_dir=FLAGS.raw_dir,
        input_dir=FLAGS.input_dir,
        ee_dataset=FLAGS.ee_dataset,
        ee_place_assets=ee_place_assets,
        ee_start_date=FLAGS.ee_start_date,
        ee_end_date=FLAGS.ee_end_date,
        ee_project=FLAGS.ee_project,
        reduce_region_scale=FLAGS.reduce_region_scale,
        skip_gcs_baseline=FLAGS.skip_gcs_baseline,
        skip_ee_fetch=FLAGS.skip_ee_fetch,
        strict_ee=FLAGS.strict_ee,
        parallelism=FLAGS.parallelism,
        ee_parallelism=FLAGS.ee_parallelism,
    )


if __name__ == '__main__':
    app.run(main)

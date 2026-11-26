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
"""Automated download and place-rollup script for DynamicWorld_FloodEvents_Places_AutoRefresh.

Downloads monthly flood extent GeoTIFF tiles directly from Google Earth Engine's
Dynamic World V1 catalog (`GOOGLE/DYNAMICWORLD/V1`) masked against permanent
water (`UMD/hansen/global_forest_change_2025_v1_13`), converts rasters to S2
Level-13 CSVs (`scripts/earthengine/raster_to_csv.py`), and aggregates flood
events & place-level SVObs (`s2CellId/*`, `country/*`, `Earth`, continents, and
administrative areas for `P1M` and `P1Y`) via `scripts/earthengine/process_events.py`
using the parameters from `scripts/floods/flood_events_pipeline_config.py`.
"""

from concurrent import futures
import csv
import datetime
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from absl import app
from absl import flags
from absl import logging
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
_UTIL_DIR = os.path.join(_REPO_ROOT, 'util')
_EE_SCRIPTS_DIR = os.path.join(_REPO_ROOT, 'scripts', 'earthengine')
_FLOODS_SCRIPTS_DIR = os.path.join(_REPO_ROOT, 'scripts', 'floods')

for _path in (_REPO_ROOT, _UTIL_DIR, _EE_SCRIPTS_DIR):
    if _path not in sys.path:
        sys.path.append(_path)

import download_util_script  # pylint: disable=wrong-import-position

_DW_COLLECTION_ID = 'GOOGLE/DYNAMICWORLD/V1'
_DEFAULT_LAND_MASK_ASSET = 'UMD/hansen/global_forest_change_2025_v1_13'
_DEFAULT_BOUNDS = '-60,-180,75,180'
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')
_DEFAULT_GCS_MOUNT_DIR = os.path.join(_SCRIPT_DIR, 'gcs_folder')
_DEFAULT_PLACE_CACHE_FILE = (
    'gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl'
)
_DEFAULT_LEGACY_RASTER_GCS_PREFIX = (
    'gs://datcom-prod-imports/scripts/floods/raster_csv')
_LEGACY_RASTER_FILENAME_TEMPLATE = (
    'ee_image_dynamic_world-band_water-r_max-mask_land-s_1000-from_'
    '{month}-01-raster_csv.csv')
_DEFAULT_PIPELINE_CONFIG = os.path.join(_FLOODS_SCRIPTS_DIR,
                                        'flood_events_pipeline_config.py')
_CONSOLIDATED_FILENAME = 'dynamicworld_floodevents_places_svobs.csv'
_PLACE_SVOBS_HEADER = [
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'area',
    'count',
]

_DEFAULT_SUBPROCESS_TIMEOUT_SECS = 10800

_FLAGS = flags.FLAGS
_EE_INIT_LOCK = threading.Lock()
_THREAD_LOCAL = threading.local()


def _define_flags():
    flags.DEFINE_string(
        'start_date',
        '',
        'Start date (YYYY-MM-DD, inclusive) for Earth Engine Dynamic World query. '
        'Defaults to Jan 1 of the current YTD cycle (prior year Jan 1 in January).',
    )
    flags.DEFINE_string(
        'end_date',
        '',
        'End date (YYYY-MM-DD, exclusive) for Earth Engine Dynamic World query. '
        'Defaults to the first day of the current calendar month.',
    )
    flags.DEFINE_string(
        'bounds',
        _DEFAULT_BOUNDS,
        'Geographic bounding box "south,west,north,east" in degrees for Earth '
        'Engine GeoTIFF tiling.',
    )
    flags.DEFINE_float(
        'tile_size_deg',
        4.0,
        'Maximum tile width/height in degrees per Earth Engine getDownloadURL '
        'request so each tile completes well within HTTP size/timeout limits.',
    )
    flags.DEFINE_integer(
        'max_workers',
        10,
        'Maximum concurrent Earth Engine tile download workers.',
    )
    flags.DEFINE_integer(
        'scale',
        1000,
        'Spatial resolution in meters for Earth Engine GeoTIFF downloads.',
    )
    flags.DEFINE_float(
        'water_threshold',
        0.7,
        'Minimum Dynamic World water band probability to classify a flooded pixel.',
    )
    flags.DEFINE_string(
        'land_mask_asset',
        _DEFAULT_LAND_MASK_ASSET,
        'Hansen Global Forest Change Earth Engine asset for masking permanent water.',
    )
    flags.DEFINE_string(
        'ee_project',
        '',
        'GCP project ID with Earth Engine API enabled. Defaults to '
        'GOOGLE_CLOUD_PROJECT, ADC project, or datcom-import-automation-prod.',
    )
    flags.DEFINE_string(
        'output_dir',
        _DEFAULT_OUTPUT_DIR,
        'Local output directory where downloaded files and CSVs are saved.',
    )
    flags.DEFINE_string(
        'cache_dir',
        '',
        'Persistent directory (such as the executor-mounted gcs_folder) used to '
        'cache monthly raster CSVs and completed annual place_svobs CSVs across '
        'runs for global default bounds. Auto-uses ./gcs_folder if present.',
    )
    flags.DEFINE_string(
        'legacy_raster_gcs_prefix',
        _DEFAULT_LEGACY_RASTER_GCS_PREFIX,
        'Optional GCS prefix containing existing legacy monthly raster CSVs '
        '(used via object-only reads for global default bounds to bootstrap YTD '
        'months without re-downloading from Earth Engine).',
    )
    flags.DEFINE_bool(
        'carry_forward_prior_years',
        True,
        'Carry forward cached prior-year annual place_svobs CSVs from --cache_dir '
        'when running with global default bounds so year rollovers do not delete '
        'prior years.',
    )
    flags.DEFINE_string(
        'consolidated_csv',
        _CONSOLIDATED_FILENAME,
        'Filename inside --output_dir for the consolidated place SVObs CSV.',
    )
    flags.DEFINE_string(
        'place_cache_file',
        _DEFAULT_PLACE_CACHE_FILE,
        'Path (local or gs://) to place_properties_cache_with_s2_10.pkl '
        'for parent administrative/country/Earth rollups during event processing.',
    )
    flags.DEFINE_bool(
        'convert_to_csv',
        True,
        'Convert downloaded GeoTIFFs locally into S2 cell CSVs and place SVObs CSVs.',
    )
    flags.DEFINE_bool(
        'use_gcs_cache',
        True,
        'Reuse persistent monthly raster CSVs from --cache_dir (gcs_folder) '
        'and legacy prod GCS bootstrap when running with global default bounds.',
    )
    flags.DEFINE_bool(
        'skip_existing',
        False,
        'Reuse existing local intermediate GeoTIFF/raster_csv files in '
        '--output_dir instead of cleaning them at startup.',
    )
    flags.DEFINE_integer(
        'subprocess_timeout_secs',
        _DEFAULT_SUBPROCESS_TIMEOUT_SECS,
        'Timeout in seconds for raster_to_csv.py and process_events.py subprocesses.',
    )


def default_month_date_range(
    reference_date: Optional[datetime.date] = None,) -> Tuple[str, str]:
    """Returns (start_date, end_date) for the previous complete calendar month."""
    today = reference_date or datetime.date.today()
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - datetime.timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev.strftime('%Y-%m-%d'), first_of_current.strftime(
        '%Y-%m-%d')


def default_ytd_date_range(
    reference_date: Optional[datetime.date] = None,) -> Tuple[str, str]:
    """Returns (start_date, end_date) covering complete YTD calendar months.

    In January, returns the full previous calendar year (Jan 1..Jan 1) so
    December's final refresh completes the prior year's annual rollup.
    """
    today = reference_date or datetime.date.today()
    first_of_current = today.replace(day=1)
    if first_of_current.month == 1:
        start = first_of_current.replace(year=first_of_current.year - 1,
                                         month=1)
    else:
        start = first_of_current.replace(month=1)
    return start.strftime('%Y-%m-%d'), first_of_current.strftime('%Y-%m-%d')


def _next_month_start(dt: datetime.date) -> datetime.date:
    if dt.month == 12:
        return datetime.date(dt.year + 1, 1, 1)
    return datetime.date(dt.year, dt.month + 1, 1)


def iter_month_ranges(
    start_date: str,
    end_date: str,
) -> List[Tuple[str, str]]:
    """Splits [start_date, end_date) into per-month (start, end) ISO strings."""
    start_dt = datetime.date.fromisoformat(start_date)
    end_dt = datetime.date.fromisoformat(end_date)
    if start_dt >= end_dt:
        raise ValueError(
            f'start_date ({start_date}) must be strictly before end_date ({end_date})'
        )
    ranges: List[Tuple[str, str]] = []
    cur = start_dt
    while cur < end_dt:
        nxt = min(end_dt, _next_month_start(cur.replace(day=1)))
        ranges.append((cur.strftime('%Y-%m-%d'), nxt.strftime('%Y-%m-%d')))
        cur = nxt
    return ranges


def parse_bounds(bounds_str: str) -> Tuple[float, float, float, float]:
    """Parses 'south,west,north,east' into validated float coordinates."""
    parts = [p.strip() for p in bounds_str.split(',') if p.strip()]
    if len(parts) != 4:
        raise ValueError(
            f'Expected "south,west,north,east" bounds, got: {bounds_str!r}')
    south, west, north, east = (float(p) for p in parts)
    if not (-90.0 <= south < north <= 90.0):
        raise ValueError(
            f'Invalid latitude bounds (require -90 <= south < north <= 90): '
            f'{bounds_str!r}')
    if not (-180.0 <= west < east <= 180.0):
        raise ValueError(
            f'Invalid longitude bounds (require -180 <= west < east <= 180): '
            f'{bounds_str!r}')
    return south, west, north, east


def _is_default_global_bounds(bounds_str: str) -> bool:
    """Returns True if bounds_str matches the default global bounding box."""
    return parse_bounds(bounds_str) == parse_bounds(_DEFAULT_BOUNDS)


def generate_tiles(
    south: float,
    west: float,
    north: float,
    east: float,
    tile_size_deg: float,
) -> List[Tuple[float, float, float, float]]:
    """Splits a bounding box into sub-tiles of at most tile_size_deg."""
    if tile_size_deg < 1e-4:
        raise ValueError(
            f'tile_size_deg must be at least 1e-4 to avoid infinite loops due '
            f'to rounding, got {tile_size_deg}')
    tiles: List[Tuple[float, float, float, float]] = []
    lat = south
    while lat < north - 1e-9:
        lat_top = min(north, round(lat + tile_size_deg, 6))
        lon = west
        while lon < east - 1e-9:
            lon_right = min(east, round(lon + tile_size_deg, 6))
            tiles.append((round(lat, 6), round(lon, 6), lat_top, lon_right))
            lon = lon_right
        lat = lat_top
    return tiles


def resolve_ee_project_and_credentials(explicit_project: str = ''):
    """Resolves ADC credentials and GCP billing/EE project ID."""
    creds, adc_project = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/earthengine',
        'https://www.googleapis.com/auth/cloud-platform',
    ])
    creds.refresh(GoogleAuthRequest())
    project = (explicit_project or os.environ.get('GOOGLE_CLOUD_PROJECT', '') or
               adc_project or 'datcom-import-automation-prod')
    return creds, project


def init_earth_engine(explicit_project: str = ''):
    """Initializes the Earth Engine SDK with ADC credentials."""
    import ee  # pylint: disable=import-outside-toplevel

    with _EE_INIT_LOCK:
        creds, project = resolve_ee_project_and_credentials(explicit_project)
        logging.info('Initializing Earth Engine with project %s', project)
        ee.Initialize(credentials=creds, project=project)
        return ee


def build_dynamic_world_flood_image(
    ee_module,
    start_date: str,
    end_date: str,
    region_geometry,
    water_threshold: float = 0.7,
    land_mask_asset: str = _DEFAULT_LAND_MASK_ASSET,
):
    """Builds a binary non-permanent water image from GOOGLE/DYNAMICWORLD/V1."""
    dw_water = (ee_module.ImageCollection(_DW_COLLECTION_ID).filterDate(
        start_date, end_date).filterBounds(region_geometry).select('water').map(
            lambda img: img.gte(water_threshold).rename('water')).max())
    if land_mask_asset:
        land_mask = ee_module.Image(land_mask_asset).select('datamask').eq(1)
        dw_water = dw_water.updateMask(land_mask)
    # Unmask to 0 before exporting so masked ocean/dry pixels become 0.0
    # rather than -inf nodata, which scripts/earthengine/raster_to_csv.py
    # would otherwise process via `np.where(arr != 0)`.
    return dw_water.unmask(0).toFloat()


def _tile_has_flood_pixels(tif_path: str) -> bool:
    """Returns True if a GeoTIFF tile contains at least one flood pixel (>= 1)."""
    import numpy as np
    import rasterio

    with rasterio.open(tif_path) as src:
        band = src.read(1)
        return bool(np.any(np.isfinite(band) & (band >= 1.0)))


def _sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}{parsed.path}'


def _get_http_session() -> requests.Session:
    """Returns a reusable per-thread requests.Session for tile downloads."""
    session = getattr(_THREAD_LOCAL, 'session', None)
    if session is None:
        session = requests.Session()
        _THREAD_LOCAL.session = session
    return session


def _csv_has_data_rows(csv_path: str) -> bool:
    """Returns True if csv_path exists and has at least one non-header row."""
    if not csv_path or not os.path.exists(csv_path) or os.path.getsize(
            csv_path) == 0:
        return False
    with open(csv_path, 'r', encoding='utf-8', newline='') as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if not header:
            return False
        return next(reader, None) is not None


def _download_with_util_atomic(
    url: str,
    target_path: str,
    headers: Optional[Dict[str, str]] = None,
    tries: int = 3,
    delay: int = 5,
    backoff: int = 2,
    session: Optional[requests.Session] = None,
) -> bool:
    """Downloads a URL via download_util_script and moves it atomically."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    http_session = session or _get_http_session()
    with tempfile.TemporaryDirectory(dir=os.path.dirname(target_path),
                                     prefix='.dw_dl_') as tmp_dir:
        ok = download_util_script.download_file(
            url=url,
            output_folder=tmp_dir,
            unzip=False,
            headers=headers,
            tries=tries,
            delay=delay,
            backoff=backoff,
            session=http_session,
        )
        if not ok:
            return False
        downloaded_files = [
            f for f in os.listdir(tmp_dir)
            if os.path.isfile(os.path.join(tmp_dir, f))
        ]
        if not downloaded_files:
            return False
        src_file = os.path.join(tmp_dir, downloaded_files[0])
        if os.path.getsize(src_file) == 0:
            logging.warning('Downloaded empty file for %s', target_path)
            return False
        os.replace(src_file, target_path)
        return True


def _format_tile_name(
    start_date: str,
    end_date: str,
    tile: Tuple[float, float, float, float],
) -> str:
    south, west, north, east = tile
    return f'dw_flood_{start_date}_{end_date}_{south}_{west}_{north}_{east}.tif'


def _download_single_tile(
    idx: int,
    total_tiles: int,
    tile: Tuple[float, float, float, float],
    geotiff_dir: str,
    start_date: str,
    end_date: str,
    scale: int,
    water_threshold: float,
    land_mask_asset: str,
    skip_existing: bool,
    retry_tries: int,
    retry_delay: int,
    retry_backoff: int,
    ee_module,
) -> Optional[str]:
    """Downloads one GeoTIFF tile or returns None if the tile has no imagery."""
    tile_path = os.path.join(geotiff_dir,
                             _format_tile_name(start_date, end_date, tile))
    if skip_existing and os.path.exists(tile_path) and os.path.getsize(
            tile_path) > 0:
        if not _tile_has_flood_pixels(tile_path):
            os.remove(tile_path)
            return None
        logging.info('[%d/%d] Skipping existing tile: %s', idx, total_tiles,
                     tile_path)
        return tile_path

    t_south, t_west, t_north, t_east = tile
    region = ee_module.Geometry.Rectangle([t_west, t_south, t_east, t_north])
    image = build_dynamic_world_flood_image(
        ee_module=ee_module,
        start_date=start_date,
        end_date=end_date,
        region_geometry=region,
        water_threshold=water_threshold,
        land_mask_asset=land_mask_asset,
    )

    last_error = None
    url = ''
    current_delay = retry_delay
    for attempt in range(1, retry_tries + 1):
        try:
            url = image.getDownloadURL({
                'scale': scale,
                'crs': 'EPSG:4326',
                'region': region,
                'format': 'GEO_TIFF',
            })
            break
        except Exception as exc:  # pylint: disable=broad-except
            if 'no bands' in str(exc).lower():
                logging.debug(
                    '[%d/%d] No Dynamic World imagery for tile %s in [%s, %s); skipping.',
                    idx,
                    total_tiles,
                    tile,
                    start_date,
                    end_date,
                )
                return None
            last_error = exc
            logging.warning(
                'Tile %d/%d getDownloadURL attempt %d/%d failed: %s',
                idx,
                total_tiles,
                attempt,
                retry_tries,
                exc,
            )
            if attempt < retry_tries:
                time.sleep(current_delay)
                current_delay *= retry_backoff

    if not url:
        raise RuntimeError(
            f'Failed to get Earth Engine download URL for tile {tile}: {last_error}'
        )

    logging.info(
        '[%d/%d] Downloading tile %s from %s',
        idx,
        total_tiles,
        os.path.basename(tile_path),
        _sanitize_url(url),
    )
    if _download_with_util_atomic(
            url=url,
            target_path=tile_path,
            tries=retry_tries,
            delay=retry_delay,
            backoff=retry_backoff,
    ):
        if not _tile_has_flood_pixels(tile_path):
            logging.debug(
                '[%d/%d] Tile %s has no flood pixels; removing.',
                idx,
                total_tiles,
                os.path.basename(tile_path),
            )
            os.remove(tile_path)
            return None
        return tile_path
    raise RuntimeError(f'Download failed for Earth Engine tile {tile}')


def download_earthengine_tiles(
    output_dir: str,
    start_date: str,
    end_date: str,
    bounds_str: str,
    tile_size_deg: float = 4.0,
    scale: int = 1000,
    water_threshold: float = 0.7,
    land_mask_asset: str = _DEFAULT_LAND_MASK_ASSET,
    ee_project: str = '',
    skip_existing: bool = False,
    retry_tries: int = 3,
    retry_delay: int = 5,
    retry_backoff: int = 2,
    max_workers: int = 10,
    ee_module=None,
) -> List[str]:
    """Downloads GeoTIFF flood tiles directly from GOOGLE/DYNAMICWORLD/V1."""
    south, west, north, east = parse_bounds(bounds_str)
    tiles = generate_tiles(south, west, north, east, tile_size_deg)
    geotiff_dir = os.path.join(output_dir, 'geotiff')
    os.makedirs(geotiff_dir, exist_ok=True)

    if ee_module is None:
        ee_module = init_earth_engine(ee_project)

    workers = max(1, min(max_workers, len(tiles)))
    results: Dict[int, str] = {}
    if workers == 1:
        for idx, tile in enumerate(tiles, start=1):
            path = _download_single_tile(
                idx=idx,
                total_tiles=len(tiles),
                tile=tile,
                geotiff_dir=geotiff_dir,
                start_date=start_date,
                end_date=end_date,
                scale=scale,
                water_threshold=water_threshold,
                land_mask_asset=land_mask_asset,
                skip_existing=skip_existing,
                retry_tries=retry_tries,
                retry_delay=retry_delay,
                retry_backoff=retry_backoff,
                ee_module=ee_module,
            )
            if path:
                results[idx] = path
    else:
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {
                executor.submit(
                    _download_single_tile,
                    idx,
                    len(tiles),
                    tile,
                    geotiff_dir,
                    start_date,
                    end_date,
                    scale,
                    water_threshold,
                    land_mask_asset,
                    skip_existing,
                    retry_tries,
                    retry_delay,
                    retry_backoff,
                    ee_module,
                ):
                    idx for idx, tile in enumerate(tiles, start=1)
            }
            for future in futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                path = future.result()
                if path:
                    results[idx] = path

    return [results[idx] for idx in sorted(results)]


def _build_events_config(
    place_cache_file: str = _DEFAULT_PLACE_CACHE_FILE,
    pipeline_config_path: str = _DEFAULT_PIPELINE_CONFIG,
) -> Dict:
    """Builds process_events config matching scripts/floods/flood_events_pipeline_config.py."""
    from config_map import ConfigMap  # pylint: disable=import-outside-toplevel

    pipeline_cfg = ConfigMap(filename=pipeline_config_path)
    events_stage = {}
    for stage_cfg in pipeline_cfg.get('stages', []):
        if stage_cfg.get('stage') == 'events':
            events_stage = dict(stage_cfg)
            break

    has_place_cache = bool(place_cache_file)
    return {
        'event_type':
            events_stage.get('event_type', 'FloodEvent'),
        'max_overlap_distance_km':
            events_stage.get('max_overlap_distance_km', 0),
        'max_overlap_place_hop':
            events_stage.get('max_overlap_place_hop', 2),
        's2_level':
            events_stage.get('s2_level', 10),
        'aggregate':
            events_stage.get('aggregate', 'sum'),
        'property_config':
            events_stage.get(
                'property_config',
                {
                    'area': {
                        'aggregate': 'sum',
                        'unit': 'SquareKilometer',
                    },
                    'affectedPlace': {
                        'aggregate': 'list',
                    },
                },
            ),
        'max_event_interval_days':
            events_stage.get('max_event_interval_days', 45),
        'dc_api_enabled':
            False,
        'place_property_cache_file':
            place_cache_file or '',
        'aggregate_by_contained_in_place':
            has_place_cache,
        'output_events':
            False,
        'output_svobs':
            False,
        'output_active_svobs':
            False,
        'output_place_svobs':
            True,
        'output_place_svobs_properties':
            events_stage.get('output_place_svobs_properties',
                             ['area', 'count']),
        'output_place_svobs_dates':
            events_stage.get('output_place_svobs_dates',
                             ['YYYY-MM-DD', 'YYYY-MM', 'YYYY']),
    }


def _consolidate_place_svobs_csvs(
    csv_files: List[str],
    output_csv: str,
) -> int:
    """Merges place SVObs CSVs into a deterministic CSV with header."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    seen_rows: Dict[Tuple[str, str, str], Tuple[str, str]] = {}
    rows_out: List[List[str]] = []
    duplicate_count = 0

    for csv_file in sorted(csv_files):
        if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
            continue
        with open(csv_file, 'r', encoding='utf-8', newline='') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                key = (
                    row.get('observationAbout', ''),
                    row.get('observationDate', ''),
                    row.get('observationPeriod', ''),
                )
                if not key[0]:
                    continue
                values = (row.get('area', ''), row.get('count', ''))
                if key in seen_rows:
                    if seen_rows[key] != values:
                        logging.error(
                            'Conflicting duplicate SVObs key %s in %s: '
                            'existing=%s vs new=%s',
                            key,
                            csv_file,
                            seen_rows[key],
                            values,
                        )
                        raise ValueError(
                            f'Conflicting duplicate SVObs for key {key}: '
                            f'{seen_rows[key]} vs {values}')
                    duplicate_count += 1
                    continue
                seen_rows[key] = values
                rows_out.append([
                    key[0],
                    key[1],
                    key[2],
                    values[0],
                    values[1],
                ])

    if duplicate_count:
        logging.warning(
            'Skipped %d identical duplicate SVObs row(s) while consolidating %s',
            duplicate_count,
            output_csv,
        )

    rows_out.sort(key=lambda r: (r[1], r[0], r[2]))
    tmp_path = f'{output_csv}.tmp'
    with open(tmp_path, 'w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh)
        writer.writerow(_PLACE_SVOBS_HEADER)
        writer.writerows(rows_out)
    os.replace(tmp_path, output_csv)
    return len(rows_out)


def convert_geotiffs_to_raster_csv(
    geotiff_files: List[str],
    output_dir: str,
    start_date: str,
    subprocess_timeout: int = _DEFAULT_SUBPROCESS_TIMEOUT_SECS,
) -> Optional[str]:
    """Converts one month of GeoTIFF tiles into a single S2 Level-13 raster CSV."""
    if not geotiff_files:
        return None
    raster_dir = os.path.join(output_dir, 'raster_csv')
    os.makedirs(raster_dir, exist_ok=True)

    obs_month = start_date[:7]
    raster_script = os.path.join(_EE_SCRIPTS_DIR, 'raster_to_csv.py')
    raster_config_path = os.path.join(raster_dir, 'raster_filter_config.py')
    with open(raster_config_path, 'w', encoding='utf-8') as fh:
        fh.write(
            "{\n    'input_data_filter': {\n        'area': {'aggregate': 'max'},\n"
            "        'water': {'min': 1.0},\n    }\n}\n")

    raster_csv = os.path.join(raster_dir, f'dw_flood_{obs_month}.csv')
    geotiff_glob = os.path.join(
        os.path.dirname(geotiff_files[0]),
        f'dw_flood_{start_date}_*.tif',
    )
    subprocess.run(
        [
            sys.executable,
            raster_script,
            f'--input_geotiff={geotiff_glob}',
            f'--output_csv={raster_csv}',
            f'--output_date={obs_month}',
            f'--config={raster_config_path}',
            '--s2_level=13',
            '--output_mode=w',
        ],
        check=True,
        timeout=subprocess_timeout,
    )
    if _csv_has_data_rows(raster_csv):
        return raster_csv
    logging.info('Skipping header-only or empty raster CSV: %s', raster_csv)
    return None


def _resolve_place_cache_file(
    place_cache_file: str,
    output_dir: str,
) -> str:
    """Downloads a gs:// place cache pickle locally using object-only read."""
    if not place_cache_file or not place_cache_file.startswith('gs://'):
        return place_cache_file

    parsed = urlparse(place_cache_file)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip('/')
    cache_dir = os.path.join(output_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    local_path = os.path.join(cache_dir, os.path.basename(blob_name))

    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        logging.info('Using cached place property file: %s', local_path)
        return local_path

    from google.cloud import storage  # pylint: disable=import-outside-toplevel

    client = storage.Client()
    blob = client.bucket(bucket_name).blob(blob_name)
    tmp_path = f'{local_path}.tmp'
    logging.info('Downloading place cache %s to %s', place_cache_file,
                 local_path)
    blob.download_to_filename(tmp_path)
    os.replace(tmp_path, local_path)
    return local_path


def generate_place_svobs_for_year(
    raster_csvs: List[str],
    output_dir: str,
    year: str,
    place_cache_file: str = _DEFAULT_PLACE_CACHE_FILE,
    subprocess_timeout: int = _DEFAULT_SUBPROCESS_TIMEOUT_SECS,
) -> List[str]:
    """Runs process_events.py across a year's raster CSVs to produce P1M + P1Y place SVObs."""
    non_empty_csvs = [p for p in sorted(raster_csvs) if _csv_has_data_rows(p)]
    if not non_empty_csvs:
        return []
    events_dir = os.path.join(output_dir, 'events')
    os.makedirs(events_dir, exist_ok=True)

    resolved_cache = _resolve_place_cache_file(place_cache_file, output_dir)
    events_script = os.path.join(_EE_SCRIPTS_DIR, 'process_events.py')
    base_config = os.path.join(_EE_SCRIPTS_DIR, 'event_config.py')
    event_cfg = _build_events_config(place_cache_file=resolved_cache)
    event_prefix = os.path.join(events_dir,
                                f'DynamicWorldFloods-events-{year}-')
    subprocess.run(
        [
            sys.executable,
            events_script,
            f'--input_csv={",".join(non_empty_csvs)}',
            f'--output_path={event_prefix}',
            f'--config={base_config}',
            f'--config_string={repr(event_cfg)}',
        ],
        check=True,
        timeout=subprocess_timeout,
    )
    return sorted(
        glob.glob(
            os.path.join(events_dir, '**',
                         f'DynamicWorldFloods-events-{year}-*place_svobs.csv'),
            recursive=True,
        ))


def _copy_file_atomic(src_path: str, dst_path: str) -> None:
    """Copies src_path to dst_path atomically via a temp file in dst_path's dir."""
    dst_dir = os.path.dirname(dst_path)
    if dst_dir:
        os.makedirs(dst_dir, exist_ok=True)
    tmp_path = f'{dst_path}.tmp.{os.getpid()}'
    try:
        shutil.copyfile(src_path, tmp_path)
        os.replace(tmp_path, dst_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _try_download_gcs_object(gcs_uri: str, local_path: str) -> bool:
    """Downloads a single gs:// object atomically without bucket listing.

    Returns True if the object was found and downloaded with non-zero size,
    or False if the object does not exist or cannot be read.
    """
    if not gcs_uri or not gcs_uri.startswith('gs://'):
        return False
    parsed = urlparse(gcs_uri)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip('/')
    if not bucket_name or not blob_name:
        return False

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    tmp_path = f'{local_path}.tmp.{os.getpid()}'
    try:
        from google.api_core import exceptions as gcp_exceptions  # pylint: disable=import-outside-toplevel
        from google.cloud import storage  # pylint: disable=import-outside-toplevel

        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        blob.download_to_filename(tmp_path)
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False
        os.replace(tmp_path, local_path)
        return True
    except gcp_exceptions.NotFound:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        logging.info('Legacy GCS raster CSV not found: %s', gcs_uri)
        return False
    except Exception as exc:  # pylint: disable=broad-except
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        logging.warning(
            'Could not download legacy GCS raster CSV %s (%s); will download '
            'from Earth Engine.', gcs_uri, exc)
        return False


def _resolve_effective_cache_dir(explicit_cache_dir: str) -> str:
    """Returns explicit cache dir, or ./gcs_folder if mounted by executor."""
    if explicit_cache_dir:
        return os.path.abspath(explicit_cache_dir)
    if os.path.isdir(_DEFAULT_GCS_MOUNT_DIR):
        return _DEFAULT_GCS_MOUNT_DIR
    return ''


def _clean_local_intermediates(output_dir: str) -> None:
    """Removes stale local intermediate directories before a fresh run."""
    for subdir in ('geotiff', 'raster_csv', 'events'):
        path = os.path.join(output_dir, subdir)
        if os.path.isdir(path):
            logging.info('Cleaning stale intermediate directory: %s', path)
            shutil.rmtree(path)


def resolve_or_download_month_raster_csv(
    output_dir: str,
    start_date: str,
    end_date: str,
    bounds_str: str = _DEFAULT_BOUNDS,
    tile_size_deg: float = 4.0,
    scale: int = 1000,
    water_threshold: float = 0.7,
    land_mask_asset: str = _DEFAULT_LAND_MASK_ASSET,
    ee_project: str = '',
    skip_existing: bool = False,
    use_gcs_cache: bool = True,
    max_workers: int = 10,
    convert_to_csv: bool = True,
    cache_dir: str = '',
    legacy_raster_gcs_prefix: str = _DEFAULT_LEGACY_RASTER_GCS_PREFIX,
    subprocess_timeout: int = _DEFAULT_SUBPROCESS_TIMEOUT_SECS,
    ee_module=None,
) -> Tuple[Optional[str], object]:
    """Resolves a month's S2-13 raster CSV from local/GCS cache or Earth Engine.

    Lookup order:
      1. Local <output_dir>/raster_csv/dw_flood_<YYYY-MM>.csv (if skip_existing)
      2. Persistent cache <cache_dir>/raster_csv/dw_flood_<YYYY-MM>.csv
         (if use_gcs_cache and global default bounds)
      3. Legacy prod GCS raster CSV (object-only read, written through to cache,
         if use_gcs_cache and global default bounds)
      4. Direct Earth Engine GeoTIFF download + raster_to_csv conversion
    """
    obs_month = start_date[:7]
    raster_dir = os.path.join(output_dir, 'raster_csv')
    local_raster_csv = os.path.join(raster_dir, f'dw_flood_{obs_month}.csv')
    use_global_cache = use_gcs_cache and _is_default_global_bounds(bounds_str)
    cached_raster_csv = (os.path.join(cache_dir, 'raster_csv',
                                      f'dw_flood_{obs_month}.csv') if
                         (use_global_cache and cache_dir) else '')

    if convert_to_csv:
        if skip_existing and _csv_has_data_rows(local_raster_csv):
            logging.info('Reusing existing local raster CSV for %s: %s',
                         obs_month, local_raster_csv)
            return local_raster_csv, ee_module

        if cached_raster_csv and _csv_has_data_rows(cached_raster_csv):
            logging.info('Reusing cached raster CSV for %s from %s', obs_month,
                         cached_raster_csv)
            _copy_file_atomic(cached_raster_csv, local_raster_csv)
            return local_raster_csv, ee_module

        if use_global_cache and legacy_raster_gcs_prefix:
            legacy_name = _LEGACY_RASTER_FILENAME_TEMPLATE.format(
                month=obs_month)
            legacy_uri = f'{legacy_raster_gcs_prefix.rstrip("/")}/{legacy_name}'
            if _try_download_gcs_object(legacy_uri, local_raster_csv):
                if _csv_has_data_rows(local_raster_csv):
                    logging.info('Bootstrapped raster CSV for %s from %s',
                                 obs_month, legacy_uri)
                    if cached_raster_csv:
                        _copy_file_atomic(local_raster_csv, cached_raster_csv)
                    return local_raster_csv, ee_module
                os.remove(local_raster_csv)

    if ee_module is None:
        ee_module = init_earth_engine(ee_project)

    tifs = download_earthengine_tiles(
        output_dir=output_dir,
        start_date=start_date,
        end_date=end_date,
        bounds_str=bounds_str,
        tile_size_deg=tile_size_deg,
        scale=scale,
        water_threshold=water_threshold,
        land_mask_asset=land_mask_asset,
        ee_project=ee_project,
        skip_existing=skip_existing,
        max_workers=max_workers,
        ee_module=ee_module,
    )
    if not convert_to_csv:
        return None, ee_module

    raster_csv = convert_geotiffs_to_raster_csv(
        geotiff_files=tifs,
        output_dir=output_dir,
        start_date=start_date,
        subprocess_timeout=subprocess_timeout,
    )
    if raster_csv and cached_raster_csv:
        _copy_file_atomic(raster_csv, cached_raster_csv)
        logging.info('Persisted raster CSV for %s to cache: %s', obs_month,
                     cached_raster_csv)
    return raster_csv, ee_module


def _persist_annual_place_svobs(
    year: str,
    place_svobs_csvs: List[str],
    cache_dir: str,
) -> Optional[str]:
    """Saves a completed/updated annual place_svobs CSV to persistent cache."""
    if not cache_dir or not place_svobs_csvs:
        return None
    cache_place_dir = os.path.join(cache_dir, 'place_svobs')
    os.makedirs(cache_place_dir, exist_ok=True)
    dest = os.path.join(cache_place_dir,
                        f'DynamicWorldFloods-events-{year}-place_svobs.csv')
    _consolidate_place_svobs_csvs(place_svobs_csvs, dest)
    logging.info('Persisted annual place SVObs for %s to cache: %s', year, dest)
    return dest


def _collect_prior_year_place_svobs_csvs(
    cache_dir: str,
    active_years: List[str],
) -> List[str]:
    """Returns cached annual place_svobs CSVs for years not in active_years."""
    if not cache_dir:
        return []
    cache_place_dir = os.path.join(cache_dir, 'place_svobs')
    if not os.path.isdir(cache_place_dir):
        return []
    active_set = set(active_years)
    carried: List[str] = []
    for path in sorted(
            glob.glob(
                os.path.join(cache_place_dir,
                             'DynamicWorldFloods-events-*-place_svobs.csv'))):
        basename = os.path.basename(path)
        parts = basename.split('-')
        year = parts[2] if len(parts) >= 4 else ''
        if year and year not in active_set and os.path.getsize(path) > 0:
            carried.append(path)
    return carried


def main(_):
    start_default, end_default = default_ytd_date_range()
    start_date = _FLAGS.start_date or start_default
    end_date = _FLAGS.end_date or end_default
    output_dir = os.path.abspath(_FLAGS.output_dir)
    consolidated_path = os.path.join(output_dir, _FLAGS.consolidated_csv)
    cache_dir = _resolve_effective_cache_dir(_FLAGS.cache_dir)
    use_global_cache = _is_default_global_bounds(_FLAGS.bounds)

    month_ranges = iter_month_ranges(start_date, end_date)
    os.makedirs(output_dir, exist_ok=True)
    if not _FLAGS.skip_existing:
        _clean_local_intermediates(output_dir)
    logging.info(
        'DynamicWorld_FloodEvents_Places_AutoRefresh download: '
        'start=%s, end=%s (%d months), bounds=%s, cache_dir=%s, '
        'use_gcs_cache=%s, skip_existing=%s, place_cache=%s, out=%s',
        start_date,
        end_date,
        len(month_ranges),
        _FLAGS.bounds,
        cache_dir or '<none>',
        _FLAGS.use_gcs_cache,
        _FLAGS.skip_existing,
        _FLAGS.place_cache_file,
        output_dir,
    )

    ee_module = None
    raster_csvs_by_year: Dict[str, List[str]] = {}

    for m_start, m_end in month_ranges:
        logging.info('Processing month window [%s, %s)', m_start, m_end)
        raster_csv, ee_module = resolve_or_download_month_raster_csv(
            output_dir=output_dir,
            start_date=m_start,
            end_date=m_end,
            bounds_str=_FLAGS.bounds,
            tile_size_deg=_FLAGS.tile_size_deg,
            scale=_FLAGS.scale,
            water_threshold=_FLAGS.water_threshold,
            land_mask_asset=_FLAGS.land_mask_asset,
            ee_project=_FLAGS.ee_project,
            skip_existing=_FLAGS.skip_existing,
            use_gcs_cache=_FLAGS.use_gcs_cache,
            max_workers=_FLAGS.max_workers,
            convert_to_csv=_FLAGS.convert_to_csv,
            cache_dir=cache_dir,
            legacy_raster_gcs_prefix=_FLAGS.legacy_raster_gcs_prefix,
            subprocess_timeout=_FLAGS.subprocess_timeout_secs,
            ee_module=ee_module,
        )
        if raster_csv:
            raster_csvs_by_year.setdefault(m_start[:4], []).append(raster_csv)

    if _FLAGS.convert_to_csv:
        all_place_svobs_csvs: List[str] = []
        active_years = sorted(raster_csvs_by_year.keys())
        for year in active_years:
            csv_list = raster_csvs_by_year[year]
            year_place_csvs = generate_place_svobs_for_year(
                raster_csvs=csv_list,
                output_dir=output_dir,
                year=year,
                place_cache_file=_FLAGS.place_cache_file,
                subprocess_timeout=_FLAGS.subprocess_timeout_secs,
            )
            all_place_svobs_csvs.extend(year_place_csvs)
            is_ytd_for_year = any(
                os.path.basename(p) == f'dw_flood_{year}-01.csv'
                for p in csv_list)
            if use_global_cache and cache_dir and is_ytd_for_year:
                _persist_annual_place_svobs(year, year_place_csvs, cache_dir)

        if (_FLAGS.carry_forward_prior_years and use_global_cache and
                cache_dir):
            prior_csvs = _collect_prior_year_place_svobs_csvs(
                cache_dir, active_years)
            if prior_csvs:
                logging.info('Carrying forward %d cached prior-year CSV(s): %s',
                             len(prior_csvs), prior_csvs)
                all_place_svobs_csvs = prior_csvs + all_place_svobs_csvs

        row_count = _consolidate_place_svobs_csvs(all_place_svobs_csvs,
                                                  consolidated_path)
        if row_count == 0:
            raise RuntimeError(
                f'Consolidated place SVObs CSV {consolidated_path} has 0 rows')
        logging.info(
            'Wrote %d consolidated place SVObs rows across %d months to %s',
            row_count,
            len(month_ranges),
            consolidated_path,
        )


if __name__ == '__main__':
    _define_flags()
    app.run(main)

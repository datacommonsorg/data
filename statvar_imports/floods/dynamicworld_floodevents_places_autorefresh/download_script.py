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
_DEFAULT_PLACE_CACHE_FILE = (
    'gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl'
)
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

_FLAGS = flags.FLAGS
_EE_INIT_LOCK = threading.Lock()


def _define_flags():
    flags.DEFINE_string(
        'start_date',
        '',
        'Start date (YYYY-MM-DD, inclusive) for Earth Engine Dynamic World query. '
        'Defaults to the first day of the previous complete calendar month.',
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
        'skip_existing',
        True,
        'Skip downloading GeoTIFF tiles whose target local file already exists.',
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
    if south >= north or west >= east:
        raise ValueError(
            f'Invalid bounds (require south < north and west < east): {bounds_str!r}'
        )
    return south, west, north, east


def generate_tiles(
    south: float,
    west: float,
    north: float,
    east: float,
    tile_size_deg: float,
) -> List[Tuple[float, float, float, float]]:
    """Splits a bounding box into sub-tiles of at most tile_size_deg."""
    if tile_size_deg <= 0:
        raise ValueError(f'tile_size_deg must be positive, got {tile_size_deg}')
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
    return dw_water.selfMask().toFloat()


def _sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}{parsed.path}'


def _download_with_util_atomic(
    url: str,
    target_path: str,
    headers: Optional[Dict[str, str]] = None,
    tries: int = 3,
    delay: int = 5,
    backoff: int = 2,
) -> bool:
    """Downloads a URL via download_util_script and moves it atomically."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
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
        tmp_dest = f'{target_path}.tmp'
        shutil.move(src_file, tmp_dest)
        os.replace(tmp_dest, target_path)
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
    skip_existing: bool = True,
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
    seen_rows = set()
    rows_out: List[List[str]] = []

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
                if not key[0] or key in seen_rows:
                    continue
                seen_rows.add(key)
                rows_out.append([
                    key[0],
                    key[1],
                    key[2],
                    row.get('area', ''),
                    row.get('count', ''),
                ])

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
    )
    if os.path.exists(raster_csv) and os.path.getsize(raster_csv) > 0:
        return raster_csv
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
) -> List[str]:
    """Runs process_events.py across a year's raster CSVs to produce P1M + P1Y place SVObs."""
    if not raster_csvs:
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
            f'--input_csv={",".join(sorted(raster_csvs))}',
            f'--output_path={event_prefix}',
            f'--config={base_config}',
            f'--config_string={repr(event_cfg)}',
        ],
        check=True,
    )
    return sorted(
        glob.glob(
            os.path.join(events_dir, '**',
                         f'DynamicWorldFloods-events-{year}-*place_svobs.csv'),
            recursive=True,
        ))


def main(_):
    start_default, end_default = default_month_date_range()
    start_date = _FLAGS.start_date or start_default
    end_date = _FLAGS.end_date or end_default
    output_dir = os.path.abspath(_FLAGS.output_dir)
    consolidated_path = os.path.join(output_dir, _FLAGS.consolidated_csv)

    month_ranges = iter_month_ranges(start_date, end_date)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(
        'DynamicWorld_FloodEvents_Places_AutoRefresh download: '
        'start=%s, end=%s (%d months), bounds=%s, place_cache=%s, out=%s',
        start_date,
        end_date,
        len(month_ranges),
        _FLAGS.bounds,
        _FLAGS.place_cache_file,
        output_dir,
    )

    ee_module = init_earth_engine(_FLAGS.ee_project)
    raster_csvs_by_year: Dict[str, List[str]] = {}

    for m_start, m_end in month_ranges:
        logging.info('Processing month window [%s, %s)', m_start, m_end)
        tifs = download_earthengine_tiles(
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
            max_workers=_FLAGS.max_workers,
            ee_module=ee_module,
        )
        if _FLAGS.convert_to_csv:
            raster_csv = convert_geotiffs_to_raster_csv(
                geotiff_files=tifs,
                output_dir=output_dir,
                start_date=m_start,
            )
            if raster_csv:
                raster_csvs_by_year.setdefault(m_start[:4],
                                               []).append(raster_csv)

    if _FLAGS.convert_to_csv:
        all_place_svobs_csvs: List[str] = []
        for year, csv_list in sorted(raster_csvs_by_year.items()):
            all_place_svobs_csvs.extend(
                generate_place_svobs_for_year(
                    raster_csvs=csv_list,
                    output_dir=output_dir,
                    year=year,
                    place_cache_file=_FLAGS.place_cache_file,
                ))
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

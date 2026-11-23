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
"""Automated local download script for Dynamic World V1 Floods data.

Downloads monthly flood extent rasters directly from Google Earth Engine's
Dynamic World V1 catalog
(https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
via `util/download_util_script.download_file()`, converts GeoTIFFs into S2
Level-13 raster CSVs and monthly per-place FloodEvent SVObs CSVs (`area`,
`count`), and publishes a consolidated CSV ready for `stat_var_processor.py`.
"""

import csv
import datetime
import glob
import os
import shutil
import subprocess
import sys
import tempfile
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

for _path in (_REPO_ROOT, _UTIL_DIR, _EE_SCRIPTS_DIR):
    if _path not in sys.path:
        sys.path.append(_path)

import download_util_script  # pylint: disable=wrong-import-position

_DW_COLLECTION_ID = 'GOOGLE/DYNAMICWORLD/V1'
_DEFAULT_LAND_MASK_ASSET = 'UMD/hansen/global_forest_change_2025_v1_13'
_DEFAULT_BOUNDS = '24.72,83.83,26.06,88.26'
_DEFAULT_OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'input_files')
_CONSOLIDATED_FILENAME = 'dynamic_world_flood_place_svobs.csv'
_PLACE_SVOBS_HEADER = [
    'observationAbout',
    'observationDate',
    'observationPeriod',
    'area',
    'count',
]

_FLAGS = flags.FLAGS


def _define_flags():
    flags.DEFINE_string(
        'start_date',
        '',
        'Start date (YYYY-MM-DD, inclusive) for Earth Engine Dynamic World query. '
        'Defaults to Jan 1 of the current year (or prior year in January).',
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
        'Engine GeoTIFF tiling (use "-60,-180,75,180" for global tiling).',
    )
    flags.DEFINE_float(
        'tile_size_deg',
        4.0,
        'Maximum tile width/height in degrees per Earth Engine getDownloadURL '
        'request so each tile completes well within HTTP size/timeout limits.',
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
        '',
        'Optional local path to place_properties_cache_with_s2_10.pkl '
        'for parent administrative place rollups during event processing.',
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
    """Returns (start_date, end_date) strings for the previous complete month."""
    today = reference_date or datetime.date.today()
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - datetime.timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    return first_of_prev.strftime('%Y-%m-%d'), first_of_current.strftime(
        '%Y-%m-%d')


def default_ytd_date_range(
    reference_date: Optional[datetime.date] = None,) -> Tuple[str, str]:
    """Returns (start_date, end_date) covering complete YTD calendar months."""
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
    ee_module=None,
) -> List[str]:
    """Downloads GeoTIFF flood tiles directly from GOOGLE/DYNAMICWORLD/V1."""
    south, west, north, east = parse_bounds(bounds_str)
    tiles = generate_tiles(south, west, north, east, tile_size_deg)
    geotiff_dir = os.path.join(output_dir, 'geotiff')
    os.makedirs(geotiff_dir, exist_ok=True)

    if ee_module is None:
        ee_module = init_earth_engine(ee_project)
    downloaded_paths: List[str] = []

    for idx, tile in enumerate(tiles, start=1):
        tile_path = os.path.join(geotiff_dir,
                                 _format_tile_name(start_date, end_date, tile))
        if skip_existing and os.path.exists(tile_path) and os.path.getsize(
                tile_path) > 0:
            logging.info('[%d/%d] Skipping existing tile: %s', idx, len(tiles),
                         tile_path)
            downloaded_paths.append(tile_path)
            continue

        t_south, t_west, t_north, t_east = tile
        region = ee_module.Geometry.Rectangle(
            [t_west, t_south, t_east, t_north])
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
        empty_tile = False
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
                    logging.info(
                        '[%d/%d] No Dynamic World imagery for tile %s in [%s, %s); skipping.',
                        idx,
                        len(tiles),
                        tile,
                        start_date,
                        end_date,
                    )
                    empty_tile = True
                    break
                last_error = exc
                logging.warning(
                    'Tile %d/%d getDownloadURL attempt %d/%d failed: %s',
                    idx,
                    len(tiles),
                    attempt,
                    retry_tries,
                    exc,
                )
                if attempt < retry_tries:
                    time.sleep(current_delay)
                    current_delay *= retry_backoff

        if empty_tile:
            continue

        if not url:
            raise RuntimeError(
                f'Failed to get Earth Engine download URL for tile {tile}: {last_error}'
            )

        logging.info(
            '[%d/%d] Downloading tile %s from %s',
            idx,
            len(tiles),
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
            downloaded_paths.append(tile_path)
        else:
            raise RuntimeError(f'Download failed for Earth Engine tile {tile}')

    return downloaded_paths


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


def convert_geotiffs_to_local_csvs(
    geotiff_files: List[str],
    output_dir: str,
    start_date: str,
    place_cache_file: str = '',
) -> Dict[str, List[str]]:
    """Converts one month of GeoTIFFs into S2 cell CSVs and place SVObs CSVs."""
    raster_dir = os.path.join(output_dir, 'raster_csv')
    events_dir = os.path.join(output_dir, 'events')
    os.makedirs(raster_dir, exist_ok=True)
    os.makedirs(events_dir, exist_ok=True)

    obs_month = start_date[:7]
    raster_script = os.path.join(_EE_SCRIPTS_DIR, 'raster_to_csv.py')
    events_script = os.path.join(_EE_SCRIPTS_DIR, 'process_events.py')

    raster_config_path = os.path.join(raster_dir, 'raster_filter_config.py')
    with open(raster_config_path, 'w', encoding='utf-8') as fh:
        fh.write(
            "{\n    'input_data_filter': {\n        'area': {'aggregate': 'sum'},\n"
            "        'water': {'min': 1.0},\n    }\n}\n")

    raster_csvs: List[str] = []
    place_svobs_csvs: List[str] = []

    for tif_path in geotiff_files:
        base_name = os.path.splitext(os.path.basename(tif_path))[0]
        raster_csv = os.path.join(raster_dir, f'{base_name}.csv')
        subprocess.run(
            [
                sys.executable,
                raster_script,
                f'--input_geotiff={tif_path}',
                f'--output_csv={raster_csv}',
                f'--output_date={obs_month}',
                f'--config={raster_config_path}',
                '--s2_level=13',
                '--output_mode=w',
            ],
            check=True,
        )
        if os.path.exists(raster_csv) and os.path.getsize(raster_csv) > 0:
            raster_csvs.append(raster_csv)

    if raster_csvs:
        event_prefix = os.path.join(events_dir,
                                    f'DynamicWorldFlood-{obs_month}-')
        base_config = os.path.join(_EE_SCRIPTS_DIR, 'event_config.py')
        has_place_cache = bool(place_cache_file)
        event_cfg = {
            'max_overlap_distance_km': 0,
            'place_property_cache_file': place_cache_file or '',
            'aggregate_by_contained_in_place': has_place_cache,
            'output_events': False,
            'output_place_svobs': True,
            'output_place_svobs_properties': ['area', 'count'],
            'output_place_svobs_dates': ['YYYY-MM'],
            'output_svobs': False,
            'output_active_svobs': False,
        }
        subprocess.run(
            [
                sys.executable,
                events_script,
                f'--input_csv={",".join(raster_csvs)}',
                f'--output_path={event_prefix}',
                f'--config={base_config}',
                f'--config_string={repr(event_cfg)}',
            ],
            check=True,
        )
        place_svobs_csvs = sorted(
            glob.glob(
                os.path.join(events_dir, '**',
                             f'DynamicWorldFlood-{obs_month}-*place_svobs.csv'),
                recursive=True,
            ))

    return {
        'raster_csvs': raster_csvs,
        'place_svobs_csvs': place_svobs_csvs,
    }


def main(_):
    start_default, end_default = default_ytd_date_range()
    start_date = _FLAGS.start_date or start_default
    end_date = _FLAGS.end_date or end_default
    output_dir = os.path.abspath(_FLAGS.output_dir)
    consolidated_path = os.path.join(output_dir, _FLAGS.consolidated_csv)

    month_ranges = iter_month_ranges(start_date, end_date)
    os.makedirs(output_dir, exist_ok=True)
    logging.info(
        'Dynamic World V1 flood download: start=%s, end=%s (%d months), bounds=%s, out=%s',
        start_date,
        end_date,
        len(month_ranges),
        _FLAGS.bounds,
        output_dir,
    )

    ee_module = init_earth_engine(_FLAGS.ee_project)
    all_place_svobs_csvs: List[str] = []

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
            ee_module=ee_module,
        )
        if _FLAGS.convert_to_csv:
            converted = convert_geotiffs_to_local_csvs(
                geotiff_files=tifs,
                output_dir=output_dir,
                start_date=m_start,
                place_cache_file=_FLAGS.place_cache_file,
            )
            all_place_svobs_csvs.extend(converted['place_svobs_csvs'])

    if _FLAGS.convert_to_csv:
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

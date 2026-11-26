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
"""Unit tests for DynamicWorld_Floods download and S2 Level-13 consolidation."""

import csv
import datetime
import os
import sys
import tempfile
import unittest
from unittest import mock

import requests

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_STATVAR_IMPORTS_DIR = os.path.dirname(os.path.dirname(_TEST_DIR))
_REPO_ROOT = os.path.dirname(_STATVAR_IMPORTS_DIR)
for _path in (_STATVAR_IMPORTS_DIR, os.path.join(_REPO_ROOT, 'util')):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from floods.dynamicworld_floods import download_script  # pylint: disable=wrong-import-position


class _FakeEEChain:
    """Minimal chainable mock recording Google Earth Engine API calls."""

    def __init__(
        self,
        calls=None,
        url='https://earthengine.example/tile:getPixels',
        download_url_error=None,
    ):
        self.calls = calls if calls is not None else []
        self._url = url
        self._download_url_error = download_url_error

    def filterDate(self, start_date, end_date):
        self.calls.append(('filterDate', start_date, end_date))
        return self

    def filterBounds(self, geom):
        self.calls.append(('filterBounds', geom))
        return self

    def select(self, band):
        self.calls.append(('select', band))
        return self

    def map(self, fn):
        self.calls.append(('map', callable(fn)))
        fn(self)
        return self

    def gte(self, threshold):
        self.calls.append(('gte', threshold))
        return self

    def eq(self, value):
        self.calls.append(('eq', value))
        return self

    def rename(self, name):
        self.calls.append(('rename', name))
        return self

    def max(self):
        self.calls.append(('max',))
        return self

    def updateMask(self, mask):
        self.calls.append(('updateMask', mask))
        return self

    def unmask(self, value):
        self.calls.append(('unmask', value))
        return self

    def toFloat(self):
        self.calls.append(('toFloat',))
        return self

    def getDownloadURL(self, params):
        self.calls.append(('getDownloadURL', params))
        if self._download_url_error is not None:
            raise self._download_url_error
        return self._url


class DownloadScriptTest(unittest.TestCase):
    """Tests for DynamicWorld_Floods download, caching, and S2 consolidation."""

    def test_default_month_date_range(self):
        start, end = download_script.default_month_date_range(
            datetime.date(2026, 11, 19))
        self.assertEqual((start, end), ('2026-10-01', '2026-11-01'))

        jan_start, jan_end = download_script.default_month_date_range(
            datetime.date(2026, 1, 5))
        self.assertEqual((jan_start, jan_end), ('2025-12-01', '2026-01-01'))

    def test_default_ytd_date_range_and_iter_month_ranges(self):
        self.assertEqual(
            download_script.default_ytd_date_range(datetime.date(2026, 11, 20)),
            ('2026-01-01', '2026-11-01'),
        )
        self.assertEqual(
            download_script.default_ytd_date_range(datetime.date(2026, 1, 5)),
            ('2025-01-01', '2026-01-01'),
        )
        self.assertEqual(
            download_script.default_ytd_date_range(datetime.date(2027, 2, 1)),
            ('2027-01-01', '2027-02-01'),
        )
        self.assertEqual(
            download_script.iter_month_ranges('2026-09-01', '2026-11-01'),
            [('2026-09-01', '2026-10-01'), ('2026-10-01', '2026-11-01')],
        )
        with self.assertRaises(ValueError):
            download_script.iter_month_ranges('2026-11-01', '2026-11-01')

    def test_parse_bounds_and_global_tiles(self):
        self.assertEqual(download_script._DEFAULT_BOUNDS, '-60,-180,75,180')
        bounds = download_script.parse_bounds('-60,-180,75,180')
        self.assertEqual(bounds, (-60.0, -180.0, 75.0, 180.0))
        tiles = download_script.generate_tiles(*bounds, tile_size_deg=4.0)
        self.assertEqual(len(tiles), 34 * 90)
        self.assertEqual(tiles[0], (-60.0, -180.0, -56.0, -176.0))
        self.assertEqual(tiles[-1], (72.0, 176.0, 75.0, 180.0))

        for bad_bounds in (
                '-91,-180,75,180',
                '-60,-180,91,180',
                '-60,-181,75,180',
                '-60,-180,75,181',
                '30.0,83.0,24.0,89.0',
                '24.0,89.0,30.0,83.0',
                '24.0,83.0,30.0',
        ):
            with self.assertRaises(ValueError):
                download_script.parse_bounds(bad_bounds)

        with self.assertRaises(ValueError):
            download_script.generate_tiles(0.0, 0.0, 1.0, 1.0, 1e-7)

    def test_build_dynamic_world_flood_image_uses_google_dynamicworld_v1(self):
        fake_ee = mock.MagicMock()
        calls = []
        chain = _FakeEEChain(calls=calls)
        fake_ee.ImageCollection.return_value = chain
        fake_ee.Image.return_value = chain

        result = download_script.build_dynamic_world_flood_image(
            ee_module=fake_ee,
            start_date='2026-10-01',
            end_date='2026-11-01',
            region_geometry='geom',
            water_threshold=0.7,
            land_mask_asset='UMD/hansen/global_forest_change_2025_v1_13',
        )
        self.assertIs(result, chain)
        fake_ee.ImageCollection.assert_called_once_with(
            'GOOGLE/DYNAMICWORLD/V1')
        fake_ee.Image.assert_called_once_with(
            'UMD/hansen/global_forest_change_2025_v1_13')
        self.assertIn(('filterDate', '2026-10-01', '2026-11-01'), calls)
        self.assertIn(('gte', 0.7), calls)
        self.assertIn(('eq', 1), calls)
        self.assertIn(('unmask', 0), calls)

    def test_download_earthengine_tiles_parallel_reuses_session_and_skips_empty(
            self):
        fake_ee = mock.MagicMock()
        chain = _FakeEEChain(
            url=
            'https://earthengine.googleapis.com/v1/projects/p/thumbnails/id:getPixels'
        )
        fake_ee.ImageCollection.return_value = chain
        fake_ee.Image.return_value = chain
        fake_ee.Geometry.Rectangle.side_effect = lambda coords: coords

        sessions_seen = []

        def _fake_download_file(url, output_folder, session=None, **_kwargs):
            sessions_seen.append(session)
            out = os.path.join(output_folder, 'id:getPixels.tif')
            with open(out, 'wb') as fh:
                fh.write(b'II*\x00fake_geotiff_bytes')
            return True

        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(
                    download_script.download_util_script,
                    'download_file',
                    side_effect=_fake_download_file,
            ), mock.patch.object(
                    download_script,
                    '_tile_has_flood_pixels',
                    return_value=True,
            ):
                paths = download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-10-01',
                    end_date='2026-11-01',
                    bounds_str='24.0,84.0,28.0,92.0',
                    tile_size_deg=4.0,
                    max_workers=2,
                    ee_module=fake_ee,
                )
            self.assertEqual(len(paths), 2)
            self.assertEqual(len(sessions_seen), 2)
            for sess in sessions_seen:
                self.assertIsInstance(sess, requests.Session)
            for p in paths:
                self.assertTrue(p.endswith('.tif'))
                self.assertTrue(os.path.exists(p))

        empty_chain = _FakeEEChain(download_url_error=RuntimeError(
            'Image.updateMask: If one image has no bands, the other must also have no bands.'
        ))
        fake_ee.ImageCollection.return_value = empty_chain
        fake_ee.Image.return_value = empty_chain
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertEqual(
                download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-07-01',
                    end_date='2026-08-01',
                    bounds_str='24.0,84.0,26.0,88.0',
                    tile_size_deg=4.0,
                    max_workers=1,
                    ee_module=fake_ee,
                ),
                [],
            )

        err_chain = _FakeEEChain(
            download_url_error=RuntimeError('EE quota error'))
        fake_ee.ImageCollection.return_value = err_chain
        fake_ee.Image.return_value = err_chain
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(RuntimeError):
                download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-07-01',
                    end_date='2026-08-01',
                    bounds_str='24.0,84.0,26.0,88.0',
                    tile_size_deg=4.0,
                    retry_tries=1,
                    max_workers=1,
                    ee_module=fake_ee,
                )

    def test_convert_geotiffs_uses_glob_sets_timeout_and_skips_header_only(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            geotiff_dir = os.path.join(tmp_dir, 'geotiff')
            os.makedirs(geotiff_dir, exist_ok=True)
            tif1 = os.path.join(geotiff_dir, 'dw_flood_2026-10-01_a.tif')
            tif2 = os.path.join(geotiff_dir, 'dw_flood_2026-10-01_b.tif')
            for tif in (tif1, tif2):
                with open(tif, 'wb') as fh:
                    fh.write(b'FAKE')

            def _fake_header_only(cmd, **_kwargs):
                out_arg = [a for a in cmd if a.startswith('--output_csv=')][0]
                out_path = out_arg.split('=', 1)[1]
                with open(out_path, 'w', encoding='utf-8') as fh:
                    fh.write('area,date,s2CellId\n')

            with mock.patch.object(
                    download_script.subprocess,
                    'run',
                    side_effect=_fake_header_only,
            ) as mock_run:
                res = download_script.convert_geotiffs_to_raster_csv(
                    geotiff_files=[tif1, tif2],
                    output_dir=tmp_dir,
                    start_date='2026-10-01',
                    subprocess_timeout=456,
                )
            self.assertIsNone(res)
            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            expected_glob = os.path.join(geotiff_dir,
                                         'dw_flood_2026-10-01_*.tif')
            self.assertIn(f'--input_geotiff={expected_glob}', cmd_args)
            self.assertEqual(mock_run.call_args[1]['timeout'], 456)

    def test_consolidate_s2_svobs_csvs_handles_raster_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raster_csv = os.path.join(tmp_dir, 'dw_flood_2026-10.csv')
            prior_csv = os.path.join(tmp_dir, 'dw_flood_s2_2025.csv')
            out = os.path.join(tmp_dir, 'consolidated.csv')

            with open(raster_csv, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['area', 'date', 's2CellId', 's2Level'])
                w.writerow(['0.214031', '2026-10', 's2CellId/0x2', '13'])
                w.writerow(['0.214031', '2026-10', 'dcid:s2CellId/0x2', '13'])

            with open(prior_csv, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area'
                ])
                w.writerow(['dcid:s2CellId/0x1', '2025-12', 'P1M', '1.500000'])

            count = download_script._consolidate_s2_svobs_csvs(
                [raster_csv, prior_csv], out)
            self.assertEqual(count, 2)
            with open(out, 'r', encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(
                rows,
                [
                    {
                        'observationAbout': 'dcid:s2CellId/0x1',
                        'observationDate': '2025-12',
                        'observationPeriod': 'P1M',
                        'area': '1.500000',
                    },
                    {
                        'observationAbout': 'dcid:s2CellId/0x2',
                        'observationDate': '2026-10',
                        'observationPeriod': 'P1M',
                        'area': '0.214031',
                    },
                ],
            )

    def test_consolidate_s2_svobs_csvs_raises_on_conflicting_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv1 = os.path.join(tmp_dir, 'a.csv')
            out = os.path.join(tmp_dir, 'out.csv')
            with open(csv1, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow(['area', 'date', 's2CellId'])
                w.writerow(['0.214031', '2026-10', 'dcid:s2CellId/0x2'])
                w.writerow(['0.999999', '2026-10', 'dcid:s2CellId/0x2'])
            with self.assertRaises(ValueError):
                download_script._consolidate_s2_svobs_csvs([csv1], out)

    def test_tile_has_flood_pixels(self):
        import numpy as np  # pylint: disable=import-outside-toplevel
        import rasterio  # pylint: disable=import-outside-toplevel
        from rasterio.transform import from_origin  # pylint: disable=import-outside-toplevel

        with tempfile.TemporaryDirectory() as tmp_dir:
            dry_tif = os.path.join(tmp_dir, 'dry.tif')
            wet_tif = os.path.join(tmp_dir, 'wet.tif')
            profile = {
                'driver': 'GTiff',
                'height': 4,
                'width': 4,
                'count': 1,
                'dtype': 'float32',
                'crs': 'EPSG:4326',
                'transform': from_origin(84.0, 26.0, 0.01, 0.01),
            }
            with rasterio.open(dry_tif, 'w', **profile) as dst:
                dry = np.zeros((4, 4), dtype='float32')
                dry[0, 0] = -np.inf
                dst.write(dry, 1)
            self.assertFalse(download_script._tile_has_flood_pixels(dry_tif))

            with rasterio.open(wet_tif, 'w', **profile) as dst:
                wet = np.zeros((4, 4), dtype='float32')
                wet[1, 2] = 1.0
                dst.write(wet, 1)
            self.assertTrue(download_script._tile_has_flood_pixels(wet_tif))

    def test_resolve_month_raster_csv_and_prior_year_carry_forward(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, 'out')
            cache_dir = os.path.join(tmp_dir, 'gcs_cache')
            os.makedirs(os.path.join(cache_dir, 'raster_csv'), exist_ok=True)
            cached_jan = os.path.join(cache_dir, 'raster_csv',
                                      'dw_flood_2026-01.csv')
            with open(cached_jan, 'w', encoding='utf-8') as fh:
                fh.write(
                    'area,date,s2CellId\n0.500000,2026-01,dcid:s2CellId/0x1\n')

            with mock.patch.object(download_script,
                                   'init_earth_engine') as mock_init_ee:
                jan_path, ee_mod = (
                    download_script.resolve_or_download_month_raster_csv(
                        output_dir=out_dir,
                        start_date='2026-01-01',
                        end_date='2026-02-01',
                        cache_dir=cache_dir,
                    ))
                self.assertTrue(os.path.exists(jan_path))
                self.assertIsNone(ee_mod)
                mock_init_ee.assert_not_called()

            persisted = download_script._persist_annual_s2_svobs(
                '2026', [jan_path], cache_dir)
            self.assertTrue(os.path.exists(persisted))
            self.assertEqual(
                download_script._collect_prior_year_s2_svobs_csvs(
                    cache_dir, ['2026']),
                [],
            )
            self.assertEqual(
                download_script._collect_prior_year_s2_svobs_csvs(
                    cache_dir, ['2027']),
                [persisted],
            )

            download_script._clean_local_intermediates(out_dir)
            self.assertFalse(os.path.exists(os.path.join(out_dir,
                                                         'raster_csv')))


if __name__ == '__main__':
    unittest.main()

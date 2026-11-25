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
"""Unit and integration tests for DynamicWorld_FloodEvents_Places_AutoRefresh."""

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

from floods.dynamicworld_floodevents_places_autorefresh import download_script  # pylint: disable=wrong-import-position


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
    """Tests for DynamicWorld_FloodEvents_Places_AutoRefresh download & SVObs."""

    def test_default_month_date_range(self):
        start, end = download_script.default_month_date_range(
            datetime.date(2026, 11, 24))
        self.assertEqual((start, end), ('2026-10-01', '2026-11-01'))

        jan_start, jan_end = download_script.default_month_date_range(
            datetime.date(2026, 1, 5))
        self.assertEqual((jan_start, jan_end), ('2025-12-01', '2026-01-01'))

    def test_default_ytd_date_range(self):
        start, end = download_script.default_ytd_date_range(
            datetime.date(2026, 11, 24))
        self.assertEqual((start, end), ('2026-01-01', '2026-11-01'))

        jan_start, jan_end = download_script.default_ytd_date_range(
            datetime.date(2027, 1, 5))
        self.assertEqual((jan_start, jan_end), ('2026-01-01', '2027-01-01'))

        feb_start, feb_end = download_script.default_ytd_date_range(
            datetime.date(2027, 2, 1))
        self.assertEqual((feb_start, feb_end), ('2027-01-01', '2027-02-01'))

    def test_iter_month_ranges_splits_multi_month(self):
        self.assertEqual(
            download_script.iter_month_ranges('2026-08-01', '2026-11-01'),
            [
                ('2026-08-01', '2026-09-01'),
                ('2026-09-01', '2026-10-01'),
                ('2026-10-01', '2026-11-01'),
            ],
        )

    def test_parse_bounds_and_global_tiles(self):
        self.assertEqual(
            download_script.parse_bounds('-60,-180,75,180'),
            (-60.0, -180.0, 75.0, 180.0),
        )
        for bad_bounds in (
                '-91,-180,75,180',
                '-60,-180,91,180',
                '-60,-181,75,180',
                '-60,-180,75,181',
                '10,0,10,10',
                '0,10,10,10',
                '10,20,30',
        ):
            with self.assertRaises(ValueError):
                download_script.parse_bounds(bad_bounds)
        tiles = download_script.generate_tiles(-60.0, -180.0, 75.0, 180.0, 4.0)
        self.assertEqual(len(tiles), 34 * 90)
        self.assertEqual(tiles[0], (-60.0, -180.0, -56.0, -176.0))
        self.assertEqual(tiles[-1], (72.0, 176.0, 75.0, 180.0))
        with self.assertRaises(ValueError):
            download_script.generate_tiles(0.0, 0.0, 1.0, 1.0, 1e-7)

    def test_build_events_config_matches_flood_pipeline_config(self):
        cfg = download_script._build_events_config(
            place_cache_file=
            'gs://datcom-prod-imports/place_cache/place_properties_cache_with_s2_10.pkl'
        )
        self.assertEqual(cfg['event_type'], 'FloodEvent')
        self.assertEqual(cfg['s2_level'], 10)
        self.assertEqual(cfg['max_overlap_distance_km'], 0)
        self.assertEqual(cfg['max_overlap_place_hop'], 2)
        self.assertEqual(cfg['max_event_interval_days'], 45)
        self.assertTrue(cfg['aggregate_by_contained_in_place'])
        self.assertTrue(cfg['output_place_svobs'])
        self.assertEqual(cfg['output_place_svobs_properties'],
                         ['area', 'count'])
        self.assertEqual(cfg['output_place_svobs_dates'],
                         ['YYYY-MM-DD', 'YYYY-MM', 'YYYY'])

    def test_build_dynamic_world_flood_image_uses_google_dynamicworld_v1(self):
        calls = []
        fake_ee = mock.MagicMock()
        chain = _FakeEEChain(calls=calls)
        fake_ee.ImageCollection.return_value = chain
        fake_ee.Image.return_value = chain

        result = download_script.build_dynamic_world_flood_image(
            ee_module=fake_ee,
            start_date='2026-10-01',
            end_date='2026-11-01',
            region_geometry='geom',
        )
        self.assertIs(result, chain)
        fake_ee.ImageCollection.assert_called_once_with(
            'GOOGLE/DYNAMICWORLD/V1')
        self.assertIn(('filterDate', '2026-10-01', '2026-11-01'), calls)
        self.assertIn(('gte', 0.7), calls)
        self.assertIn(('max',), calls)
        self.assertIn(('unmask', 0), calls)

    def test_download_earthengine_tiles_parallel_and_skips_empty(self):
        fake_ee = mock.MagicMock()
        fake_ee.Geometry.Rectangle.side_effect = lambda coords: coords
        chain = _FakeEEChain(url='https://earthengine.example/a:getPixels')
        fake_ee.ImageCollection.return_value = chain
        fake_ee.Image.return_value = chain

        sessions_seen = []

        def _fake_download_file(url, output_folder, session=None, **_kwargs):
            sessions_seen.append(session)
            out = os.path.join(output_folder, 'tile.tif')
            with open(out, 'wb') as fh:
                fh.write(b'FAKE_TIFF')
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
                self.assertTrue(os.path.exists(p))

        empty_chain = _FakeEEChain(download_url_error=RuntimeError(
            'Image.clipToBoundsAndScale: Image has no bands.'))
        fake_ee.ImageCollection.return_value = empty_chain
        fake_ee.Image.return_value = empty_chain
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.assertEqual(
                download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-10-01',
                    end_date='2026-11-01',
                    bounds_str='24.0,84.0,26.0,86.0',
                    tile_size_deg=4.0,
                    max_workers=1,
                    ee_module=fake_ee,
                ),
                [],
            )

    def test_consolidate_place_svobs_csvs_supports_p1m_and_p1y(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv1 = os.path.join(tmp_dir, 'a.csv')
            out = os.path.join(tmp_dir, 'consolidated.csv')
            with open(csv1, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area', 'count'
                ])
                w.writerow(['country/IND', '2026-10', 'P1M', '10.5', '2'])
                w.writerow(['country/IND', '2026', 'P1Y', '10.5', '2'])
                w.writerow(['country/IND', '2026', 'P1Y', '10.5', '2'])

            count = download_script._consolidate_place_svobs_csvs([csv1], out)
            self.assertEqual(count, 2)
            with open(out, 'r', encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['observationPeriod'], 'P1Y')
            self.assertEqual(rows[1]['observationPeriod'], 'P1M')

    def test_consolidate_place_svobs_csvs_raises_on_conflicting_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv1 = os.path.join(tmp_dir, 'a.csv')
            out = os.path.join(tmp_dir, 'consolidated.csv')
            with open(csv1, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area', 'count'
                ])
                w.writerow(['country/IND', '2026-10', 'P1M', '10.5', '2'])
                w.writerow(['country/IND', '2026-10', 'P1M', '99.0', '3'])

            with self.assertRaises(ValueError):
                download_script._consolidate_place_svobs_csvs([csv1], out)

    def test_csv_has_data_rows_and_clean_local_intermediates(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            header_only = os.path.join(tmp_dir, 'header_only.csv')
            with open(header_only, 'w', encoding='utf-8') as fh:
                fh.write('area,date,s2CellId\n')
            self.assertFalse(download_script._csv_has_data_rows(header_only))

            with_row = os.path.join(tmp_dir, 'with_row.csv')
            with open(with_row, 'w', encoding='utf-8') as fh:
                fh.write('area,date,s2CellId\n1.0,2026-10,dcid:s2CellId/0x1\n')
            self.assertTrue(download_script._csv_has_data_rows(with_row))

            for sub in ('geotiff', 'raster_csv', 'events', 'cache'):
                os.makedirs(os.path.join(tmp_dir, sub), exist_ok=True)
            download_script._clean_local_intermediates(tmp_dir)
            for sub in ('geotiff', 'raster_csv', 'events'):
                self.assertFalse(os.path.exists(os.path.join(tmp_dir, sub)))
            self.assertTrue(os.path.isdir(os.path.join(tmp_dir, 'cache')))

    def test_resolve_place_cache_file_downloads_from_gcs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_blob = mock.MagicMock()

            def _write_cache(dest_path):
                with open(dest_path, 'wb') as fh:
                    fh.write(b'PICKLE')

            mock_blob.download_to_filename.side_effect = _write_cache
            mock_client = mock.MagicMock()
            mock_client.bucket.return_value.blob.return_value = mock_blob
            with mock.patch('google.cloud.storage.Client',
                            return_value=mock_client):
                local_path = download_script._resolve_place_cache_file(
                    'gs://datcom-prod-imports/place_cache/test.pkl',
                    tmp_dir,
                )
            self.assertTrue(os.path.exists(local_path))
            mock_client.bucket.assert_called_once_with('datcom-prod-imports')
            mock_client.bucket.return_value.blob.assert_called_once_with(
                'place_cache/test.pkl')

    def test_generate_place_svobs_for_year_skips_header_only_and_sets_timeout(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            header_only = os.path.join(tmp_dir, 'dw_flood_2026-01.csv')
            with open(header_only, 'w', encoding='utf-8') as fh:
                fh.write('area,date,s2CellId\n')
            with mock.patch.object(download_script.subprocess,
                                   'run') as mock_run:
                res = download_script.generate_place_svobs_for_year(
                    raster_csvs=[header_only],
                    output_dir=tmp_dir,
                    year='2026',
                    place_cache_file='',
                    subprocess_timeout=123,
                )
            self.assertEqual(res, [])
            mock_run.assert_not_called()

            valid_csv = os.path.join(tmp_dir, 'dw_flood_2026-02.csv')
            with open(valid_csv, 'w', encoding='utf-8') as fh:
                fh.write('area,date,s2CellId\n1.0,2026-02,dcid:s2CellId/0x1\n')
            with mock.patch.object(download_script.subprocess,
                                   'run') as mock_run:
                download_script.generate_place_svobs_for_year(
                    raster_csvs=[header_only, valid_csv],
                    output_dir=tmp_dir,
                    year='2026',
                    place_cache_file='',
                    subprocess_timeout=123,
                )
            mock_run.assert_called_once()
            cmd_args = mock_run.call_args[0][0]
            self.assertIn(f'--input_csv={valid_csv}', cmd_args)
            self.assertEqual(mock_run.call_args[1]['timeout'], 123)

    def test_tile_has_flood_pixels(self):
        import numpy as np
        import rasterio
        from rasterio.transform import from_origin

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

    def test_resolve_month_raster_csv_reuses_persistent_and_legacy_gcs_cache(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, 'out')
            cache_dir = os.path.join(tmp_dir, 'gcs_cache')
            os.makedirs(os.path.join(cache_dir, 'raster_csv'), exist_ok=True)
            cached_jan = os.path.join(cache_dir, 'raster_csv',
                                      'dw_flood_2026-01.csv')
            with open(cached_jan, 'w', encoding='utf-8') as fh:
                fh.write('area,date,s2CellId\n1.0,2026-01,dcid:s2CellId/0x1\n')

            with mock.patch.object(download_script,
                                   'init_earth_engine') as mock_init_ee:
                # 1. Persistent cache hit should not initialize Earth Engine.
                jan_path, ee_mod = (
                    download_script.resolve_or_download_month_raster_csv(
                        output_dir=out_dir,
                        start_date='2026-01-01',
                        end_date='2026-02-01',
                        cache_dir=cache_dir,
                    ))
                self.assertEqual(
                    jan_path,
                    os.path.join(out_dir, 'raster_csv', 'dw_flood_2026-01.csv'),
                )
                self.assertTrue(os.path.exists(jan_path))
                self.assertIsNone(ee_mod)
                mock_init_ee.assert_not_called()

                # 2. Legacy GCS bootstrap hit should copy into persistent cache.
                def _fake_download(gcs_uri, local_path):
                    self.assertTrue(
                        gcs_uri.endswith('from_2026-02-01-raster_csv.csv'))
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    with open(local_path, 'w', encoding='utf-8') as fh:
                        fh.write(
                            'area,date,s2CellId\n2.0,2026-02,dcid:s2CellId/0x2\n'
                        )
                    return True

                with mock.patch.object(
                        download_script,
                        '_try_download_gcs_object',
                        side_effect=_fake_download,
                ):
                    feb_path, ee_mod = (
                        download_script.resolve_or_download_month_raster_csv(
                            output_dir=out_dir,
                            start_date='2026-02-01',
                            end_date='2026-03-01',
                            cache_dir=cache_dir,
                        ))
                self.assertTrue(os.path.exists(feb_path))
                self.assertTrue(
                    os.path.exists(
                        os.path.join(cache_dir, 'raster_csv',
                                     'dw_flood_2026-02.csv')))
                self.assertIsNone(ee_mod)
                mock_init_ee.assert_not_called()

    def test_resolve_month_raster_csv_skips_global_cache_for_custom_bounds(
            self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = os.path.join(tmp_dir, 'out')
            cache_dir = os.path.join(tmp_dir, 'gcs_cache')
            os.makedirs(os.path.join(cache_dir, 'raster_csv'), exist_ok=True)
            with open(
                    os.path.join(cache_dir, 'raster_csv',
                                 'dw_flood_2026-10.csv'),
                    'w',
                    encoding='utf-8',
            ) as fh:
                fh.write('GLOBAL_CACHE_DATA\n')

            fake_ee = mock.MagicMock()
            with mock.patch.object(
                    download_script,
                    'init_earth_engine',
                    return_value=fake_ee,
            ), mock.patch.object(
                    download_script,
                    'download_earthengine_tiles',
                    return_value=['/tmp/fake.tif'],
            ) as mock_dl, mock.patch.object(
                    download_script,
                    'convert_geotiffs_to_raster_csv',
                    return_value=os.path.join(out_dir, 'raster_csv',
                                              'dw_flood_2026-10.csv'),
            ):
                os.makedirs(os.path.join(out_dir, 'raster_csv'), exist_ok=True)
                path, ee_mod = (
                    download_script.resolve_or_download_month_raster_csv(
                        output_dir=out_dir,
                        start_date='2026-10-01',
                        end_date='2026-11-01',
                        bounds_str='24.0,84.0,26.0,88.0',
                        cache_dir=cache_dir,
                    ))
            mock_dl.assert_called_once()
            self.assertIs(ee_mod, fake_ee)
            self.assertTrue(path.endswith('dw_flood_2026-10.csv'))
            # Global cache file must not have been overwritten by regional run.
            with open(
                    os.path.join(cache_dir, 'raster_csv',
                                 'dw_flood_2026-10.csv'),
                    'r',
                    encoding='utf-8',
            ) as fh:
                self.assertEqual(fh.read(), 'GLOBAL_CACHE_DATA\n')

    def test_persist_and_collect_prior_year_place_svobs_csvs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = os.path.join(tmp_dir, 'gcs_cache')
            csv_2026 = os.path.join(tmp_dir, '2026.csv')
            with open(csv_2026, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area', 'count'
                ])
                w.writerow(['country/IND', '2026', 'P1Y', '100.0', '5'])

            persisted = download_script._persist_annual_place_svobs(
                '2026', [csv_2026], cache_dir)
            self.assertTrue(os.path.exists(persisted))
            # Running 2026 again should NOT duplicate 2026 from prior-year cache.
            self.assertEqual(
                download_script._collect_prior_year_place_svobs_csvs(
                    cache_dir, ['2026']),
                [],
            )
            # Rolling over into 2027 carries forward 2026 automatically.
            self.assertEqual(
                download_script._collect_prior_year_place_svobs_csvs(
                    cache_dir, ['2027']),
                [persisted],
            )


if __name__ == '__main__':
    unittest.main()

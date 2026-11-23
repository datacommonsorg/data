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
"""Unit and integration tests for dynamic_world_flood download & processing."""

import csv
import datetime
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_TEST_DIR))
if _TEST_DIR not in sys.path:
    sys.path.insert(0, _TEST_DIR)
if os.path.join(_REPO_ROOT, 'util') not in sys.path:
    sys.path.insert(0, os.path.join(_REPO_ROOT, 'util'))

import download_script  # pylint: disable=wrong-import-position


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

    def selfMask(self):
        self.calls.append(('selfMask',))
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
    """Tests for Dynamic World V1 flood download and StatVar processing."""

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
            download_script.iter_month_ranges('2026-09-01', '2026-11-01'),
            [('2026-09-01', '2026-10-01'), ('2026-10-01', '2026-11-01')],
        )
        with self.assertRaises(ValueError):
            download_script.iter_month_ranges('2026-11-01', '2026-11-01')

    def test_parse_bounds_and_generate_tiles(self):
        bounds = download_script.parse_bounds('24.0, 83.0, 30.0, 89.0')
        self.assertEqual(bounds, (24.0, 83.0, 30.0, 89.0))
        tiles = download_script.generate_tiles(*bounds, tile_size_deg=4.0)
        self.assertEqual(
            tiles,
            [
                (24.0, 83.0, 28.0, 87.0),
                (24.0, 87.0, 28.0, 89.0),
                (28.0, 83.0, 30.0, 87.0),
                (28.0, 87.0, 30.0, 89.0),
            ],
        )
        with self.assertRaises(ValueError):
            download_script.parse_bounds('30.0,83.0,24.0,89.0')

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
        self.assertIn(('selfMask',), calls)

    def test_download_earthengine_tiles_moves_downloaded_file_to_tif(self):
        fake_ee = mock.MagicMock()
        chain = _FakeEEChain(
            url=
            'https://earthengine.googleapis.com/v1/projects/p/thumbnails/id:getPixels'
        )
        fake_ee.ImageCollection.return_value = chain
        fake_ee.Image.return_value = chain
        fake_ee.Geometry.Rectangle.side_effect = lambda coords: coords

        def _fake_download_file(url, output_folder, **_kwargs):
            out = os.path.join(output_folder, 'id:getPixels.xlsx')
            with open(out, 'wb') as fh:
                fh.write(b'II*\x00fake_geotiff_bytes')
            return True

        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch.object(download_script,
                                   'init_earth_engine',
                                   return_value=fake_ee), mock.patch.object(
                                       download_script.download_util_script,
                                       'download_file',
                                       side_effect=_fake_download_file,
                                   ) as dl_mock:
                paths = download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-10-01',
                    end_date='2026-11-01',
                    bounds_str='24.0,84.0,26.0,88.0',
                    tile_size_deg=4.0,
                    skip_existing=True,
                )
                self.assertEqual(len(paths), 1)
                self.assertTrue(paths[0].endswith('.tif'))
                self.assertTrue(os.path.exists(paths[0]))
                dl_mock.assert_called_once()

                paths_second = download_script.download_earthengine_tiles(
                    output_dir=tmp_dir,
                    start_date='2026-10-01',
                    end_date='2026-11-01',
                    bounds_str='24.0,84.0,26.0,88.0',
                    tile_size_deg=4.0,
                    skip_existing=True,
                )
                self.assertEqual(paths_second, paths)
                dl_mock.assert_called_once()

    def test_download_earthengine_tiles_skips_empty_collection_and_raises_on_error(
        self,):
        fake_ee = mock.MagicMock()
        empty_chain = _FakeEEChain(download_url_error=RuntimeError(
            'Image.updateMask: If one image has no bands, the other must also have no bands.'
        ))
        fake_ee.ImageCollection.return_value = empty_chain
        fake_ee.Image.return_value = empty_chain
        fake_ee.Geometry.Rectangle.side_effect = lambda coords: coords

        with tempfile.TemporaryDirectory() as tmp_dir:
            paths = download_script.download_earthengine_tiles(
                output_dir=tmp_dir,
                start_date='2026-07-01',
                end_date='2026-08-01',
                bounds_str='24.0,84.0,26.0,88.0',
                tile_size_deg=4.0,
                ee_module=fake_ee,
            )
            self.assertEqual(paths, [])

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
                    ee_module=fake_ee,
                )

    def test_consolidate_place_svobs_csvs_deduplicates_and_sorts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv1 = os.path.join(tmp_dir, 'a.csv')
            csv2 = os.path.join(tmp_dir, 'b.csv')
            out = os.path.join(tmp_dir, 'consolidated.csv')
            with open(csv1, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area', 'count'
                ])
                w.writerow(['s2CellId/0x2', '2026-10', 'P1M', '1.5', '1'])
            with open(csv2, 'w', encoding='utf-8', newline='') as fh:
                w = csv.writer(fh)
                w.writerow([
                    'observationAbout', 'observationDate', 'observationPeriod',
                    'area', 'count'
                ])
                w.writerow(['s2CellId/0x2', '2026-10', 'P1M', '1.5', '1'])
                w.writerow(['s2CellId/0x1', '2026-09', 'P1M', '2.5', '2'])

            count = download_script._consolidate_place_svobs_csvs([csv1, csv2],
                                                                  out)
            self.assertEqual(count, 2)
            with open(out, 'r', encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['observationDate'], '2026-09')
            self.assertEqual(rows[1]['observationDate'], '2026-10')

    def test_stat_var_processor_end_to_end_on_sample_fixture(self):
        sample_csv = os.path.join(_TEST_DIR, 'test_data',
                                  'sample_place_svobs.csv')
        expected_csv = os.path.join(_TEST_DIR, 'test_data',
                                    'expected_output.csv')
        expected_tmcf = os.path.join(_TEST_DIR, 'test_data',
                                     'expected_output.tmcf')
        processor = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                                 'stat_var_processor.py')
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_prefix = os.path.join(tmp_dir, 'out')
            counters = os.path.join(tmp_dir, 'counters.csv')
            res = subprocess.run(
                [
                    sys.executable,
                    processor,
                    f'--input_data={sample_csv}',
                    f'--pv_map={os.path.join(_TEST_DIR, "dynamic_world_flood_pvmap.csv")}',
                    f'--config_file={os.path.join(_TEST_DIR, "dynamic_world_flood_metadata.csv")}',
                    f'--existing_schema_mcf={os.path.join(_TEST_DIR, "dynamic_world_flood_schema.mcf")}',
                    f'--output_path={out_prefix}',
                    f'--output_counters={counters}',
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, msg=res.stderr)
            out_csv = f'{out_prefix}.csv'
            out_tmcf = f'{out_prefix}.tmcf'
            self.assertTrue(os.path.exists(out_csv))
            self.assertTrue(os.path.exists(out_tmcf))
            with open(out_csv, 'r', encoding='utf-8') as fh:
                actual_rows = list(csv.DictReader(fh))
            with open(expected_csv, 'r', encoding='utf-8') as fh:
                expected_rows = list(csv.DictReader(fh))
            self.assertEqual(actual_rows, expected_rows)
            with open(out_tmcf, 'r', encoding='utf-8') as fh:
                actual_tmcf = fh.read().replace('out->', 'expected_output->')
            with open(expected_tmcf, 'r', encoding='utf-8') as fh:
                self.assertEqual(actual_tmcf, fh.read())


if __name__ == '__main__':
    unittest.main()

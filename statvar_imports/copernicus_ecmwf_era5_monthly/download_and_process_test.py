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
"""Unit and end-to-end tests for download_and_process.py."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
_STATVAR_PROCESSOR_PATH = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                                       'stat_var_processor.py')
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download_and_process


class DownloadAndProcessTest(unittest.TestCase):

    def setUp(self):
        self.test_data_dir = os.path.join(_SCRIPT_DIR, 'test_data')
        self.temp_dir = tempfile.mkdtemp()
        self.pv_map_path = os.path.join(
            _SCRIPT_DIR, 'copernicus_ecmwf_era5_monthly_pvmap.csv')
        self.config_file_path = os.path.join(
            _SCRIPT_DIR, 'copernicus_ecmwf_era5_monthly_metadata.csv')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_kelvin_to_celsius_matches_expected_csv(self):
        """Verifies exact parity with kelvin2celsius.sh on historical test data."""
        in_csv = os.path.join(self.test_data_dir,
                              'all_administrativearea2_2020-06.ee.csv')
        expected_csv = os.path.join(
            self.test_data_dir,
            'all_administrativearea2_2020-06.ee.celsius.csv')
        got_csv = os.path.join(
            self.temp_dir, 'all_administrativearea2_2020-06.ee.celsius.csv')

        download_and_process.convert_kelvin_to_celsius_csv(in_csv, got_csv)

        with open(got_csv, mode='r',
                  encoding='utf-8') as got_f, open(expected_csv,
                                                   mode='r',
                                                   encoding='utf-8') as want_f:
            self.assertEqual(got_f.read(), want_f.read())

    def test_kelvin_to_celsius_edge_cases(self):
        """Tests empty, non-positive, and non-numeric values in conversion."""
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value(''), '')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('   '), '   ')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('NA'), 'NA')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('inf'), 'inf')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('-inf'),
            '-inf')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('nan'), 'nan')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('0'), '0')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('-5.0'),
            '-5.0')
        self.assertEqual(
            download_and_process.convert_kelvin_to_celsius_value('304.15'),
            '31')

        empty_csv = os.path.join(self.temp_dir, 'empty.csv')
        out_empty_csv = os.path.join(self.temp_dir, 'empty.celsius.csv')
        with open(empty_csv, mode='w', encoding='utf-8') as f:
            f.write('')
        download_and_process.convert_kelvin_to_celsius_csv(
            empty_csv, out_empty_csv)
        with open(out_empty_csv, mode='r', encoding='utf-8') as f:
            self.assertEqual(f.read(), '')

    def test_era5_land_band_mapping_and_conversion(self):
        """Tests ERA5-Land band renaming and Kelvin-to-Celsius conversion."""
        era5_land_csv = os.path.join(self.temp_dir, 'era5_land_raw.csv')
        converted_csv = os.path.join(self.temp_dir, 'era5_land.celsius.csv')
        with open(era5_land_csv, mode='w', encoding='utf-8', newline='') as f:
            f.write(
                'system:index,date,dcid,dewpoint_temperature_2m,'
                'temperature_2m_max,temperature_2m,temperature_2m_min,'
                'surface_pressure,total_precipitation_sum,'
                'u_component_of_wind_10m,v_component_of_wind_10m,.geo\n'
                'idx_1,2020-07,wikidataId/Q29036,296.66422655124086,'
                '310.00189208984375,300.50272208478117,291.9393310546875,'
                '95121.29368130582,0.30748571691043497,-1.1752337022832051,'
                '0.5645652925423121,"{""type"":""MultiPoint"",""coordinates"":[]}"\n'
            )

        download_and_process.convert_kelvin_to_celsius_csv(
            era5_land_csv, converted_csv)

        with open(converted_csv, mode='r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        self.assertEqual(
            lines[0],
            'system:index,date,dcid,dewpoint_2m_temperature,'
            'maximum_2m_air_temperature,mean_2m_air_temperature,'
            'minimum_2m_air_temperature,surface_pressure,total_precipitation,'
            'u_component_of_wind_10m,v_component_of_wind_10m,.geo',
        )
        self.assertIn('23.5142,36.8519,27.3527,18.7893', lines[1])

    def test_write_ee_feature_collection_to_csv(self):
        """Tests writing an Earth Engine FeatureCollection dict to CSV."""
        fc_info = {
            'features': [{
                'id': '0001_202007',
                'properties': {
                    'date': '2020-07',
                    'dcid': 'geoId/06',
                    'dewpoint_temperature_2m': 285.15,
                    'temperature_2m_max': 303.15,
                    'temperature_2m': 293.15,
                    'temperature_2m_min': 283.15,
                    'surface_pressure': 101325.0,
                    'total_precipitation_sum': 0.05,
                    'u_component_of_wind_10m': 1.5,
                    'v_component_of_wind_10m': -0.5,
                },
            }]
        }
        raw_csv = os.path.join(self.temp_dir,
                               'all_administrativearea1_2020-07.ee.csv')
        count = download_and_process.write_ee_feature_collection_to_csv(
            fc_info, raw_csv)
        self.assertEqual(count, 1)

        celsius_csv = os.path.join(
            self.temp_dir, 'all_administrativearea1_2020-07.ee.celsius.csv')
        download_and_process.convert_kelvin_to_celsius_csv(raw_csv, celsius_csv)
        with open(celsius_csv, mode='r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn(
            '0001_202007,2020-07,geoId/06,12,30,20,10,101325.0,0.05,1.5,-0.5',
            lines[1])

    def test_generate_year_months(self):
        """Tests generating YYYY-MM ranges across year boundaries."""
        self.assertEqual(
            download_and_process.generate_year_months('2020-11', '2021-02'),
            ['2020-11', '2020-12', '2021-01', '2021-02'],
        )
        self.assertEqual(
            download_and_process.generate_year_months('2020-07', '2020-07'),
            ['2020-07'],
        )
        self.assertEqual(
            download_and_process.generate_year_months('2021-01', '2020-07'),
            [],
        )

    def test_sync_baseline_from_gcs_via_util(self):
        """Tests GCS baseline download into history_files using util helpers."""
        gcs_uri = (
            'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/'
            'era5_monthly/all_administrativearea2_2020-06.ee.celsius.csv')
        history_dir = os.path.join(self.temp_dir, 'history_files')

        def fake_download_file(url, output_folder, unzip=False, **kwargs):
            del unzip, kwargs
            self.assertEqual(
                url,
                'https://storage.googleapis.com/datacommons_public/'
                'unresolved_mcf/copernicus_ecmwf/era5_monthly/'
                'all_administrativearea2_2020-06.ee.celsius.csv',
            )
            os.makedirs(output_folder, exist_ok=True)
            out_path = os.path.join(
                output_folder, 'all_administrativearea2_2020-06.ee.celsius.csv')
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write('date,dcid\n2020-06,geoId/06\n')
            return True

        with patch.object(
                download_and_process.file_util,
                'file_get_matching',
                return_value=[gcs_uri],
        ) as mock_get_matching, patch.object(
                download_and_process.download_util_script,
                'download_file',
                side_effect=fake_download_file,
        ) as mock_download_file:
            downloaded = download_and_process.sync_baseline_from_gcs(
                'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/',
                history_dir,
                max_workers=2,
            )

        mock_get_matching.assert_called_once()
        mock_download_file.assert_called_once()
        self.assertEqual(len(downloaded), 1)
        self.assertTrue(os.path.exists(downloaded[0]))

    def test_sync_baseline_from_gcs_fallback_to_file_copy(self):
        """Tests fallback to file_util.file_copy when download_file returns False."""
        gcs_uri = (
            'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/'
            'era5_monthly/all_administrativearea2_2020-06.ee.celsius.csv')
        history_dir = os.path.join(self.temp_dir, 'history_files_fallback')

        def fake_file_copy(src, dst):
            self.assertEqual(src, gcs_uri)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'w', encoding='utf-8') as f:
                f.write('date,dcid\n2020-06,geoId/06\n')
            return dst

        with patch.object(
                download_and_process.file_util,
                'file_get_matching',
                return_value=[gcs_uri],
        ), patch.object(
                download_and_process.download_util_script,
                'download_file',
                return_value=False,
        ), patch.object(
                download_and_process.file_util,
                'file_copy',
                side_effect=fake_file_copy,
        ) as mock_file_copy:
            downloaded = download_and_process.sync_baseline_from_gcs(
                'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/',
                history_dir,
                max_workers=2,
            )

        mock_file_copy.assert_called_once()
        self.assertEqual(len(downloaded), 1)
        self.assertTrue(os.path.exists(downloaded[0]))

    def test_end_to_end_pipeline_produces_expected_csv_and_tmcf(self):
        """Tests full pipeline from raw Kelvin CSV through StatVarProcessor."""
        history_dir = os.path.join(self.temp_dir, 'history_files')
        raw_dir = os.path.join(self.temp_dir, 'raw_files')
        input_dir = os.path.join(self.temp_dir, 'input_files')
        output_dir = os.path.join(self.temp_dir, 'output')
        counters_dir = os.path.join(self.temp_dir, 'counters')
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(counters_dir, exist_ok=True)

        shutil.copyfile(
            os.path.join(self.test_data_dir,
                         'all_administrativearea2_2020-06.ee.csv'),
            os.path.join(raw_dir, 'all_administrativearea2_2020-06.ee.csv'),
        )

        history_files, input_files = download_and_process.run_pipeline(
            gcs_baseline_prefix=
            'gs://datacommons_public/unresolved_mcf/copernicus_ecmwf/era5_monthly/',
            history_dir=history_dir,
            raw_dir=raw_dir,
            input_dir=input_dir,
            ee_dataset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
            ee_place_assets=[],
            ee_start_date='2020-07',
            ee_end_date='2020-07',
            ee_project='datcom-earth-engine',
            reduce_region_scale=1000,
            skip_gcs_baseline=True,
            skip_ee_fetch=True,
            strict_ee=False,
            parallelism=2,
        )

        self.assertEqual(history_files, [])
        self.assertEqual(len(input_files), 1)

        output_prefix = os.path.join(output_dir, 'era5_monthly')
        counters_path = os.path.join(counters_dir, 'era5_monthly_counters.csv')
        input_pattern = (f'{os.path.join(history_dir, "*.celsius.csv")},'
                         f'{os.path.join(input_dir, "*.celsius.csv")}')
        cmd = [
            sys.executable,
            _STATVAR_PROCESSOR_PATH,
            f'--input_data={input_pattern}',
            f'--pv_map={self.pv_map_path}',
            f'--config_file={self.config_file_path}',
            f'--output_path={output_prefix}',
            f'--output_counters={counters_path}',
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(
            res.returncode,
            0,
            f'stat_var_processor.py failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}',
        )

        output_csv = f'{output_prefix}.csv'
        output_tmcf = f'{output_prefix}.tmcf'
        self.assertTrue(os.path.exists(output_csv))
        self.assertTrue(os.path.exists(output_tmcf))
        self.assertTrue(os.path.exists(counters_path))

        expected_output_csv = os.path.join(self.test_data_dir,
                                           'era5_monthly.csv')
        expected_output_tmcf = os.path.join(self.test_data_dir,
                                            'era5_monthly.tmcf')
        with open(output_csv, mode='r', encoding='utf-8') as got_csv_f, open(
                expected_output_csv, mode='r', encoding='utf-8') as want_csv_f:
            self.assertEqual(got_csv_f.read(), want_csv_f.read())

        with open(output_tmcf, mode='r', encoding='utf-8') as got_tmcf_f, open(
                expected_output_tmcf, mode='r',
                encoding='utf-8') as want_tmcf_f:
            got_tmcf_lines = got_tmcf_f.read().splitlines()
            want_tmcf_lines = want_tmcf_f.read().splitlines()
            self.assertEqual(got_tmcf_lines[0], want_tmcf_lines[0])
            self.assertEqual(sorted(got_tmcf_lines), sorted(want_tmcf_lines))

    def test_end_to_end_pipeline_merges_history_and_input_files(self):
        """Tests that StatVarProcessor processes both history_files and input_files."""
        history_dir = os.path.join(self.temp_dir, 'history_files')
        input_dir = os.path.join(self.temp_dir, 'input_files')
        output_dir = os.path.join(self.temp_dir, 'output_merged')
        counters_dir = os.path.join(self.temp_dir, 'counters_merged')
        os.makedirs(history_dir, exist_ok=True)
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(counters_dir, exist_ok=True)

        # Stage a 2020-06 historical baseline file in history_files/
        shutil.copyfile(
            os.path.join(self.test_data_dir,
                         'all_administrativearea2_2020-06.ee.celsius.csv'),
            os.path.join(history_dir,
                         'all_administrativearea2_2020-06.ee.celsius.csv'),
        )
        # Stage a 2020-07 newly converted file in input_files/
        with open(
                os.path.join(input_dir,
                             'all_administrativearea2_2020-07.ee.celsius.csv'),
                mode='w',
                encoding='utf-8',
                newline='',
        ) as f:
            f.write(
                'system:index,date,dcid,dewpoint_2m_temperature,'
                'maximum_2m_air_temperature,mean_2m_air_temperature,'
                'minimum_2m_air_temperature,surface_pressure,'
                'total_precipitation,u_component_of_wind_10m,'
                'v_component_of_wind_10m,.geo\n'
                'idx_202007,2020-07,wikidataId/Q29036,24.5,38.0,29.0,20.0,'
                '95100.0,0.2,-1.0,0.5,"{""type"":""MultiPoint"",""coordinates"":[]}"\n'
            )

        output_prefix = os.path.join(output_dir, 'era5_monthly')
        counters_path = os.path.join(counters_dir, 'era5_monthly_counters.csv')
        input_pattern = (f'{os.path.join(history_dir, "*.celsius.csv")},'
                         f'{os.path.join(input_dir, "*.celsius.csv")}')
        cmd = [
            sys.executable,
            _STATVAR_PROCESSOR_PATH,
            f'--input_data={input_pattern}',
            f'--pv_map={self.pv_map_path}',
            f'--config_file={self.config_file_path}',
            f'--output_path={output_prefix}',
            f'--output_counters={counters_path}',
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(
            res.returncode,
            0,
            f'stat_var_processor.py failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}',
        )

        with open(f'{output_prefix}.csv', mode='r', encoding='utf-8') as f:
            rows = f.read().splitlines()
        # 1 header + 35 rows from 2020-06 + 7 rows from 2020-07 = 43 lines
        self.assertEqual(len(rows), 43)
        self.assertTrue(any(r.startswith('2020-06,') for r in rows[1:]))
        self.assertTrue(any(r.startswith('2020-07,') for r in rows[1:]))

    def test_fetch_ee_feature_collection_pagination_and_retry(self):
        """Tests multi-page computeFeatures pagination and transient retry."""
        mock_ee = MagicMock()
        mock_dataset = MagicMock()
        mock_dataset.first.return_value.getInfo.return_value = {'id': '202007'}
        mock_dataset.map.side_effect = lambda img_fn: [img_fn(MagicMock())]
        mock_ee.ImageCollection.return_value.filterDate.return_value = (
            mock_dataset)

        mock_places = MagicMock()
        mock_places.first.return_value.getInfo.return_value = {'id': 'place1'}
        mock_place = MagicMock()
        mock_flattened = MagicMock()
        mock_mapped_places = MagicMock()
        mock_mapped_places.flatten.return_value = mock_flattened

        def places_map_side_effect(place_fn):
            place_fn(mock_place)
            return mock_mapped_places

        mock_places.map.side_effect = places_map_side_effect
        mock_ee.FeatureCollection.return_value = mock_places

        calls = {'count': 0}

        def compute_features_side_effect(params):
            calls['count'] += 1
            self.assertEqual(
                params.get('pageSize'),
                download_and_process.EE_COMPUTE_FEATURES_PAGE_SIZE,
            )
            if calls['count'] == 1:
                raise RuntimeError('Transient EE 503 error')
            if 'pageToken' not in params:
                return {
                    'type': 'FeatureCollection',
                    'features': [{
                        'id': 'f1',
                        'properties': {
                            'date': '2020-07',
                            'dcid': 'geoId/06',
                            'temperature_2m': 293.15,
                        },
                    }],
                    'nextPageToken': 'page_2',
                }
            return {
                'type':
                    'FeatureCollection',
                'features': [{
                    'id': 'f2',
                    'properties': {
                        'date': '2020-07',
                        'dcid': 'geoId/36',
                        'temperature_2m': 298.15,
                    },
                }],
            }

        mock_ee.data.computeFeatures.side_effect = compute_features_side_effect

        raw_dir = os.path.join(self.temp_dir, 'ee_raw')
        input_dir = os.path.join(self.temp_dir, 'ee_input')
        with patch.object(download_and_process, 'ee',
                          mock_ee), patch('download_and_process.time.sleep'):
            generated = download_and_process.fetch_era5_land_from_ee(
                dataset_asset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
                place_assets=[
                    'projects/datcom-earth-engine/assets/all_administrativearea2'
                ],
                start_ym='2020-07',
                end_ym='2020-07',
                raw_dir=raw_dir,
                input_dir=input_dir,
                ee_project='datcom-earth-engine',
                reduce_region_scale=1000,
                strict=True,
            )

        self.assertEqual(len(generated), 1)
        self.assertEqual(calls['count'], 3)
        # Once per _compute_ee_monthly_features attempt (2 attempts due to retry).
        self.assertEqual(mock_place.geometry.call_count, 2)
        mock_ee.Reducer.mean.return_value.unweighted.assert_called()
        self.assertEqual(
            mock_ee.Algorithms.If.call_args_list[0].args[1:],
            (download_and_process.ADAPTIVE_LARGE_REGION_SCALE, 1000),
        )
        with open(generated[0], mode='r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn('geoId/06', content)
        self.assertIn('geoId/36', content)

    def test_fetch_era5_land_from_ee_parallel_and_skips_cached(self):
        """Verifies parallel EE fetches and skipping existing celsius CSVs."""
        mock_ee = MagicMock()
        raw_dir = os.path.join(self.temp_dir, 'raw_par')
        input_dir = os.path.join(self.temp_dir, 'input_par')
        os.makedirs(input_dir, exist_ok=True)
        cached_file = os.path.join(
            input_dir, 'all_administrativearea1_2020-07.ee.celsius.csv')
        with open(cached_file, mode='w', encoding='utf-8') as f:
            f.write('date,dcid\n2020-07,geoId/06\n')

        fetched_pairs = []

        def fake_compute(dataset_asset, geo_locations_asset, year_month,
                         reduce_region_scale):
            del dataset_asset
            self.assertEqual(reduce_region_scale, 1000)
            fetched_pairs.append(
                (os.path.basename(geo_locations_asset), year_month))
            return {
                'type':
                    'FeatureCollection',
                'features': [{
                    'id': f'{year_month}_1',
                    'properties': {
                        'date': year_month,
                        'dcid': 'geoId/06',
                        'temperature_2m': 293.15,
                    },
                }],
            }

        with patch.object(download_and_process, 'ee', mock_ee), patch.object(
                download_and_process,
                '_compute_ee_monthly_features_with_retry',
                side_effect=fake_compute):
            generated = download_and_process.fetch_era5_land_from_ee(
                dataset_asset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
                place_assets=[
                    'projects/datcom-earth-engine/assets/all_administrativearea1',
                    'projects/datcom-earth-engine/assets/all_administrativearea2',
                ],
                start_ym='2020-07',
                end_ym='2020-08',
                raw_dir=raw_dir,
                input_dir=input_dir,
                ee_project='datcom-earth-engine',
                reduce_region_scale=1000,
                strict=True,
                ee_parallelism=3,
            )

        self.assertEqual(len(generated), 4)
        self.assertEqual(
            sorted(fetched_pairs),
            [
                ('all_administrativearea1', '2020-08'),
                ('all_administrativearea2', '2020-07'),
                ('all_administrativearea2', '2020-08'),
            ],
        )

    def test_fetch_era5_land_from_ee_strict_raises_on_init_failure(self):
        """Verifies strict=True propagates Earth Engine initialization failures."""
        mock_ee = MagicMock()
        mock_ee.Initialize.side_effect = RuntimeError('Auth error')
        with patch.object(download_and_process, 'ee', mock_ee):
            with self.assertRaises(RuntimeError):
                download_and_process.fetch_era5_land_from_ee(
                    dataset_asset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
                    place_assets=[
                        'projects/datcom-earth-engine/assets/all_administrativearea1'
                    ],
                    start_ym='2020-07',
                    end_ym='2020-07',
                    raw_dir=os.path.join(self.temp_dir, 'raw'),
                    input_dir=os.path.join(self.temp_dir, 'input'),
                    ee_project='datcom-earth-engine',
                    reduce_region_scale=1000,
                    strict=True,
                )

    def test_fetch_era5_land_from_ee_strict_raises_on_empty_features(self):
        """Verifies strict=True raises when EE returns no features for a month."""
        mock_ee = MagicMock()
        mock_ee.ImageCollection.return_value.filterDate.return_value.first.return_value.getInfo.return_value = None
        with patch.object(download_and_process, 'ee', mock_ee):
            with self.assertRaises(RuntimeError):
                download_and_process.fetch_era5_land_from_ee(
                    dataset_asset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
                    place_assets=[
                        'projects/datcom-import-automation-prod/assets/all_administrativearea1'
                    ],
                    start_ym='2020-07',
                    end_ym='2020-07',
                    raw_dir=os.path.join(self.temp_dir, 'raw_empty'),
                    input_dir=os.path.join(self.temp_dir, 'input_empty'),
                    ee_project='datcom-import-automation-prod',
                    reduce_region_scale=1000,
                    strict=True,
                )

    def test_fetch_era5_land_from_ee_non_strict_stops_on_permission_error(self):
        """Verifies strict=False aborts remaining months on 403 permission error."""
        mock_ee = MagicMock()
        mock_ee.ImageCollection.return_value.filterDate.return_value.first.return_value.getInfo.side_effect = (
            RuntimeError(
                "403 Permission 'earthengine.computations.create' denied"))
        with patch.object(download_and_process, 'ee', mock_ee), patch(
                'download_and_process.time.sleep') as mock_sleep:
            generated = download_and_process.fetch_era5_land_from_ee(
                dataset_asset='ECMWF/ERA5_LAND/MONTHLY_AGGR',
                place_assets=[
                    'projects/datcom-earth-engine/assets/all_administrativearea1',
                    'projects/datcom-earth-engine/assets/all_administrativearea2',
                ],
                start_ym='2020-07',
                end_ym='2020-12',
                raw_dir=os.path.join(self.temp_dir, 'raw_perm'),
                input_dir=os.path.join(self.temp_dir, 'input_perm'),
                ee_project='datcom-earth-engine',
                reduce_region_scale=1000,
                strict=False,
            )

        self.assertEqual(generated, [])
        mock_sleep.assert_not_called()
        self.assertEqual(
            mock_ee.ImageCollection.return_value.filterDate.call_count, 1)


if __name__ == '__main__':
    unittest.main()

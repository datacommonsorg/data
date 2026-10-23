# Copyright 2025 Google LLC
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
"""Unit tests for California School Performance (CAASPP) download and processing."""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Ensure import directory is in sys.path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import download
import process


class CaliforniaSchoolPerformanceTest(unittest.TestCase):

    def test_discover_year_urls_known_years(self):
        """Verify known year URL mapping retrieval and probe_latest revision upgrade."""
        urls_2015 = download.discover_year_urls(2015)
        self.assertIsNotNone(urls_2015)
        self.assertEqual(urls_2015,
                         ('sb_ca2015_all_csv_v3.zip', 'sb_ca2015_1_csv_v3.zip'))

        urls_2024 = download.discover_year_urls(2024)
        self.assertIsNotNone(urls_2024)
        self.assertEqual(urls_2024,
                         ('sb_ca2024_all_csv_v1.zip', 'sb_ca2024_1_csv_v1.zip'))

        # Verify probe_latest=True upgrades recent year (e.g. 2024) if v2 is published
        with patch.object(
                download,
                'probe_url_exists',
                side_effect=lambda u: u.endswith('sb_ca2024_all_csv_v2.zip'),
        ):
            urls_2024_v2 = download.discover_year_urls(2024,
                                                       data_mode='all_groups',
                                                       probe_latest=True)
        self.assertEqual(urls_2024_v2,
                         ('sb_ca2024_all_csv_v2.zip', 'sb_ca2024_1_csv_v2.zip'))

    def test_discover_year_urls_probes_descending(self):
        """Verify future years probe versions in descending order (v4 down to v1) for the active data_mode."""
        probed_urls = []

        def fake_probe(url):
            probed_urls.append(url)
            # Simulate both v2 and v1 existing on the server; v2 should be picked first.
            return url.endswith('_v2.zip') or url.endswith('_v1.zip')

        with patch.object(download, 'probe_url_exists', side_effect=fake_probe):
            urls_2027 = download.discover_year_urls(2027,
                                                    data_mode='all_groups')

        self.assertEqual(urls_2027,
                         ('sb_ca2027_all_csv_v2.zip', 'sb_ca2027_1_csv_v2.zip'))
        self.assertEqual(
            probed_urls,
            [
                f'{download.BASE_URL}sb_ca2027_all_csv_v4.zip',
                f'{download.BASE_URL}sb_ca2027_all_csv_v3.zip',
                f'{download.BASE_URL}sb_ca2027_all_csv_v2.zip',
            ],
        )

    @patch.object(download, 'probe_url_exists', return_value=False)
    def test_download_parse_years(self, _):
        """Verify year string parsing logic for single, list, range, and 'all'."""
        self.assertEqual(download.parse_years('2023'), [2023])
        self.assertEqual(download.parse_years('2023, 2024'), [2023, 2024])
        self.assertEqual(download.parse_years('2021-2023'), [2021, 2022, 2023])
        self.assertEqual(download.parse_years('2023-present'),
                         [2023, 2024, 2025])
        all_years = download.parse_years('all')
        self.assertIn(2015, all_years)
        self.assertIn(2024, all_years)

    def test_normalize_and_filter_stream_caret_delimited(self):
        """Verify record normalization and entity filtering for caret-delimited format."""
        sample_caret = (
            'County Code^District Code^School Code^Type ID^Test Year^Test ID^Student Group ID^Grade^'
            'Total Students Tested^Total Students Tested with Scores^Mean Scale Score^Percentage Standard Exceeded^'
            'Percentage Standard Met^Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
            '00^00000^0000000^4^2024^1^1^3^102^100^2400.0^20.0^25.0^45.0^25.0^30.0\n'
            '01^00000^0000000^5^2024^1^1^3^62^60^2410.0^22.0^28.0^50.0^20.0^30.0\n'
            '01^12345^6789012^7^2024^1^1^3^51^50^*^10.0^20.0^30.0^30.0^40.0\n')
        # Default keep_all_entities=True retains all 3 entities (State, County, School)
        rows_all = list(
            download.normalize_and_filter_stream(io.StringIO(sample_caret)))
        self.assertEqual(len(rows_all), 3)
        self.assertEqual(rows_all[0][3], 'geoId/06')
        self.assertEqual(rows_all[0][4], '2024')
        self.assertEqual(rows_all[0][5], '1')  # Student Group ID
        self.assertEqual(rows_all[0][6], '3')  # Grade
        self.assertEqual(rows_all[0][7], '1')  # Test ID
        self.assertEqual(rows_all[0][8], '102')  # Total Students Tested
        self.assertEqual(rows_all[1][3], 'geoId/06001')
        self.assertEqual(rows_all[2][9], '')  # '*' Mean Scale Score -> ''

        # Explicitly passing keep_all_entities=False filters out Type ID 7
        rows_filtered = list(
            download.normalize_and_filter_stream(io.StringIO(sample_caret),
                                                 keep_all_entities=False))
        self.assertEqual(len(rows_filtered), 2)

    def test_normalize_and_filter_stream_comma_delimited_legacy_headers(self):
        """Verify record normalization for comma-delimited data with older header aliases."""
        sample_comma = (
            '"County Code","District Code","School Code","Type ID","Test Year","Test Id","Subgroup ID","Grade",'
            '"Students Tested","Students with Scores","Mean Scale Score","Percentage Standard Exceeded",'
            '"Percentage Standard Met","Percentage Standard Met and Above","Percentage Standard Nearly Met","Percentage Standard Not Met"\n'
            '"00","00000","0000000","4","2016","1","1","4","125","120","2450.0","25.0","30.0","55.0","20.0","25.0"\n'
        )
        stream = io.StringIO(sample_comma)
        rows = list(download.normalize_and_filter_stream(stream))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], '00')
        self.assertEqual(rows[0][3], 'geoId/06')
        self.assertEqual(rows[0][4], '2016')
        self.assertEqual(rows[0][5], '1')  # Mapped Subgroup ID
        self.assertEqual(rows[0][6], '4')  # Grade
        self.assertEqual(rows[0][7], '1')  # Mapped Test Id
        self.assertEqual(rows[0][8], '125')  # Mapped Students Tested

    def test_missing_required_headers_raises_value_error(self):
        """Verify missing required columns raise ValueError instead of silently dropping rows."""
        bad_header_stream = io.StringIO(
            'County Code^District Code^School Code^Grade^Mean Scale Score\n'
            '00^00000^0000000^3^2400.0\n')
        with self.assertRaises(ValueError):
            list(download.normalize_and_filter_stream(bad_header_stream))

    @patch.object(download, 'download_file')
    def test_corrupt_zip_redownload(self, mock_download):
        """Verify that a corrupted or truncated raw zip is detected and re-downloaded."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = os.path.join(tmp_dir, 'raw_files')
            os.makedirs(raw_dir, exist_ok=True)
            corrupt_zip = os.path.join(raw_dir, 'sb_ca2024_1_csv_v1.zip')
            with open(corrupt_zip, 'w') as f:
                f.write('corrupted non-zip content')
            self.assertTrue(os.path.exists(corrupt_zip))

            def side_effect(url, output_folder, unzip=False, headers=None):
                import zipfile
                dest_path = os.path.join(output_folder, os.path.basename(url))
                with zipfile.ZipFile(dest_path, 'w') as z:
                    z.writestr(
                        'sb_ca2024_1_csv_v1.txt',
                        'County Code^District Code^School Code^Type ID^Test Year^Test ID^Student Group ID^Grade^'
                        'Total Students Tested^Mean Scale Score^Percentage Standard Exceeded^'
                        'Percentage Standard Met^Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
                        '00^00000^0000000^4^2024^1^1^3^100^2400.0^20.0^25.0^45.0^25.0^30.0\n',
                    )
                return True

            mock_download.side_effect = side_effect

            with patch.object(download,
                              'discover_year_urls',
                              return_value=('sb_ca2024_all_csv_v1.zip',
                                            'sb_ca2024_1_csv_v1.zip')):
                out = download.download_and_process_year(2024,
                                                         'all_students',
                                                         tmp_dir,
                                                         True,
                                                         raw_dir=raw_dir)
                mock_download.assert_called_once()
                self.assertTrue(os.path.exists(out))

    def test_build_statvar_lookup_exact_canonical_count(self):
        """Verify build_statvar_lookup deterministically constructs all 5,966 canonical Google3 StatVars."""
        pv_map_path = os.path.join(_SCRIPT_DIR, 'config',
                                   'california_school_performance_pvmap.csv')
        sv_lookup = process.build_statvar_lookup(pv_map_path)
        self.assertEqual(len(sv_lookup), 868)
        unique_svs = {
            sv for entry in sv_lookup.values() for sv in entry.values() if sv
        }
        self.assertEqual(len(unique_svs), 5966)

    def test_process_emits_only_unmapped_ca_place_nodes_to_mcf(self):
        """Verify .mcf output emits only unmapped CA-... place nodes and zero StatisticalVariable nodes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_file = os.path.join(tmp_dir, 'input.txt')
            with open(in_file, 'w', encoding='utf-8') as f:
                f.write(
                    'County Code^District Code^School Code^Place^Test Year^Student Group ID^Grade^Test ID^'
                    'Total Students Tested^Mean Scale Score^Percentage Standard Exceeded^Percentage Standard Met^'
                    'Percentage Standard Met and Above^Percentage Standard Nearly Met^Percentage Standard Not Met\n'
                    '01^99999^9999999^CA-0199999-9999999^2025^1^3^1^50^2410.0^20.0^25.0^45.0^25.0^30.0\n'
                )
            out_prefix = os.path.join(tmp_dir, 'out')
            counters = process.process_files(
                input_pattern=in_file,
                pv_map_path=os.path.join(
                    _SCRIPT_DIR, 'config',
                    'california_school_performance_pvmap.csv'),
                school_map_path=os.path.join(_SCRIPT_DIR, 'config',
                                             'school_code_mapping.json'),
                output_prefix=out_prefix,
            )
            self.assertEqual(counters['generated_place_nodes'], 1)
            with open(f'{out_prefix}.mcf', 'r', encoding='utf-8') as f_mcf:
                mcf_content = f_mcf.read()
            self.assertIn('Node: dcid:CA-0199999-9999999', mcf_content)
            self.assertIn('typeOf: dcs:School', mcf_content)
            self.assertIn('containedInPlace: dcid:geoId/06001', mcf_content)
            self.assertNotIn('StatisticalVariable', mcf_content)

    def test_end_to_end_process_matches_golden_output(self):
        """Verify process.py generates exact expected CSV, TMCF, and MCF outputs on test_data."""
        sample_input = os.path.join(_SCRIPT_DIR, 'test_data',
                                    'sample_input.txt')
        expected_csv = os.path.join(_SCRIPT_DIR, 'test_data',
                                    'sample_state_output.csv')
        expected_tmcf = os.path.join(_SCRIPT_DIR, 'test_data',
                                     'sample_state_output.tmcf')

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_prefix = os.path.join(tmp_dir, 'sample_state_output')
            counters_file = os.path.join(tmp_dir, 'counters.csv')
            counters = process.process_files(
                input_pattern=sample_input,
                pv_map_path=os.path.join(
                    _SCRIPT_DIR, 'config',
                    'california_school_performance_pvmap.csv'),
                school_map_path=os.path.join(_SCRIPT_DIR, 'config',
                                             'school_code_mapping.json'),
                output_prefix=out_prefix,
                counters_path=counters_file,
            )

            self.assertEqual(counters['input_data_rows'], 19)
            self.assertEqual(counters['output_svobs_rows'], 131)
            self.assertTrue(os.path.exists(f'{out_prefix}.mcf'))
            self.assertTrue(os.path.exists(counters_file))

            # State-only sample has no unmapped CA-... schools, and canonical StatVars
            # must not be re-emitted in node_mcf.
            with open(f'{out_prefix}.mcf', 'r', encoding='utf-8') as f_mcf:
                self.assertEqual(f_mcf.read(), '')

            with open(f'{out_prefix}.csv', 'r', encoding='utf-8') as f_actual, \
                 open(expected_csv, 'r', encoding='utf-8') as f_exp:
                self.assertEqual(f_actual.read(), f_exp.read())

            with open(f'{out_prefix}.tmcf', 'r', encoding='utf-8') as f_actual, \
                 open(expected_tmcf, 'r', encoding='utf-8') as f_exp:
                self.assertEqual(f_actual.read(), f_exp.read())

    def test_single_year_download_updates_master_file(self):
        """Verify single-year download.main() writes both sb_ca<year>_normalized.txt and sb_ca_all_years_normalized.txt."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            single_path = os.path.join(tmp_dir, 'sb_ca2024_normalized.txt')

            def fake_download_year(year,
                                   data_mode,
                                   output_dir,
                                   keep_all_entities,
                                   raw_dir=None):
                with open(single_path, 'w', encoding='utf-8') as f:
                    f.write('^'.join(download.UNIFIED_HEADER) + '\n')
                    f.write(
                        '00^00000^0000000^geoId/06^2024^1^3^1^100^2400.0^20.0^25.0^45.0^25.0^30.0\n'
                    )
                return single_path

            with patch.object(download, 'FLAGS') as mock_flags, \
                 patch.object(download, 'download_and_process_year', side_effect=fake_download_year):
                mock_flags.output_dir = tmp_dir
                mock_flags.raw_dir = os.path.join(tmp_dir, 'raw')
                mock_flags.clean = False
                mock_flags.test_mode = False
                mock_flags.years = '2024'
                mock_flags.data_mode = 'all_groups'
                mock_flags.keep_all_entities = True
                download.main([])

            master_path = os.path.join(tmp_dir, 'sb_ca_all_years_normalized.txt')
            self.assertTrue(os.path.exists(single_path))
            self.assertTrue(os.path.exists(master_path))
            with open(single_path, 'r', encoding='utf-8') as f1, \
                 open(master_path, 'r', encoding='utf-8') as f2:
                self.assertEqual(f1.read(), f2.read())


if __name__ == '__main__':
    unittest.main()

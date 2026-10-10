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
"""Unit and PVMAP integration tests for OpportunityInsightsOutcomes download.py."""

import csv
import io
import os
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from statvar_imports.opportunity_insights_outcomes import download
from statvar_imports.opportunity_insights_outcomes import preprocess


def _load_expected_header_to_sv(
    expected_input_dir: str, expected_output_csv: str
) -> dict[str, tuple[str, str, str, str]]:
    """Reconstructs header_to_sv from committed test_data without running stat_var_processor.py."""
    ordered_headers = []
    for fname in sorted(os.listdir(expected_input_dir)):
        if not fname.endswith('_cleaned.csv'):
            continue
        with open(
            os.path.join(expected_input_dir, fname), 'r', encoding='utf-8'
        ) as f:
            reader = csv.reader(f)
            headers = next(reader)[1:]
            for row in reader:
                for idx, val in enumerate(row[1:]):
                    if val.strip():
                        ordered_headers.append(headers[idx])

    header_to_sv = {}
    with open(expected_output_csv, 'r', encoding='utf-8') as f:
        for norm_h, row in zip(ordered_headers, csv.DictReader(f)):
            header_to_sv[norm_h] = (
                row['observationDate'],
                row['observationPeriod'],
                row['variableMeasured'],
                row.get('unit', ''),
            )
    return header_to_sv


class DownloadAndPvmapTest(unittest.TestCase):

    def test_format_geo_id(self):
        self.assertEqual(
            preprocess.format_geo_id({'cz': '100'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            preprocess.format_geo_id({'cz': '100.0'}, 'commuting_zone'),
            'geoId/cz00100',
        )
        self.assertEqual(
            preprocess.format_geo_id({'state': '6', 'county': '85'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            preprocess.format_geo_id({'state': '6.0', 'county': '85.0'}, 'county'),
            'geoId/06085',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6', 'county': '85', 'tract': '500100'}, 'tract'
            ),
            'geoId/06085500100',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6.0', 'county': '85.0', 'tract': '500100.0'}, 'tract'
            ),
            'geoId/06085500100',
        )
        for bad_cz in ('', '0', '-1', 'NA'):
            self.assertEqual(
                preprocess.format_geo_id({'cz': bad_cz}, 'commuting_zone'), ''
            )
        self.assertEqual(
            preprocess.format_geo_id({'state': '0', 'county': '85'}, 'county'),
            '',
        )
        self.assertEqual(
            preprocess.format_geo_id(
                {'state': '6', 'county': '85', 'tract': ''}, 'tract'
            ),
            '',
        )

    def test_download_file_atomic_and_retry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, 'sample.csv')
            fake_response = mock.MagicMock()
            fake_response.__enter__.return_value = fake_response
            fake_response.iter_content.return_value = [b'cz,val\n', b'100,0.5\n']
            with mock.patch(
                'util.download_util_script._retry_method',
                return_value=fake_response,
            ) as mock_req:
                download.download_file(
                    'https://example.com/sample.csv',
                    dest_path,
                    max_retries=2,
                    retry_backoff_sec=0.01,
                )

            mock_req.assert_called_once()
            self.assertTrue(os.path.exists(dest_path))
            self.assertFalse(os.path.exists(f'{dest_path}.tmp'))
            with open(dest_path, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'cz,val\n100,0.5\n')

            with mock.patch(
                'util.download_util_script._retry_method', return_value=None
            ), mock.patch.object(download.logging, 'fatal') as mock_fatal:
                download.download_file(
                    'https://example.com/fail.csv',
                    os.path.join(tmpdir, 'fail.csv'),
                )
                mock_fatal.assert_called_once()

    def test_skips_missing_value_placeholders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = os.path.join(tmpdir, 'raw')
            shard_dir = os.path.join(tmpdir, 'input_files')
            out_dir = os.path.join(tmpdir, 'output')
            os.makedirs(raw_dir, exist_ok=True)
            for filename, _, mode in preprocess.DATASET_CONFIGS:
                with open(
                    os.path.join(raw_dir, filename), 'w', encoding='utf-8', newline=''
                ) as f:
                    w = csv.writer(f)
                    if filename == 'commuting_zone_outcomes.csv':
                        w.writerow([
                            'cz',
                            'kir_natam_female_p1',
                            'kir_natam_female_mean',
                        ])
                        w.writerow(['0', '0.99', '0.88'])
                        w.writerow(['100'])  # truncated row
                        w.writerow(['100', 'NA', '0.35973939'])
                        w.writerow(['101', '', 'n/a'])
                        w.writerow(['102', '0.25', '0.50'])
                    elif mode == 'annual_cohort_1978_1992':
                        w.writerow(['state', 'county', 'cz', 'cohort', 'kir_natam_female_mean'])
                        w.writerow(['6', '85', '100', 'NA', '0.5'])
                        w.writerow(['6', '85', '100', '.', '0.5'])
                        w.writerow(['6', '85', '100', 'Inf', '0.5'])
                        w.writerow(['6', '85', '100', '1978.5', '0.5'])
                        w.writerow(['6', '85', '100'])  # truncated row
                    else:
                        w.writerow(['state', 'county', 'tract', 'cz', 'kir_natam_female_mean'])

            with mock.patch.object(
                preprocess,
                '_resolve_headers_via_svp',
                return_value={
                    'kir_natam_female_p1': ('2014', 'P2Y', 'dc/p1', ''),
                    'kir_natam_female_mean': ('2014', 'P2Y', 'dc/mean', ''),
                },
            ):
                obs_count = preprocess.prepare_parallel_shards_and_svp_inputs(
                    raw_dir,
                    shard_dir,
                    os.path.join(out_dir, 'output'),
                    rows_per_chunk=1,
                    workers=1,
                    existing_statvar_mcf='',
                )
            self.assertEqual(obs_count, 1)

            out_csv = os.path.join(shard_dir, 'commuting_zone_outcomes_cleaned.csv')
            with open(out_csv, 'r', encoding='utf-8') as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]['geo_id'], 'geoId/cz00100')
            self.assertEqual(rows[0]['kir_natam_female_p1'], '')
            self.assertEqual(rows[0]['kir_natam_female_mean'], '0.35973939')
            self.assertEqual(rows[1]['geo_id'], 'geoId/cz00102')
            self.assertEqual(rows[1]['kir_natam_female_p1'], '0.25')
            with self.assertRaises(ValueError):
                preprocess._validate_required_columns(
                    {'state': 0}, 'county', 'annual_cohort_1978_1992', 'bad.csv'
                )

    def test_main_raises_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                preprocess.prepare_parallel_shards_and_svp_inputs(
                    raw_dir=os.path.join(tmpdir, 'raw'),
                    shard_dir=os.path.join(tmpdir, 'out'),
                    sv_output_prefix=os.path.join(tmpdir, 'output', 'output'),
                    existing_statvar_mcf='',
                )

    def test_extract_csv_from_zip_skips_nested_macosx(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, 'archive.zip')
            target_csv = os.path.join(tmpdir, 'extracted.csv')
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.writestr('folder/__MACOSX/._data.csv', 'corrupted,metadata\n')
                zf.writestr('folder/readme.csv', 'wrong,file\n')
                zf.writestr('folder/extracted.csv', 'cz,val\n100,0.5\n')

            download.extract_csv_from_zip(zip_path, target_csv)
            with open(target_csv, 'r', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'cz,val\n100,0.5\n')

            bad_zip = os.path.join(tmpdir, 'bad.zip')
            bad_target = os.path.join(tmpdir, 'bad.csv')
            with open(bad_zip, 'w', encoding='utf-8') as f:
                f.write('<html>Error</html>')
            with mock.patch.object(download.logging, 'fatal') as mock_fatal:
                download.extract_csv_from_zip(bad_zip, bad_target)
                mock_fatal.assert_called_once()
            self.assertFalse(os.path.exists(bad_target))

    def test_sharding_all_datasets(self):
        test_data_dir = os.path.join(_MODULE_DIR, 'test_data')
        raw_dir = os.path.join(test_data_dir, 'raw_data')
        expected_input_dir = os.path.join(test_data_dir, 'input_files')
        expected_output_dir = os.path.join(test_data_dir, 'output')
        fake_header_to_sv = _load_expected_header_to_sv(
            expected_input_dir, os.path.join(expected_output_dir, 'output.csv')
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = os.path.join(tmpdir, 'input_files')
            out_dir = os.path.join(tmpdir, 'output')
            os.makedirs(shard_dir, exist_ok=True)
            os.makedirs(out_dir, exist_ok=True)

            sv_out_prefix = os.path.join(out_dir, 'output')
            with mock.patch.object(
                preprocess,
                '_resolve_headers_via_svp',
                return_value=fake_header_to_sv,
            ):
                preprocess.prepare_parallel_shards_and_svp_inputs(
                    raw_dir,
                    shard_dir,
                    sv_out_prefix,
                    rows_per_chunk=5000,
                    workers=2,
                    existing_statvar_mcf='',
                )

            actual_cleaned = sorted(
                f for f in os.listdir(shard_dir) if f.endswith('_cleaned.csv')
            )
            expected_cleaned = sorted(
                f
                for f in os.listdir(expected_input_dir)
                if f.endswith('_cleaned.csv')
            )
            self.assertEqual(actual_cleaned, expected_cleaned)
            for fname in expected_cleaned:
                with open(
                    os.path.join(shard_dir, fname), 'r', encoding='utf-8'
                ) as f_actual, open(
                    os.path.join(expected_input_dir, fname),
                    'r',
                    encoding='utf-8',
                ) as f_expected:
                    self.assertEqual(f_actual.read(), f_expected.read())

            actual_parts = sorted(
                f
                for f in os.listdir(out_dir)
                if f.startswith('output_part_') and f.endswith('.csv')
            )
            expected_parts = sorted(
                f
                for f in os.listdir(expected_output_dir)
                if f.startswith('output_part_') and f.endswith('.csv')
            )
            self.assertEqual(actual_parts, expected_parts)
            for fname in expected_parts:
                with open(
                    os.path.join(out_dir, fname), 'r', encoding='utf-8'
                ) as f_actual, open(
                    os.path.join(expected_output_dir, fname),
                    'r',
                    encoding='utf-8',
                ) as f_expected:
                    self.assertEqual(f_actual.read(), f_expected.read())

            sv_rows = []
            for fname in actual_parts:
                with open(
                    os.path.join(out_dir, fname), 'r', encoding='utf-8'
                ) as f:
                    sv_rows.extend(list(csv.DictReader(f)))
            self.assertEqual(len(sv_rows), 120)

    def test_is_valid_number(self):
        self.assertTrue(preprocess._is_valid_number('0.35973939'))
        self.assertTrue(preprocess._is_valid_number('-12.5'))
        for invalid in ('', 'NA', 'N/A', '.', 'nan', 'null', '-', 's', 'Inf', '-Inf'):
            self.assertFalse(preprocess._is_valid_number(invalid))

    def test_discover_latest_urls_matches_cohort_zips(self):
        sample_html = (
            '<a href="https://opportunityinsights.org/wp-content/uploads/2024/07/county_cohort.zip">County</a>'
            '<a href="https://opportunityinsights.org/wp-content/uploads/2024/07/cz_cohort.zip">CZ</a>'
        )
        with mock.patch(
            'util.download_util.request_url',
            return_value=sample_html,
        ):
            urls = download.discover_latest_urls('https://example.com/data/')
        self.assertEqual(
            urls['county_by_cohort_outcomes.csv'],
            'https://opportunityinsights.org/wp-content/uploads/2024/07/county_cohort.zip',
        )
        self.assertEqual(
            urls['cz_by_cohort_outcomes.csv'],
            'https://opportunityinsights.org/wp-content/uploads/2024/07/cz_cohort.zip',
        )

    def test_download_all_sources(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w') as zf:
                zf.writestr('data.csv', 'state,county,val\n6,85,1.0\n')
            zip_bytes = zip_buf.getvalue()

            def fake_download(url, dest_path):
                with open(dest_path, 'wb') as f:
                    if url.endswith('.zip') or dest_path.endswith('.zip'):
                        f.write(zip_bytes)
                    else:
                        f.write(b'cz,val\n100,0.5\n')

            with mock.patch.object(
                download,
                'discover_latest_urls',
                return_value={k: v['url'] for k, v in download.DEFAULT_SOURCE_FILES.items()},
            ), mock.patch.object(
                download, 'download_file', side_effect=fake_download
            ) as mock_dl:
                files = download.download_all_sources(tmpdir, force_download=False)
                self.assertEqual(len(files), 6)
                self.assertEqual(mock_dl.call_count, 6)

                download.download_all_sources(tmpdir, force_download=False)
                self.assertEqual(mock_dl.call_count, 6)

                download.download_all_sources(tmpdir, force_download=True)
                self.assertEqual(mock_dl.call_count, 12)

    def test_resolve_headers_via_svp_logs_missing_headers_and_counters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for filename, _, mode in preprocess.DATASET_CONFIGS:
                with open(
                    os.path.join(tmpdir, filename), 'w', encoding='utf-8', newline=''
                ) as f:
                    w = csv.writer(f)
                    if mode == 'annual_cohort_1978_1992':
                        w.writerow(['state', 'county', 'cz', 'cohort', 'kfr_pooled_pooled_p25'])
                    else:
                        w.writerow(['state', 'county', 'tract', 'cz', 'kfr_pooled_pooled_p25'])

            def fake_run_success(cmd, **kwargs):
                del kwargs
                out_prefix = [a.split('=', 1)[1] for a in cmd if a.startswith('--output_path=')][0]
                counters_path = [a.split('=', 1)[1] for a in cmd if a.startswith('--output_counters=')][0]
                with open(f'{out_prefix}.csv', 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f)
                    w.writerow([
                        'observationAbout',
                        'observationDate',
                        'observationPeriod',
                        'variableMeasured',
                        'value',
                        'unit',
                    ])
                    for idx in range(1, 18):
                        w.writerow(['geoId/seed000', '2014', 'P2Y', f'dc/sv{idx}', str(idx), ''])
                with open(counters_path, 'w', encoding='utf-8', newline='') as f:
                    csv.writer(f).writerow(['key', 'value'])
                return mock.Mock(returncode=0, stderr='')

            with mock.patch('subprocess.run', side_effect=fake_run_success):
                resolved = preprocess._resolve_headers_via_svp(
                    tmpdir, existing_statvar_mcf=''
                )
            self.assertEqual(len(resolved), 17)
            self.assertEqual(resolved['kfr_p25'], ('2014', 'P2Y', 'dc/sv1', ''))

            def fake_run_fail(cmd, **kwargs):
                del kwargs
                out_prefix = [a.split('=', 1)[1] for a in cmd if a.startswith('--output_path=')][0]
                counters_path = [a.split('=', 1)[1] for a in cmd if a.startswith('--output_counters=')][0]
                with open(f'{out_prefix}.csv', 'w', encoding='utf-8', newline='') as f:
                    csv.writer(f).writerow([
                        'observationAbout',
                        'observationDate',
                        'observationPeriod',
                        'variableMeasured',
                        'value',
                        'unit',
                    ])
                with open(counters_path, 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['key', 'value'])
                    w.writerow(['unmapped_pvs', '1'])
                return mock.Mock(returncode=0, stderr='')

            with mock.patch('subprocess.run', side_effect=fake_run_fail):
                with self.assertRaisesRegex(
                    RuntimeError, r'kfr_p25.*unmapped_pvs'
                ):
                    preprocess._resolve_headers_via_svp(
                        tmpdir, existing_statvar_mcf=''
                    )


if __name__ == '__main__':
    unittest.main()

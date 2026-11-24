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
"""Unit tests for BEAGDPPriceParity (download.py & stat_var_processor PVMaps)."""

import csv
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

import requests

from statvar_imports.us_bea.bea_gdp_price_parity import download

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_INPUT_DIR = os.path.join(_PACKAGE_DIR, 'test_data', 'sample_input')
_SAMPLE_OUTPUT_DIR = os.path.join(_PACKAGE_DIR, 'test_data', 'sample_output')
_REPO_ROOT = os.path.abspath(os.path.join(_PACKAGE_DIR, '..', '..', '..'))
_PROCESSOR = os.path.join(_REPO_ROOT, 'tools', 'statvar_importer',
                          'stat_var_processor.py')


def _build_zip_bytes(entries: dict[str, bytes]) -> bytes:
    """Builds an in-memory ZIP archive from filename -> payload entries."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _make_response(status_code: int, content: bytes) -> requests.Response:
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = content  # pylint: disable=protected-access
    resp.url = 'https://apps.bea.gov/regional/zip/MARPP.zip'
    return resp


def _non_comment_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith('#')
    ]


class BeaGdpPriceParityTest(unittest.TestCase):

    def test_pvmap_and_metadata_csv_files_are_well_formed(self):
        for fname in (
                'bea_years_pvmap.csv',
                'bea_rpp_pvmap.csv',
                'bea_county_gdp_pvmap.csv',
                'bea_metro_gdp_pvmap.csv',
        ):
            fpath = os.path.join(_PACKAGE_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
            self.assertGreater(len(rows), 1, f'{fname} must have mapping rows')
            for row in rows:
                trimmed = list(row)
                while trimmed and trimmed[-1].strip() == '':
                    trimmed.pop()
                self.assertEqual(
                    len(trimmed) % 2,
                    1,
                    f'{fname} row {trimmed} must have key + (prop, val) pairs',
                )

        for fname in (
                'bea_rpp_metadata.csv',
                'bea_county_gdp_metadata.csv',
                'bea_metro_gdp_metadata.csv',
        ):
            fpath = os.path.join(_PACKAGE_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], ['parameter', 'value'])
            self.assertGreater(len(rows), 1)

    def test_download_and_extract_success_and_cleans_stale_csvs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            stale_csv = Path(tmp_dir) / 'MARPP_MSA_2008_2023.csv'
            stale_csv.write_text('stale\n', encoding='utf-8')

            zip_payload = _build_zip_bytes({
                'MARPP_MSA_2008_2024.csv': b'GeoFIPS,2024\n"10180",90.3\n',
                'MARPP_Footnotes.html': b'<html>Footnotes</html>',
            })
            session = mock.MagicMock(spec=requests.Session)
            session.get.return_value = _make_response(200, zip_payload)

            extracted = download.download_and_extract(
                'https://apps.bea.gov/regional/zip/MARPP.zip',
                'MARPP_MSA_',
                tmp_dir,
                retries=2,
                delay=0,
                session=session,
            )
            self.assertEqual(
                extracted,
                [os.path.join(tmp_dir, 'MARPP_MSA_2008_2024.csv')],
            )
            self.assertTrue((Path(tmp_dir) / 'MARPP.zip').exists())
            self.assertTrue(
                (Path(tmp_dir) / 'MARPP_MSA_2008_2024.csv').exists())
            self.assertFalse(stale_csv.exists())

    def test_download_and_extract_retries_transient_503_then_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_payload = _build_zip_bytes({
                'SARPP_STATE_2008_2024.csv': b'GeoFIPS,2024\n"01000",88.1\n',
            })
            session = mock.MagicMock(spec=requests.Session)
            session.get.side_effect = [
                _make_response(503, b'Service Unavailable'),
                _make_response(200, zip_payload),
            ]

            extracted = download.download_and_extract(
                'https://apps.bea.gov/regional/zip/SARPP.zip',
                'SARPP_STATE_',
                tmp_dir,
                retries=3,
                delay=0,
                session=session,
            )
            self.assertEqual(len(extracted), 1)
            self.assertEqual(session.get.call_count, 2)

    def test_download_and_extract_rejects_soft_404_html_without_retrying(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = mock.MagicMock(spec=requests.Session)
            session.get.return_value = _make_response(
                200, b'<html><body>404 Not Found</body></html>')

            with self.assertRaises(ValueError):
                download.download_and_extract(
                    'https://apps.bea.gov/regional/zip/MAGDP1.zip',
                    'MAGDP1_',
                    tmp_dir,
                    retries=3,
                    delay=0,
                    session=session,
                )
            self.assertEqual(session.get.call_count, 1)

    def test_download_and_extract_fails_fast_on_404_and_missing_prefix(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            session = mock.MagicMock(spec=requests.Session)
            session.get.return_value = _make_response(404, b'Not Found')
            with self.assertRaises(requests.exceptions.HTTPError):
                download.download_and_extract(
                    'https://apps.bea.gov/regional/zip/MAGDP1.zip',
                    'MAGDP1_',
                    tmp_dir,
                    retries=3,
                    delay=0,
                    session=session,
                )
            self.assertEqual(session.get.call_count, 1)

            other_zip = _build_zip_bytes({'UNEXPECTED.csv': b'a,b\n1,2\n'})
            session.reset_mock()
            session.get.return_value = _make_response(200, other_zip)
            with self.assertRaises(RuntimeError):
                download.download_and_extract(
                    'https://apps.bea.gov/regional/zip/MARPP.zip',
                    'MARPP_MSA_',
                    tmp_dir,
                    retries=3,
                    delay=0,
                    session=session,
                )
            self.assertEqual(session.get.call_count, 1)

    @mock.patch.object(download.storage, 'Client')
    def test_copy_historical_data_from_gcs(self, mock_client_cls):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mock_client = mock.MagicMock()
            mock_client_cls.return_value = mock_client
            mock_bucket = mock.MagicMock()
            mock_client.bucket.return_value = mock_bucket
            mock_blob = mock.MagicMock()
            mock_bucket.blob.return_value = mock_blob

            def fake_download(dest_filename, timeout=300):
                del timeout
                Path(dest_filename).write_text(
                    'geoid\tyear\tgrossDomesticProduct\nC10180\t2012\t6397000000\n',
                    encoding='utf-8',
                )

            mock_blob.download_to_filename.side_effect = fake_download

            copied = download.copy_historical_data_from_gcs(output_dir=tmp_dir,
                                                            skip_existing=True)
            self.assertEqual(len(copied), len(download.HISTORICAL_FILENAMES))
            for fname in download.HISTORICAL_FILENAMES:
                self.assertTrue((Path(tmp_dir) / fname).exists())

            mock_client_cls.reset_mock()
            copied_again = download.copy_historical_data_from_gcs(
                output_dir=tmp_dir, skip_existing=True)
            self.assertEqual(copied_again, copied)
            mock_client_cls.assert_not_called()

    def _assert_processor_matches_fixtures(
        self,
        tmp_dir: str,
        input_files: list[str],
        pv_maps: list[str],
        config_file: str,
        output_stem: str,
        check_statvar_mcf: bool = False,
    ) -> dict[str, str]:
        out_prefix = os.path.join(tmp_dir, output_stem)
        counters_csv = os.path.join(tmp_dir, f'{output_stem}_counters.csv')
        input_paths = ','.join(
            os.path.join(_SAMPLE_INPUT_DIR, f) for f in input_files)
        cmd = [
            sys.executable,
            _PROCESSOR,
            f'--input_data={input_paths}',
            f'--pv_map={",".join(os.path.join(_PACKAGE_DIR, m) for m in pv_maps)}',
            f'--config_file={os.path.join(_PACKAGE_DIR, config_file)}',
            f'--output_path={out_prefix}',
            f'--output_counters={counters_csv}',
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as err:
            self.fail(f'stat_var_processor.py failed (exit {err.returncode}).\n'
                      f'STDOUT:\n{err.stdout}\nSTDERR:\n{err.stderr}')

        actual_csv = (Path(f'{out_prefix}.csv').read_text(
            encoding='utf-8').splitlines())
        expected_csv = (Path(
            os.path.join(
                _SAMPLE_OUTPUT_DIR,
                f'{output_stem}.csv')).read_text(encoding='utf-8').splitlines())
        self.assertEqual(actual_csv, expected_csv)

        actual_tmcf = _non_comment_lines(
            Path(f'{out_prefix}.tmcf').read_text(encoding='utf-8'))
        expected_tmcf = _non_comment_lines(
            Path(os.path.join(
                _SAMPLE_OUTPUT_DIR,
                f'{output_stem}.tmcf')).read_text(encoding='utf-8'))
        self.assertEqual(actual_tmcf[0], expected_tmcf[0])
        self.assertCountEqual(actual_tmcf, expected_tmcf)

        if check_statvar_mcf:
            actual_mcf = _non_comment_lines(
                Path(f'{out_prefix}_stat_vars.mcf').read_text(encoding='utf-8'))
            expected_mcf = _non_comment_lines(
                Path(
                    os.path.join(_SAMPLE_OUTPUT_DIR,
                                 f'{output_stem}_stat_vars.mcf')).read_text(
                                     encoding='utf-8'))
            self.assertEqual(actual_mcf, expected_mcf)

        with open(counters_csv, 'r', encoding='utf-8') as f:
            return {r['key']: r['value'] for r in csv.DictReader(f)}

    def test_rpp_pvmap_matches_sample_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._assert_processor_matches_fixtures(
                tmp_dir=tmp_dir,
                input_files=[
                    'SARPP_STATE_sample_input.csv',
                    'MARPP_MSA_sample_input.csv',
                ],
                pv_maps=['bea_rpp_pvmap.csv', 'bea_years_pvmap.csv'],
                config_file='bea_rpp_metadata.csv',
                output_stem='bea_rpp_sample_output',
                check_statvar_mcf=True,
            )

    def test_county_gdp_and_growth_pvmaps_match_sample_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gdp_counters = self._assert_processor_matches_fixtures(
                tmp_dir=tmp_dir,
                input_files=['CAGDP1__ALL_AREAS_sample_input.csv'],
                pv_maps=['bea_county_gdp_pvmap.csv', 'bea_years_pvmap.csv'],
                config_file='bea_county_gdp_metadata.csv',
                output_stem='bea_county_gdp_sample_output',
            )
            self.assertEqual(
                gdp_counters.get('1:process_input_input-rows-ignored'), '2')
            self.assertNotIn('error-svobs-missing-property', gdp_counters)

            growth_counters = self._assert_processor_matches_fixtures(
                tmp_dir=tmp_dir,
                input_files=['CAGDP11__ALL_AREAS_sample_input.csv'],
                pv_maps=['bea_county_gdp_pvmap.csv', 'bea_years_pvmap.csv'],
                config_file='bea_county_gdp_metadata.csv',
                output_stem='bea_county_gdp_growth_sample_output',
            )
            self.assertEqual(
                growth_counters.get('1:process_input_input-rows-ignored'), '1')
            self.assertNotIn('error-svobs-missing-property', growth_counters)

    def test_metro_gdp_pvmap_matches_sample_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._assert_processor_matches_fixtures(
                tmp_dir=tmp_dir,
                input_files=['metro_gdp.csv', 'metro_nominal_gdp.csv'],
                pv_maps=['bea_metro_gdp_pvmap.csv'],
                config_file='bea_metro_gdp_metadata.csv',
                output_stem='bea_metro_gdp_sample_output',
            )


if __name__ == '__main__':
    unittest.main()

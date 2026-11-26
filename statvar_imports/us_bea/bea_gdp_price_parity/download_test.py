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
"""Unit tests for BEAGDPPriceParity download.py and PVMap/metadata configs."""

import csv
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import requests

from statvar_imports.us_bea.bea_gdp_price_parity import download

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_INPUT_DIR = os.path.join(_PACKAGE_DIR, 'test_data', 'sample_input')
_SAMPLE_OUTPUT_DIR = os.path.join(_PACKAGE_DIR, 'test_data', 'sample_output')


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


class BeaGdpPriceParityTest(unittest.TestCase):

    def test_pvmap_and_metadata_csv_files_are_well_formed(self):
        for fname in (
                'bea_years_pvmap.csv',
                'bea_rpp_pvmap.csv',
                'bea_county_gdp_pvmap.csv',
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
        ):
            fpath = os.path.join(_PACKAGE_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], ['parameter', 'value'])
            self.assertGreater(len(rows), 1)

    def test_sample_fixtures_exist_and_non_empty(self):
        for fname in (
                'SARPP_STATE_sample_input.csv',
                'MARPP_MSA_sample_input.csv',
                'CAGDP1__ALL_AREAS_sample_input.csv',
                'CAGDP11__ALL_AREAS_sample_input.csv',
        ):
            fpath = Path(_SAMPLE_INPUT_DIR) / fname
            self.assertTrue(fpath.is_file(), f'Missing sample input {fname}')
            self.assertGreater(fpath.stat().st_size, 0)

        for fname in (
                'bea_rpp_sample_output.csv',
                'bea_rpp_sample_output.tmcf',
                'bea_county_gdp_sample_output.csv',
                'bea_county_gdp_sample_output.tmcf',
                'bea_county_gdp_growth_sample_output.csv',
                'bea_county_gdp_growth_sample_output.tmcf',
        ):
            fpath = Path(_SAMPLE_OUTPUT_DIR) / fname
            self.assertTrue(fpath.is_file(), f'Missing sample output {fname}')
            self.assertGreater(fpath.stat().st_size, 0)

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


if __name__ == '__main__':
    unittest.main()

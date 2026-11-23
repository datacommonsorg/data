# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for process.py"""

import csv
import gzip
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

from absl import flags
from absl.testing import flagsaver
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.us_usda.nass_census import process

_SAMPLE_DATASETS_HTML = """
<html><body>
<section class="nass-datasets">
  <ul>
    <li><a href="/sites/default/files/datasets/qs.animals_products_20261120.txt.gz">old</a></li>
    <li><a href="/sites/default/files/datasets/qs.animals_products_20261121.txt.gz" download>animals</a></li>
    <li><a href="/sites/default/files/datasets/qs.crops_20261121.txt.gz" download>crops</a></li>
    <li><a href="https://www.nass.usda.gov/sites/default/files/datasets/qs.demographics_20261121.txt.gz">demo</a></li>
    <li><a href="/sites/default/files/datasets/qs.economics_20261121.txt.gz">econ</a></li>
    <li><a href="/sites/default/files/datasets/qs.environmental_20261121.txt.gz">env</a></li>
    <li><a href="https://evil.example.com/qs.crops_20990101.txt.gz">untrusted</a></li>
  </ul>
</section>
</body></html>
"""


def _make_gzip_bytes(text: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
        gz.write(text.encode('utf-8'))
    return buf.getvalue()


def _mock_stream_response(
    chunks: list[bytes],
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> mock.MagicMock:
    resp = mock.MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.iter_content.return_value = chunks
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(
            f'HTTP {status_code}', response=resp)
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


class ProcessTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if 'output' not in flags.FLAGS:
            process._define_flags()
        flags.FLAGS.mark_as_parsed()

    def test_write_csv(self):
        input_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                  'ag_census_input.txt')
        statvars_path = os.path.join(_SCRIPT_DIR, 'statvars')
        expected_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                     'ag_census_output.csv')
        with open(input_path, encoding='utf-8') as f_in:
            d = process.get_statvars(statvars_path)
            reader = csv.DictReader(f_in, delimiter='\t')
            f_out = io.StringIO()
            with open(expected_path, encoding='utf-8') as f_expected:
                expected = f_expected.read()
            process.write_csv(reader, f_out, d)
            self.assertEqual(expected, f_out.getvalue())

    def test_is_census_year(self):
        self.assertTrue(process.is_census_year('2002'))
        self.assertTrue(process.is_census_year('2007'))
        self.assertTrue(process.is_census_year('2022'))
        self.assertTrue(process.is_census_year('2027'))
        self.assertFalse(process.is_census_year('1997'))
        self.assertFalse(process.is_census_year('2013'))
        self.assertFalse(process.is_census_year('2023'))
        self.assertFalse(process.is_census_year(''))
        self.assertFalse(process.is_census_year('abc'))

    def test_write_csv_filters_survey_and_non_census_years(self):
        tsv_data = '\n'.join([
            'SOURCE_DESC\tSHORT_DESC\tDOMAINCAT_DESC\tAGG_LEVEL_DESC\tSTATE_FIPS_CODE\tCOUNTY_CODE\tYEAR\tVALUE',
            'SURVEY\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t2022\t999',
            'CENSUS\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t2023\t888',
            'CENSUS\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t1997\t777',
            'CENSUS\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t2022\t (NA) ',
            'CENSUS\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t2002\t 2,128,982 ',
            'CENSUS\tFARM OPERATIONS - NUMBER OF OPERATIONS\tNOT SPECIFIED\tNATIONAL\t\t\t2027\t1,900,000',
        ])
        d = {
            'FARM OPERATIONS - NUMBER OF OPERATIONS%%NOT SPECIFIED':
                ('Count_Farm',)
        }
        reader = csv.DictReader(io.StringIO(tsv_data), delimiter='\t')
        out = io.StringIO()
        written = process.write_csv(reader, out, d)
        self.assertEqual(written, 2)
        rows = list(csv.DictReader(io.StringIO(out.getvalue())))
        self.assertEqual(
            rows,
            [
                {
                    'variableMeasured': 'dcs:Count_Farm',
                    'observationAbout': 'dcid:country/USA',
                    'value': '2128982',
                    'unit': '',
                    'observationDate': '2002',
                },
                {
                    'variableMeasured': 'dcs:Count_Farm',
                    'observationAbout': 'dcid:country/USA',
                    'value': '1900000',
                    'unit': '',
                    'observationDate': '2027',
                },
            ],
        )

    def test_write_csv_missing_required_columns_raises(self):
        reader = csv.DictReader(io.StringIO('SHORT_DESC\tVALUE\nA\t1\n'),
                                delimiter='\t')
        with self.assertRaises(ValueError):
            process.write_csv(reader, io.StringIO(), {})

    def test_discover_sector_urls_success_and_dedup(self):
        urls = process.discover_sector_urls(_SAMPLE_DATASETS_HTML)
        self.assertEqual(
            urls,
            [
                'https://www.nass.usda.gov/sites/default/files/datasets/qs.animals_products_20261121.txt.gz',
                'https://www.nass.usda.gov/sites/default/files/datasets/qs.crops_20261121.txt.gz',
                'https://www.nass.usda.gov/sites/default/files/datasets/qs.demographics_20261121.txt.gz',
                'https://www.nass.usda.gov/sites/default/files/datasets/qs.economics_20261121.txt.gz',
                'https://www.nass.usda.gov/sites/default/files/datasets/qs.environmental_20261121.txt.gz',
            ],
        )

    def test_discover_sector_urls_missing_sector_raises(self):
        incomplete_html = (
            '<a href="/sites/default/files/datasets/qs.crops_20261121.txt.gz">'
            'crops</a>')
        with self.assertRaises(RuntimeError) as ctx:
            process.discover_sector_urls(incomplete_html)
        self.assertIn('Missing expected Quick Stats sector archives',
                      str(ctx.exception))

    def test_download_file_streaming_success(self):
        gz_payload = _make_gzip_bytes('hello world\n')
        resp = _mock_stream_response(
            [gz_payload[:5], b'', gz_payload[5:]],
            status_code=200,
            headers={
                'Content-Length': str(len(gz_payload)),
                'ETag': '"v1"'
            },
        )
        mock_session = mock.MagicMock()
        mock_session.get.return_value = resp

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = os.path.join(tmp_dir, 'test.txt.gz')
            process.download_file('https://www.nass.usda.gov/test.txt.gz',
                                  out_path,
                                  session=mock_session)
            self.assertTrue(os.path.exists(out_path))
            self.assertFalse(os.path.exists(f'{out_path}.part'))
            with gzip.open(out_path, 'rt', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'hello world\n')

    def test_download_file_resumes_on_truncated_transfer(self):
        gz_payload = _make_gzip_bytes('resumed payload line\n')
        split_at = len(gz_payload) // 2
        first_resp = _mock_stream_response(
            [gz_payload[:split_at]],
            status_code=200,
            headers={
                'Content-Length': str(len(gz_payload)),
                'ETag': '"abc"'
            },
        )
        second_resp = _mock_stream_response(
            [gz_payload[split_at:]],
            status_code=206,
            headers={'Content-Length': str(len(gz_payload) - split_at)},
        )
        mock_session = mock.MagicMock()
        mock_session.get.side_effect = [first_resp, second_resp]

        with tempfile.TemporaryDirectory() as tmp_dir, \
             mock.patch('time.sleep') as mock_sleep:
            out_path = os.path.join(tmp_dir, 'resume.txt.gz')
            process.download_file('https://www.nass.usda.gov/resume.txt.gz',
                                  out_path,
                                  session=mock_session)
            self.assertEqual(mock_sleep.call_count, 1)
            self.assertEqual(mock_session.get.call_count, 2)
            second_headers = mock_session.get.call_args_list[1].kwargs[
                'headers']
            self.assertEqual(
                second_headers,
                {
                    'Range': f'bytes={split_at}-',
                    'If-Range': '"abc"'
                },
            )
            with gzip.open(out_path, 'rt', encoding='utf-8') as f:
                self.assertEqual(f.read(), 'resumed payload line\n')

    def test_download_file_permanent_404_does_not_retry(self):
        resp_404 = _mock_stream_response([], status_code=404)
        mock_session = mock.MagicMock()
        mock_session.get.return_value = resp_404

        with tempfile.TemporaryDirectory() as tmp_dir, \
             mock.patch('time.sleep') as mock_sleep:
            out_path = os.path.join(tmp_dir, 'missing.txt.gz')
            with self.assertRaises(requests.HTTPError):
                process.download_file(
                    'https://www.nass.usda.gov/missing.txt.gz',
                    out_path,
                    session=mock_session,
                )
            self.assertEqual(mock_sleep.call_count, 0)
            self.assertEqual(mock_session.get.call_count, 1)
            self.assertFalse(os.path.exists(f'{out_path}.part'))

    def test_main_download_and_process_modes(self):
        fixture_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                    'ag_census_input.txt')
        expected_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                     'ag_census_output.csv')
        with open(fixture_path, encoding='utf-8') as f:
            fixture_tsv = f.read()
        with open(expected_path, encoding='utf-8') as f:
            expected_csv = f.read()

        empty_header = fixture_tsv.splitlines()[0] + '\n'
        payload_by_sector = {
            'economics': _make_gzip_bytes(fixture_tsv),
            'animals_products': _make_gzip_bytes(empty_header),
            'crops': _make_gzip_bytes(empty_header),
            'demographics': _make_gzip_bytes(empty_header),
            'environmental': _make_gzip_bytes(empty_header),
        }

        def fake_download(url, dest_path, session=None):
            for sector, gz_bytes in payload_by_sector.items():
                if f'qs.{sector}_' in url:
                    with open(dest_path, 'wb') as out_f:
                        out_f.write(gz_bytes)
                    return
            raise AssertionError(f'Unexpected URL: {url}')

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_dir = os.path.join(tmp_dir, 'input')
            os.makedirs(input_dir, exist_ok=True)
            stale_file = os.path.join(input_dir, 'qs.crops_20260101.txt.gz')
            with open(stale_file, 'wb') as f:
                f.write(b'stale')
            output_csv = os.path.join(tmp_dir, 'output', 'agriculture.csv')

            with mock.patch.object(process,
                                   'fetch_datasets_html',
                                   return_value=_SAMPLE_DATASETS_HTML), \
                 mock.patch.object(process,
                                   'download_file',
                                   side_effect=fake_download):
                # 1. --mode=download fetches datasets.html + 5 .txt.gz archives and removes stale files.
                with flagsaver.flagsaver(mode='download',
                                         input_dir=input_dir,
                                         output=output_csv):
                    process.main([])
                self.assertFalse(os.path.exists(stale_file))
                self.assertTrue(
                    os.path.exists(os.path.join(input_dir, 'datasets.html')))
                self.assertEqual(len(os.listdir(input_dir)), 6)
                self.assertFalse(os.path.exists(output_csv))

                # 2. --mode=process streams existing .txt.gz files and writes outputs.
                with flagsaver.flagsaver(mode='process',
                                         input_dir=input_dir,
                                         output=output_csv):
                    process.main([])
                with open(output_csv, encoding='utf-8') as f:
                    self.assertEqual(f.read(), expected_csv)
                year_csv = os.path.join(tmp_dir, 'output',
                                        'agriculture_2022.csv')
                self.assertTrue(os.path.exists(year_csv))

                # 3. Default --mode='' downloads and processes in a single run.
                with flagsaver.flagsaver(mode='',
                                         input_dir=input_dir,
                                         output=output_csv):
                    process.main([])
                with open(output_csv, encoding='utf-8') as f:
                    self.assertEqual(f.read(), expected_csv)

    def test_process_input_files_empty_observations_raises(self):
        header_only = (
            'SOURCE_DESC\tSHORT_DESC\tDOMAINCAT_DESC\tAGG_LEVEL_DESC\t'
            'STATE_FIPS_CODE\tCOUNTY_CODE\tYEAR\tVALUE\n')
        with tempfile.TemporaryDirectory() as tmp_dir:
            gz_path = os.path.join(tmp_dir, 'qs.crops_20261121.txt.gz')
            with open(gz_path, 'wb') as f:
                f.write(_make_gzip_bytes(header_only))
            output_csv = os.path.join(tmp_dir, 'output', 'agriculture.csv')
            with self.assertRaises(RuntimeError) as ctx:
                process.process_input_files([gz_path], output_csv, {})
            self.assertIn('No census observations were produced',
                          str(ctx.exception))

    def test_process_input_files_plain_txt_utf8(self):
        fixture_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                    'ag_census_input.txt')
        expected_path = os.path.join(_SCRIPT_DIR, 'testdata',
                                     'ag_census_output.csv')
        statvars_map = process.get_statvars(
            os.path.join(_SCRIPT_DIR, 'statvars'))
        with open(expected_path, encoding='utf-8') as f:
            expected_csv = f.read()

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = os.path.join(tmp_dir, 'output', 'agriculture.csv')
            process.process_input_files([fixture_path], output_csv,
                                        statvars_map)
            with open(output_csv, encoding='utf-8') as f:
                self.assertEqual(f.read(), expected_csv)


if __name__ == '__main__':
    unittest.main()

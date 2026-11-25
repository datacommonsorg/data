import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pandas as pd
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from download_input_data import AGE_STEMS
from download_input_data import LOC_STEMS
from download_input_data import SEX_STEMS
from download_input_data import _fetch_secret_api_key
from download_input_data import build_canonical_template
from download_input_data import download_and_process
from download_input_data import fetch_unit_batch_records
from download_input_data import fetch_units
from download_input_data import fetch_variables
from download_input_data import get_http_session
from download_input_data import get_pvmap_supported_years
from download_input_data import get_request_headers
from download_input_data import get_template_map
from download_input_data import load_template_from_gcs
from download_input_data import make_request
from download_input_data import map_units_to_regions
from download_input_data import parse_retry_after_seconds


class DownloadInputDataTest(unittest.TestCase):

    def test_fetch_secret_api_key_direct(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch('google.cloud.secretmanager.SecretManagerServiceClient'
                      ) as mock_sm:
                self.assertEqual(_fetch_secret_api_key(), '')
                mock_sm.assert_not_called()

        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.payload.data = b'  rotated-secret-key \n'
        mock_client.access_secret_version.return_value = mock_resp
        resource = 'projects/p/secrets/s/versions/latest'
        with patch.dict(os.environ, {'BDL_API_SECRET_RESOURCE': resource},
                        clear=True):
            with patch('google.cloud.secretmanager.SecretManagerServiceClient',
                       return_value=mock_client):
                self.assertEqual(_fetch_secret_api_key(), 'rotated-secret-key')
                mock_client.access_secret_version.assert_called_once_with(
                    request={'name': resource}, timeout=5.0)

                mock_client.access_secret_version.side_effect = PermissionError(
                    'IAM denied')
                with self.assertLogs(level='WARNING') as cm:
                    self.assertEqual(
                        _fetch_secret_api_key(secret_resource=resource), '')
                self.assertTrue(
                    any('PermissionError' in line for line in cm.output),
                    f'Expected PermissionError warning in logs, got: {cm.output}',
                )

    def test_get_request_headers_runtime_and_strip(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_request_headers(), {})

        with patch.dict(os.environ, {'BDL_API_KEY': '   '}, clear=True):
            self.assertEqual(get_request_headers(), {})

        with patch('download_input_data._fetch_secret_api_key',
                   return_value='  secret-mgr-key  '):
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(get_request_headers(),
                                 {'X-ClientId': 'secret-mgr-key'})

        with patch.dict(os.environ, {'BDL_API_KEY': '  my-key-456 \n'},
                        clear=True):
            self.assertEqual(get_request_headers(),
                             {'X-ClientId': 'my-key-456'})

        self.assertEqual(get_request_headers(api_key='  explicit-key  '),
                         {'X-ClientId': 'explicit-key'})

    def test_build_canonical_template_17x108(self):
        df = build_canonical_template()
        self.assertEqual(len(df.index), 17)
        self.assertEqual(len(df.columns), 108)
        self.assertIn(('0', 'POLAND'), df.index)
        self.assertIn(('3200000', 'ZACHODNIOPOMORSKIE'), df.index)

    def test_get_pvmap_supported_years(self):
        years = get_pvmap_supported_years()
        self.assertIn('2003', years)
        self.assertIn('2025', years)
        self.assertIn('2050', years)

    def test_get_template_map_and_collision_safe_region_mapping(self):
        df = build_canonical_template()
        region_map = get_template_map(df)
        self.assertEqual(region_map['OPOLSKIE'], '1600000')
        self.assertEqual(region_map['WIELKOPOLSKIE'], '3000000')
        self.assertEqual(region_map['POMORSKIE'], '2200000')
        self.assertEqual(region_map['ZACHODNIOPOMORSKIE'], '3200000')

        prefixed_units = []
        for idx, (_, name) in enumerate(df.index):
            raw = 'POLSKA' if name == 'POLAND' else f'WOJ. {name}'
            prefixed_units.append((f'u{idx}', raw))

        mapped = map_units_to_regions(prefixed_units, region_map)
        mapped_dict = {name: code for _, code, name in mapped}
        self.assertEqual(mapped_dict['WIELKOPOLSKIE'], '3000000')
        self.assertEqual(mapped_dict['MAŁOPOLSKIE'], '1200000')
        self.assertEqual(mapped_dict['OPOLSKIE'], '1600000')
        self.assertEqual(mapped_dict['ZACHODNIOPOMORSKIE'], '3200000')
        self.assertEqual(mapped_dict['KUJAWSKO-POMORSKIE'], '400000')
        self.assertEqual(mapped_dict['POMORSKIE'], '2200000')
        self.assertEqual(mapped_dict['DOLNOŚLĄSKIE'], '200000')
        self.assertEqual(mapped_dict['ŚLĄSKIE'], '2400000')

    def test_map_units_raises_on_unmapped_or_missing_regions(self):
        region_map = {'POLAND': '0', 'OPOLSKIE': '1600000'}
        with self.assertRaises(RuntimeError) as ctx:
            map_units_to_regions([('u1', 'POLSKA'), ('u2', 'NIEZNANY_REGION')],
                                 region_map)
        self.assertIn('could not be mapped', str(ctx.exception))

        with self.assertRaises(RuntimeError) as ctx_missing:
            map_units_to_regions([('u1', 'POLSKA')], region_map)
        self.assertIn('Missing expected territorial units',
                      str(ctx_missing.exception))

    def test_get_http_session(self):
        session = get_http_session(retries=3, backoff_factor=0.5)
        self.assertIsNotNone(session)
        adapter = session.adapters['https://']
        self.assertEqual(adapter.max_retries.total, 3)
        self.assertFalse(adapter.max_retries.respect_retry_after_header)
        self.assertNotIn(429, adapter.max_retries.status_forcelist)

    def test_parse_polish_retry_after_and_429_recovery(self):
        self.assertEqual(parse_retry_after_seconds('456 sek'), 457.0)
        self.assertEqual(parse_retry_after_seconds('30 sek.'), 31.0)
        self.assertEqual(parse_retry_after_seconds('12'), 13.0)
        self.assertEqual(parse_retry_after_seconds('', default_seconds=7.5),
                         7.5)
        self.assertEqual(
            parse_retry_after_seconds('99999 sek', max_seconds=1200.0), 1200.0)

        session = MagicMock()
        r_429 = requests.Response()
        r_429.status_code = 429
        r_429.headers['Retry-After'] = '456 sek'

        r_200 = requests.Response()
        r_200.status_code = 200
        r_200._content = b'{"results": []}'
        session.get.side_effect = [r_429, r_200]

        slept = []
        with self.assertLogs(level='WARNING') as cm:
            resp = make_request(
                session,
                'https://bdl.stat.gov.pl/api/v1/data/by-unit/000000000000',
                sleep_fn=slept.append,
            )
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(slept, [457.0])
        self.assertTrue(any('456 sek' in line for line in cm.output))

    def test_stems_definitions(self):
        self.assertEqual(AGE_STEMS['0-2'], '0-2')
        self.assertEqual(AGE_STEMS['65 and more'], '65')
        self.assertIn('męż', SEX_STEMS['males'])
        self.assertIn('kob', SEX_STEMS['females'])
        self.assertIn('miast', LOC_STEMS['in urban areas'])
        self.assertIn('wsi', LOC_STEMS['in rural areas'])

    @patch('download_input_data.storage.Client')
    def test_load_template_from_gcs_success_and_fallback(
            self, mock_storage_client):
        mock_blob = MagicMock()
        sample_csv = ("Age,,0-2,0-2\n"
                      "Sex,,total,males\n"
                      "Location,,total,total\n"
                      "Year,,2024,2024\n"
                      "Code,Name,,\n"
                      "0,POLAND,100,50\n")
        mock_blob.download_as_text.return_value = sample_csv
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        df = load_template_from_gcs("gs://test-bucket/test-template.csv")
        self.assertEqual(len(df.columns), 2)

        mock_storage_client.side_effect = RuntimeError("GCS unreachable")
        fallback_df = load_template_from_gcs(
            "gs://non-existent-bucket/non-existent.csv")
        self.assertEqual(len(fallback_df.index), 17)
        self.assertEqual(len(fallback_df.columns), 108)

    def test_make_request_headers_redaction_and_error(self):
        session = MagicMock()
        mock_resp = requests.Response()
        mock_resp.status_code = 200
        session.get.return_value = mock_resp

        headers = {'X-ClientId': 'secret-key-123', 'Accept': 'application/json'}
        resp = make_request(session, 'https://example.com/api', headers=headers)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.status_code, 200)

        session.get.side_effect = requests.RequestException("Connection error")
        self.assertIsNone(make_request(session, 'https://example.com/api'))

    def test_response_status_code_logging_not_none_on_http_error(self):
        session = MagicMock()
        mock_resp = requests.Response()
        mock_resp.status_code = 403
        session.get.return_value = mock_resp

        with self.assertLogs(level='ERROR') as cm:
            with self.assertRaises(RuntimeError):
                fetch_variables(session, headers={})
            self.assertTrue(any("status 403" in log for log in cm.output))

    def test_fetch_variables_and_units_pagination(self):
        session = MagicMock()
        p0 = requests.Response()
        p0.status_code = 200
        p0._content = (b'{"results": [' + b','.join(
            f'{{"id": {i}, "n1": "v{i}"}}'.encode() for i in range(100)) +
                       b'], "links": {"next": "page1"}}')
        p1 = requests.Response()
        p1.status_code = 200
        p1._content = b'{"results": [{"id": 100, "n1": "v100"}]}'
        session.get.side_effect = [p0, p1]

        v_map = fetch_variables(session, headers={})
        self.assertEqual(len(v_map), 101)

        u0 = requests.Response()
        u0.status_code = 200
        u0._content = (
            b'{"results": [{"id": "000000000000", "name": "POLSKA"}], '
            b'"links": {"next": "u_page1"}}')
        u1 = requests.Response()
        u1.status_code = 200
        u1._content = (
            b'{"results": [{"id": "030200000000", "name": "DOLNO\xc5\x9aL\xc4\x84SKIE"}]}'
        )
        session.get.side_effect = [u0, u1]

        units = fetch_units(session, headers={})
        self.assertEqual(len(units), 2)
        first_call_params = session.get.call_args_list[2].kwargs['params']
        self.assertIn(('lang', 'pl'), first_call_params)

    def test_fetch_unit_batch_records_pagination_and_completeness(self):
        session = MagicMock()
        r0 = requests.Response()
        r0.status_code = 200
        r0._content = (
            b'{"results": [{"id": 101, "values": [{"year": 2024, "val": 50}]}], '
            b'"links": {"next": "next-url"}}')
        r1 = requests.Response()
        r1.status_code = 200
        r1._content = (
            b'{"results": [{"id": 102, "values": [{"year": 2024, "val": 100}]}]}'
        )
        session.get.side_effect = [r0, r1]

        var_map = {
            '101': ('0-2', 'males', 'total'),
            '102': ('0-2', 'total', 'total')
        }
        records = fetch_unit_batch_records(
            session=session,
            unit_id='000000000000',
            matched_code='0',
            matched_name='POLAND',
            batch=['101', '102'],
            year_params=[('year', '2024')],
            var_id_to_slice=var_map,
            headers={},
        )
        self.assertEqual(len(records), 2)

        r_incomplete = requests.Response()
        r_incomplete.status_code = 200
        r_incomplete._content = (
            b'{"results": [{"id": 101, "values": [{"year": 2024, "val": 50}]}]}'
        )
        session.get.side_effect = [r_incomplete]
        with self.assertRaises(RuntimeError) as ctx:
            fetch_unit_batch_records(
                session=session,
                unit_id='000000000000',
                matched_code='0',
                matched_name='POLAND',
                batch=['101', '102'],
                year_params=[('year', '2024')],
                var_id_to_slice=var_map,
                headers={},
            )
        self.assertIn('missing 1 variable IDs', str(ctx.exception))

    @patch('download_input_data.fetch_units')
    @patch('download_input_data.fetch_variables')
    @patch('download_input_data.load_template_from_gcs')
    @patch('download_input_data.make_request')
    def test_download_and_process_mocked_and_partial_sum_guard(
            self, mock_make_request, mock_load_template, mock_fetch_vars,
            mock_fetch_units):
        template_index = pd.MultiIndex.from_tuples([('0', 'POLAND'),
                                                    ('200000', 'DOLNOŚLĄSKIE')],
                                                   names=['Code', 'Name'])
        template_columns = pd.MultiIndex.from_tuples(
            [
                ('0-2', 'total', 'total', '2024'),
                ('3-6', 'total', 'total', '2024'),
                ('total', 'total', 'total', '2024'),
            ],
            names=['Age', 'Sex', 'Location', 'Year'])
        template_df = pd.DataFrame(10,
                                   index=template_index,
                                   columns=template_columns)
        mock_load_template.return_value = template_df
        mock_fetch_vars.return_value = {
            '101': 'ludność 0-2',
            '102': 'ludność 3-6',
        }
        mock_fetch_units.return_value = [('000000000000', 'POLSKA'),
                                         ('030200000000', 'DOLNOŚLĄSKIE')]

        def full_side_effect(session,
                             url,
                             headers=None,
                             params=None,
                             timeout=60):
            r = requests.Response()
            r.status_code = 200
            if '000000000000' in url:
                r._content = b'''{
                    "results": [
                        {"id": 101, "values": [{"year": 2024, "val": 40}]},
                        {"id": 102, "values": [{"year": 2024, "val": 60}]}
                    ]
                }'''
            else:
                r._content = b'''{
                    "results": [
                        {"id": 101, "values": [{"year": 2024, "val": 15}]},
                        {"id": 102, "values": [{"year": 2024, "val": 25}]}
                    ]
                }'''
            return r

        mock_make_request.side_effect = full_side_effect
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('download_input_data.OUTPUT_DIR', temp_dir):
                download_and_process()
                output_csv = os.path.join(temp_dir,
                                          "StatisticsPoland_input_2024.csv")
                self.assertTrue(os.path.exists(output_csv))
                result_df = pd.read_csv(output_csv,
                                        header=[0, 1, 2, 3],
                                        index_col=[0, 1],
                                        dtype={
                                            0: str,
                                            1: str
                                        })
                self.assertEqual(
                    float(result_df.loc[('0', 'POLAND'),
                                        ('total', 'total', 'total', '2024')]),
                    100.0)

        # Now drop age '3-6' for 2024 on DOLNOŚLĄSKIE: min_count=2 must prevent
        # synthesizing an undercounted total and fail loudly on NaN cells!
        def partial_side_effect(session,
                                url,
                                headers=None,
                                params=None,
                                timeout=60):
            r = requests.Response()
            r.status_code = 200
            if '000000000000' in url:
                r._content = b'''{
                    "results": [
                        {"id": 101, "values": [{"year": 2024, "val": 40}]},
                        {"id": 102, "values": [{"year": 2024, "val": 60}]}
                    ]
                }'''
            else:
                r._content = b'''{
                    "results": [
                        {"id": 101, "values": [{"year": 2024, "val": 15}]},
                        {"id": 102, "values": [{"year": 2024, "val": null}]}
                    ]
                }'''
            return r

        mock_make_request.side_effect = partial_side_effect
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('download_input_data.OUTPUT_DIR', temp_dir):
                with self.assertRaises(RuntimeError) as ctx:
                    download_and_process()
                self.assertIn('Incomplete population matrix',
                              str(ctx.exception))

    @patch('download_input_data.fetch_variables')
    @patch('download_input_data.load_template_from_gcs')
    def test_download_and_process_raises_on_unmapped_slice(
            self, mock_load_template, mock_fetch):
        template_index = pd.MultiIndex.from_tuples([('0', 'POLAND')],
                                                   names=['Code', 'Name'])
        template_columns = pd.MultiIndex.from_tuples(
            [('0-2', 'total', 'total', '2024')],
            names=['Age', 'Sex', 'Location', 'Year'])
        mock_load_template.return_value = pd.DataFrame(10,
                                                       index=template_index,
                                                       columns=template_columns)
        mock_fetch.return_value = {'999': 'unrelated_variable'}

        with self.assertRaises(RuntimeError) as ctx:
            download_and_process()
        self.assertIn("Failed to match variable for slice", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()

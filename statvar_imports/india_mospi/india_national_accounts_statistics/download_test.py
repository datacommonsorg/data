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
"""Unit tests for India_NationalAccountsStatistics download.py."""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from google.api_core import exceptions as gcs_exceptions
import pandas as pd
import requests

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

try:
    from statvar_imports.india_mospi.india_national_accounts_statistics import download
except ModuleNotFoundError:
    import download  # type: ignore[no-redef]


def _mock_response(status_code: int,
                   payload: dict[str, object] | None = None,
                   text: str = '') -> mock.Mock:
    resp = mock.Mock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    if payload is None:
        resp.json.side_effect = ValueError('No JSON')
    else:
        resp.json.return_value = payload
    if status_code >= 400:
        resp.raise_for_status.side_effect = requests.HTTPError(
            f'HTTP {status_code}', response=resp)
    else:
        resp.raise_for_status.return_value = None
    return resp


def _gdp_record(year: str = '2025-26',
                revision: str = 'First Advance Estimates',
                cur: str | None = '35713886',
                const: str | None = '20189918') -> dict[str, object]:
    return {
        'base_year': '2011-12',
        'series': 'Current',
        'year': year,
        'indicator': 'Gross Domestic Product',
        'frequency': 'Annual',
        'revision': revision,
        'quarter': None,
        'current_price': cur,
        'constant_price': const,
        'unit': '₹ Crore',
    }


def _gva_record(
    year: str = '2025-26',
    revision: str = 'First Advance Estimates',
    industry: str | None = 'Manufacturing',
    subindustry: str | None = None,
    institutional_sector: str | None = None,
    cur: str | None = '4554580',
    const: str | None = '3161363',
) -> dict[str, object]:
    return {
        'base_year': '2011-12',
        'series': 'Current',
        'year': year,
        'indicator': 'Gross Value Added',
        'frequency': 'Annual',
        'revision': revision,
        'industry': industry,
        'subindustry': subindustry,
        'institutional_sector': institutional_sector,
        'quarter': None,
        'current_price': cur,
        'constant_price': const,
        'unit': '₹ Crore',
    }


def _gsdp_record(
    year: str = '2025-26',
    state: str = 'Andhra Pradesh',
    indicator: str = 'Gross State Domestic Product',
    cur: str | None = '1762357',
    const: str | None = '952261',
    unit: str = '₹ Crore',
    base_year: str = '2011-12',
) -> dict[str, object]:
    return {
        'base_year': base_year,
        'series': 'Current',
        'year': year,
        'indicator': indicator,
        'frequency': 'Annual',
        'state': state,
        'current_price': cur,
        'constant_price': const,
        'unit': unit,
    }


class DownloadTest(unittest.TestCase):

    def test_fetch_paginated_indicator_paginates_all_pages(self):
        session = mock.Mock(spec=requests.Session)
        page1 = {
            'statusCode': True,
            'meta_data': {
                'page': 1,
                'totalRecords': 3,
                'totalPages': 2,
                'recordPerPage': 2,
            },
            'data': [
                _gdp_record('2025-26', 'First Advance Estimates'),
                _gdp_record('2024-25', 'First Advance Estimates'),
            ],
        }
        page2 = {
            'statusCode': True,
            'meta_data': {
                'page': 2,
                'totalRecords': 3,
                'totalPages': 2,
                'recordPerPage': 2,
            },
            'data': [
                _gdp_record('2021-22', 'Second Revised Estimates'),
            ],
        }
        session.get.side_effect = [
            _mock_response(200, page1),
            _mock_response(200, page2),
        ]

        records, raw_pages = download.fetch_paginated_indicator(
            session=session,
            api_url='https://api.mospi.gov.in/api/nas/getNasData',
            query_params={
                'series': 'Current',
                'base_year': '2011-12',
                'frequency_code': 1,
                'indicator_code': 5,
            },
            page_size=2,
            retry_delay_seconds=0.01,
        )

        self.assertEqual(session.get.call_count, 2)
        self.assertEqual(len(records), 3)
        self.assertEqual(len(raw_pages), 2)

    def test_fetch_paginated_indicator_raises_on_record_count_mismatch(self):
        session = mock.Mock(spec=requests.Session)
        payload = {
            'statusCode': True,
            'meta_data': {
                'page': 1,
                'totalRecords': 5,
                'totalPages': 1,
                'recordPerPage': 200,
            },
            'data': [_gdp_record()],
        }
        session.get.return_value = _mock_response(200, payload)

        with self.assertRaisesRegex(RuntimeError, 'does not match'):
            download.fetch_paginated_indicator(
                session=session,
                api_url='https://api.mospi.gov.in/api/nas/getNasData',
                query_params={'indicator_code': 5},
                retry_delay_seconds=0.01,
            )

    @mock.patch.object(download.time, 'sleep')
    def test_fetch_page_retries_transient_503_and_timeout(self, mock_sleep):
        session = mock.Mock(spec=requests.Session)
        ok_payload = {'statusCode': True, 'data': [], 'meta_data': {}}
        session.get.side_effect = [
            _mock_response(503, {}),
            requests.Timeout('read timed out'),
            _mock_response(200, ok_payload),
        ]

        result = download._fetch_page(
            session=session,
            api_url='https://api.mospi.gov.in/api/nas/getNasData',
            params={'page': 1},
            max_retries=3,
            retry_delay_seconds=1.0,
            retry_backoff=2.0,
        )

        self.assertEqual(result, ok_payload)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @mock.patch.object(download.time, 'sleep')
    def test_fetch_page_does_not_retry_permanent_400(self, mock_sleep):
        session = mock.Mock(spec=requests.Session)
        session.get.return_value = _mock_response(400, {'msg': 'Bad Request'})

        with self.assertRaises(requests.HTTPError):
            download._fetch_page(
                session=session,
                api_url='https://api.mospi.gov.in/api/nas/getNasData',
                params={'limit': 500},
                max_retries=3,
            )

        self.assertEqual(session.get.call_count, 1)
        mock_sleep.assert_not_called()

    def test_fetch_page_raises_on_soft_error_or_non_json(self):
        session = mock.Mock(spec=requests.Session)
        session.get.return_value = _mock_response(
            200, {'statusCode': False, 'msg': 'No Data Found'})
        with self.assertRaisesRegex(RuntimeError, 'statusCode=False'):
            download._fetch_page(
                session=session,
                api_url='https://api.mospi.gov.in/api/nas/getNasData',
                params={'page': 1},
            )

        session.get.return_value = _mock_response(200, None, '<html>404</html>')
        with self.assertRaisesRegex(RuntimeError, 'Non-JSON response'):
            download._fetch_page(
                session=session,
                api_url='https://api.mospi.gov.in/api/nas/getNasData',
                params={'page': 1},
            )

    def test_normalize_gdp_records_filters_allowed_revisions(self):
        records = [
            _gdp_record('2025-26', 'First Advance Estimates'),
            _gdp_record('2021-22', 'Second Revised Estimates'),
            _gdp_record('2022-23', 'Final Estimates'),
            _gdp_record('2013-14', 'Additional Revision'),
            _gdp_record('2024-25', 'First Advance Estimates', None, None),
        ]
        df = download.normalize_gdp_records(records)
        self.assertEqual(len(df), 2)
        self.assertEqual(
            set(df['revision']),
            {'First Advance Estimates', 'Second Revised Estimates'},
        )

    def test_normalize_gva_filters_subindustry_institutional_and_splits_third(
            self):
        records = [
            _gva_record('2025-26', 'First Advance Estimates', 'Manufacturing'),
            _gva_record('2021-22', 'Second Revised Estimates', 'Manufacturing',
                        subindustry='Metal Products'),
            _gva_record('2021-22', 'Second Revised Estimates', None,
                        institutional_sector='General Government'),
            _gva_record('2020-21', 'Third Revised Estimates',
                        'Trade, Repair, Hotels and Restaurants'),
            _gva_record('2012-13', 'Additional Revision', 'Manufacturing'),
        ]
        std_df, third_df = download.normalize_gva_records(records)
        self.assertEqual(len(std_df), 1)
        self.assertEqual(std_df.iloc[0]['revision'], 'First Advance Estimates')
        self.assertEqual(len(third_df), 1)
        self.assertEqual(third_df.iloc[0]['revision'],
                         'Third Revised Estimates')

    def test_normalize_gsdp_filters_base_year_and_drops_empty_rows(self):
        records = [
            _gsdp_record('2025-26', 'Andhra Pradesh', cur='1762357',
                         const='952261'),
            _gsdp_record('2025-26', 'Chandigarh', cur=None, const=None),
            _gsdp_record('2025-26', 'Andhra Pradesh', cur='1800000',
                         const='1000000', base_year='2022-23'),
        ]
        df = download.normalize_gsdp_records(records, 'GSDP')
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['state'], 'Andhra Pradesh')
        self.assertEqual(df.iloc[0]['base_year'], '2011-12')

    def test_merge_records_preserves_missing_states_and_avoids_null_clobber(
            self):
        baseline_df = pd.DataFrame(
            [
                {
                    'base_year': '2011-12',
                    'series': 'Current',
                    'year': '2024-25',
                    'indicator': 'Gross State Domestic Product',
                    'frequency': 'Annual',
                    'state': 'Assam',
                    'current_price': '643667',
                    'constant_price': '337933',
                    'unit': '₹ Crore',
                },
                {
                    'base_year': '2011-12',
                    'series': 'Current',
                    'year': '2024-25',
                    'indicator': 'Gross State Domestic Product',
                    'frequency': 'Annual',
                    'state': 'Andhra Pradesh',
                    'current_price': '1590000',
                    'constant_price': '865013',
                    'unit': '₹ Crore',
                },
                {
                    'base_year': '2011-12',
                    'series': 'Current',
                    'year': '2022-23',
                    'indicator': 'Gross State Domestic Product',
                    'frequency': 'Annual',
                    'state': 'Ladakh',
                    'current_price': '8500',
                    'constant_price': '',
                    'unit': '₹ Crore',
                },
            ],
            columns=download.GSDP_COLUMNS,
        )
        live_df = pd.DataFrame(
            [
                {
                    'base_year': '2011-12',
                    'series': 'Current',
                    'year': '2024-25',
                    'indicator': 'Gross State Domestic Product',
                    'frequency': 'Annual',
                    'state': 'Andhra Pradesh',
                    'current_price': '',  # Empty live cell must not clobber baseline
                    'constant_price': '866646',
                    'unit': '₹ Crore',
                },
                {
                    'base_year': '2011-12',
                    'series': 'Current',
                    'year': '2025-26',
                    'indicator': 'Gross State Domestic Product',
                    'frequency': 'Annual',
                    'state': 'Andhra Pradesh',
                    'current_price': '1762357',
                    'constant_price': '952261',
                    'unit': '₹ Crore',
                },
            ],
            columns=download.GSDP_COLUMNS,
        )

        merged = download.merge_records(baseline_df, live_df,
                                        download.GSDP_COLUMNS,
                                        download.GSDP_KEY_COLUMNS)

        self.assertEqual(len(merged), 4)
        by_key = {(r['year'], r['state']): r for _, r in merged.iterrows()}
        self.assertIn(('2024-25', 'Assam'), by_key)
        self.assertIn(('2022-23', 'Ladakh'), by_key)
        self.assertEqual(by_key[('2024-25', 'Andhra Pradesh')]['current_price'],
                         '1590000')
        self.assertEqual(
            by_key[('2024-25', 'Andhra Pradesh')]['constant_price'], '866646')
        self.assertEqual(by_key[('2025-26', 'Andhra Pradesh')]['current_price'],
                         '1762357')

    @mock.patch.object(download, 'create_session')
    def test_run_download_merges_and_saves_raw_json_and_csvs(
            self, mock_create_session):
        session = mock.MagicMock(spec=requests.Session)
        session.__enter__.return_value = session
        mock_create_session.return_value = session

        def _fake_get(url, params, timeout):
            del url, timeout
            ic = params['indicator_code']
            if ic == download.INDICATOR_GDP:
                data = [_gdp_record('2025-26', 'First Advance Estimates')]
            elif ic == download.INDICATOR_GVA:
                data = [
                    _gva_record('2025-26', 'First Advance Estimates',
                                'Manufacturing'),
                    _gva_record('2020-21', 'Third Revised Estimates',
                                'Trade, Repair, Hotels and Restaurants'),
                ]
            elif ic == download.INDICATOR_GSDP:
                data = [_gsdp_record('2025-26', 'Andhra Pradesh')]
            else:
                data = [
                    _gsdp_record('2025-26', 'Andhra Pradesh',
                                 'GSDP Growth Rate', '10.8', '9.9', '%')
                ]
            return _mock_response(
                200, {
                    'statusCode': True,
                    'meta_data': {
                        'page': 1,
                        'totalRecords': len(data),
                        'totalPages': 1,
                        'recordPerPage': 200,
                    },
                    'data': data,
                })

        session.get.side_effect = _fake_get

        with tempfile.TemporaryDirectory() as tmp_dir:
            baseline_dir = os.path.join(tmp_dir, 'baseline')
            raw_dir = os.path.join(tmp_dir, 'raw_source')
            input_dir = os.path.join(tmp_dir, 'input_files')

            def _write_legacy(filename: str, rows: list[dict[str, str]]) -> None:
                download.write_csv_atomically(
                    pd.DataFrame(rows,
                                 columns=[
                                     'observationDate',
                                     'observationAbout',
                                     'variableMeasured',
                                     'value',
                                     'unit',
                                     'measurementMethod',
                                     'observationPeriod',
                                 ]),
                    os.path.join(baseline_dir, filename),
                )

            _write_legacy('GDP_ANNUAL.csv', [{
                'observationDate': '2022',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                'value': '235973985282904',
                'unit': 'INR',
                'measurementMethod': 'MOSPISecondRevisedEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GDP_India_FirstAdvanced.csv', [{
                'observationDate': '2025',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                'value': '330000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIFirstAdvanceEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GVA_FristAdvanceEstimates_output.csv', [{
                'observationDate': '2025',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_ManufacturingSector',
                'value': '40000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIFirstAdvanceEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GVA_AdvancedEstimates_output.csv', [{
                'observationDate': '2025',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_ConstructionSector',
                'value': '25000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPISecondAdvanceEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GVA_ProvisionalEstimates_output.csv', [{
                'observationDate': '2025',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_MiningQuarrying',
                'value': '5000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIProvisionalEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GVA_SecondRevisedEstimates_output.csv', [{
                'observationDate': '2022',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_ConstructionSector',
                'value': '21000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPISecondRevisedEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GVA_ThirdRevisedEstimates_output.csv', [{
                'observationDate': '2020',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_MOSPIOtherService',
                'value': '12000000000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIThirdRevisedEstimates',
                'observationPeriod': 'P1Y',
            }])
            _write_legacy('GSDP_CONSTANT.csv', [
                {
                    'observationDate': '2025',
                    'observationAbout': 'wikidataId/Q1164',  # Assam
                    'variableMeasured':
                        'dcid:Amount_EconomicActivity_GrossDomesticProduction_RealValue',
                    'value': '3379330000000',
                    'unit': 'INR',
                    'measurementMethod': 'ConstantPrice_WithBaseYear2011_12',
                    'observationPeriod': 'P1Y',
                },
                {
                    'observationDate': '2025',
                    'observationAbout': 'wikidataId/Q200667',  # Corrupted Ladakh -> Puducherry
                    'variableMeasured':
                        'dcid:Amount_EconomicActivity_GrossDomesticProduction_RealValue',
                    'value': '295410000000',
                    'unit': 'INR',
                    'measurementMethod': 'ConstantPrice_WithBaseYear2011_12',
                    'observationPeriod': 'P1Y',
                },
                {
                    'observationDate': '2025',
                    'observationAbout': 'wikidataId/Q1164',  # Assam growth
                    'variableMeasured':
                        'dcid:RealValue_GrowthRate_Amount_EconomicActivity_GrossDomesticProduction',
                    'value': '7.9',
                    'unit': 'Percent',
                    'measurementMethod': 'ConstantPrice_WithBaseYear2011_12',
                    'observationPeriod': 'P1Y',
                },
            ])
            _write_legacy('GSDP_CURRENT.csv', [
                {
                    'observationDate': '2025',
                    'observationAbout': 'wikidataId/Q1164',  # Assam
                    'variableMeasured':
                        'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                    'value': '6436670000000',
                    'unit': 'INR',
                    'measurementMethod': 'CurrentPrice_WithBaseYear2011_12',
                    'observationPeriod': 'P1Y',
                },
                {
                    'observationDate': '2025',
                    'observationAbout': 'wikidataId/Q66743',  # Puducherry
                    'variableMeasured':
                        'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                    'value': '521630000000',
                    'unit': 'INR',
                    'measurementMethod': 'CurrentPrice_WithBaseYear2011_12',
                    'observationPeriod': 'P1Y',
                },
            ])

            results = download.run_download(
                gcs_baseline_dir=baseline_dir,
                raw_source_dir=raw_dir,
                input_dir=input_dir,
                retry_delay_seconds=0.01,
            )

            self.assertEqual(len(results['india_nas_gdp.csv']), 3)
            self.assertEqual(set(results['india_nas_gsdp.csv']['state']),
                             {'Assam', 'Puducherry', 'Andhra Pradesh'})
            gsdp_by_state = {
                r['state']: r for _, r in results['india_nas_gsdp.csv'].iterrows()
            }
            self.assertEqual(gsdp_by_state['Puducherry']['constant_price'],
                             '29541')
            self.assertEqual(gsdp_by_state['Puducherry']['current_price'],
                             '52163')
            self.assertTrue(
                os.path.exists(os.path.join(raw_dir, 'nas_gdp_2011_12.json')))
            with open(os.path.join(raw_dir, 'nas_gsdp_2011_12.json'),
                      encoding='utf-8') as f:
                raw_payload = json.load(f)
            self.assertEqual(raw_payload['query_params']['base_year'],
                             '2011-12')

    @mock.patch.object(download, '_get_gcs_client')
    def test_read_csv_if_exists_uses_object_level_gcs_read(
            self, mock_get_client):
        client = mock.MagicMock()
        bucket = mock.MagicMock()
        blob = mock.MagicMock()
        blob.download_as_bytes.return_value = b'col_a,col_b\n1,2\n'
        bucket.blob.return_value = blob
        client.bucket.return_value = bucket
        mock_get_client.return_value = client

        df = download._read_csv_if_exists(
            'gs://unresolved_mcf/india_mospi/economy/baseline/GDP_ANNUAL.csv')

        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)
        client.bucket.assert_called_once_with('unresolved_mcf')
        client.get_bucket.assert_not_called()
        bucket.blob.assert_called_once_with(
            'india_mospi/economy/baseline/GDP_ANNUAL.csv')

        blob.download_as_bytes.side_effect = gcs_exceptions.NotFound('missing')
        self.assertIsNone(
            download._read_csv_if_exists(
                'gs://unresolved_mcf/india_mospi/economy/baseline/missing.csv'))


class LegacyBaselineConversionTest(unittest.TestCase):

    def test_repair_gsdp_constant_reassigns_ladakh_to_puducherry(self):
        gsdp_constant_df = pd.DataFrame([
            {
                'observationDate': '2025',
                'observationAbout': 'wikidataId/Q200667',  # Corrupted Ladakh
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_RealValue',
                'value': '295410000000',
                'unit': 'INR',
                'measurementMethod': 'ConstantPrice_WithBaseYear2011_12',
                'observationPeriod': 'P1Y',
            },
            {
                'observationDate': '2025',
                'observationAbout': 'wikidataId/Q200667',
                'variableMeasured':
                    'dcid:RealValue_GrowthRate_Amount_EconomicActivity_GrossDomesticProduction',
                'value': '7.96',
                'unit': 'Percent',
                'measurementMethod': 'ConstantPrice_WithBaseYear2011_12',
                'observationPeriod': 'P1Y',
            },
        ])
        gsdp_current_df = pd.DataFrame([
            {
                'observationDate': '2025',
                'observationAbout': 'wikidataId/Q66743',
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                'value': '521630000000',
                'unit': 'INR',
                'measurementMethod': 'CurrentPrice_WithBaseYear2011_12',
                'observationPeriod': 'P1Y',
            },
            {
                'observationDate': '2023',
                'observationAbout': 'wikidataId/Q200667',  # Real Ladakh current-price row
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                'value': '85000000000',
                'unit': 'INR',
                'measurementMethod': 'CurrentPrice_WithBaseYear2011_12',
                'observationPeriod': 'P1Y',
            },
        ])
        dcid_to_place = download.load_dcid_to_place_name(
            os.path.join(_SCRIPT_DIR, 'india_nas_places.csv'))

        gsdp_df, growth_df = download.convert_gsdp_prod_dfs(
            gsdp_constant_df, gsdp_current_df, dcid_to_place)

        by_state = {r['state']: r for _, r in gsdp_df.iterrows()}
        self.assertEqual(by_state['Puducherry']['constant_price'], '29541')
        self.assertEqual(by_state['Puducherry']['current_price'], '52163')
        self.assertEqual(by_state['Ladakh']['current_price'], '8500')
        self.assertEqual(by_state['Ladakh']['constant_price'], '')
        self.assertEqual(len(growth_df), 1)
        self.assertEqual(growth_df.iloc[0]['state'], 'Puducherry')
        self.assertEqual(growth_df.iloc[0]['constant_price'], '7.96')

    def test_convert_gdp_and_gva_preserves_decimal_precision_and_splits_third(
            self):
        gdp_df = pd.DataFrame([
            {
                'observationDate': '2022',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Amount_EconomicActivity_GrossDomesticProduction_Nominal',
                'value': '235973985282904',
                'unit': 'INR',
                'measurementMethod': 'MOSPISecondRevisedEstimates',
                'observationPeriod': 'P1Y',
            },
        ])
        tidy_gdp = download.convert_gdp_prod_dfs([gdp_df])
        self.assertEqual(len(tidy_gdp), 1)
        self.assertEqual(tidy_gdp.iloc[0]['year'], '2021-22')
        self.assertEqual(tidy_gdp.iloc[0]['current_price'], '23597398.5282904')

        gva_df = pd.DataFrame([
            {
                'observationDate': '2026',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_FinanceService',
                'value': '76201230000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIFirstAdvanceEstimates',
                'observationPeriod': 'P1Y',
            },
            {
                'observationDate': '2021',
                'observationAbout': 'country/IND',
                'variableMeasured':
                    'dcid:Nominal_Amount_EconomicActivity_GrossValueAdded_TradeSectorOrMaintenanceAndRepairOrRestaurantAndHotels',
                'value': '19557980000000',
                'unit': 'INR',
                'measurementMethod': 'MOSPIThirdRevisedEstimates',
                'observationPeriod': 'P1Y',
            },
        ])
        std_gva, third_gva = download.convert_gva_prod_dfs([gva_df])
        self.assertEqual(std_gva.iloc[0]['industry'],
                         'Financial, Real Estate & Professional Services')
        self.assertEqual(third_gva.iloc[0]['industry'],
                         'Trade, Repair, Hotels and Restaurants')


if __name__ == '__main__':
    unittest.main()

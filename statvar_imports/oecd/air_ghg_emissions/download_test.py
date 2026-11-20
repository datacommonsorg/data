#!/usr/bin/env python3
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
"""Unit and hermetic integration tests for OECD_Air_GHG_emissions."""

import csv
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '../../..'))
_EXECUTOR_ROOT = os.path.join(_REPO_ROOT, 'import-automation', 'executor')
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
if _EXECUTOR_ROOT not in sys.path:
    sys.path.append(_EXECUTOR_ROOT)

from absl import flags
from app.executor import validation as manifest_validation
import pandas as pd
import requests

from statvar_imports.oecd.air_ghg_emissions import download

_NEW_PRODUCTIVITY_SV = (
    'RealValue_Amount_EconomicActivity_GrossDomesticProduction_AsAFractionOf_'
    'Annual_Amount_Emissions_CarbonDioxide')

_SAMPLE_EXISTING_STATVARS_MCF = """Node: dcid:Annual_Amount_Emissions_CarbonDioxide
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:CarbonDioxide
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_CarbonDioxide_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:CarbonDioxide
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person

Node: dcid:Annual_Emissions_GreenhouseGas
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:GreenhouseGas
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_GreenhouseGas_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:GreenhouseGas
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person

Node: dcid:Annual_Amount_Emissions_CarbonMonoxide
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:CarbonMonoxide
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_CarbonMonoxide_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:CarbonMonoxide
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person

Node: dcid:Annual_Amount_Emissions_OxidesOfNitrogen
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:OxidesOfNitrogen
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_OxidesOfNitrogen_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:OxidesOfNitrogen
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person

Node: dcid:Annual_Amount_Emissions_OxidesOfSulfur
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:OxidesOfSulfur
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_OxidesOfSulfur_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:OxidesOfSulfur
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person

Node: dcid:Annual_Amount_Emissions_VolatileOrganicCompound
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:VolatileOrganicCompound
measurementQualifier: dcs:Annual

Node: dcid:Annual_Amount_Emissions_VolatileOrganicCompound_AsAFractionOf_Count_Person
typeOf: dcs:StatisticalVariable
populationType: dcs:Emissions
measuredProperty: dcs:amount
statType: dcs:measuredValue
emittedThing: dcs:VolatileOrganicCompound
measurementQualifier: dcs:Annual
measurementDenominator: dcs:Count_Person
"""


def _make_csv_http_response(
    payload: bytes,
    url: str = 'https://sdmx.oecd.org/public/rest/data/test',
) -> mock.MagicMock:
    """Builds a mock streaming requests.Response yielding payload bytes."""
    resp = mock.MagicMock()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    resp.url = url
    resp.raise_for_status.return_value = None
    resp.iter_content.return_value = [payload]
    return resp


class DownloadTest(unittest.TestCase):
    """Hermetic unit and config integration tests for OECD_Air_GHG_emissions."""

    def setUp(self) -> None:
        super().setUp()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.places_csv = self.base_dir / 'places_resolved.csv'
        self.places_csv.write_text(
            'place_name,dcid\n'
            'AUS,country/AUS\n'
            'DEU,country/DEU\n'
            'W,Earth\n',
            encoding='utf-8',
        )
        self.valid_places = download.load_resolved_places(str(self.places_csv))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        super().tearDown()

    def test_load_resolved_places_errors(self) -> None:
        with self.assertRaises(FileNotFoundError):
            download.load_resolved_places(str(self.base_dir / 'missing.csv'))

        bad_header = self.base_dir / 'bad_header.csv'
        bad_header.write_text('foo,bar\nAUS,country/AUS\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            download.load_resolved_places(str(bad_header))

        empty_csv = self.base_dir / 'empty.csv'
        empty_csv.write_text('place_name,dcid\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            download.load_resolved_places(str(empty_csv))

    def test_normalize_sdmx_feed_ghg_scales_and_enforces_expected_series(
        self,) -> None:
        df = pd.DataFrame([
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2024',
                'value': 518566.806,
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'KG_CO2E_PS',
                'TIME_PERIOD': '2024',
                'value': 19.41238,
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'OECD',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2024',
                'value': 999999.0,
                'UNIT_MULT': '3',
            },
        ])
        records = download.normalize_sdmx_feed(
            'ghg',
            df,
            self.valid_places,
            expected_series=download.SDMX_FEEDS[0].expected_series,
        )
        self.assertEqual(
            records,
            {
                ('AUS', 'GHG', 'THND_TONNECO2', '2024'): '518566.806',
                ('AUS', 'GHG', 'TONNE_CAP', '2024'): '19.41238',
            },
        )

        with self.assertRaises(RuntimeError):
            download.normalize_sdmx_feed(
                'ghg',
                df.iloc[:1],
                self.valid_places,
                expected_series=download.SDMX_FEEDS[0].expected_series,
            )

    def test_normalize_sdmx_feed_air_emissions_maps_nmvoc_and_units(
        self,) -> None:
        df = pd.DataFrame([
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'CO',
                'MEASURE': 'T_EM_MM',
                'UNIT_MEASURE': 'T',
                'TIME_PERIOD': '2024',
                'value': 2585.979,
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'NMVOC',
                'MEASURE': 'T_EM_MM',
                'UNIT_MEASURE': 'KG_PS',
                'TIME_PERIOD': '2024',
                'value': 46.70406,
                'UNIT_MULT': '0',
            },
            {
                'REF_AREA': 'DEU',
                'FREQ': 'A',
                'POLLUTANT': 'SOX',
                'MEASURE': 'T_EM_MM',
                'UNIT_MEASURE': 'T',
                'TIME_PERIOD': '2024',
                'value': 400000.0,
                'UNIT_MULT': '0',
            },
        ])
        records = download.normalize_sdmx_feed('air_emissions', df,
                                               self.valid_places)
        self.assertEqual(records[('AUS', 'CO', 'THND_TONNE', '2024')],
                         '2585.979')
        self.assertEqual(records[('AUS', 'VOC', 'KG_CAP', '2024')], '46.70406')
        self.assertEqual(records[('DEU', 'SOX', 'THND_TONNE', '2024')], '400')

    def test_normalize_sdmx_feed_green_growth_co2(self) -> None:
        df = pd.DataFrame([
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'MEASURE': 'CO2_PBEM',
                'UNIT_MEASURE': 'T',
                'ACTIVITY': '_T',
                'TIME_PERIOD': '2024',
                'value': 355.97,
                'UNIT_MULT': '6',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'MEASURE': 'CO2_PBEMCAP',
                'UNIT_MEASURE': 'T_CO2E_PS',
                'ACTIVITY': '_T',
                'TIME_PERIOD': '2024',
                'value': 13.33,
                'UNIT_MULT': '0',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'MEASURE': 'CO2_PBPROD',
                'UNIT_MEASURE': 'USD_CO2',
                'ACTIVITY': '_T',
                'TIME_PERIOD': '2024',
                'value': 4.47,
                'UNIT_MULT': '0',
            },
            {
                'REF_AREA': 'W',
                'FREQ': 'A',
                'MEASURE': 'CO2_PBEM',
                'UNIT_MEASURE': 'T',
                'ACTIVITY': '_T',
                'TIME_PERIOD': '2020',
                'value': 34000.5,
                'UNIT_MULT': '6',
            },
        ])
        records = download.normalize_sdmx_feed(
            'green_growth_co2',
            df,
            self.valid_places,
            expected_series=download.SDMX_FEEDS[2].expected_series,
        )
        self.assertEqual(
            records,
            {
                ('AUS', 'CO2', 'MLN_TONNE', '2024'): '355.97',
                ('AUS', 'CO2', 'TONNE_CAP', '2024'): '13.33',
                ('AUS', 'CO2_PBPROD', 'USD_CO2', '2024'): '4.47',
                ('W', 'CO2', 'MLN_TONNE', '2020'): '34000.5',
            },
        )

    def test_parse_historical_prefers_canonical_earth_and_drops_oeu(
        self,) -> None:
        hist_csv = self.base_dir / 'hist.csv'
        hist_csv.write_text(
            'observationAbout,observationDate,value,variableMeasured,unit,scalingFactor\n'
            'dcid:Earth,1960,9500000000,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n'
            'dcid:country/AUS,1960,88452975,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n'
            'dcid:country/WLD,1960,9400000000,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n'
            'dcid:country/WLD,2020,33000000000,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n'
            'dcid:country/OEU,2020,3000000000,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n',
            encoding='utf-8',
        )
        hist_records = download.parse_historical_baseline_csv(
            str(hist_csv), self.valid_places)
        self.assertNotIn(('OEU', 'CO2', 'MLN_TONNE', '2020'), hist_records)
        self.assertEqual(hist_records[('AUS', 'CO2', 'MLN_TONNE', '1960')],
                         '88.452975')
        # Canonical dcid:Earth (9500) must not be overwritten by later country/WLD (9400).
        self.assertEqual(hist_records[('W', 'CO2', 'MLN_TONNE', '1960')],
                         '9500')

        live_records = {
            ('W', 'CO2', 'MLN_TONNE', '2020'): '34000.5',
        }
        merged_rows, retained_count = download.merge_observations(
            live_records=live_records,
            historical_records=hist_records,
        )
        self.assertEqual(retained_count, 2)
        self.assertEqual(len(merged_rows), 3)
        by_key = {
            (r['LOCATION'], r['SUBJECT'], r['MEASURE'], r['TIME']): r['Value']
            for r in merged_rows
        }
        self.assertEqual(by_key[('W', 'CO2', 'MLN_TONNE', '2020')], '34000.5')
        self.assertEqual(by_key[('W', 'CO2', 'MLN_TONNE', '1960')], '9500')

        conflict_csv = self.base_dir / 'conflict_hist.csv'
        conflict_csv.write_text(
            'observationAbout,observationDate,value,variableMeasured\n'
            'dcid:country/AUS,1960,1000000,dcid:Annual_Amount_Emissions_CarbonDioxide\n'
            'dcid:country/AUS,1960,2000000,dcid:Annual_Amount_Emissions_CarbonDioxide\n',
            encoding='utf-8',
        )
        with self.assertRaises(ValueError):
            download.parse_historical_baseline_csv(str(conflict_csv),
                                                   self.valid_places)

    @mock.patch('statvar_imports.oecd.air_ghg_emissions.download.time.sleep')
    def test_fetch_sdmx_dataframe_retries_transient_http_429(
        self,
        mock_sleep: mock.MagicMock,
    ) -> None:
        raw_dir = self.base_dir / 'raw'
        spec = download.SDMX_FEEDS[0]
        mock_session = mock.MagicMock()

        resp_429 = requests.Response()
        resp_429.status_code = 429
        err_429 = requests.exceptions.HTTPError('Too Many Requests',
                                                response=resp_429)
        err_ctx = mock.MagicMock()
        err_ctx.__enter__.return_value = err_ctx
        err_ctx.__exit__.return_value = False
        err_ctx.raise_for_status.side_effect = err_429

        csv_payload = (
            b'DATAFLOW,REF_AREA,FREQ,POLLUTANT,MEASURE,UNIT_MEASURE,'
            b'TIME_PERIOD,OBS_VALUE,UNIT_MULT\n'
            b'OECD.ENV.EPI:DSD_AIR_GHG@DF_AIR_GHG(1.0),AUS,A,GHG,_T,T_CO2E,'
            b'2024,518566.8,3\n')
        mock_session.get.side_effect = [
            err_ctx,
            _make_csv_http_response(csv_payload),
        ]

        df = download.fetch_sdmx_dataframe(
            session=mock_session,
            spec=spec,
            raw_dir=str(raw_dir),
            max_retries=3,
            retry_delay=0.01,
        )
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['OBS_VALUE'], '518566.8')
        self.assertEqual(mock_session.get.call_count, 2)
        mock_sleep.assert_called_once()
        self.assertTrue((raw_dir / spec.raw_filename).is_file())

    def test_fetch_sdmx_dataframe_fails_fast_on_permanent_404(self) -> None:
        raw_dir = self.base_dir / 'raw'
        spec = download.SDMX_FEEDS[0]
        mock_session = mock.MagicMock()
        resp_404 = requests.Response()
        resp_404.status_code = 404
        err_ctx = mock.MagicMock()
        err_ctx.__enter__.return_value = err_ctx
        err_ctx.__exit__.return_value = False
        err_ctx.raise_for_status.side_effect = requests.exceptions.HTTPError(
            'Not Found', response=resp_404)
        mock_session.get.return_value = err_ctx

        with self.assertRaises(RuntimeError):
            download.fetch_sdmx_dataframe(
                session=mock_session,
                spec=spec,
                raw_dir=str(raw_dir),
                max_retries=3,
                retry_delay=0.01,
            )
        self.assertEqual(mock_session.get.call_count, 1)

    def test_fetch_sdmx_dataframe_rejects_invalid_csv_and_cleans_tmp(
        self,) -> None:
        raw_dir = self.base_dir / 'raw'
        spec = download.SDMX_FEEDS[0]
        for bad_payload in (b'<html>Maintenance</html>', b'FOO,BAR\n1,2\n'):
            mock_session = mock.MagicMock()
            mock_session.get.return_value = _make_csv_http_response(bad_payload)
            with self.assertRaises(RuntimeError):
                download.fetch_sdmx_dataframe(
                    session=mock_session,
                    spec=spec,
                    raw_dir=str(raw_dir),
                    max_retries=3,
                    retry_delay=0.01,
                )
            self.assertFalse((raw_dir / spec.raw_filename).exists())
            self.assertFalse((raw_dir / f'{spec.raw_filename}.tmp').exists())

    def test_normalize_sdmx_feed_skips_placeholders_and_detects_conflicts(
        self,) -> None:
        df_placeholders = pd.DataFrame([
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2023',
                'OBS_VALUE': '-',
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2022',
                'OBS_VALUE': True,
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2021',
                'OBS_VALUE': 'n.a.',
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'WLD',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2024',
                'OBS_VALUE': '100.0',
                'UNIT_MULT': '3',
            },
        ])
        records = download.normalize_sdmx_feed('ghg', df_placeholders,
                                               self.valid_places)
        self.assertEqual(records,
                         {('W', 'GHG', 'THND_TONNECO2', '2024'): '100'})
        with self.assertRaises(ValueError):
            download._parse_unit_mult('THOUSANDS')

        df_conflict = pd.DataFrame([
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2024',
                'OBS_VALUE': '100.0',
                'UNIT_MULT': '3',
            },
            {
                'REF_AREA': 'AUS',
                'FREQ': 'A',
                'POLLUTANT': 'GHG',
                'MEASURE': '_T',
                'UNIT_MEASURE': 'T_CO2E',
                'TIME_PERIOD': '2024',
                'OBS_VALUE': '200.0',
                'UNIT_MULT': '3',
            },
        ])
        with self.assertRaises(ValueError):
            download.normalize_sdmx_feed('ghg', df_conflict, self.valid_places)

        df_empty = pd.DataFrame([{
            'REF_AREA': 'OECD',
            'FREQ': 'A',
            'POLLUTANT': 'GHG',
            'MEASURE': '_T',
            'UNIT_MEASURE': 'T_CO2E',
            'TIME_PERIOD': '2024',
            'OBS_VALUE': '100.0',
            'UNIT_MULT': '3',
        }])
        with self.assertRaises(RuntimeError):
            download.normalize_sdmx_feed('ghg', df_empty, self.valid_places)

    @mock.patch(
        'statvar_imports.oecd.air_ghg_emissions.download.storage.Client')
    def test_download_historical_baseline_cleans_tmp_on_empty_blob(
        self,
        mock_storage_cls: mock.MagicMock,
    ) -> None:
        raw_dir = self.base_dir / 'raw_gcs'
        mock_blob = mock.MagicMock()

        def write_empty(filename: str, timeout: int = 300) -> None:
            Path(filename).write_text('', encoding='utf-8')

        mock_blob.download_to_filename.side_effect = write_empty
        mock_storage_cls.return_value.bucket.return_value.blob.return_value = (
            mock_blob)
        with self.assertRaises(ValueError):
            download.download_historical_baseline_from_gcs(
                'unresolved_mcf', 'blob.csv', str(raw_dir))
        self.assertEqual(list(raw_dir.iterdir()), [])

    def test_write_staging_csv_atomic_and_main_validation(self) -> None:
        with self.assertRaises(ValueError):
            download.write_staging_csv_atomic(str(self.base_dir / 'out'), [])
        with self.assertRaises(ValueError):
            download.main(['download.py', 'unexpected_arg'])

        local_flags = flags.FlagValues()
        download._define_flags(flag_values=local_flags)
        local_flags(['download.py'])
        with (
                mock.patch.object(download, '_FLAGS', local_flags),
                mock.patch.object(download, 'download_and_process') as mock_run,
        ):
            download.main(['download.py'])
        mock_run.assert_called_once_with(
            output_dir=os.path.join(_MODULE_DIR, 'input_files'),
            raw_dir=os.path.join(_MODULE_DIR, 'input_files'),
            places_resolved_csv=os.path.join(
                _MODULE_DIR, 'oecd_air_ghg_emissions_places_resolved.csv'),
            gcs_bucket=download.HISTORICAL_GCS_BUCKET,
            gcs_blob=download.HISTORICAL_GCS_BLOB,
        )

    def test_create_http_session_and_timeout_adapter(self) -> None:
        session = download._create_http_session(timeout=45)
        self.assertEqual(
            session.headers.get('User-Agent'),
            download.DEFAULT_USER_AGENT,
        )
        self.assertEqual(
            download._build_sdmx_csv_url(download.SDMX_FEEDS[0]),
            'https://sdmx.oecd.org/public/rest/data/'
            'OECD.ENV.EPI,DSD_AIR_GHG@DF_AIR_GHG,/.A.GHG._T.T_CO2E+KG_CO2E_PS',
        )
        https_adapter = session.get_adapter('https://sdmx.oecd.org/')
        http_adapter = session.get_adapter('http://sdmx.oecd.org/')
        self.assertIsInstance(https_adapter, download._TimeoutHTTPAdapter)
        self.assertIsInstance(http_adapter, download._TimeoutHTTPAdapter)

        req = requests.Request('GET', 'https://sdmx.oecd.org/').prepare()
        with mock.patch.object(
                requests.adapters.HTTPAdapter,
                'send',
                return_value='ok',
        ) as mock_send:
            https_adapter.send(req, timeout=None)
            mock_send.assert_called_once_with(req, timeout=45)
            mock_send.reset_mock()
            https_adapter.send(req, timeout=15)
            mock_send.assert_called_once_with(req, timeout=15)
        session.close()

    @mock.patch(
        'statvar_imports.oecd.air_ghg_emissions.download.storage.Client')
    @mock.patch(
        'statvar_imports.oecd.air_ghg_emissions.download._create_http_session')
    def test_download_and_process_end_to_end_purges_stale_csv(
        self,
        mock_create_session: mock.MagicMock,
        mock_storage_cls: mock.MagicMock,
    ) -> None:
        out_dir = self.base_dir / 'input_files'
        out_dir.mkdir(parents=True)
        stale_csv = out_dir / 'old_stale.csv'
        stale_csv.write_text('stale\n', encoding='utf-8')
        stale_json = out_dir / 'obsolete_raw.json'
        stale_json.write_text('{}', encoding='utf-8')

        ghg_csv = ('REF_AREA,FREQ,POLLUTANT,MEASURE,UNIT_MEASURE,TIME_PERIOD,'
                   'OBS_VALUE,UNIT_MULT\n'
                   'AUS,A,GHG,_T,T_CO2E,2024,518566.8,3\n'
                   'AUS,A,GHG,_T,KG_CO2E_PS,2024,19.41,3\n').encode('utf-8')
        air_lines = [
            'REF_AREA,FREQ,POLLUTANT,MEASURE,UNIT_MEASURE,TIME_PERIOD,'
            'OBS_VALUE,UNIT_MULT'
        ]
        for pollutant in ('CO', 'NOX', 'SOX', 'NMVOC'):
            for unit_measure, unit_mult in (('T', '3'), ('KG_PS', '0')):
                air_lines.append(
                    f'AUS,A,{pollutant},T_EM_MM,{unit_measure},2024,100.0,'
                    f'{unit_mult}')
        air_csv = ('\n'.join(air_lines) + '\n').encode('utf-8')
        gg_csv = ('REF_AREA,FREQ,MEASURE,UNIT_MEASURE,ACTIVITY,TIME_PERIOD,'
                  'OBS_VALUE,UNIT_MULT\n'
                  'AUS,A,CO2_PBEM,T,_T,2024,355.97,6\n'
                  'AUS,A,CO2_PBEMCAP,T_CO2E_PS,_T,2024,13.33,0\n'
                  'AUS,A,CO2_PBPROD,USD_CO2,_T,2024,4.47,0\n').encode('utf-8')

        sess = mock.MagicMock()
        sess.__enter__.return_value = sess
        sess.__exit__.return_value = False
        sess.get.side_effect = [
            _make_csv_http_response(ghg_csv),
            _make_csv_http_response(air_csv),
            _make_csv_http_response(gg_csv),
        ]
        mock_create_session.return_value = sess

        mock_blob = mock.MagicMock()

        def fake_gcs_download(filename: str, timeout: int = 300) -> None:
            Path(filename).write_text(
                'observationAbout,observationDate,value,variableMeasured,unit,scalingFactor\n'
                'dcid:country/AUS,1960,88452975,dcid:Annual_Amount_Emissions_CarbonDioxide,MetricTon,\n',
                encoding='utf-8',
            )

        mock_blob.download_to_filename.side_effect = fake_gcs_download
        mock_storage_cls.return_value.bucket.return_value.blob.return_value = (
            mock_blob)

        # Default behavior downloads raw CSVs directly into input_files and
        # retains all 4 raw CSVs alongside oecd_air_ghg_emissions_input.csv.
        staging_path = download.download_and_process(
            output_dir=str(out_dir),
            raw_dir=str(out_dir),
            places_resolved_csv=str(self.places_csv),
        )
        self.assertFalse(stale_csv.exists())
        self.assertFalse(stale_json.exists())
        self.assertTrue((out_dir / 'oecd_air_ghg_raw.csv').is_file())
        self.assertTrue((out_dir / 'oecd_air_emissions_raw.csv').is_file())
        self.assertTrue((out_dir / 'oecd_green_growth_co2_raw.csv').is_file())
        self.assertTrue((out_dir / 'historical_baseline_2024.csv').is_file())
        self.assertTrue(Path(staging_path).is_file())
        with open(staging_path, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 14)

    def test_resolve_module_path_handles_relative_and_absolute(self) -> None:
        abs_path = '/tmp/example_dir'
        self.assertEqual(download._resolve_module_path(abs_path), abs_path)
        rel_resolved = download._resolve_module_path('input_files')
        self.assertTrue(os.path.isabs(rel_resolved))
        self.assertTrue(rel_resolved.endswith('/input_files'))

    def test_checked_in_configs_manifest_validation_and_sample_parity(
        self,) -> None:
        module_path = Path(_MODULE_DIR)
        places = download.load_resolved_places(
            str(module_path / 'oecd_air_ghg_emissions_places_resolved.csv'))
        self.assertEqual(places['AUS'], 'country/AUS')
        self.assertEqual(places['W'], 'Earth')
        self.assertNotIn('OEU', places)
        self.assertNotIn('WLD', places)

        manifest_data = json.loads(
            (module_path / 'manifest.json').read_text(encoding='utf-8'))
        manifest_validation.is_manifest_valid(
            manifest_data,
            _REPO_ROOT,
            'statvar_imports/oecd/air_ghg_emissions',
        )
        spec_cfg = manifest_data['import_specifications'][0]
        self.assertEqual(spec_cfg['scripts'][0], 'download.py')
        self.assertNotIn('raw_files/*', spec_cfg['source_files'])

        stats_csv = self.base_dir / 'summary_report.csv'
        all_svs = sorted(
            [sv[len('dcid:'):] for sv in download.HISTORICAL_SV_MAP] +
            [_NEW_PRODUCTIVITY_SV])
        current_year = datetime.datetime.now(datetime.UTC).year

        def write_stats(prod_year: int, co2_year: int, ghg_year: int) -> None:
            with open(stats_csv, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'StatVar',
                    'NumPlaces',
                    'NumObservations',
                    'MinValue',
                    'MaxValue',
                    'MinDate',
                    'MaxDate',
                ])
                for sv in all_svs:
                    if sv == _NEW_PRODUCTIVITY_SV:
                        yr = prod_year
                    elif 'CarbonDioxide' in sv:
                        yr = co2_year
                    elif 'GreenhouseGas' in sv:
                        yr = ghg_year
                    else:
                        yr = current_year - 1
                    writer.writerow([sv, 80, 3000, 0.0, 100000.0, 1990, yr])

        # Staggered current and future-year updates pass cleanly.
        for valid_ghg_year in (current_year, current_year + 5):
            write_stats(
                prod_year=max(2024, current_year - 3),
                co2_year=current_year + 1,
                ghg_year=valid_ghg_year,
            )
            val_out = self.base_dir / 'validation_output.csv'
            val_cmd = [
                sys.executable,
                '-m',
                'tools.import_validation.runner',
                f'--validation_config={module_path / "validation_config.json"}',
                f'--stats_summary={stats_csv}',
                f'--validation_output={val_out}',
            ]
            val_proc = subprocess.run(
                val_cmd,
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(val_proc.returncode, 0, msg=val_proc.stderr)

        # Stale regressions (< max(2024, current_year - 4)) fail.
        for stale_year in (2021, current_year - 5):
            write_stats(
                prod_year=stale_year,
                co2_year=current_year,
                ghg_year=current_year,
            )
            bad_proc = subprocess.run(
                val_cmd,
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(bad_proc.returncode, 0)

        existing_mcf = self.base_dir / 'existing_statvars.mcf'
        existing_mcf.write_text(_SAMPLE_EXISTING_STATVARS_MCF, encoding='utf-8')
        hermetic_cfg = self.base_dir / 'hermetic_overrides.csv'
        hermetic_cfg.write_text(
            'parameter,value\n'
            'recon_lookup_api,False\n'
            'check_url,False\n'
            'output_only_new_statvars,False\n',
            encoding='utf-8',
        )
        out_prefix = self.base_dir / 'sample_output'
        proc = subprocess.run(
            [
                sys.executable,
                os.path.join(
                    _REPO_ROOT,
                    'tools/statvar_importer/stat_var_processor.py',
                ),
                f'--input_data={module_path / "test_data/sample_input.csv"}',
                f'--pv_map={module_path / "oecd_air_ghg_emissions_pvmap.csv"}',
                f'--config_file={module_path / "oecd_air_ghg_emissions_metadata.csv"},{hermetic_cfg}',
                f'--places_resolved_csv={module_path / "oecd_air_ghg_emissions_places_resolved.csv"}',
                f'--existing_statvar_mcf={existing_mcf}',
                f'--output_path={out_prefix}',
            ],
            cwd=str(self.base_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(
            (self.base_dir / 'sample_output.csv').read_text(encoding='utf-8'),
            (module_path /
             'test_data/sample_output.csv').read_text(encoding='utf-8'),
        )
        self.assertEqual(
            (self.base_dir / 'sample_output.tmcf').read_text(encoding='utf-8'),
            (module_path /
             'test_data/sample_output.tmcf').read_text(encoding='utf-8'),
        )
        emitted_mcf = (self.base_dir / 'sample_output_stat_vars.mcf').read_text(
            encoding='utf-8')
        self.assertEqual(emitted_mcf.count('Node: '), 13)
        self.assertIn('Node: dcid:Annual_Emissions_GreenhouseGas', emitted_mcf)
        self.assertIn(f'Node: dcid:{_NEW_PRODUCTIVITY_SV}', emitted_mcf)
        self.assertIn(
            'name: "Production-based CO2 productivity, GDP per unit of '
            'energy-related CO2 emissions"',
            emitted_mcf,
        )


if __name__ == '__main__':
    unittest.main()

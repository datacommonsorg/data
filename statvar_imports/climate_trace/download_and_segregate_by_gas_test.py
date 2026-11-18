# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
import zipfile

import pandas as pd
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)
import download_and_segregate_by_gas

TEST_DATA_DIR = os.path.join(SCRIPT_DIR, 'test_data')
SV_PROCESSOR = os.path.abspath(
    os.path.join(SCRIPT_DIR, '..', '..', 'tools', 'statvar_importer',
                 'stat_var_processor.py'))


class DownloadAndSegregateByGasTest(unittest.TestCase):

    def test_format_emission(self):
        self.assertEqual(download_and_segregate_by_gas._format_emission(0.0),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission(-0.0),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission('0'),
                         '0')
        self.assertEqual(download_and_segregate_by_gas._format_emission(1e-7),
                         '0.0000001')
        self.assertEqual(
            download_and_segregate_by_gas._format_emission(123.4500), '123.45')
        self.assertEqual(download_and_segregate_by_gas._format_emission(None),
                         '')
        self.assertEqual(
            download_and_segregate_by_gas._format_emission(float('nan')), '')
        self.assertEqual(download_and_segregate_by_gas._format_emission(''), '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('   '),
                         '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('N/A'),
                         '')
        self.assertEqual(download_and_segregate_by_gas._format_emission('null'),
                         '')

    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_country_list_api_failure_raises_exception(self,
                                                       mock_get_retry_session):
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.get.side_effect = requests.exceptions.RequestException(
            "API failure")
        mock_get_retry_session.return_value = mock_session

        with self.assertRaises(requests.exceptions.RequestException):
            download_and_segregate_by_gas.download_and_segregate_by_gas()
        mock_session.__exit__.assert_called_once()

    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('download_and_segregate_by_gas.download_and_process_zip')
    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_empty_gas_dataframes_raises_runtime_error(self,
                                                       mock_get_retry_session,
                                                       mock_download_zip,
                                                       mock_open):
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'id': 'USA'}, {'id': 'IND'}]
        mock_session.get.return_value = mock_response
        mock_get_retry_session.return_value = mock_session

        # Simulate all downloads returning None (e.g., HTTP 404 or no relevant CSVs)
        mock_download_zip.return_value = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(
                    download_and_segregate_by_gas, '__file__',
                    os.path.join(tmp_dir, 'download_and_segregate_by_gas.py')):
                with self.assertRaisesRegex(
                        RuntimeError, "No data was downloaded for gas: co2"):
                    download_and_segregate_by_gas.download_and_segregate_by_gas(
                    )
        self.assertEqual(mock_download_zip.call_count, 2)
        mock_session.__exit__.assert_called_once()

    def test_download_and_process_zip_404_returns_none(self):
        mock_session = MagicMock()
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.raise_for_status.side_effect = (
            requests.exceptions.HTTPError(response=mock_response_404))
        mock_session.get.return_value = mock_response_404

        result = download_and_segregate_by_gas.download_and_process_zip(
            "http://example.com/test.zip", "USA", "co2", session=mock_session)
        self.assertIsNone(result)

    def test_download_and_process_zip_non_404_raises(self):
        mock_session = MagicMock()
        mock_response_500 = MagicMock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error",
                                          response=mock_response_500))
        mock_session.get.return_value = mock_response_500

        with self.assertRaises(requests.exceptions.HTTPError):
            download_and_segregate_by_gas.download_and_process_zip(
                "http://example.com/test.zip",
                "USA",
                "co2",
                session=mock_session)

    def test_download_and_process_zip_bad_zip_raises(self):
        mock_session = MagicMock()
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = b"not a valid zip payload"
        mock_session.get.return_value = mock_response_ok

        with self.assertRaises(zipfile.BadZipFile):
            download_and_segregate_by_gas.download_and_process_zip(
                "http://example.com/test.zip",
                "USA",
                "co2",
                session=mock_session)

    def test_download_and_process_zip_valid_zip(self):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("country_agriculture_emissions.csv",
                        "iso3_country,gas,emissions_quantity\nUSA,co2,100.5\n")
            zf.writestr("other_metadata.csv", "col1,col2\n1,2\n")
            zf.writestr("readme.txt", "ignore me")

        mock_session = MagicMock()
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.content = zip_buffer.getvalue()
        mock_session.get.return_value = mock_response_ok

        df = download_and_segregate_by_gas.download_and_process_zip(
            "http://example.com/USA.zip", "USA", "co2", session=mock_session)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, 'iso3_country'], 'USA')
        self.assertAlmostEqual(df.loc[0, 'emissions_quantity'], 100.5)

    @patch('download_and_segregate_by_gas.download_and_process_zip')
    @patch('download_and_segregate_by_gas.get_retry_session')
    def test_download_and_segregate_by_gas_happy_path(self,
                                                      mock_get_retry_session,
                                                      mock_download_zip):
        with tempfile.TemporaryDirectory() as tmp_dir:
            check_country_path = os.path.join(tmp_dir, 'check_country.csv')
            with open(check_country_path, 'w') as f:
                f.write("IND\n")

            mock_session = MagicMock()
            mock_session.__enter__.return_value = mock_session
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{'id': 'USA'}]
            mock_session.get.return_value = mock_response
            mock_get_retry_session.return_value = mock_session

            def side_effect(url, iso, gas, session):
                if iso == 'USA':
                    return pd.DataFrame({
                        'iso3_country': ['USA', 'USA'],
                        'sector': ['agriculture', 'transportation'],
                        'subsector': ['cropland-fires', 'domestic-shipping'],
                        'start_time': [
                            '2020-01-01 00:00:00',
                            '2020-01-01 00:00:00',
                        ],
                        'gas': [gas, gas],
                        'emissions_quantity': [1e-7, 0.0],
                    })
                return None

            mock_download_zip.side_effect = side_effect

            with patch.object(
                    download_and_segregate_by_gas, '__file__',
                    os.path.join(tmp_dir, 'download_and_segregate_by_gas.py')):
                download_and_segregate_by_gas.download_and_segregate_by_gas()

            output_dir = os.path.join(tmp_dir, 'input_files')
            for gas in ["co2", "ch4", "n2o", "co2e_20yr", "co2e_100yr"]:
                csv_path = os.path.join(output_dir, f"all_countries_{gas}.csv")
                tmp_path = f"{csv_path}.tmp"
                self.assertTrue(os.path.exists(csv_path))
                self.assertFalse(os.path.exists(tmp_path))
                with open(csv_path, 'r') as f:
                    content = f.read()
                self.assertIn("0.0000001", content)
                self.assertNotIn("1e-07", content)

            ghg_csv_path = os.path.join(output_dir,
                                        "greenhousegas_co2e_100yr.csv")
            self.assertTrue(os.path.exists(ghg_csv_path))
            ghg_df = pd.read_csv(ghg_csv_path, dtype=str)
            self.assertIn("co2e_100yr", set(ghg_df["gas"]))
            self.assertIn("sector_agriculture", set(ghg_df["gas"]))
            self.assertIn("sector_maritime", set(ghg_df["gas"]))
            self.assertIn("subsector_cropland-fires", set(ghg_df["gas"]))
            self.assertIn("subsector_shipping", set(ghg_df["gas"]))

            mock_session.__exit__.assert_called_once()

    def test_generate_greenhousegas_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_df = pd.DataFrame({
                'iso3_country': ['USA'] * 6,
                'sector': [
                    'transportation',
                    'transportation',
                    'waste',
                    'waste',
                    'agriculture',
                    'fluorinated-gases',
                ],
                'subsector': [
                    'domestic-shipping',
                    'international-shipping',
                    'domestic-wastewater-treatment-and-discharge',
                    'industrial-wastewater-treatment-and-discharge',
                    'net-soil-organic-carbon',
                    'fluorinated-gases',
                ],
                'start_time': ['2020-01-01 00:00:00'] * 6,
                'end_time': ['2020-12-31 00:00:00'] * 6,
                'gas': ['co2e_100yr'] * 6,
                'emissions_quantity': [10.0, 25.5, 5.0, 15.0, 100.0, 50.0],
            })
            download_and_segregate_by_gas.generate_greenhousegas_input(
                raw_df, tmp_dir)
            ghg_path = os.path.join(tmp_dir, 'greenhousegas_co2e_100yr.csv')
            ghg_df = pd.read_csv(ghg_path, dtype=str)
            ghg_map = dict(zip(ghg_df['gas'], ghg_df['emissions_quantity']))

            self.assertEqual(ghg_map['co2e_100yr'], '205.5')
            self.assertEqual(ghg_map['sector_maritime'], '35.5')
            self.assertEqual(ghg_map['subsector_shipping'], '35.5')
            self.assertEqual(
                ghg_map['subsector_wastewater-treatment-and-discharge'], '20')
            self.assertEqual(ghg_map['subsector_fluorinated-gases'], '50')
            # Unmapped keys must be filtered out
            self.assertNotIn('subsector_net-soil-organic-carbon', ghg_map)
            self.assertNotIn('sector_fluorinated-gases', ghg_map)

    def test_generate_greenhousegas_input_missing_columns_raises(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_df = pd.DataFrame({
                'iso3_country': ['USA'],
                'start_time': ['2020-01-01 00:00:00'],
            })
            with self.assertRaisesRegex(
                    ValueError,
                    r'Missing required columns.*emissions_quantity.*sector.*subsector',
            ):
                download_and_segregate_by_gas.generate_greenhousegas_input(
                    bad_df, tmp_dir)

    def test_append_legacy_subsector_rollups(self):
        raw_df = pd.DataFrame({
            'iso3_country': ['USA'] * 5,
            'sector': [
                'transportation',
                'transportation',
                'waste',
                'waste',
                'agriculture',
            ],
            'subsector': [
                'domestic-shipping',
                'international-shipping',
                'domestic-wastewater-treatment-and-discharge',
                'industrial-wastewater-treatment-and-discharge',
                'cropland-fires',
            ],
            'start_time': ['2020-01-01 00:00:00'] * 5,
            'end_time': ['2020-12-31 00:00:00'] * 5,
            'gas': ['co2'] * 5,
            'emissions_quantity': ['10', '25.5', '5', '15', '100'],
        })
        rolled_df = download_and_segregate_by_gas.append_legacy_subsector_rollups(
            raw_df)
        sub_map = dict(
            zip(rolled_df['subsector'], rolled_df['emissions_quantity']))
        sec_map = dict(zip(rolled_df['subsector'], rolled_df['sector']))
        self.assertEqual(sub_map['shipping'], '35.5')
        self.assertEqual(sub_map['wastewater-treatment-and-discharge'], '20')
        self.assertEqual(sec_map['shipping'], '')
        self.assertEqual(sec_map['wastewater-treatment-and-discharge'], '')


# Pre-existing baseline emissionSource enums resolved from
# gs://unresolved_mcf/scripts/statvar/stat_vars.mcf in production runs.
# New subsector StatVars and legacy composite rollups are NOT listed here so
# that the test verifies resolution through statvar_remap.csv.
_EXISTING_BASELINE_EMISSION_SOURCES = (
    # Sectors
    'Agriculture',
    'FluorinatedGases',
    'ForestryAndLandUse',
    'FossilFuelOperations',
    'FuelCombustionInBuildings',
    'Manufacturing',
    'MineralExtraction',
    'Power',
    'Transportation',
    'WasteManagement',
    # Pre-existing subsectors
    'AluminumProduction',
    'BauxiteMining',
    'BiologicalTreatmentOfSolidWasteAndBiogenic',
    'CementProduction',
    'ChemicalPetrochemicalIndustry',
    'ClimateTrace_OtherAgriculturalSoilEmissions',
    'ClimateTrace_OtherEnergyUse',
    'ClimateTrace_OtherFossilFuelOperations',
    'ClimateTrace_OtherManufacturing',
    'ClimateTrace_OtherOnsiteFuelUsage',
    'ClimateTrace_OtherTransportation',
    'CoalMining',
    'CopperMining',
    'CroplandFire',
    'ElectricityGeneration',
    'EntericFermentation',
    'ForestClearing',
    'ForestLandDegredation',
    'ForestLandFire',
    'FuelCombustionForDomesticAviation',
    'FuelCombustionForInternationalAviation',
    'FuelCombustionForRailways',
    'FuelCombustionForResidentialCommercialOnsiteHeating',
    'FuelCombustionForRoadVehicles',
    'IronMining',
    'ManureManagement',
    'NetForestEmissions',
    'NetGrasslandEmissions',
    'NetWetlandEmissions',
    'OilAndGasProduction',
    'OilAndGasRefining',
    'OpenBurningWaste',
    'PulpAndPaperManufacturing',
    'RiceCultivation',
    'RockQuarry',
    'SandQuarry',
    'ShrublandFire',
    'SolidFuelTransformation',
    'SolidWasteDisposal',
    'SteelManufacturing',
    'SyntheticFertilizerApplication',
    'WetlandFire',
)

_EMITTED_THINGS = (
    'CarbonDioxide',
    'CarbonDioxideEquivalent20YearGlobalWarmingPotential',
    'CarbonDioxideEquivalent100YearGlobalWarmingPotential',
    'Methane',
    'NitrousOxide',
)


def _write_offline_existing_statvars_mcf(path: str) -> None:
    """Writes a minimal offline MCF of existing ClimateTrace StatVars."""
    blocks = []
    for gas in _EMITTED_THINGS:
        for src in _EXISTING_BASELINE_EMISSION_SOURCES:
            dcid = f'Annual_Emissions_{gas}_{src}'
            blocks.append(f'Node: dcid:{dcid}\n'
                          'typeOf: dcs:StatisticalVariable\n'
                          'populationType: dcs:Emissions\n'
                          'measuredProperty: dcs:amount\n'
                          'measurementQualifier: dcs:Annual\n'
                          'statType: dcs:measuredValue\n'
                          f'emissionSource: dcs:{src}\n'
                          f'emittedThing: dcs:{gas}\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(blocks))


class StatVarProcessorFixturesTest(unittest.TestCase):
    """Hermetic regression tests running stat_var_processor on paired fixtures."""

    def _run_processor(self,
                       tmp_dir: str,
                       input_csv: str,
                       pv_map_file: str,
                       output_name: str,
                       existing_mcf: str = '',
                       remap_csv: str = '') -> tuple[str, str, str]:
        test_config = os.path.join(tmp_dir, f'{output_name}_metadata.csv')
        with open(os.path.join(SCRIPT_DIR, 'common_metadata.csv'),
                  'r',
                  encoding='utf-8') as f_in, open(test_config,
                                                  'w',
                                                  encoding='utf-8') as f_out:
            f_out.write(f_in.read())
            f_out.write('generate_statvar_mcf,False\n')
            f_out.write('generate_schema_mcf,False\n')
            f_out.write('reconcile_nodes,False\n')
            f_out.write('recon_lookup_api,False\n')

        output_prefix = os.path.join(tmp_dir, output_name)
        counters_csv = os.path.join(tmp_dir, f'{output_name}_counters.csv')
        cmd = [
            sys.executable,
            SV_PROCESSOR,
            f'--input_data={input_csv}',
            f'--pv_map={os.path.join(SCRIPT_DIR, pv_map_file)}',
            f'--config_file={test_config}',
            f'--output_path={output_prefix}',
            f'--output_counters={counters_csv}',
            f'--existing_statvar_mcf={existing_mcf}',
        ]
        if remap_csv:
            cmd.append(
                f'--statvar_dcid_remap_csv={os.path.join(SCRIPT_DIR, remap_csv)}'
            )
        subprocess.run(cmd, check=True, cwd=tmp_dir, capture_output=True)
        return f'{output_prefix}.csv', f'{output_prefix}.tmcf', counters_csv

    def _assert_fixture_matches(self,
                                prefix: str,
                                pv_map_file: str,
                                use_existing_mcf: bool = False,
                                remap_csv: str = '') -> None:
        input_csv = os.path.join(TEST_DATA_DIR, f'{prefix}_input.csv')
        expected_csv = os.path.join(TEST_DATA_DIR, f'{prefix}_output.csv')
        expected_tmcf = os.path.join(TEST_DATA_DIR, f'{prefix}_output.tmcf')
        self.assertTrue(os.path.exists(input_csv))
        self.assertTrue(os.path.exists(expected_csv))
        self.assertTrue(os.path.exists(expected_tmcf))

        with tempfile.TemporaryDirectory() as tmp_dir:
            existing_mcf = ''
            if use_existing_mcf:
                existing_mcf = os.path.join(tmp_dir, 'existing_statvars.mcf')
                _write_offline_existing_statvars_mcf(existing_mcf)

            actual_csv, actual_tmcf, _ = self._run_processor(
                tmp_dir=tmp_dir,
                input_csv=input_csv,
                pv_map_file=pv_map_file,
                output_name=f'{prefix}_output',
                existing_mcf=existing_mcf,
                remap_csv=remap_csv,
            )
            with open(expected_csv, 'r', encoding='utf-8') as f_exp, open(
                    actual_csv, 'r', encoding='utf-8') as f_act:
                self.assertEqual(f_exp.read().splitlines(),
                                 f_act.read().splitlines())
            with open(expected_tmcf, 'r', encoding='utf-8') as f_exp, open(
                    actual_tmcf, 'r', encoding='utf-8') as f_act:
                self.assertEqual(sorted(f_exp.read().splitlines()),
                                 sorted(f_act.read().splitlines()))

    def test_sectors_fixture(self):
        self._assert_fixture_matches(
            prefix='sectors',
            pv_map_file='climate_pvmap_sectors.csv',
            use_existing_mcf=True,
        )
        df = pd.read_csv(os.path.join(TEST_DATA_DIR, 'sectors_output.csv'),
                         dtype=str)
        self.assertFalse(
            df['variableMeasured'].str.contains('FluorinatedGases').any(),
            'fluorinated-gases must be ignored in climate_pvmap_sectors.csv '
            'to avoid duplicate observations with climate_pvmap_subsectors.csv',
        )

    def test_subsectors_fixture(self):
        self._assert_fixture_matches(
            prefix='subsectors',
            pv_map_file='climate_pvmap_subsectors.csv',
            use_existing_mcf=True,
            remap_csv='statvar_remap.csv',
        )
        df = pd.read_csv(os.path.join(TEST_DATA_DIR, 'subsectors_output.csv'),
                         dtype=str,
                         keep_default_na=False)
        fg = df[df['variableMeasured'].str.contains('FluorinatedGases')]
        self.assertGreater(len(fg), 0)
        self.assertTrue((fg['measurementMethod'] == '').all())

    def test_greenhousegas_fixture(self):
        self._assert_fixture_matches(
            prefix='greenhousegas',
            pv_map_file='climate_pvmap_greenhousegas.csv',
            use_existing_mcf=False,
        )

    def test_dynamic_future_year_extraction(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            existing_mcf = os.path.join(tmp_dir, 'existing_statvars.mcf')
            _write_offline_existing_statvars_mcf(existing_mcf)

            raw_input = os.path.join(tmp_dir, 'future_raw.csv')
            with open(raw_input, 'w', encoding='utf-8') as f:
                f.write('iso3_country,sector,subsector,start_time,end_time,'
                        'gas,emissions_quantity\n')
                f.write('USA,transportation,road-transportation,'
                        '2031-01-01 00:00:00,2031-12-31 00:00:00,co2,12345.5\n')

            ghg_input = os.path.join(tmp_dir, 'future_ghg.csv')
            with open(ghg_input, 'w', encoding='utf-8') as f:
                f.write('iso3_country,sector,subsector,start_time,end_time,'
                        'gas,emissions_quantity\n')
                f.write('USA,,,2031-01-01 00:00:00,,co2e_100yr,98765.25\n')

            for name, inp, pvmap, remap in (
                ('sectors', raw_input, 'climate_pvmap_sectors.csv', ''),
                ('subsectors', raw_input, 'climate_pvmap_subsectors.csv',
                 'statvar_remap.csv'),
                ('greenhousegas', ghg_input, 'climate_pvmap_greenhousegas.csv',
                 ''),
            ):
                out_csv, _, counters_csv = self._run_processor(
                    tmp_dir=tmp_dir,
                    input_csv=inp,
                    pv_map_file=pvmap,
                    output_name=f'future_{name}',
                    existing_mcf=existing_mcf,
                    remap_csv=remap,
                )
                df = pd.read_csv(out_csv, dtype=str)
                self.assertEqual(len(df), 1, msg=f'Pass {name} failed')
                self.assertEqual(df.loc[0, 'observationDate'], '2031')
                with open(counters_csv, 'r', encoding='utf-8') as f_cnt:
                    counters = dict(csv.reader(f_cnt))
                self.assertEqual(
                    counters.get(
                        '1:process_input_warning-unresolved-value-ref'),
                    '2',
                    msg=f'Unexpected unresolved-value-ref warnings in {name}',
                )

    def test_pvmap_uniform_column_widths(self):
        for pvmap in (
                'climate_pvmap_sectors.csv',
                'climate_pvmap_subsectors.csv',
                'climate_pvmap_greenhousegas.csv',
        ):
            with open(os.path.join(SCRIPT_DIR, pvmap),
                      'r',
                      encoding='utf-8',
                      newline='') as f:
                widths = {len(row) for row in csv.reader(f) if row}
            self.assertEqual(len(widths),
                             1,
                             msg=f'Inconsistent column widths in {pvmap}: '
                             f'{sorted(widths)}')


if __name__ == '__main__':
    unittest.main()

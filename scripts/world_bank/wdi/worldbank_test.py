# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from worldbank import *
import numpy as np
import unittest

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = "test_data/output"
if not os.path.exists(
        os.path.join(_MODULE_DIR, OUTPUT_PATH, "output_generated.csv")):
    os.makedirs(os.path.join(_MODULE_DIR, OUTPUT_PATH), exist_ok=True)
GENERATED_CSV_PATH = os.path.join(_MODULE_DIR, OUTPUT_PATH,
                                  "output_generated.csv")
GENERATED_TMCF_PATH = os.path.join(_MODULE_DIR, OUTPUT_PATH,
                                   "output_generated.tmcf")
EXPECTED_CSV_PATH = os.path.join(
    _MODULE_DIR, 'test_data/expected_ouput/expected_output.csv')
EXPECTED_TMCF_PATH = os.path.join(
    _MODULE_DIR, 'test_data/expected_ouput/expected_output.tmcf')

INPUT_ROWS = np.array([
    [
        0, 'Afghanistan', 'AFG', "Intentional homicides (per 100,000 people)",
        'VC.IHR.PSRC.P5', 2009, 4.0715263102304, 'AFG',
        'WorldBank/VC_IHR_PSRC_P5'
    ],
    [
        26621, 'North Macedonia', 'MKD',
        'Renewable energy consumption (% of total final energy consumption)',
        'EG.FEC.RNEW.ZS', 2001, 15.2, 'MKD', 'WorldBank/EG_FEC_RNEW_ZS'
    ],
    [
        1632, 'Uzbekistan', 'UZB', "Life expectancy at birth, male (years)",
        'SP.DYN.LE00.MA.IN', 1973, 58.621, 'UZB', 'WorldBank/SP_DYN_LE00_MA_IN'
    ],
])

EXPECTED_OUTPUT_CSV = pd.read_csv(EXPECTED_CSV_PATH)
worldbank_dataframe = pd.DataFrame(INPUT_ROWS,
                                   columns=[
                                       '', 'CountryName', 'CountryCode',
                                       'IndicatorName', 'IndicatorCode', 'Year',
                                       'Value', 'ISO3166Alpha3',
                                       'StatisticalVariable'
                                   ])


class WDITest(unittest.TestCase):

    def test_WDI(self):
        indicator_codes = pd.read_csv(os.path.join(
            _MODULE_DIR, "schema_csvs", "WorldBankIndicators_prod.csv"),
                                      dtype=str)
        outputGenerated = process(indicator_codes,
                                  worldbank_dataframe,
                                  saveOutput=False)
        outputGenerated.to_csv(GENERATED_CSV_PATH)
        GENERATED_OUTPUT_CSV = pd.read_csv(GENERATED_CSV_PATH)
        self.assertTrue(GENERATED_OUTPUT_CSV.equals(EXPECTED_OUTPUT_CSV))

        with open(EXPECTED_TMCF_PATH, encoding="UTF-8") as expected_tmcf_file:
            expected_tmcf_data = expected_tmcf_file.read()
        with open(GENERATED_TMCF_PATH, encoding="UTF-8") as generated_tmcf_file:
            generated_tmcf_data = generated_tmcf_file.read()
        self.assertEqual(expected_tmcf_data.strip(),
                         generated_tmcf_data.strip())

    def test_merge_historical_data(self):
        fresh_df = pd.DataFrame({
            'StatisticalVariable': ['dcid:SV1', 'dcid:SV2'],
            'ISO3166Alpha3': ['dcid:country/USA', 'dcid:country/IRQ'],
            'Year': ['2020', '1991'],
            'observationPeriod': ['P1Y', 'P1Y'],
            'Value0': [10.5, 200.0],
            'unit': ['USD', 'USD'],
            'measurementMethod': ['', ''],
            'scalingFactor': ['100', '']
        })
        historical_csv = io.StringIO(
            "StatisticalVariable,ISO3166Alpha3,Year,observationPeriod,Value0,"
            "unit,measurementMethod,scalingFactor\n"
            "dcid:SV2,dcid:country/IRQ,1991,P1Y,150.0,USD,,\n"
            "dcid:SV2,dcid:country/IRQ,1992,P1Y,175.0,USD,,100\n")
        merged = merge_historical_data(fresh_df, historical_csv)
        self.assertEqual(len(merged), 3)
        # Verify fresh observation (200.0) takes precedence over historical (150.0)
        irq_1991 = merged[(merged['ISO3166Alpha3'] == 'dcid:country/IRQ') &
                          (merged['Year'] == '1991')]
        self.assertEqual(float(irq_1991['Value0'].iloc[0]), 200.0)
        # Verify scalingFactor remains string '100' without float decimal formatting
        csv_out = merged.to_csv(float_format='%.10f', index=False)
        self.assertIn(',100\n', csv_out)
        self.assertNotIn('100.0000000000', csv_out)


if __name__ == '__main__':
    unittest.main()

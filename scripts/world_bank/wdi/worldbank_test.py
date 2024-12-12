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
    os.mkdir(os.path.join(_MODULE_DIR, OUTPUT_PATH))
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


if __name__ == '__main__':
    unittest.main()

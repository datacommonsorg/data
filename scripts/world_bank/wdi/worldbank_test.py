from worldbank import *
import numpy as np
import unittest

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_OUTPUT_PATH = os.path.join(_MODULE_DIR,
                                     "test_data/output/output_generated.csv")
EXPECTED_OUTPUT_PATH = os.path.join(
    _MODULE_DIR, 'test_data/expected_ouput/expected_output.csv')

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

EXPECTED_OUTPUT = pd.read_csv(EXPECTED_OUTPUT_PATH)
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
        outputGenerated.to_csv(GENERATED_OUTPUT_PATH)
        GENERATED_OUTPUT = pd.read_csv(GENERATED_OUTPUT_PATH)
        self.assertTrue(GENERATED_OUTPUT.equals(EXPECTED_OUTPUT))


if __name__ == '__main__':
    unittest.main()

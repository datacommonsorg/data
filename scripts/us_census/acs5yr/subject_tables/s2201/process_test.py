"""Tests for py. for S2201"""

import csv
import json
import os
import tempfile
import sys
import unittest

_CODEDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(1, _CODEDIR)

# Import the functions from 'process.py' in the correct directory
from .process import convert_column_to_stat_var, create_csv, create_tmcf, write_csv

_FEATURES = os.path.join(_CODEDIR, 'features.json')
_STAT_VAR_LIST = os.path.join(_CODEDIR, 'stat_vars.csv')
_TEST_DATA = os.path.join(_CODEDIR, 'testdata')
_EXPECTED_TMCF = os.path.join(_CODEDIR, 'output.tmcf')


class ProcessTest(unittest.TestCase):

    def test_convert_column_to_stat_var(self):
        f = open(_FEATURES)
        features = json.load(f)
        f.close()
        self.assertEqual(
            convert_column_to_stat_var(
                'Estimate!!Households receiving food stamps/SNAP!!Households',
                features), 'Count_Household_WithFoodStampsInThePast12Months')
        self.assertEqual(
            convert_column_to_stat_var(
                'Margin of Error!!' +
                'Households receiving food stamps/SNAP!!Households!!' +
                'No children under 18 years!!Other family:!!' +
                'Male householder, no spouse present', features),
            'MarginOfError_Count_Household_WithFoodStampsInThePast12Months_' +
            'WithoutChildrenUnder18_SingleFatherFamilyHousehold')
        self.assertEqual(
            convert_column_to_stat_var(
                'Estimate!!Households receiving food stamps/SNAP!!Households!!'
                + 'HOUSEHOLD INCOME IN THE PAST 12 MONTHS' +
                '(IN 2019 INFLATION-ADJUSTED DOLLARS)!!Median income (dollars)',
                features),
            'Median_Income_Household_WithFoodStampsInThePast12Months')

    def test_create_csv(self):
        f = open(_FEATURES)
        features = json.load(f)
        f.close()
        f = open(_STAT_VAR_LIST)
        stat_vars = f.read().splitlines()
        f.close()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_csv.csv')
            create_csv(test_csv, stat_vars)

            year = 2023
            filename = f'ACSST5Y{year}.S2201-Data.csv'

            with open(os.path.join(_TEST_DATA, filename)) as f:
                reader = csv.DictReader(f)
                write_csv(filename, reader, test_csv, features, stat_vars)

            with open(test_csv) as f_result:
                test_result = f_result.read()
                with open(os.path.join(_TEST_DATA, 'expected.csv')) as f_test:
                    expected = f_test.read()
                    self.assertEqual(test_result, expected)

            os.remove(test_csv)

    def test_write_csv_pre_2015_and_sentinel_filtering(self):
        with open(_FEATURES) as f:
            features = json.load(f)
        with open(_STAT_VAR_LIST) as f:
            stat_vars = f.read().splitlines()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_pre_2015.csv')
            create_csv(test_csv, stat_vars)

            # In pre-2015 S2201 tables, _002E reported a percentage without
            # "Percent" in the header; only _001, _016, and _017 are kept.
            rows = [
                {
                    'GEO_ID':
                        'Geography',
                    'S2201_C02_001E':
                        'Households receiving food stamps!!Estimate!!Households',
                    'S2201_C02_001M':
                        'Households receiving food stamps!!Margin of Error!!'
                        'Households',
                    'S2201_C02_002E':
                        'Households receiving food stamps!!Estimate!!'
                        'Households!!With one or more people in the household '
                        '60 years and over',
                    'S2201_C02_016E':
                        'Households receiving food stamps!!Estimate!!'
                        'Households!!POVERTY STATUS IN THE PAST 12 MONTHS!!'
                        'Below poverty level',
                    'S2201_C02_016M':
                        'Households receiving food stamps!!Margin of Error!!'
                        'Households!!POVERTY STATUS IN THE PAST 12 MONTHS!!'
                        'Below poverty level',
                },
                {
                    'GEO_ID': '0400000US53',
                    'S2201_C02_001E': '2,600,000',
                    'S2201_C02_001M': '-222222222',
                    'S2201_C02_002E': '35',
                    'S2201_C02_016E': '310,000',
                    'S2201_C02_016M': '-555555555',
                },
            ]
            fieldnames = list(rows[0].keys())
            csv_buffer = ['"' + '","'.join(fieldnames) + '"']
            for r in rows:
                csv_buffer.append('"' + '","'.join(r[k] for k in fieldnames) +
                                  '"')

            reader = csv.DictReader(csv_buffer)
            write_csv('ACSST5Y2014.S2201-Data.csv', reader, test_csv, features,
                      stat_vars)

            with open(test_csv) as f_result:
                result_rows = list(csv.DictReader(f_result))

            self.assertEqual(len(result_rows), 1)
            self.assertEqual(result_rows[0]['observationDate'], '2014')
            self.assertEqual(result_rows[0]['observationAbout'],
                             'dcid:geoId/53')
            self.assertEqual(
                result_rows[0]
                ['Count_Household_WithFoodStampsInThePast12Months'], '2600000')
            self.assertEqual(
                result_rows[0]
                ['MarginOfError_Count_Household_WithFoodStampsInThePast12Months'],
                '')
            # _002E (unlabeled pre-2015 percentage) must be filtered out
            self.assertEqual(
                result_rows[0]
                ['Count_Household_WithFoodStampsInThePast12Months_WithPeopleOver60'],
                '')
            self.assertEqual(
                result_rows[0]
                ['Count_Household_WithFoodStampsInThePast12Months_BelowPovertyLevelInThePast12Months'],
                '310000')
            self.assertEqual(
                result_rows[0]
                ['MarginOfError_Count_Household_WithFoodStampsInThePast12Months_BelowPovertyLevelInThePast12Months'],
                '')

    def test_write_csv_data_with_overlays(self):
        with open(_FEATURES) as f:
            features = json.load(f)
        with open(_STAT_VAR_LIST) as f:
            stat_vars = f.read().splitlines()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_csv = os.path.join(tmp_dir, 'test_overlays.csv')
            create_csv(test_csv, stat_vars)

            rows = [
                {
                    'GEO_ID': 'id',
                    'S2201_C03_001E':
                        'Estimate!!Households receiving food stamps/SNAP!!'
                        'Households',
                    'S2201_C04_001E':
                        'Estimate!!Percent!!Households receiving food '
                        'stamps/SNAP!!Households',
                    'S2201_C05_001E':
                        'Estimate!!Households not receiving food stamps/SNAP!!'
                        'Households',
                    'S2201_C03_034E':
                        'Estimate!!Households receiving food stamps/SNAP!!'
                        'Households!!HOUSEHOLD INCOME IN THE PAST 12 MONTHS '
                        '(IN 2024 INFLATION-ADJUSTED DOLLARS)!!'
                        'Median income (dollars)',
                },
                {
                    'GEO_ID': '9500000US2740860',
                    'S2201_C03_001E': '26.0',
                    'S2201_C04_001E': '24.0',
                    'S2201_C05_001E': '757.0',
                    'S2201_C03_034E': '250,000+',
                },
            ]
            fieldnames = list(rows[0].keys())
            csv_buffer = ['"' + '","'.join(fieldnames) + '"']
            for r in rows:
                csv_buffer.append('"' + '","'.join(r[k] for k in fieldnames) +
                                  '"')

            reader = csv.DictReader(csv_buffer)
            write_csv('ACSST5Y2024.S2201_data_with_overlays.csv', reader,
                      test_csv, features, stat_vars)

            with open(test_csv) as f_result:
                result_rows = list(csv.DictReader(f_result))

            self.assertEqual(len(result_rows), 1)
            self.assertEqual(result_rows[0]['observationDate'], '2024')
            self.assertEqual(result_rows[0]['observationAbout'],
                             'dcid:geoId/sch2740860')
            # .0-suffixed integer counts should be stripped, while .0-suffixed
            # whole-number percentage in S2201_C04_001E is ignored.
            self.assertEqual(
                result_rows[0]
                ['Count_Household_WithFoodStampsInThePast12Months'], '26')
            self.assertEqual(
                result_rows[0]
                ['Count_Household_WithoutFoodStampsInThePast12Months'], '757')
            self.assertEqual(
                result_rows[0]
                ['Median_Income_Household_WithFoodStampsInThePast12Months'],
                '250000')

    def test_create_tmcf(self):
        f = open(_FEATURES)
        features = json.load(f)
        f.close()
        f = open(_STAT_VAR_LIST)
        stat_vars = f.read().splitlines()
        f.close()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_tmcf = os.path.join(tmp_dir, 'test_tmcf.tmcf')
            create_tmcf(test_tmcf, features, stat_vars)
            with open(test_tmcf) as f_result:
                test_result = f_result.read()
                with open(_EXPECTED_TMCF) as f_test:
                    expected = f_test.read()
                    self.assertEqual(test_result, expected)
            os.remove(test_tmcf)


def main(argv):
    a = ProcessTest(unittest.TestCase)


if __name__ == '__main__':
    unittest.main()

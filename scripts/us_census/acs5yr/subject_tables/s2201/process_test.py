"""Tests for process.py. for S2201"""

import csv
import json
import os
import tempfile
import sys
import unittest

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from common import process

_FEATURES = 'features.json'
_STAT_VAR_LIST = 'stat_vars.csv'
_TEST_DATA = 'testdata'
_EXPECTED_TMCF = 'output.tmcf'


class ProcessTest(unittest.TestCase):

    def test_convert_column_to_stat_var(self):
        f = open(_FEATURES)
        features = json.load(f)
        f.close()
        self.assertEqual(
            process.convert_column_to_stat_var(
                'Estimate!!Households receiving food stamps/SNAP!!Households',
                features), 'Count_Household_WithFoodStampsInThePast12Months')
        self.assertEqual(
            process.convert_column_to_stat_var(
                'Margin of Error!!' +
                'Households receiving food stamps/SNAP!!Households!!' +
                'No children under 18 years!!Other family:!!' +
                'Male householder, no spouse present', features),
            'MarginOfError_Count_Household_WithFoodStampsInThePast12Months_' +
            'WithoutChildrenUnder18_SingleFatherFamilyHousehold')
        self.assertEqual(
            process.convert_column_to_stat_var(
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
            process.create_csv(test_csv, stat_vars)
            for year in range(2010, 2020):
                filename = f'testACSST5Y{year}.csv'
                with open(os.path.join(_TEST_DATA, filename)) as f:
                    reader = csv.DictReader(f)
                    process.write_csv(filename, reader, test_csv, features,
                                      stat_vars)
            with open(test_csv) as f_result:
                test_result = f_result.read()
                with open(os.path.join(_TEST_DATA, 'expected.csv')) as f_test:
                    expected = f_test.read()
                    self.assertEqual(test_result, expected)
            os.remove(test_csv)

    def test_create_tmcf(self):
        f = open(_FEATURES)
        features = json.load(f)
        f.close()
        f = open(_STAT_VAR_LIST)
        stat_vars = f.read().splitlines()
        f.close()
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_tmcf = os.path.join(tmp_dir, 'test_tmcf.tmcf')
            process.create_tmcf(test_tmcf, features, stat_vars)
            with open(test_tmcf) as f_result:
                test_result = f_result.read()
                with open(_EXPECTED_TMCF) as f_test:
                    expected = f_test.read()
                    self.assertEqual(test_result, expected)
            os.remove(test_tmcf)


if __name__ == '__main__':
    unittest.main()

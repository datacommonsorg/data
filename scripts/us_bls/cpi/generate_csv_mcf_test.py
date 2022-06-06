# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import sys
import os

import pandas as pd

# Allows the following module imports to work when running as a script
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))
from us_bls.cpi import generate_csv_mcf


class TestGenerateCSVMCF(unittest.TestCase):

    def test_parse_series_id(self):
        info = generate_csv_mcf.parse_series_id('CUSR0000SA0')
        self.assertEqual('CU', info.survey_abbreviation)
        self.assertEqual('S', info.seasonal_code)
        self.assertEqual('R', info.periodicity_code)
        self.assertEqual('0000', info.area_code)
        self.assertEqual('SA0', info.item_code)
        self.assertEqual('CUSR0000SA0', info.series_id)

    def test_valid_series_id(self):
        info = generate_csv_mcf.parse_series_id('CUUR0000SEFV02')
        self.assertTrue(info.is_us())
        self.assertTrue(info.is_monthly())
        self.assertFalse(info.is_semiannually())
        self.assertEqual('BLSUnchained', info.get_mmethod())
        self.assertEqual('BLSItem/SEFV02', info.get_pop_type())
        self.assertEqual('UrbanConsumer', info.get_consumer())
        self.assertEqual('BLSSeasonallyUnadjusted', info.get_mqual())
        self.assertEqual(('ConsumerPriceIndex_BLSItem/SEFV02_UrbanConsumer'
                          '_BLSSeasonallyUnadjusted'), info.get_statvar())
        self.assertEqual(('IndexPointBasePeriodDecember2009Equals100',
                          'The reference base is December 2009 equals 100.'),
                         info.get_unit(
                             pd.DataFrame({
                                 'series_id': ('CUUR0000SEFV02',),
                                 'base_period': ('DECEMBER 2009=100',)
                             })))

    def test_invalid_series_id(self):
        self.assertRaises(ValueError, generate_csv_mcf.parse_series_id,
                          'CCUR0000SEFV02')
        self.assertRaises(ValueError, generate_csv_mcf.parse_series_id,
                          'CWUR0000SEFV0212312')
        self.assertRaises(ValueError, generate_csv_mcf.parse_series_id,
                          'CWUT0000SEFV02')
        self.assertRaises(ValueError, generate_csv_mcf.parse_series_id,
                          'CWGR0000SEFV02')
        self.assertRaises(
            ValueError,
            generate_csv_mcf.parse_series_id('CWUR0000SEFV02').get_unit,
            pd.DataFrame({
                'series_id': ('CUUR0000SEFV02',),
                'base_period': ('DECEMBER 2009=100',)
            }))
        self.assertRaises(
            ValueError,
            generate_csv_mcf.parse_series_id('CWUR0000SEFV02').get_unit,
            pd.DataFrame({
                'series_id': ('CWUR0000SEFV02',),
                'base_period': ('DECEMBER2009=100',)
            }))

    def test_filter_series(self):
        self.assertCountEqual({'CWUR0000SEFV02'},
                              generate_csv_mcf.filter_series(
                                  pd.DataFrame({
                                      'series_id':
                                          ('CWUR0001SEFV02', 'CWUS0000SEFV02',
                                           'CWUR0000SEFV02')
                                  })))

    def test_generate_statvar(self):
        self.assertEqual(
            ('Node: dcid:ConsumerPriceIndex_BLSItem/SEFV02_'
             'UrbanWageEarnerAndClericalWorker_BLSSeasonallyUnadjusted\n'
             'typeOf: dcs:StatisticalVariable\n'
             'populationType: dcs:ConsumerGoodsAndServices\n'
             'consumedThing: dcs:BLSItem/SEFV02\n'
             'measurementQualifier: dcs:BLSSeasonallyUnadjusted\n'
             'measuredProperty: dcs:consumerPriceIndex\n'
             'statType: dcs:measuredValue\n'
             'consumer: dcs:UrbanWageEarnerAndClericalWorker\n'
             'description: "The series ID is CWUR0000SEFV02."\n'),
            generate_csv_mcf._generate_statvar('CWUR0000SEFV02'))


if __name__ == '__main__':
    unittest.main()

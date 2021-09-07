# Copyright 2021 Google LLC
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
"""Tests for util.statvar_dcid_generator."""

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import unittest
from util import statvar_dcid_generator


class TestStatVarDcidGenerator(unittest.TestCase):

    def test_ignore_props(self):
        stat_var_dict = {
            'typeOf': 'StatisticalVariable',
            'statType': 'medianValue',
            'measuredProperty': 'income',
            'populationType': 'Person',
            'age': '[15 - Years]',
            'incomeStatus': 'WithIncome'
        }
        ignore_props = ['age', 'incomeStatus']
        dcid = statvar_dcid_generator.get_stat_var_dcid(
            stat_var_dict, ignore_props=ignore_props)
        expected_dcid = ('Median_Income_Person')
        self.assertEqual(dcid, expected_dcid)

    def test_namespace_removal(self):
        stat_var_dict = {
            'typeOf': 'StatisticalVariable',
            'statType': 'dcs:medianValue',
            'measuredProperty': 'dcid:age',
            'populationType': 'Person',
            'nativity': 'USC_Native',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict)
        expected_dcid = 'Median_Age_Person_USCNative'
        self.assertEqual(dcid, expected_dcid)

    def test_quantity_name_generation(self):
        stat_var_dict1 = {
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'gender': 'Female',
            'age': '[20 Years]'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict1)
        expected_dcid = 'Count_Person_20Years_Female'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'gender': 'Female',
            'age': '[Years 20]'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict2)
        expected_dcid = 'Count_Person_20Years_Female'
        self.assertEqual(dcid, expected_dcid)

    def test_quantity_range_name_generation(self):
        stat_var_dict1 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'HousingUnit',
            'numberOfRooms': '[9 - Rooms]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict1)
        expected_dcid = 'Count_HousingUnit_9OrMoreRooms'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'HousingUnit',
            'numberOfRooms': '[Rooms 9 -]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict2)
        expected_dcid = 'Count_HousingUnit_9OrMoreRooms'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict3 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householdWorkerSize': '[- 3 Worker]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict3)
        expected_dcid = 'Count_Household_3OrLessWorker'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict4 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householdWorkerSize': '[Worker - 3]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict4)
        expected_dcid = 'Count_Household_3OrLessWorker'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict5 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'income': '[10000 14999 USDollar]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict5)
        expected_dcid = 'Count_Person_10000To14999USDollar'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict6 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'income': '[USDollar 10000 14999]',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict6)
        expected_dcid = 'Count_Person_10000To14999USDollar'
        self.assertEqual(dcid, expected_dcid)

    def test_sorted_constraints(self):
        stat_var_dict = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'age': '[25 - Years]',
            'educationalAttainment': 'BachelorsDegreeOrHigher',
            'race': 'AsianAlone',
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict)
        expected_dcid = ('Count_Person_25OrMoreYears_BachelorsDegreeOrHigher'
                         '_AsianAlone')
        self.assertEqual(dcid, expected_dcid)

    def test_stat_type(self):
        stat_var_dict1 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:marginOfError',
            'populationType': 'dcid:Person',
            'ratioToPovertyLine': '[1 1.49 RatioToPovertyLine]',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict1)
        expected_dcid = ('MarginOfError_Count_Person_NoHealthInsurance_'
                         '1To1.49RatioToPovertyLine')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'measuredProperty': 'concentration',
            'statType': 'meanValue',
            'populationType': 'Atmosphere',
            'pollutant': 'PM2.5'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict2)
        expected_dcid = 'Mean_Concentration_Atmosphere_PM2.5'
        self.assertEqual(dcid, expected_dcid)

    def test_measured_property(self):
        stat_var_dict = {
            'statType': 'meanValue',
            'measuredProperty': 'wagesDaily',
            'populationType': 'Person',
            'placeOfResidenceClassification': 'Urban'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict)
        expected_dcid = 'Mean_WagesDaily_Person_Urban'
        self.assertEqual(dcid, expected_dcid)

    def test_measurement_qualifier(self):
        stat_var_dict = {
            'statType': 'measuredValue',
            'measuredProperty': 'precipitationRate',
            'populationType': 'Place',
            'memberOf': 'Climate',
            'measurementQualifier': 'Daily'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict)
        expected_dcid = 'Daily_PrecipitationRate_Place'
        self.assertEqual(dcid, expected_dcid)

    def test_measurement_denominator(self):
        stat_var_dict = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'age': '[25 64 Years]',
            'educationalAttainment': 'TertiaryEducation',
            'measurementDenominator': 'Count_Person_25To64Years'
        }
        dcid = statvar_dcid_generator.get_stat_var_dcid(stat_var_dict)
        expected_dcid = ('Count_Person_25To64Years_TertiaryEducation'
                         '_AsAFractionOf_Count_Person_25To64Years')
        self.assertEqual(dcid, expected_dcid)


if __name__ == '__main__':
    unittest.main()

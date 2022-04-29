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
import re
from util import statvar_dcid_generator


class TestStatVarDcidGenerator(unittest.TestCase):

    def test_ignore_props(self):
        statvar_dict = {
            'typeOf': 'StatisticalVariable',
            'statType': 'medianValue',
            'measuredProperty': 'income',
            'populationType': 'Person',
            'age': '[15 - Years]',
            'incomeStatus': 'WithIncome'
        }
        ignore_props = ['age', 'incomeStatus']
        dcid = statvar_dcid_generator.get_statvar_dcid(
            statvar_dict, ignore_props=ignore_props)
        expected_dcid = 'Median_Income_Person'
        self.assertEqual(dcid, expected_dcid)

    def test_double_underscore(self):
        statvar_dict1 = {
            'typeOf': 'StatisticalVariable',
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'CriminalIncidents',
            'locationOfCrime': 'Park__Playground',
            'crimeType': 'UCR_OtherCrimeAgainstProperty'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = ('Count_CriminalIncidents_OtherCrimeAgainstProperty_'
                         'LocationOfCrimeParkOrPlayground')
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'populationType': 'dcs:CriminalIncidents',
            'measurementQualifier': 'dcs:Offense',
            'victimType': 'dcs:UCR_OtherVictimType&UCR_UnknownVictimType',
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'dcs:count',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = ('Offense_Count_CriminalIncidents_VictimType'
                         'OtherVictimTypeOrUnknownVictimType')
        self.assertEqual(dcid, expected_dcid)

        statvar_dict1 = {
            'typeOf': 'StatisticalVariable',
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'CriminalIncidents',
            'locationOfCrime': 'Park__Playground&NightClub',
            'crimeType': 'UCR_OtherCrimeAgainstProperty'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = ('Count_CriminalIncidents_OtherCrimeAgainstProperty_'
                         'LocationOfCrimeParkOrPlaygroundOrNightClub')
        self.assertEqual(dcid, expected_dcid)

    def test_namespace_removal(self):
        statvar_dict = {
            'typeOf': 'StatisticalVariable',
            'statType': 'dcs:medianValue',
            'measuredProperty': 'dcid:age',
            'populationType': 'Person',
            'nativity': 'USC_Native',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict)
        expected_dcid = 'Median_Age_Person_Native'
        self.assertEqual(dcid, expected_dcid)

    def test_measurement_constraint_removal(self):
        statvar_dict1 = {
            'typeOf': 'StatisticalVariable',
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Student',
            'race': 'USC_AsianAlone',
            'schoolGradeLevel': 'NCESThirdGrade',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = 'Count_Student_AsianAlone_ThirdGrade'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'typeOf': 'StatisticalVariable',
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'dcid:count',
            'populationType': 'Person',
            'citizenship': 'dcid:USCitizenBornInTheUnitedStates',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = 'Count_Person_USCitizenBornInTheUnitedStates'
        self.assertEqual(dcid, expected_dcid)

    def test_quantity_name_generation(self):
        statvar_dict1 = {
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'gender': 'Female',
            'age': '[20 Years]'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = 'Count_Person_20Years_Female'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'statType': 'dcs:measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'gender': 'Female',
            'age': '[Years 20]'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = 'Count_Person_20Years_Female'
        self.assertEqual(dcid, expected_dcid)

    def test_quantity_range_name_generation(self):
        statvar_dict1 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'HousingUnit',
            'numberOfRooms': '[9 - Rooms]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = 'Count_HousingUnit_WithTotal9OrMoreRooms'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'HousingUnit',
            'numberOfRooms': '[Rooms 9 -]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = 'Count_HousingUnit_WithTotal9OrMoreRooms'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict3 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householdWorkerSize': '[- 3 Worker]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict3)
        expected_dcid = 'Count_Household_With3OrLessWorker'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict4 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householdWorkerSize': '[Worker - 3]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict4)
        expected_dcid = 'Count_Household_With3OrLessWorker'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict5 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'income': '[10000 14999 USDollar]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict5)
        expected_dcid = 'Count_Person_IncomeOf10000To14999USDollar'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict6 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'income': '[USDollar 10000 14999]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict6)
        expected_dcid = 'Count_Person_IncomeOf10000To14999USDollar'
        self.assertEqual(dcid, expected_dcid)

    def test_sorted_constraints(self):
        statvar_dict = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'age': '[25 - Years]',
            'educationalAttainment': 'BachelorsDegreeOrHigher',
            'race': 'AsianAlone',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict)
        expected_dcid = ('Count_Person_25OrMoreYears_'
                         'EducationalAttainmentBachelorsDegreeOrHigher_'
                         'AsianAlone')
        self.assertEqual(dcid, expected_dcid)

    def test_stat_type(self):
        statvar_dict1 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:marginOfError',
            'populationType': 'dcid:Person',
            'ratioToPovertyLine': '[1 1.49 RatioToPovertyLine]',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = ('MarginOfError_Count_Person_NoHealthInsurance_'
                         '1To1.49RatioToPovertyLine')
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'measuredProperty': 'concentration',
            'statType': 'meanValue',
            'populationType': 'Atmosphere',
            'pollutant': 'PM2.5'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = 'Mean_Concentration_Atmosphere_PM2.5'
        self.assertEqual(dcid, expected_dcid)

    def test_measured_property(self):
        statvar_dict = {
            'statType': 'meanValue',
            'measuredProperty': 'wagesDaily',
            'populationType': 'Person',
            'placeOfResidenceClassification': 'Urban'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict)
        expected_dcid = 'Mean_WagesDaily_Person_Urban'
        self.assertEqual(dcid, expected_dcid)

    def test_measurement_qualifier(self):
        statvar_dict = {
            'statType': 'measuredValue',
            'measuredProperty': 'precipitationRate',
            'populationType': 'Place',
            'memberOf': 'Climate',
            'measurementQualifier': 'Daily'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict)
        expected_dcid = 'Daily_PrecipitationRate_Place'
        self.assertEqual(dcid, expected_dcid)

    def test_measurement_denominator(self):
        statvar_dict1 = {
            'statType': 'measuredValue',
            'measuredProperty': 'amount',
            'populationType': 'Consumption',
            'consumedThing': 'Electricity',
            'measurementDenominator': 'PerCapita'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict1)
        expected_dcid = 'Amount_Consumption_Electricity_PerCapita'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict2 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'memberOf': 'Demographics',
            'measurementDenominator': 'area'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict2)
        expected_dcid = 'Count_Person_PerArea'
        self.assertEqual(dcid, expected_dcid)

        statvar_dict3 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'age': '[25 64 Years]',
            'educationalAttainment': 'TertiaryEducation',
            'measurementDenominator': 'dcid:Count_Person_25To64Years'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(statvar_dict3)
        expected_dcid = ('Count_Person_25To64Years_'
                         'EducationalAttainmentTertiaryEducation_'
                         'AsAFractionOf_Count_Person_25To64Years')
        self.assertEqual(dcid, expected_dcid)

    def test_legacy_mapping(self):
        stat_var_dict = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'disabilityStatus': 'dcid:WithDisability',
            'armedForcesStatus': 'dcid:Civilian',
            'institutionalization': 'dcid:USC_NonInstitutionalized'
        }
        ignore_props = ['armedForcesStatus', 'institutionalization']
        dcid = statvar_dcid_generator.get_statvar_dcid(
            stat_var_dict, ignore_props=ignore_props)
        expected_dcid = 'Count_Person_NoHealthInsurance_WithDisability'
        self.assertEqual(dcid, expected_dcid)

    def test_prepend_append_replace(self):
        stat_var_dict1 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householderAge': '[25 44 Years]',
            'householderRace': 'AmericanIndianOrAlaskaNativeAlone',
            'income': '[60000 74999 USDollar]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict1)
        expected_dcid = ('Count_Household_HouseholderAge25To44Years_'
                         'HouseholderRaceAmericanIndianOrAlaskaNativeAlone_'
                         'IncomeOf60000To74999USDollar')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Person',
            'languageSpokenAtHome': 'OnlyEnglish',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict2)
        expected_dcid = 'Count_Person_OnlyEnglishSpokenAtHome'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict3 = {
            'statType': 'measuredValue',
            'measuredProperty': 'count',
            'populationType': 'Household',
            'householderRelatedChildrenUnder18Years': '[1 2 Child]',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict3)
        expected_dcid = 'Count_Household_Householder1To2RelatedChildren'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict4 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'age': '[16 64 Years]',
            'workStatus': 'dcid:WorkedInThePast12Months',
            'usualHoursWorked': '[35 - Hour]',
            'workPeriod': '[48 49 Week]',
            'typeOf': 'dcs:StatisticalVariable'
        }
        ignore_props = ['age', 'workStatus']
        dcid = statvar_dcid_generator.get_statvar_dcid(
            stat_var_dict4, ignore_props=ignore_props)
        expected_dcid = ('Count_Person_WorkPerWeek35OrMoreHour_'
                         'WorkPerYear48To49Week')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict5 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'nativity': 'dcid:USC_ForeignBorn',
            'dateOfEntry': '[2000 2009 Date]',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict5)
        expected_dcid = 'Count_Person_DateOfEntry2000To2009_ForeignBorn'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict6 = {
            'statType': 'dcid:measuredValue',
            'measuredProperty': 'dcid:count',
            'populationType': 'dcid:HousingUnit',
            'occupancyStatus': 'dcid:OccupiedHousingUnit',
            'dateMovedIn': '[2017 - Date]',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict6)
        expected_dcid = ('Count_HousingUnit_MovedInDate2017OrLater_'
                         'OccupiedHousingUnit')
        self.assertEqual(dcid, expected_dcid)

    def test_naics_name_generation(self):
        stat_var_dict1 = {
            'typeOf': 'dcs:StatisticalVariable',
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredValue',
            'naics': 'dcid:NAICS/54-56',
            'age': '[16 - Years]',
            'healthInsurance': 'dcs:NoHealthInsurance'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict1)
        expected_dcid = (
            'Count_Person_16OrMoreYears_NoHealthInsurance_'
            'NAICSProfessionalScientificTechnicalServices'
            'ManagementOfCompaniesEnterprises'
            'AdministrativeSupportWasteManagementRemediationServices')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'populationType': 'dcs:Person',
            'measuredProperty': 'dcs:count',
            'statType': 'dcs:measuredValue',
            'naics': 'NAICS/11_21',
            'race': 'TwoOrMoreRaces'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict2)
        expected_dcid = ('Count_Person_NAICSAgricultureForestryFishingHunting'
                         'MiningQuarryingOilGasExtraction_TwoOrMoreRaces')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict3 = {
            'populationType': 'USCEstablishment',
            'measuredProperty': 'wagesAnnual',
            'statType': 'dcs:measuredValue',
            'naics': 'NAICS/44-45_51',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict3)
        expected_dcid = 'WagesAnnual_Establishment_NAICSRetailTradeInformation'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict4 = {
            'populationType': 'BLSEstablishment',
            'measuredProperty': 'count',
            'statType': 'dcs:measuredValue',
            'naics': 'NAICS/23',
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict4)
        expected_dcid = 'Count_Establishment_NAICSConstruction'
        self.assertEqual(dcid, expected_dcid)

    def test_soc_name_generation(self):
        stat_var_dict1 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'occupation': 'dcid:SOCv2018/highLevelAggregation-5',
            'armedForcesStatus': 'dcid:Civilian',
            'institutionalization': 'dcid:USC_NonInstitutionalized',
            'age': '[16 - Years]',
            'workerStatus': 'dcid:Worker',
            'typeOf': 'dcs:StatisticalVariable'
        }
        ignore_props = ['armedForcesStatus', 'institutionalization']
        dcid = statvar_dcid_generator.get_statvar_dcid(
            stat_var_dict1, ignore_props=ignore_props)
        expected_dcid = ('Count_Person_16OrMoreYears_NoHealthInsurance_'
                         'SOCProductionTransportationMaterialMoving'
                         'Occupation_Worker')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'occupation': 'dcid:SOCv2018/highLevelAggregation-3',
            'workerStatus': 'dcid:Worker',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict2)
        expected_dcid = 'Count_Person_SOCSalesOfficeOccupation_Worker'
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict3 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'occupation': 'dcid:SOCv2018/highLevelAggregation-1',
            'age': '[16 - Years]',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict3)
        expected_dcid = ('Count_Person_16OrMoreYears_'
                         'SOCManagementBusinessScienceArtsOccupation')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict4 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'occupation': 'dcid:SOCv2018/highLevelAggregation-4',
            'workerStatus': 'dcid:Worker',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict4)
        expected_dcid = ('Count_Person_NoHealthInsurance_'
                         'SOCNaturalResourcesConstructionMaintenance'
                         'Occupation_Worker')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict5 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'healthInsurance': 'dcid:NoHealthInsurance',
            'occupation': 'dcid:SOCv2018/intermediateAggregation-5',
            'armedForcesStatus': 'dcid:Civilian',
            'institutionalization': 'dcid:USC_NonInstitutionalized',
            'age': '[16 - Years]',
            'workerStatus': 'dcid:Worker',
            'typeOf': 'dcs:StatisticalVariable'
        }
        ignore_props = ['armedForcesStatus', 'institutionalization']
        dcid = statvar_dcid_generator.get_statvar_dcid(
            stat_var_dict5, ignore_props=ignore_props)
        expected_dcid = ('Count_Person_16OrMoreYears_NoHealthInsurance_'
                         'SOCServiceOccupation_Worker')
        self.assertEqual(dcid, expected_dcid)

        # Test for code not in SOC_MAP
        stat_var_dict6 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Person',
            'occupation': 'SOCv2018/highLevelAggregation-99',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict6)
        expected_dcid = ('Count_Person_'
                         'SOCv2018/highLevelAggregation-99Occupation')
        self.assertEqual(dcid, expected_dcid)

    def test_boolean_naming(self):
        stat_var_dict1 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:CriminalActivities',
            'isHateCrime': 'True',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict1)
        expected_dcid = ('Count_CriminalActivities_IsHateCrime')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict2 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:CriminalActivities',
            'isHateCrime': 'False',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict2)
        expected_dcid = ('Count_CriminalActivities_NotHateCrime')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict3 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Household',
            'hasComputer': 'True',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict3)
        expected_dcid = ('Count_Household_HasComputer')
        self.assertEqual(dcid, expected_dcid)

        stat_var_dict4 = {
            'measuredProperty': 'dcid:count',
            'statType': 'dcid:measuredValue',
            'populationType': 'dcid:Household',
            'hasComputer': 'False',
            'typeOf': 'dcs:StatisticalVariable'
        }
        dcid = statvar_dcid_generator.get_statvar_dcid(stat_var_dict4)
        expected_dcid = ('Count_Household_NoComputer')
        self.assertEqual(dcid, expected_dcid)

    def test_soc_map(self):
        soc_values = statvar_dcid_generator.SOC_MAP.values()
        alphanumeric_regex = re.compile(r'[A-Za-z0-9]+')
        # Check if all values contain only alphanumeric characters
        for val in soc_values:
            self.assertTrue(alphanumeric_regex.fullmatch(val) is not None)


if __name__ == '__main__':
    unittest.main()

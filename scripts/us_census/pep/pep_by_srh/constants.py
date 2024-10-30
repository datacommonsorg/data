# Copyright 2022 Google LLC
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
"""
Constant value used in processing SRH are defined here.

This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.

While preprocessing files column names are changed to SV names as used in
DC import
"""

DOWNLOAD_DIR = '/input_files/'
PROCESS_AS_IS_DIR = '/process_files/as_is/'
PROCESS_AGG_DIR = '/process_files/agg/'
OUTPUT_DIR = '/output_files/'

# pylint: disable=line-too-long
STAT_VAR_COL_MAPPING = {
    'NH-W-M':
        'Count_Person_Male_WhiteAloneNotHispanicOrLatino',
    'NHWA_MALE':
        'Count_Person_Male_WhiteAloneNotHispanicOrLatino',
    'NH-W-F':
        'Count_Person_Female_WhiteAloneNotHispanicOrLatino',
    'NHWA_FEMALE':
        'Count_Person_Female_WhiteAloneNotHispanicOrLatino',
    'NH-B-M':
        'Count_Person_Male_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NHBA_MALE':
        'Count_Person_Male_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NH-B-F':
        'Count_Person_Female_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NHBA_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NH-AI-M':
        'Count_Person_Male_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-AI-F':
        'Count_Person_Female_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-AIAN-M':
        'Count_Person_Male_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NHIA_MALE':
        'Count_Person_Male_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-AIAN-F':
        'Count_Person_Female_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NHIA_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-API-M':
        'Count_Person_Male_NotHispanicOrLatino_AsianOrPacificIslander',
    'NH-API-F':
        'Count_Person_Female_NotHispanicOrLatino_AsianOrPacificIslander',
    'H-W-M':
        'Count_Person_Male_HispanicOrLatino_WhiteAlone',
    'HWA_MALE':
        'Count_Person_Male_HispanicOrLatino_WhiteAlone',
    'H-W-F':
        'Count_Person_Female_HispanicOrLatino_WhiteAlone',
    'HWA_FEMALE':
        'Count_Person_Female_HispanicOrLatino_WhiteAlone',
    'H-B-M':
        'Count_Person_Male_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'HBA_MALE':
        'Count_Person_Male_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'H-B-F':
        'Count_Person_Female_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'HBA_FEMALE':
        'Count_Person_Female_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'H-AI-M':
        'Count_Person_Male_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-AI-F':
        'Count_Person_Female_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-AIAN-M':
        'Count_Person_Male_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'HIA_MALE':
        'Count_Person_Male_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-AIAN-F':
        'Count_Person_Female_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'HIA_FEMALE':
        'Count_Person_Female_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-API-M':
        'Count_Person_Male_HispanicOrLatino_AsianOrPacificIslander',
    'H-API-F':
        'Count_Person_Female_HispanicOrLatino_AsianOrPacificIslander',
    'NHAA_MALE':
        'Count_Person_Male_NotHispanicOrLatino_AsianAlone',
    'NHAA_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_AsianAlone',
    'NHNA_MALE':
        'Count_Person_Male_NotHispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'NHNA_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'NHTOM_MALE':
        'Count_Person_Male_NotHispanicOrLatino_TwoOrMoreRaces',
    'NHTOM_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_TwoOrMoreRaces',
    'NHWAC_MALE':
        'Count_Person_Male_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHWAC_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHBAC_MALE':
        'Count_Person_Male_NotHispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHBAC_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHIAC_MALE':
        'Count_Person_Male_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHIAC_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHAAC_MALE':
        'Count_Person_Male_NotHispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHAAC_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHNAC_MALE':
        'Count_Person_Male_NotHispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHNAC_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HAA_MALE':
        'Count_Person_Male_HispanicOrLatino_AsianAlone',
    'HAA_FEMALE':
        'Count_Person_Female_HispanicOrLatino_AsianAlone',
    'HNA_MALE':
        'Count_Person_Male_HispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'HNA_FEMALE':
        'Count_Person_Female_HispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'HTOM_MALE':
        'Count_Person_Male_HispanicOrLatino_TwoOrMoreRaces',
    'HTOM_FEMALE':
        'Count_Person_Female_HispanicOrLatino_TwoOrMoreRaces',
    'HWAC_MALE':
        'Count_Person_Male_HispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HWAC_FEMALE':
        'Count_Person_Female_HispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HBAC_MALE':
        'Count_Person_Male_HispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HBAC_FEMALE':
        'Count_Person_Female_HispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HIAC_MALE':
        'Count_Person_Male_HispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HIAC_FEMALE':
        'Count_Person_Female_HispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HAAC_MALE':
        'Count_Person_Male_HispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HAAC_FEMALE':
        'Count_Person_Female_HispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HNAC_MALE':
        'Count_Person_Male_HispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HNAC_FEMALE':
        'Count_Person_Female_HispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NH_MALE':
        'Count_Person_Male_NotHispanicOrLatino',
    'NH_FEMALE':
        'Count_Person_Female_NotHispanicOrLatino',
    'H_MALE':
        'Count_Person_Male_HispanicOrLatino',
    'H_FEMALE':
        'Count_Person_Female_HispanicOrLatino',
    'H':
        'Count_Person_HispanicOrLatino',
    'H-AI':
        'Count_Person_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-AIAN':
        'Count_Person_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'H-API':
        'Count_Person_HispanicOrLatino_AsianOrPacificIslander',
    'H-B':
        'Count_Person_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'H-W':
        'Count_Person_HispanicOrLatino_WhiteAlone',
    'HAA':
        'Count_Person_HispanicOrLatino_AsianAlone',
    'HAAC':
        'Count_Person_HispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HBA':
        'Count_Person_HispanicOrLatino_BlackOrAfricanAmericanAlone',
    'HBAC':
        'Count_Person_HispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HIA':
        'Count_Person_HispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'HIAC':
        'Count_Person_HispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HNA':
        'Count_Person_HispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'HNAC':
        'Count_Person_HispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'HTOM':
        'Count_Person_HispanicOrLatino_TwoOrMoreRaces',
    'HWA':
        'Count_Person_HispanicOrLatino_WhiteAlone',
    'HWAC':
        'Count_Person_HispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NH':
        'Count_Person_NotHispanicOrLatino',
    'NH-AI':
        'Count_Person_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-AIAN':
        'Count_Person_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NH-API':
        'Count_Person_NotHispanicOrLatino_AsianOrPacificIslander',
    'NH-B':
        'Count_Person_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NH-W':
        'Count_Person_WhiteAloneNotHispanicOrLatino',
    'NHAA':
        'Count_Person_NotHispanicOrLatino_AsianAlone',
    'NHAAC':
        'Count_Person_NotHispanicOrLatino_AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHBA':
        'Count_Person_NotHispanicOrLatino_BlackOrAfricanAmericanAlone',
    'NHBAC':
        'Count_Person_NotHispanicOrLatino_BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHIA':
        'Count_Person_NotHispanicOrLatino_AmericanIndianOrAlaskaNativeAlone',
    'NHIAC':
        'Count_Person_NotHispanicOrLatino_AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHNA':
        'Count_Person_NotHispanicOrLatino_NativeHawaiianOrOtherPacificIslanderAlone',
    'NHNAC':
        'Count_Person_NotHispanicOrLatino_NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'NHTOM':
        'Count_Person_NotHispanicOrLatino_TwoOrMoreRaces',
    'NHWA':
        'Count_Person_WhiteAloneNotHispanicOrLatino',
    'NHWAC':
        'Count_Person_NotHispanicOrLatino_WhiteAloneOrInCombinationWithOneOrMoreOtherRaces'
}

WORKING_DIRECTORIES = [
    '/process_files/agg/1990_2000/county/',
    '/process_files/agg/2000_2010/county/',
    '/process_files/agg/2010_2020/county/',
    '/process_files/agg/2020_2023/county/',
    '/process_files/as_is/1990_2000/county/',
    '/process_files/as_is/2000_2010/county/',
    '/process_files/as_is/2010_2020/county/',
    '/process_files/as_is/2020_2023/county/',
    '/process_files/as_is/1980_1990/state/',
    '/process_files/as_is/1990_2000/state/',
    '/process_files/as_is/2000_2010/state/',
    '/process_files/as_is/2010_2020/state/',
    '/process_files/as_is/2020_2023/state/',
    '/process_files/agg/1980_1990/state/',
    '/process_files/agg/1990_2000/state/',
    '/process_files/agg/2000_2010/state/',
    '/process_files/agg/2010_2020/state/',
    '/process_files/agg/2020_2023/state/',
    '/process_files/as_is/1980_1990/national/',
    '/process_files/as_is/1990_2000/national/',
    '/process_files/as_is/2000_2010/national/',
    '/process_files/as_is/2010_2020/national/',
    '/process_files/as_is/2020_2023/national/',
    '/process_files/agg/1980_1990/national/',
    '/process_files/agg/1990_2000/national/',
    '/process_files/agg/2000_2010/national/',
    '/process_files/agg/2020_2023/national/',
    '/process_files/agg/2010_2020/national/',
    '/output_files/',
    '/input_files/',
    '/input_files/1990_2000/county/',
    '/input_files/2000_2010/county/',
    '/input_files/2010_2020/county/',
    '/input_files/2020_2023/county/',
    '/input_files/1980_1990/state/',
    '/input_files/1990_2000/state/'
]

MCF_SRH = '''Node: dcid:{node_name}
typeOf: dcs:StatisticalVariable
statType: dcs:measuredValue
measuredProperty: dcs:count
populationType: dcs:Person
gender: dcs:{gender}
race: dcs:{race}

'''

MCF_SH = '''Node: dcid:{node_name}
typeOf: dcs:StatisticalVariable
statType: dcs:measuredValue
measuredProperty: dcs:count
populationType: dcs:Person
gender: dcs:{gender}

'''

MCF_RH = '''Node: dcid:{node_name}
typeOf: dcs:StatisticalVariable
statType: dcs:measuredValue
measuredProperty: dcs:count
populationType: dcs:Person
race: dcs:{race}

'''

POPULATION_ESTIMATE_BY_SRH = '''Node: E:population_estimate_by_srh->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:population_estimate_by_srh->SV
observationAbout: C:population_estimate_by_srh->LOCATION
observationDate: C:population_estimate_by_srh->YEAR
observationPeriod: "P1Y"
measurementMethod: C:population_estimate_by_srh->MEASUREMENT_METHOD
value: C:population_estimate_by_srh->OBSERVATION
'''

POPULATION_ESTIMATE_BY_SRH_AGG = '''Node: E:population_estimate_by_srh_agg->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:population_estimate_by_srh_agg->SV
observationAbout: C:population_estimate_by_srh_agg->LOCATION
observationDate: C:population_estimate_by_srh_agg->YEAR
observationPeriod: "P1Y"
measurementMethod: C:population_estimate_by_srh_agg->MEASUREMENT_METHOD
value: C:population_estimate_by_srh_agg->OBSERVATION
'''

RACE = {
    'WhiteAloneOrInCombinationWithOneOrMoreOtherRaces',
    'AmericanIndianOrAlaskaNativeAlone', 'WhiteAlone',
    'AsianAloneOrInCombinationWithOneOrMoreOtherRaces',
    'BlackOrAfricanAmericanAloneOrInCombinationWithOneOrMoreOtherRaces',
    'AsianOrPacificIslander', 'TwoOrMoreRaces', 'AsianAlone',
    'NativeHawaiianAndOtherPacificIslanderAloneOrInCombinationWithOneOrMoreOtherRaces',
    'AmericanIndianAndAlaskaNativeAloneOrInCombinationWithOneOrMoreOtherRaces',
    'BlackOrAfricanAmericanAlone', 'NativeHawaiianOrOtherPacificIslanderAlone'
}

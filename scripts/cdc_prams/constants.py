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
Constant value used in processing US Tract are defined here.
This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.
While preprocessing files column names are changed to SV names as used in
DC import
"""

_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                "typeOf: dcs:StatisticalVariable\n"
                "populationType: dcs:LivePregnancyEvent\n"
                "measurementDenominator: dcs:Count_BirthEvent_LiveBirth\n"
                "{xtra_pvs}\n")


_TMCF_TEMPLATE = (
    "Node: E:US_Prams->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:US_Prams->SV\n"
    "measurementMethod: C:US_Prams->"
    "Measurement_Method\n"
    "observationAbout: C:US_Prams->Geo\n"
    "observationDate: C:US_Prams->Year\n"
    "scalingFactor: 100\n"
    "value: C:US_Prams->Observation\n")

DEFAULT_SV_PROP = {
    "typeOf": "dcs:StatisticalVariable",
    # "populationType": "dcs:LivePregnancyEvent",
    # "statType": "dcs:confidenceIntervalLowerLimit",
    # "measuredProperty": "dcs:count",
    "measurementDenominator": "dcs:Count_BirthEvent_LiveBirth"
}

_PV_PROP = {
    "OneMonth":"1Month",
    "SampleSize_Count_LivePregnancyEvent_":"sampleSize",
    "Percent_LivePregnancyEvent_":"measuredValue",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"confidenceIntervalLowerLimit",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":"confidenceIntervalUpperLimit"
}

_PROP = {
    "OneMonth":"1Month",
    "MoreThan4TimesAWeek":"",
    "InLast2Years":"",
    "3MonthsBeforePregnancy":"",
    "Last3MonthsOfPregnancy":"",
    "Postpartum":"",
    "Hookah":"HookahUsage",
    "Obese":"Obesity",
    "healthInsuranceStatus1MonthBeforePregnancyprivateinsurance":"WithPrivateHealthInsurance",
    "healthInsuranceStatus1MonthBeforePregnancyMedicaid":"Medicaid",
    "healthInsuranceStatus1MonthBeforePregnancyNoInsurance":"NoHealthInsurance",
    "healthInsuranceStatusForPrenatalCareprivateinsurance":"WithPrivateHealthInsurance",
    "healthInsuranceStatusForPrenatalCareMedicaid":"Medicaid",
    "healthInsuranceStatusForPrenatalCareNoInsurance":"NoHealthInsurance",
    "DuringPregnancy":"",
    "12MonthsBeforePregnancy":"",
    "InFirstTrimester":"",
    "ECigaretteSmoking":"Smoking",
    "CigaretteSmoking" :"Smoking",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_TIME = {
    "OneMonth":"1Month",
    "MultivitaminUse":"",
    "PrenatalCareIn":"",
    "FluShot":"",
    "MaternalCheckup":"",
    "TeethCleanedByDentistOrHygienist":"",
    "HealthCareVisit":"",
    "ECigaretteSmoking":"",
    "CigaretteSmoking":"",
    "HookahInLast2Years":"Last2YearsBeforePregnancy",
    "HeavyDrinking":"",
    "CDC_SelfReportedDepression":"",
    "healthInsuranceStatus1MonthBeforePregnancyprivateinsurance":"1MonthBeforePregnancy",
    "healthInsuranceStatus1MonthBeforePregnancyMedicaid":"1MonthBeforePregnancy",
    "healthInsuranceStatus1MonthBeforePregnancyNoInsurance":"1MonthBeforePregnancy",
    "healthInsuranceStatusPostpartumprivateinsurance":"Postpartum",
    "healthInsuranceStatusPostpartumMedicaid":"Postpartum",
    "healthInsuranceStatusPostpartumNoInsurance":"Postpartum",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "SampleSize_Count_LivePregnancyvent_MoreThan4TimesAWeek":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_INSURANCE = {
    "OneMonth":"1Month",
    "healthInsuranceStatusPostpartumprivateinsurance":"WithPrivateHealthInsurance",
    "healthInsuranceStatusPostpartumMedicaid":"Medicaid",
    "healthInsuranceStatusPostpartumNoInsurance":"NoHealthInsurance",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_PROP4 = {
    "ECigaretteSmoking3MonthsBeforePregnancy":"ECigarettes",
    "ECigaretteSmokingLast3MonthsOfPregnancy":"ECigarettes",
    "CigaretteSmoking3MonthsBeforePregnancy" :"Cigarettes",
    "CigaretteSmokingLast3MonthsOfPregnancy":"Cigarettes",
    "CigaretteSmokingPostpartum":"Cigarettes",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_YEAR = {
    '2016_sampleSize':'2016',
    '2017_sampleSize':'2017',
    '2018_sampleSize':'2018',
    '2019_sampleSize':'2019', 
    '2020_sampleSize':'2020', 
    '2016_CI_PERCENT':'2016',
    '2016_CI_LOWER':'2016', 
    '2016_CI_UPPER':'2016', 
    '2017_CI_PERCENT':'2017', 
    '2017_CI_LOWER':'2017',
    '2017_CI_UPPER':'2017', 
    '2018_CI_PERCENT':'2018', 
    '2018_CI_LOWER':'2018', 
    '2018_CI_UPPER':'2018',
    '2019_CI_PERCENT':'2019', 
    '2019_CI_LOWER':'2019', 
    '2019_CI_UPPER':'2019', 
    '2020_CI_PERCENT':'2020',
    '2020_CI_LOWER':'2020', 
    '2020_CI_UPPER':'2020', 
    'Overall_2020_CI_PERCENT':'2020',
    'Overall_2020_CI_LOWER':'2020',
    'Overall_2020_CI_UPPER':'2020'
}
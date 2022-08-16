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
    "SampleSize_Count_LivePregnancyEvent_":"sampleSize",
    "Percent_LivePregnancyEvent_":"measuredValue",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"confidenceIntervalLowerLimit",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":"confidenceIntervalUpperLimit"
}

_PROP = {
    "MoreThan4TimesAWeek":"",
    "InLast2Years":"",
    "3MonthsBeforePregnancy":"",
    "Last3MonthsOfPregnancy":"",
    "Postpartum":"",
    "privateinsurance":"",
    "Medicaid":"",
    "DuringPregnancy":"",
    "12MonthsBeforePregnancy":"",
    "InFirstTrimester":"",
    "NoInsurance":"",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_TIME = {
    "MultivitaminUse":"",
    "PrenatalCare":"",
    "FluShot":"",
    "MaternalCheckup":"",
    "TeethCleanedByDentistOrHygienist":"",
    "HealthCareVisit":"",
    "CigaretteSmoking":"",
    "ECigaretteSmoking":"",
    "HookahIn":"",
    "HeavyDrinking":"",
    "CDC_SelfReportedDepression":"",
    "healthInsuranceStatusOneMonthBeforePregnancyprivateinsurance":"OneMonthBeforePregnancy",
    "healthInsuranceStatusOneMonthBeforePregnancyMedicaid":"OneMonthBeforePregnancy",
    "healthInsuranceStatusOneMonthBeforePregnancyNoInsurance":"OneMonthBeforePregnancy",
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
    "privateinsurance":"",
    "Medicaid":"",
    "NoInsurance":"",
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}

_PROP4 = {
    "SampleSize_Count_LivePregnancyEvent_":"",
    "Percent_LivePregnancyEvent_":"",
    "ConfidenceIntervalLowerLimit_Count_LivePregnancyEvent_":"",
    "ConfidenceIntervalUpperLimit_Count_LivePregnancyEvent_":""
}
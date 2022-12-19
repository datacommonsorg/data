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
Constant value used in processing US Prams are defined here.
This module also consists of mapping between various forms of column names
found in downloaded files and its corresponding SV name.
While preprocessing files column names are changed to SV names as used in
DC import
"""
_MCF_TEMPLATE = ("Node: dcid:{dcid}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:LiveBirthPregnancyEvent\n"
                 "{xtra_pvs}\n")

_TMCF_TEMPLATE = ("Node: E:US_Prams->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: C:US_Prams->SV\n"
                  "observationAbout: C:US_Prams->Geo\n"
                  "observationDate: C:US_Prams->Year\n"
                  "scalingFactor: C:US_Prams->ScalingFactor\n"
                  "value: C:US_Prams->Observation\n")

DEFAULT_SV_PROP = {
    "typeOf": "dcs:StatisticalVariable",
    "populationType": "dcs:LiveBirthPregnancyEvent",
}

# The dictionaries are used to replace the present value according
# to the schema.
PV_PROP = {
    "OneMonth": "1Month",
    "SampleSize_Count": "sampleSize",
    "Percent": "measuredValue",
    "ConfidenceIntervalLowerLimit_Count": "confidenceIntervalLowerLimit",
    "ConfidenceIntervalUpperLimit_Count": "confidenceIntervalUpperLimit"
}

# The change is based on the property values according to the schema by
#  removing the unwanted keywords from the property value.
_PROP = {
    "OneMonth":
        "1Month",
    "MoreThan4TimesAWeek":
        "",
    "InLast2Years":
        "",
    "3MonthsBeforePregnancy":
        "",
    "Last3MonthsOfPregnancy":
        "",
    "Postpartum":
        "",
    "Hookah":
        "HookahUsage",
    "Obese":
        "Obesity",
    "healthInsuranceStatus1MonthBeforePregnancyPrivateInsurance":
        "WithPrivateHealthInsurance",
    "healthInsuranceStatus1MonthBeforePregnancyMedicaid":
        "WithMedicaid",
    "healthInsuranceStatus1MonthBeforePregnancyNoInsurance":
        "NoHealthInsurance",
    "healthInsuranceStatusForPrenatalCarePrivateInsurance":
        "WithPrivateHealthInsurance",
    "healthInsuranceStatusForPrenatalCareMedicaid":
        "WithMedicaid",
    "healthInsuranceStatusForPrenatalCareNoInsurance":
        "NoHealthInsurance",
    "DuringPregnancy":
        "",
    "12MonthsBeforePregnancy":
        "",
    "12MonthsBeforeDelivery":
        "",
    "InFirstTrimester":
        "",
    "ECigaretteSmoking":
        "Smoking",
    "CigaretteSmoking":
        "Smoking",
    "SampleSize_Count":
        "",
    "Percent":
        "",
    "ConfidenceIntervalLowerLimit_Count":
        "",
    "ConfidenceIntervalUpperLimit_Count":
        "",
    "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband"+\
        "12MonthsBeforePregnancy":
        "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband",
    "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband"+\
        "DuringPregnancy":
        "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband"
}

_TIME = {
    "OneMonth":
        "1Month",
    "MultivitaminUse":
        "",
    "PrenatalCareIn":
        "",
    "FluShot12MonthsBeforeDelivery":
        "12MonthsBeforeBirth",
    "MaternalCheckup":
        "",
    "TeethCleanedByDentistOrHygienist":
        "",
    "HealthCareVisit":
        "",
    "ECigaretteSmoking":
        "",
    "CigaretteSmoking":
        "",
    "HookahInLast2Years":
        "Last2YearsBeforePregnancy",
    "HeavyDrinking":
        "",
    "CDC_SelfReportedDepression":
        "",
    "healthInsuranceStatus1MonthBeforePregnancyPrivateInsurance":
        "1MonthBeforePregnancy",
    "healthInsuranceStatus1MonthBeforePregnancyMedicaid":
        "1MonthBeforePregnancy",
    "healthInsuranceStatus1MonthBeforePregnancyNoInsurance":
        "1MonthBeforePregnancy",
    "healthInsuranceStatusPostpartumPrivateInsurance":
        "Postpartum",
    "healthInsuranceStatusPostpartumMedicaid":
        "Postpartum",
    "healthInsuranceStatusPostpartumNoInsurance":
        "Postpartum",
    "SampleSize_Count":
        "",
    "SampleSize_Count_LivePregnancyvent_MoreThan4TimesAWeek":
        "",
    "Percent":
        "",
    "ConfidenceIntervalLowerLimit_Count":
        "",
    "ConfidenceIntervalUpperLimit_Count":
        "",
    "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband"+\
        "12MonthsBeforePregnancy":
        "12MonthsBeforePregnancy",
    "IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOr"+\
        "ExHusbandDuringPregnancy":
        "DuringPregnancy",
    "AnyBreastfeedingAt8Weeks": "8WeeksAfterPregnancy"
}

_INSURANCE = {
    "OneMonth":
        "1Month",
    "healthInsuranceStatusPostpartumPrivateInsurance":
        "WithPrivateHealthInsurance",
    "healthInsuranceStatusPostpartumMedicaid":
        "WithMedicaid",
    "healthInsuranceStatusPostpartumNoInsurance":
        "NoHealthInsurance",
    "SampleSize_Count":
        "",
    "Percent":
        "",
    "ConfidenceIntervalLowerLimit_Count":
        "",
    "ConfidenceIntervalUpperLimit_Count":
        ""
}

_CIGARETTES = {
    "ECigaretteSmoking3MonthsBeforePregnancy": "ECigarettes",
    "ECigaretteSmokingLast3MonthsOfPregnancy": "ECigarettes",
    "CigaretteSmoking3MonthsBeforePregnancy": "Cigarettes",
    "CigaretteSmokingLast3MonthsOfPregnancy": "Cigarettes",
    "CigaretteSmokingPostpartum": "Cigarettes",
    "SampleSize_Count": "",
    "Percent": "",
    "ConfidenceIntervalLowerLimit_Count": "",
    "ConfidenceIntervalUpperLimit_Count": ""
}

_YEAR = {
    '2016_sampleSize': '2016',
    '2017_sampleSize': '2017',
    '2018_sampleSize': '2018',
    '2019_sampleSize': '2019',
    '2020_sampleSize': '2020',
    '2016_CI_PERCENT': '2016',
    '2016_CI': '2016',
    '2017_CI': '2017',
    '2018_CI': '2018',
    '2019_CI': '2019',
    '2020_CI': '2020',
    '2016_CI_LOWER': '2016',
    '2016_CI_UPPER': '2016',
    '2017_CI_PERCENT': '2017',
    '2017_CI_LOWER': '2017',
    '2017_CI_UPPER': '2017',
    '2018_CI_PERCENT': '2018',
    '2018_CI_LOWER': '2018',
    '2018_CI_UPPER': '2018',
    '2019_CI_PERCENT': '2019',
    '2019_CI_LOWER': '2019',
    '2019_CI_UPPER': '2019',
    '2020_CI_PERCENT': '2020',
    '2020_CI_LOWER': '2020',
    '2020_CI_UPPER': '2020'
}

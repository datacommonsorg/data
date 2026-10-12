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
Statistical Variables value used in processing US Prams are defined here.
While preprocessing files column names are changed to SV names as used in
DC import
"""


statvar_col = {
    'Nutrition__Multivitamin use ≥4 times a week during the month'+\
        ' before pregnancy':
        'MultivitaminUseMoreThan4TimesAWeek',
    'Pre-pregnancy Weight__Underweight (body mass index [BMI] <18.5 kg/m2)':
        'Underweight',
    'Pre-pregnancy Weight__Overweight (BMI 25–29.9 kg/m2)':
        'Overweight',
    'Pre-pregnancy Weight__Obese (BMI ≥30 kg/m2)':
        'Obese',
    'Substance Use_Any cigarette smoking_During the 3 months before pregnancy':
        'CigaretteSmoking3MonthsBeforePregnancy',
    'Substance Use_Any cigarette smoking_During the last 3 months of pregnancy':
        'CigaretteSmokingLast3MonthsOfPregnancy',
    'Substance Use_Any cigarette smoking_Postpartum':
        'CigaretteSmokingPostpartum',
    'Substance Use_Any e-cigarette use_During the 3 months before pregnancy':
        'ECigaretteSmoking3MonthsBeforePregnancy',
    'Substance Use_Any e-cigarette use_During the last 3 months of pregnancy':
        'ECigaretteSmokingLast3MonthsOfPregnancy',
    'Substance Use__Hookah use in the last 2 years':
        'HookahInLast2Years',
    'Substance Use__Heavy drinking (≥8 drinks a week) during the 3 months'+\
        ' before pregnancy':
        'HeavyDrinking3MonthsBeforePregnancy',
    'Intimate Partner Violence (IPV)¥__Experienced IPV during the 12 months'+\
        ' before pregnancy by a2.5 husband or partner and/or by an '+\
            'ex-husband or ex-partner':
        'IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband'+\
            '12MonthsBeforePregnancy',
    'Intimate Partner Violence (IPV)¥__Experienced IPV during the 12 months '+\
    'before pregnancy by a husband or partner and/or an ex-husband or partner':
        'IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband12'+\
            'MonthsBeforePregnancy',
    'Intimate Partner Violence (IPV)¥__Experienced IPV during pregnancy by a'+\
        ' husband or partner and/or an ex-husband or partner':
    'IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOr'+\
        'ExHusbandDuringPregnancy',
    'Intimate Partner Violence (IPV)¥__Experienced IPV during the 12 months'+\
    ' before pregnancy by a husband or partner and/or by an ex-husband'+\
        ' or ex-partner':
        'IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband12'+\
            'MonthsBeforePregnancy',
    'Intimate Partner Violence (IPV)¥__Experienced IPV during pregnancy by a'+\
        ' husband or partner and/or by an ex-husband or ex-partner':
    'IntimatePartnerViolenceByCurrentOrExPartnerOrCurrentOrExHusband'+\
        'DuringPregnancy',
    'Depression__Self-reported depression in the 3 months before pregnancy':
        'CDC_SelfReportedDepression3MonthsBeforePregnancy',
    'Depression__Self-reported depression during pregnancy':
        'CDC_SelfReportedDepressionDuringPregnancy',
    'Depression__Self-reported postpartum depressive symptoms**':
        'CDC_SelfReportedDepressionPostpartum',
    'Health Care Services__Health care visit in the 12 months before pregnancy':
        'HealthCareVisit12MonthsBeforePregnancy',
    'Health Care Services__Began prenatal care in 1st trimester':
        'PrenatalCareInFirstTrimester',
    'Health Care Services__Had a flu shot in the 12 months before delivery':
        'FluShot12MonthsBeforeDelivery',
    'Health Care Services__Had maternal postpartum checkup':
        'MaternalCheckupPostpartum',
    'Pregnancy Intention__Mistimed':
        'MistimedPregnancy',
    'Pregnancy Intention__Unwanted pregnancy':
        'UnwantedPregnancy',
    'Pregnancy Intention__Unsure whether wanted pregnancy':
        'UnsureIfWantedPregnancy',
    'Pregnancy Intention__Intended pregnancy':
        'IntendedPregnancy',
    'Postpartum†† Family Planning__Use of any postpartum contraception††‡‡':
        'AnyPostpartumFamilyPlanning',
    'Postpartum†† Family Planning_Highly effective contraceptive methods_Male'+\
        ' or female sterilization':
        'MaleOrFemaleSterilization',
    'Postpartum†† Family Planning_Highly effective contraceptive'+\
        ' methods_Long-acting reversible contraceptive method§§':
        'LongActingReversibleContraceptiveMethods',
    'Postpartum†† Family Planning__Moderately effective contraceptive'+\
        ' methods§§':
        'ModeratelyEffectiveContraceptiveMethods',
    'Postpartum†† Family Planning__Least effective contraceptive methods§§':
        'LeastEffectiveContraceptiveMethods',
    'Oral Health__Teeth cleaned during pregnancy by a dentist or '+\
        'dentalhygienist':
        'TeethCleanedByDentistOrHygienistDuringPregnancy',
    'Oral Health__Teeth cleaned during pregnancy by a dentist or'+\
        ' dental hygienist':
        'TeethCleanedByDentistOrHygienistDuringPregnancy',
    'Health Insurance Status One Month Before Pregnancy¶¶__Private insurance':
        'healthInsuranceStatusOneMonthBeforePregnancyPrivateInsurance',
    'Health Insurance Status One Month Before Pregnancy¶¶__Medicaid':
        'healthInsuranceStatusOneMonthBeforePregnancyMedicaid',
    'Health Insurance Status One Month Before Pregnancy¶¶__No insurance':
        'healthInsuranceStatusOneMonthBeforePregnancyNoInsurance',
    'Health Insurance Status for Prenatal Care¶¶__Private insurance':
        'healthInsuranceStatusForPrenatalCarePrivateInsurance',
    'Health Insurance Status for Prenatal Care¶¶__Medicaid':
        'healthInsuranceStatusForPrenatalCareMedicaid',
    'Health Insurance Status for Prenatal Care¶¶__No insurance':
        'healthInsuranceStatusForPrenatalCareNoInsurance',
    'Health Insurance Status Postpartum††¶¶__Private insurance':
        'healthInsuranceStatusPostpartumPrivateInsurance',
    'Health Insurance Status Postpartum††¶¶__Medicaid':
        'healthInsuranceStatusPostpartumMedicaid',
    'Health Insurance Status Postpartum††¶¶__No insurance':
        'healthInsuranceStatusPostpartumNoInsurance',
    'Infant Sleep Practices__Baby most often laid on back to sleep':
        'BabyMostOftenLaidOnBackToSleep',
    'Breastfeeding Practices__Ever breastfed':
        'EverBreastfed',
    'Breastfeeding Practices__Any breastfeeding at 8 weeks':
        'AnyBreastfeedingAt8Weeks'
}

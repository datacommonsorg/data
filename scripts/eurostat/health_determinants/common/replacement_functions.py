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
Replacement Functions for specific Column Values
which are common for all the Eurostat Health Inputs.
"""
import pandas as pd

_SEX = {'F': 'Female', 'M': 'Male', 'T': 'Total'}

_PHYSACT = {
    'MV_AERO': 'Aerobic',
    'MV_MSC': 'MuscleStrengthening',
    'MV_AERO_MSC': 'AerobicOrMuscleStrengthening',
    'MV_WALK_GET': 'Walking',
    'MV_CYCL_GET': 'Cycling',
    'MV_AERO_SPRT': 'AerobicSports'
}

_ISCED11 = {
    'ED0-2': 'LessThanPrimaryEducation'+\
    'OrPrimaryEducationOrLowerSecondaryEducation',
    'ED0_2': 'LessThanPrimaryEducation'+\
    'OrPrimaryEducationOrLowerSecondaryEducation',
    'ED3-4': 'UpperSecondaryEducation'+\
    'OrPostSecondaryNonTertiaryEducation',
    'ED3_4': 'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
    'ED5_6' : 'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
    'ED5-8': 'TertiaryEducation',
    'ED5_8': 'TertiaryEducation',
    'TOTAL': 'Total'
}

_QUANT_INC = {
    'TOTAL': 'Total',
    'QU1': 'IncomeOf0To20Percentile',
    'QU2': 'IncomeOf20To40Percentile',
    'QU3': 'IncomeOf40To60Percentile',
    'QU4': 'IncomeOf60To80Percentile',
    'QU5': 'IncomeOf80To100Percentile'
}

_FREQUENC = {
    'DAY': 'Daily',
    'LT1M': 'LessThanOnceAMonth',
    'MTH': 'EveryMonth',
    'NM12': 'NotInTheLast12Months',
    'NVR': 'Never',
    'NVR_NM12': 'NeverOrNotInTheLast12Months',
    'WEEK': 'EveryWeek',
    'GE1W': 'AtLeastOnceAWeek',
    'NVR_OCC': 'NeverOrOccasionallyUsage',
    'NBINGE': 'Never'
}

_DEG_URB = {
    'TOTAL': 'Total',
    'DEG1': 'Urban',
    'DEG2': 'SemiUrban',
    'DEG3': 'Rural',
}

_LEVELS = {
    'HVY': 'HeavyActivity',
    'MOD': 'ModerateActivity',
    'MOD_HVY': 'ModerateActivityOrHeavyActivity',
    'NONE_LGHT': 'NoActivityOrLightActivity'
}

_DURATION = {
    'MN0': '0Minutes',
    'MN1-149': '1To149Minutes',
    'MN150-299': '150To299Minutes',
    'MN_GE150': '150OrMoreMinutes',
    'MN_GE300': '300OrMoreMinutes',
    'Y_LT1': 'LessThan1Year',
    'Y1-5': 'From1To5Years',
    'Y5-10': 'From5To10Years',
    'Y_GE10': '10YearsOrOver'
}

_C_BIRTH = {
    'EU28_FOR': 'ForeignBornWithinEU28',
    'NEU28_FOR': 'ForeignBornOutsideEU28',
    'FOR': 'ForeignBorn',
    'NAT': 'Native'
}

_CITIZEN = {
    'EU28_FOR': 'WithinEU28AndNotACitizen',
    'NEU28_FOR': 'CitizenOutsideEU28',
    'FOR': 'NotACitizen',
    'NAT': 'Citizen'
}

_LEV_LIMIT = {
    'MOD': 'ModerateActivityLimitation',
    'SEV': 'SevereActivityLimitation',
    'SM_SEV': 'LimitedActivityLimitation',
    'NONE': 'NoActivityLimitation'
}

_BMI = {
    'BMI_LT18P5': 'Underweight',
    'BMI18P5-24': 'Normalweight',
    'BMI_GE25': 'Overweight',
    'BMI25-29': 'PreObese',
    'BMI_GE30': 'Obesity',
    'LT18P5': 'Underweight',
    '18P5-25': 'Normalweight',
    '25-30': 'Overweight',
    'GE30': 'Obesity'
}

_SMOKING = {
    'TOTAL': 'Total',
    'NSM': 'NonSmoker',
    'SM_CUR': 'TobaccoSmoking',
    'SM_DAY': 'Daily_TobaccoSmoking',
    'SM_OCC': 'Occasional_TobaccoSmoking',
    'SM_LT20D': 'LessThan20CigarettesPerDay',
    'SM_GE20D': '20OrMoreCigarettesPerDay',
    'DSM_GE20': '20OrMoreCigarettesPerDay',
    'DSM_LT20': 'LessThan20CigarettesPerDay'
}

_FREQUENC_TOBACCO = {
    'DAY_GE1HD': 'AtLeastOneHourPerDay',
    'DAY_LT1HD': 'LessThanOneHourPerDay',
    'LT1W': 'LessThanOnceAWeek',
    'GE1W': 'AtLeastOnceAWeek',
    'RAR_NVR': 'RarelyOrNever',
    'DAY': 'Daily_TobaccoSmoking',
    'FMR': 'FormerSmoker_Formerly',
    'OCC': 'Occasional_TobaccoSmoking',
    'NVR': 'TobaccoSmoking_NeverUsed'
}

_FREQUENC_ALCOHOL = {
    'DAY': 'Daily',
    'LT1M': 'LessThanOnceAMonth',
    'MTH': 'EveryMonth',
    'NM12': 'NotInTheLast12Months',
    'NVR': 'Never',
    'NVR_NM12': 'NeverOrNotInTheLast12Months',
    'WEEK': 'EveryWeek',
    'GE1W': 'AtLeastOnceAWeek',
    'NVR_OCC': 'NeverOrOccasional',
    'NBINGE': 'Never'
}

_LEV_PERC = {'STR': 'Strong', 'INT': 'Intermediate', 'POOR': 'Poor'}

_ASSIST = {
    'PROV': 'ProvidingInformalCare',
    'PROV_R': 'Relatives_ProvidingInformalCare',
    'PROV_NR': 'NonRelatives_ProvidingInformalCare',
    'NPROV': 'NotProvidingInformalCare'
}

_N_PORTION = {
    '0': '0Portion',
    '1-4': 'From1To4Portion',
    'GE5': '5PortionOrMore'
}

_COICOP = {'CP0116': 'ConsumptionOfFruits', 'CP0117': 'ConsumptionOfVegetables'}

_ISCED97 = {
    'ED0-2': 'PrePrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
    'ED3_4': 'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
    'ED5_6': 'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
    'TOTAL': 'Total'
}

_FREQUENC_FRUITS_VEGETABLES = {
    'DAY': 'Daily',
    'NVR': 'Never',
    'NVR_OCC': 'NeverOrOccasionally',
    'GE1D': 'AtLeastOnceADay',
    'GE2D': 'AtLeastTwiceADay',
    '1-3W': 'From1To3TimesAWeek',
    '4-6W': 'From4To6TimesAWeek',
    '1D': 'OnceADay',
    'LT1W': 'LessThanOnceAWeek'
}


def replace_col_values(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        data_df (pd.DataFrame): data_df as the input, to change column values

    Returns:
        data_df (pd.DataFrame): Updated DataFrame
    """
    mapper = {
        'sex': _SEX,
        'physact': _PHYSACT,
        'isced11': _ISCED11,
        'quant_inc': _QUANT_INC,
        'frequenc': _FREQUENC,
        'deg_urb': _DEG_URB,
        'levels': _LEVELS,
        'duration': _DURATION,
        'c_birth': _C_BIRTH,
        'citizen': _CITIZEN,
        'lev_limit': _LEV_LIMIT,
        'bmi': _BMI,
        'smoking': _SMOKING,
        'frequenc_tobacco': _FREQUENC_TOBACCO,
        'frequenc_alcohol': _FREQUENC_ALCOHOL,
        'frequenc_fruitsvegetables': _FREQUENC_FRUITS_VEGETABLES,
        'lev_perc': _LEV_PERC,
        'assist': _ASSIST,
        'n_portion': _N_PORTION,
        'coicop': _COICOP,
        'isced97': _ISCED97
    }
    df_columns = data_df.columns.to_list()
    for column, replacements in mapper.items():
        if column in df_columns:
            data_df = data_df.replace({column: replacements})

    return data_df


def split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to divide the column
        col (str) : column names

    Returns:
        df (pd.DataFrame): modified df as output
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df
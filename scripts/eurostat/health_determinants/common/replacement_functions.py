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
which are common for all the Eurostat Health Inputs
"""
import pandas as pd


def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace({'sex': {'F': 'Female', 'M': 'Male', 'T': 'Total'}})
    return df


def _replace_physact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'physact': {
            'MV_AERO': 'Aerobic',
            'MV_MSC': 'MuscleStrengthening',
            'MV_AERO_MSC': 'AerobicOrMuscleStrengthening',
            'MV_WALK_GET': 'Walking',
            'MV_CYCL_GET': 'Cycling',
            'MV_AERO_SPRT': 'AerobicSports'
        }
    })
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({'isced11': {
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
        }})
    return df


def _replace_quant_inc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.
    Args:
        df (pd.DataFrame): df as the input, to change column values
    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'quant_inc': {
            'TOTAL': 'Total',
            'QU1': 'IncomeOf0To20Percentile',
            'QU2': 'IncomeOf20To40Percentile',
            'QU3': 'IncomeOf40To60Percentile',
            'QU4': 'IncomeOf60To80Percentile',
            'QU5': 'IncomeOf80To100Percentile'
        }
    })
    return df


def _replace_frequenc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.
    Args:
        df (pd.DataFrame): df as the input, to change column values
    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'frequenc': {
            'DAY': 'DailyUsage',
            'LT1M': 'LessThanOnceAMonth',
            'MTH': 'EveryMonth',
            'NM12': 'NotUsedInTheLast12Months',
            'NVR': 'NeverUsed',
            'NVR_NM12': 'NeverUsedOrNotUsedInTheLast12Months',
            'WEEK': 'EveryWeek',
            'GE1W': 'AtLeastOnceAWeek',
            'NVR_OCC': 'NeverUsedOrOccasionallyUsage',
            'NBINGE': 'NeverUsed'
        }
    })
    return df


def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'deg_urb': {
            'TOTAL': 'Total',
            'DEG1': 'Urban',
            'DEG2': 'SemiUrban',
            'DEG3': 'Rural',
        }
    })
    return df


def _replace_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'levels': {
            'HVY': 'HeavyActivityLevel',
            'MOD': 'ModerateActivityLevel',
            'MOD_HVY': 'ModerateActivityLevelOrHeavyActivityLevel',
            'NONE_LGHT': 'NoActivityOrLightActivityLevel'
        }
    })
    return df


def _replace_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'duration': {
            'MN0': '0Minutes',
            'MN1-149': '1To149Minutes',
            'MN150-299': '150To299Minutes',
            'MN_GE150': '150OrMoreMinutes',
            'MN_GE300': '300OrMoreMinutes'
        }
    })
    return df


def _replace_c_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'c_birth': {
            'EU28_FOR': 'ForeignBornWithinEU28',
            'NEU28_FOR': 'ForeignBornOutsideEU28',
            'FOR': 'ForeignBorn',
            'NAT': 'Native'
        }
    })
    return df


def _replace_citizen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'citizen': {
            'EU28_FOR': 'WithinEU28AndNotACitizen',
            'NEU28_FOR': 'CitizenOutsideEU28',
            'FOR': 'NotACitizen',
            'NAT': 'Citizen'
        }
    })
    return df


def _replace_lev_limit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'lev_limit': {
            'MOD': 'ModerateActivityLimitation',
            'SEV': 'SevereActivityLimitation',
            'SM_SEV': 'LimitedActivityLimitation',
            'NONE': 'NoActivityLimitation'
        }
    })
    return df


def _replace_bmi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to change column values

    Returns:
        df (pd.DataFrame): modified df as output
    """
    df = df.replace({
        'bmi': {
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
    })
    return df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF.

    Args:
        df (pd.DataFrame): df as the input, to divide the column

    Returns:
        df (pd.DataFrame): modified df as output
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df

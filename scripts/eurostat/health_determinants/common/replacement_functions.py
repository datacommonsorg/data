"""
Replacement Functions for specific Column Values
which are common for all the Eurostat Health Inputs
"""
import pandas as pd


def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
   """
    df = df.replace({'sex': {'F': 'Female', 'M': 'Male', 'T': 'Total'}})
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
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


def _replace_isced97(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Arguments: df (pd.DataFrame)

   Returns: df (pd.DataFrame)
   """
    isced97 = {
        'ED0-2':
            'PrePrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED3_4':
            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5_6':
            'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
        'TOTAL':
            'Total'
    }
    df = df.replace({'isced97': isced97})
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

   Arguments: df (pd.DataFrame)

   Returns: df (pd.DataFrame)
   """
    frequenc = {
        '1D': 'OnceADay',
        'GE1D': 'AtLeastOnceADay',
        'GE2D': 'AtleastTwiceADay',
        'LT1W': 'LessThanOnceAWeek',
        '1-3W': 'From1To3TimesAWeek',
        '4-6W': 'From4To6TimesAWeek',
        'NVR': 'Never',
        'NVR_OCC': 'NeverOrOccasionally'
    }
    df = df.replace({'frequenc': frequenc})
    return df


# def _replace_frequenc(df: pd.DataFrame) -> pd.DataFrame:
#    """
#    Replaces values of a single column into true values
#    from metadata returns the DF.
#    Args:
#        df (pd.DataFrame): df as the input, to change column values
#    Returns:
#        df (pd.DataFrame): modified df as output
#    """
#    df = df.replace({
#        'frequenc': {
#            'DAY': 'Daily',
#            'LT1M': 'LessThanOnceAMonth',
#            'MTH': 'EveryMonth',
#            'NM12': 'NotInTheLast12Months',
#            'NVR': 'Never',
#            'NVR_NM12': 'NeverOrNotInTheLast12Months',
#            'WEEK': 'EveryWeek',
#            'GE1W': 'AtLeastOnceAWeek',
#            'NVR_OCC': 'NeverOrOccasionallyUsage',
#            'NBINGE': 'Never'
#        }
#    })
#    return df


def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
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


def _replace_c_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
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

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
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

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
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

   Args: df (pd.DataFrame): df as the input, to change column values

   Returns: df (pd.DataFrame): modified df as output
   """
    df = df.replace({
        'bmi': {
            'TOTAL': 'Total',
            'BMI_LT18P5': 'Underweight',
            'BMI18P5-24': 'Normalweight',
            'BMI_GE25': 'Overweight',
            'BMI25-29': 'PreObese',
            'BMI_GE30': 'Obesity'
        }
    })
    return df


def _replace_n_portion(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Arguments: df (pd.DataFrame)

   Returns: df (pd.DataFrame)
   """
    n_portion = {
        '0': '0Portions',
        '1-4': 'From1To4Portions',
        'GE5': '5PortionsOrMore'
    }
    df = df.replace({'n_portion': n_portion})
    return df


def _replace_coicop(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF.

   Arguments: df (pd.DataFrame)

   Returns: df (pd.DataFrame)
   """
    coicop = {
        'CP0116': 'ConsumptionOfFruits',
        'CP0117': 'ConsumptionOfVegetables'
    }
    df = df.replace({'coicop': coicop})
    return df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
   Divides a single column into multiple columns and returns the DF.

   Args: df (pd.DataFrame): df as the input, to divide the column

   Returns: df (pd.DataFrame): modified df as output
   """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df

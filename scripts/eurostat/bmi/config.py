import pandas as pd

_BMI_VALUES_MAPPER = {
    'BMI_LT18P5': 'Underweight',
    'BMI18P5-24': 'Normal',
    'BMI_GE25': 'Overweight',
    'BMI25-29': 'PreObese',
    'BMI_GE30': 'Obesity',
    'LT18P5': 'Underweight',
    '18P5-25': 'Normal',
    '25-30': 'Overweight',
    'GE30': 'Obesity',
}

_EDUCATIONAL_VALUES_MAPPER = {
    'ED0-2': 'EducationalAttainment'+\
    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
    'ED0_2': 'EducationalAttainment'+\
    'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
    'ED3-4': 'EducationalAttainment'+\
    'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
    'ED3_4': 'EducationalAttainment'+\
        'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
    'ED5_6' : 'TertiaryEducationStageOneOrTertiaryEducationStageTwo',
    'ED5-8': 'EducationalAttainmentTertiaryEducation',
    'ED5_8': 'EducationalAttainmentTertiaryEducation',
    'TOTAL': 'Total'
}

_SEX_VALUES_MAPPER = {'F': 'Female', 'M': 'Male', 'T': 'Total'}

_INCOME_QUANTILE_VALUES_MAPPER = {
    'TOTAL': 'Total',
    'QU1': 'Percentile0To20',
    'QU2': 'Percentile20To40',
    'QU3': 'Percentile40To60',
    'QU4': 'Percentile60To80',
    'QU5': 'Percentile80To100'
}

_DEGREE_URBANISATION_VALUES_MAPPER = {
    'TOTAL': 'Total',
    'DEG1': 'Cities',
    'DEG2': 'TownsAndSuburbs',
    'DEG3': 'RuralAreas',
}

_BIRTH_COUNTRY_VALUES_MAPPER = {
    'EU28_FOR': 'ForeignBornWithinEU28',
    'NEU28_FOR': 'ForeignBornOutsideEU28',
    'FOR': 'ForeignBorn',
    'NAT': 'Native'
}

_CITIZENSHIP_COUNTRY_VALUES_MAPPER = {
    'EU28_FOR': 'ForeignWithinEU28',
    'NEU28_FOR': 'ForeignOutsideEU28',
    'FOR': 'NotACitizen',
    'NAT': 'Citizen'
}

_ACTIVITY_LEVEL_VALUES_MAPPER = {
    'MOD': 'Moderate',
    'SEV': 'Severe',
    'SM_SEV': 'SomeOrSevere',
    'NONE': 'None'
}

_COLUMN_MAPPER = {
    "bmi": _BMI_VALUES_MAPPER,
    "education": _EDUCATIONAL_VALUES_MAPPER,
    "sex": _SEX_VALUES_MAPPER,
    "income_quantile": _INCOME_QUANTILE_VALUES_MAPPER,
    "degree_of_urbanisation": _DEGREE_URBANISATION_VALUES_MAPPER,
    "birth_country": _BIRTH_COUNTRY_VALUES_MAPPER,
    "citizenship_country": _CITIZENSHIP_COUNTRY_VALUES_MAPPER,
    "activity_level": _ACTIVITY_LEVEL_VALUES_MAPPER
}


def map_to_full_form(df: pd.DataFrame, category: str,
                     df_col: str) -> pd.DataFrame:
    df[df_col] = df[df_col].map(_COLUMN_MAPPER.get(category))
    return df

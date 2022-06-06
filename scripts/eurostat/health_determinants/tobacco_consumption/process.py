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
This Python Script Load the datasets, cleans it
and generates cleaned CSV, MCF, TMCF file
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, 'util')
# from alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags

# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def health_determinant_eurostat_smoking_county_of_birth(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,smoking,sex,age,c_birth,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,smoking,sex,age,c_birth,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_c_birth(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['c_birth']+'_'+df['sex']+\
        '_'+'Smoking_TobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['c_birth']+'_'+df['sex']
    df.drop(columns=['smoking', 'c_birth', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df.to_csv("sk1b.csv")
    return df


def health_determinant_eurostat_smoking_country_of_citizenship(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,smoking,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "unit,smoking,sex,age,citizen,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_citizen(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['citizen']+'_'+df['sex']+\
        '_'+'Smoking_TobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['citizen']+'_'+df['sex']
    df.drop(columns=['smoking', 'citizen', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df.to_csv("sk1c.csv")
    return df


def health_determinant_eurostat_smoking_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'Smoking_TobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    df.to_csv("sk1e.csv")
    return df


def health_determinant_eurostat_smoking_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,quant_inc,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,quant_inc,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'Smoking_TobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    df.to_csv("sk1i.csv")
    return df


def health_determinant_eurostat_smoking_degree_of_urbanisation(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'smoking,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "smoking,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['deg_urb']+'_'+df['sex']+\
        '_'+'Smoking_TobaccoProducts'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df.to_csv("sk1u.csv")
    return df


def health_determinant_eurostat_former_daily_tobacco_smoking_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,sex,age,quant_inc,time', 'EU27_2020', 'BE', 'BG', 'CZ', 'DK',
        'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT', 'LU',
        'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS',
        'NO', 'RS', 'TR'
    ]
    df.columns = cols
    col1 = "unit,sex,age,quant_inc,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020'], inplace=True)
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'Former_daily_tobacco_smoking'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df.to_csv("sk2i.csv")
    return df


def health_determinant_eurostat_daily_smokers_education_attainment_level(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,isced11,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_isced11(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['isced11']+'_'+df['sex']+\
        '_'+'Daily_Smokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['isced11']+'_'+df['sex']
    df.drop(columns=['smoking', 'isced11', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    df.to_csv("sk3e.csv")
    return df


def health_determinant_eurostat_daily_smokers_income_quintile(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['unit,smoking,quant_inc,sex,age,geo', '2019', '2014']
    df.columns = cols
    col1 = "unit,smoking,quant_inc,sex,age,geo"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_quant_inc(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['quant_inc']+'_'+df['sex']+\
        '_'+'Daily_Smokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['quant_inc']+'_'+df['sex']
    df.drop(columns=['smoking', 'quant_inc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    df.to_csv("sk3i.csv")
    return df


def health_determinant_eurostat_daily_smokers_degree_of_urbanisation(
        df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'smoking,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    col1 = "smoking,deg_urb,sex,age,unit,time"
    df = _split_column(df, col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_levels(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Count_Person_'+ df['deg_urb']+'_'+df['sex']+\
        '_'+'Daily_Smokers'+'_'+df['smoking']+\
        '_AsAFractionOf_Count_Person_'+df['deg_urb']+'_'+df['sex']
    df.drop(columns=['smoking', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    df.to_csv("sk3u.csv")
    return df


# ............................................................................................................................................
def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {'F': 'Female', 'M': 'Male', 'T': 'Total'}
    df = df.replace({'sex': _dict})
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    _dict = {
        'ED0-2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED0_2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED3-4': 'EducationalAttainment'+\
        'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED3_4': 'EducationalAttainment'+\
            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5-8': 'EducationalAttainmentTertiaryEducation',
        'ED5_8': 'EducationalAttainmentTertiaryEducation',
        'TOTAL': 'Total'
        }
    df = df.replace({'isced11': _dict})
    return df


def _replace_quant_inc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """

    _dict = {
        'TOTAL': 'Total',
        'QU1': 'FirstQuintile',
        'QU2': 'SecondQuintile',
        'QU3': 'ThirdQuintile',
        'QU4': 'FourthQuintile',
        'QU5': 'FifthQuintile'
    }
    df = df.replace({'quant_inc': _dict})
    return df


def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'TOTAL': 'Total',
        'DEG1': 'Cities',
        'DEG2': 'TownsAndSuburbs',
        'DEG3': 'RuralAreas',
    }
    df = df.replace({'deg_urb': _dict})
    return df


def _replace_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'NSM': 'NonSmoker',
        'SM_CUR': 'CurrentSmoker',
        'SM_DAY': 'DailySmoker',
        'SM_OCC': 'OccasionalSmoker',
        'SM_LT20D': 'LessThan20CigarettesPerDay',
        'SM_GE20D': '20OrMoreCigarettesPerDay'
    }
    df = df.replace({'smoking': _dict})
    return df


def _replace_c_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'EU28_FOR': 'CountryOfBirthEU28CountriesExceptReportingCountry',
        'NEU28_FOR': 'CountryOfBirthNonEU28CountriesNorReportingCountry',
        'FOR': 'CountryOfBirthForeignCountry',
        'NAT': 'CountryOfBirthReportingCountry'
    }
    df = df.replace({'c_birth': _dict})
    return df


def _replace_citizen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _dict = {
        'EU28_FOR': 'CitizenshipEU28CountriesExceptReportingCountry',
        'NEU28_FOR': 'CitizenshipNonEU28CountriesNorReportingCountry',
        'FOR': 'CitizenshipForeignCountry',
        'NAT': 'CitizenshipReportingCountry'
    }
    df = df.replace({'citizen': _dict})
    return df


def _replace_frequenc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    _frequenc = {
        'DAY': 'EveryDay',
        'FMR': 'Formerly',
        'OCC': 'Occasionally',
        'NVR': 'Never',
    }
    df = df.replace({'frequenc': _frequenc})
    return df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df


df = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1b.tsv.gz",
    sep='\t')
health_determinant_eurostat_smoking_county_of_birth(df)

df = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1c.tsv.gz",
    sep='\t')
health_determinant_eurostat_smoking_country_of_citizenship(df)

df = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1e.tsv.gz",
    sep='\t')
health_determinant_eurostat_smoking_education_attainment_level(df)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1i.tsv.gz",
    sep='\t')
health_determinant_eurostat_smoking_income_quintile(df1)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk1u.tsv.gz",
    sep='\t')
health_determinant_eurostat_smoking_degree_of_urbanisation(df1)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk2i.tsv.gz",
    sep='\t')
health_determinant_eurostat_former_daily_tobacco_smoking_income_quintile(df1)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3e.tsv.gz",
    sep='\t')
health_determinant_eurostat_daily_smokers_education_attainment_level(df1)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3i.tsv.gz",
    sep='\t')
health_determinant_eurostat_daily_smokers_income_quintile(df1)

df1 = pd.read_csv(
    "https://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?file=data/hlth_ehis_sk3u.tsv.gz",
    sep='\t')
health_determinant_eurostat_daily_smokers_degree_of_urbanisation(df1)

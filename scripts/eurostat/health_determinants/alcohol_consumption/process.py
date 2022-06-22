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
and generates cleaned CSV, MCF, TMCF file.
Before running this module, run download_input_files.py script, it downloads
required input files, creates necessary folders for processing.
Folder information
input_files - downloaded files (from US census website) are placed here
output_files - output files (mcf, tmcf and csv are written here)
"""
import os
import sys
import re
import pandas as pd
import numpy as np
from absl import app, flags

# For import common.replacement_functions
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from common.replacement_functions import (_replace_sex, _replace_frequenc,
                                          _replace_isced11, _replace_quant_inc,
                                          _replace_deg_urb, _replace_c_birth,
                                          _replace_citizen, _split_column)
# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)

from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=import-error
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                        "{pv11}\n"
                        "typeOf: dcs:StatisticalVariable\n"
                        "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                        "{pv6}{pv7}{pv8}{pv9}{pv10}\n"
                        "statType: dcs:measuredValue\n"
                        "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = (
            "Node: E:EuroStat_Population_AlcoholConsumption->E0\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: C:EuroStat_Population_AlcoholConsumption->SV\n"
            "measurementMethod: C:EuroStat_Population_AlcoholConsumption->"
            "Measurement_Method\n"
            "observationAbout: C:EuroStat_Population_AlcoholConsumption->geo\n"
            "observationDate: C:EuroStat_Population_AlcoholConsumption->time\n"
            "value: C:EuroStat_Population_AlcoholConsumption->observation\n")

def _alcoholconsumption_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file alcoholconsumption_by_sex_education
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+\
        df['frequenc']+'_In_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def _alcoholconsumption_by_sex_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file alcoholconsumption_by_sex_income
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,frequenc,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,frequenc,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+df['frequenc']\
            +'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
    # dropping unwanted columns
    df.drop(columns=['quant_inc','frequenc','sex','age','unit'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df

def _alcoholconsumption_by_sex_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file alcoholconsumption_by_sex_urbanisation
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE',
    'BG','CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_frequenc(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+df['frequenc']\
        +'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['frequenc','deg_urb','sex','unit','age'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _bingedrinking_by_sex_education(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file bingedrinking_by_sex_education
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,isced11,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,isced11,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Percent_BingeDrinking_'+\
        df['frequenc']+'_In_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','frequenc','sex'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def _bingedrinking_by_sex_income(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file bingedrinking_by_sex_income for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,frequenc,sex,age,geo', '2019', '2014']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,frequenc,sex,age,geo"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Percent_BingeDrinking_'+df['frequenc']\
        +'_In_Count_Person_'+df['sex']+'_'+df['quant_inc']
    # dropping unwanted columns
    df.drop(columns=['unit','age','quant_inc','frequenc','sex'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df

def _bingedrinking_by_sex_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file bingedrinking_by_sex_urbanisation
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,deg_urb,sex,age,unit,time','EU27_2020','EU28','BE',
    'BG','CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_frequenc(df)
    # giving proper statvar name
    df['SV'] = 'Percent_BingeDrinking_'+df['frequenc']\
        +'_In_Count_Person_'+df['deg_urb']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['frequenc','deg_urb','sex','unit','age'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _hazardousalcoholconsumption_by_sex_education(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file hazardousalcoholconsumption_by_sex_education
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,isced11,sex,age,time','EU27_2020','EU28','BE','BG','CZ',
    'DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE', 'IS', 'NO', 'UK', 'TR' ]
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,isced11,sex,age,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_sex(df)
    df = _replace_isced11(df)
    # giving proper statvar name
    df['SV'] = 'Percent_HazardousAlcoholConsumption_In_Count_Person_'\
        +df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['unit','age','isced11','sex'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df

def _hazardousalcoholconsumption_by_sex_income(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file hazardousalcoholconsumption_by_sex_income
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,quant_inc,sex,age,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,quant_inc,sex,age,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_sex(df)
    df = _replace_quant_inc(df)
    # giving proper statvar name
    df['SV'] = 'Percent_HazardousAlcoholConsumption_In_Count_Person_'\
        +df['sex']+'_'+df['quant_inc']
    # dropping unwanted columns
    df.drop(columns=['unit','age' ,'quant_inc','sex'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df

def _hazardousalcoholconsumption_by_sex_urbanisation(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file hazardousalcoholconsumption_by_sex_urbanisation
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['deg_urb,sex,age,unit,time','EU27_2020','EU28','BE','BG',
    'CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "deg_urb,sex,age,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Percent_HazardousAlcoholConsumption_In_Count_Person_'\
        +df['deg_urb']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['deg_urb','sex','unit','age'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _alcoholconsumption_by_sex_country_of_birth(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file alcoholconsumption_by_sex_country_of_birth
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,sex,age,c_birth,time','EU27_2020','EU28','BE',
    'BG','CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,sex,age,c_birth,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_c_birth(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+df['frequenc']+\
        '_In_Count_Person_'+df['sex']+'_'+df['c_birth']
    # dropping unwanted columns
    df.drop(columns=['frequenc','c_birth','sex','unit','age'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _alcoholconsumption_by_sex_citizen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file alcoholconsumption_by_sex_citizen
    for concatenation in Final CSV
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['unit,frequenc,sex,age,citizen,time','EU27_2020','EU28','BE',
    'BG','CZ','DK','DE','EE','IE','EL','ES','HR','IT','CY','LV','LT','LU','HU',
    'MT','AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "unit,frequenc,sex,age,citizen,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020','EU28'])
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+df['frequenc']+\
        '_In_Count_Person_'+df['citizen']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['frequenc','citizen','sex','unit','age'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _historical_alcoholconsumption_by_sex_education(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file historical_alcoholconsumption_by_sex_education
    for concatenation in Final CSV.
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['sex,age,isced11,frequenc,unit,time','BE','BG','CZ','EL',
        'ES','FR','CY','LV','HU','MT','PL','RO','SI','SK','TR']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "sex,age,isced11,frequenc,unit,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Percent_AlcoholConsumption_'+\
        df['frequenc']+'_In_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['isced11','sex','age','frequenc','unit'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _historical_bingedrinking_by_sex_education(df: pd.DataFrame)\
    -> pd.DataFrame:
    """
    Cleans the file historical_bingedrinking_by_sex_education
    for concatenation in Final CSV.
    Args:
        df (pd.DataFrame): The raw df as the input
    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    # providing column names
    columns = ['frequenc,sex,age,isced11,time','BE','BG','CZ','EL',
        'ES','CY','LV','HU','MT','RO','SI','SK']
    df.columns=columns
    # spliting the first column to multiple columns
    split_columns = "frequenc,sex,age,isced11,time"
    df = _split_column(df,split_columns)
    # Filtering out the wanted rows and columns.
    df = df[df['age'] == 'TOTAL']
    df = _replace_isced11(df)
    df = _replace_frequenc(df)
    df = _replace_sex(df)
    # giving proper statvar name
    df['SV'] = 'Percent_BingeDrinking_'+\
        df['frequenc']+'_In_Count_Person_'+\
            df['isced11']+'_'+df['sex']
    # dropping unwanted columns
    df.drop(columns=['isced11','sex','age','frequenc'],inplace=True)
    # arraning the dataframe in long format
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


class EuroStatAlcoholConsumption:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    def __init__(self, input_files: list, csv_file_path: str,\
        mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Args:
            None
        Returns:
            None
        """
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(_TMCF_TEMPLATE.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Args:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        # pylint: disable=R0914
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc = healthbehavior =\
            residence = countryofbirth = citizenship = sv_name = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            sv_prop1 = sv_temp[1].split("_")
            for prop in sv_prop:
                if prop in ["Percent"]:
                    sv_name = sv_name + "Percentage "
                if "AlcoholConsumption" in prop or "BingeDrinking" in prop\
                    or "HazardousAlcoholConsumption" in prop: 
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Daily" in prop or "LessThanOnceAMonth" in prop \
                    or "EveryMonth" in prop or "NotInTheLast12Months" in prop\
                    or "Never" in prop:
                    frequenc = "\nhealthBehaviorFrequency: dcs:" + prop\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "NeverOrNotInTheLast12Months" in\
                    prop or "EveryWeek" in prop or "AtLeastOnceAWeek" in prop\
                    or "NeverOrOccasional" in prop:
                    frequenc = "\nhealthBehaviorFrequency: dcs:" + prop\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
            sv_name = sv_name + "Among "
            for prop in sv_prop1:
                if prop in ["Count","Person"]:
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Percentile",\
                        "").replace("IncomeOf","").replace("To"," ")\
                            +" Percentile]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "Urban" in prop or "SemiUrban" in prop \
                    or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "WithinEU28AndNotACitizen" in prop or\
                    "CitizenOutsideEU28" in prop or "Citizen"\
                        in prop or "NotACitizen" in prop:
                    citizenship = "\ncitizenship: dcs:"+\
                    prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "

            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            sv_name = sv_name.rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace("AWeek","A Week")\
                .replace("Last12","Last 12").replace("ACitizen","A Citizen")\
                    .replace("AMonth","A Month")

            final_mcf_template += _MCF_TEMPLATE.format( pv1=sv,
                                                        pv11=sv_name,
                                                        pv2=denominator,
                                                        pv3=healthbehavior,
                                                        pv4=gender,
                                                        pv5=frequenc,
                                                        pv6=education,
                                                        pv7=incomequin,
                                                        pv8=residence,
                                                        pv9=countryofbirth,
                                                        pv10=citizenship,
                                                      ) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
        Args:
            None
        Returns:
            None
        """

        final_df = pd.DataFrame(columns=['time','geo','SV','observation',\
            'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:
            df = pd.read_csv(file_path, sep='\t', header=0)
            # Taking the File name out of the complete file address
            # Used -1 to pickup the last part which is file name
            # Read till -4 inorder to remove the .tsv extension
            file_name = file_path.split("/")[-1][:-4]
            file_to_function_mapping = {
                "hlth_ehis_al1b": _alcoholconsumption_by_sex_country_of_birth,
                "hlth_ehis_al1c": _alcoholconsumption_by_sex_citizen,
                "hlth_ehis_al1e": _alcoholconsumption_by_sex_education,
                "hlth_ehis_al1i": _alcoholconsumption_by_sex_income,
                "hlth_ehis_al1u": _alcoholconsumption_by_sex_urbanisation,
                "hlth_ehis_al2e":\
                    _hazardousalcoholconsumption_by_sex_education,
                "hlth_ehis_al2i": _hazardousalcoholconsumption_by_sex_income,
                "hlth_ehis_al2u":\
                    _hazardousalcoholconsumption_by_sex_urbanisation,
                "hlth_ehis_al3e": _bingedrinking_by_sex_education,
                "hlth_ehis_al3i": _bingedrinking_by_sex_income,
                "hlth_ehis_al3u": _bingedrinking_by_sex_urbanisation,
                "hlth_ehis_de6": _historical_bingedrinking_by_sex_education,
                "hlth_ehis_de10":\
                    _historical_alcoholconsumption_by_sex_education
            }
            df = file_to_function_mapping[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV','observation'])
        final_df = final_df.drop_duplicates(subset=['time','geo','SV'],\
            keep='first')
        final_df['observation'] = final_df['observation'].astype(str)\
            .str.strip()
        # derived_df generated to get the year/SV/location sets
        # where 'u' exist
        derived_df = final_df[final_df['observation'].astype(str)
            .str.contains('u')]
        u_rows = list(derived_df['SV']+derived_df['geo'])
        final_df['info'] = final_df['SV']+final_df['geo']
        # Adding Measurement Method based on a condition, whereever u is found
        # in an observation. The corresponding measurement method for all the
        # years of that perticular SV/Country is made as Low Reliability.
        # Eg: 2014
        #   country/BEL
        #   Percent_AlcoholConsumption_Daily_In_Count_Person
        #   14.2 u,
        # so measurement method for all 2008, 2014 and 2019 years shall be made
        # low reliability.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_LowReliability',
            'EurostatRegionalStatistics')
        derived_df = final_df[final_df['observation'].astype(str)
            .str.contains('d')]
        u_rows = list(derived_df['SV']+derived_df['geo'])
        final_df['info'] = final_df['SV']+final_df['geo']
        # Adding Measurement Method based on a condition, whereever d is found
        # in an observation. The corresponding measurement method for all the
        # years of that perticular SV/Country is made as Definition Differs.
        # Eg: 2014
        #   country/ITA
        #   Percent_AlcoholConsumption_Daily_In_Count_Person
        #   14.1 d,
        # so measurement method for both 2014 and 2019 years shall be made
        # Definition Differs.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_DefinitionDiffers',
            final_df['Measurement_Method'])
        final_df.drop(columns=['info'],inplace=True)
        final_df['observation'] = (final_df['observation'].astype(str)
            .str.replace(':', '').str.replace(' ', '').str.replace('u', '')
            .str.replace('d', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
            errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'],inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()

def main(_):
    input_path = _FLAGS.input_path
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    csv_name = "eurostat_population_alcoholconsumption.csv"
    mcf_name = "eurostat_population_alcoholconsumption.mcf"
    tmcf_name = "eurostat_population_alcoholconsumption.tmcf"
    cleaned_csv_path = data_file_path + os.sep + csv_name
    mcf_path = data_file_path + os.sep + mcf_name
    tmcf_path = data_file_path + os.sep + tmcf_name
    loader = EuroStatAlcoholConsumption(ip_files, cleaned_csv_path,\
        mcf_path, tmcf_path)
    loader.process()

if __name__ == "__main__":
    app.run(main)

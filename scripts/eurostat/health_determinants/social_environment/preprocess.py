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
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)

import pandas as pd
import numpy as np
import re
from util.alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags
# pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)
FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "input_file")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv2}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = (
    "Node: E:EuroStat_Population_PhysicalActivity->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:EuroStat_Population_PhysicalActivity->SV\n"
    "measurementMethod: C:EuroStat_Population_PhysicalActivity->"
    "Measurement_Method\n"
    "observationAbout: C:EuroStat_Population_PhysicalActivity->geo\n"
    "observationDate: C:EuroStat_Population_PhysicalActivity->time\n"
    "value: C:EuroStat_Population_PhysicalActivity->observation\n")

def _hlth_ehis_ss1e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV

    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,lev_perc,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_lev_perc(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Percent_' + df['lev_perc'] + 'SocialSupport_In_Count_Person_'\
        + df['isced11'] + '_' + df['sex']
    df.drop(columns=['unit', 'age', 'isced11', 'lev_perc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
        ,value_name='observation')
    return df


def _hlth_ehis_ss1u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe1u for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'lev_perc,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_lev_perc(df)
    df.drop(columns=['unit', 'age'], inplace=True)
    df['SV'] = 'Percent_' + df['lev_perc']+'SocialSupport_In_Count_Person_' +\
        df['deg_urb'] + '_' + df['sex']
    df.drop(columns=['lev_perc', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df


def _hlth_ehis_ic1e(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = ['unit,assist,isced11,sex,age,geo', '2019', '2014']
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df[(df['geo'] != 'EU27_2020') & (df['geo'] != 'EU28')]
    df = _replace_assist(df)
    df = _replace_sex(df)
    df = _replace_isced11(df)
    df['SV'] = 'Percent_' + 'AtLeastOnceAWeek_' + df['assist'] +\
        '_In_Count_Person_' + df['isced11']+ '_' + df['sex']
    df.drop(columns=['unit', 'age', 'isced11', 'assist', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return df


def _hlth_ehis_ic1u(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'assist,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_deg_urb(df)
    df = _replace_sex(df)
    df = _replace_assist(df)
    df['SV'] = 'Percent_' + 'AtLeastOnceAWeek_' + df['assist'] +\
        '_In_Count_Person_' + df['deg_urb'] + '_' + df['sex']
    df.drop(columns=['unit', 'age', 'assist', 'deg_urb', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df


def _hlth_ehis_ss1b(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,lev_perc,sex,age,c_birth,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_lev_perc(df)
    df = _replace_sex(df)
    df = _replace_c_birth(df)
    df['SV'] = 'Percent_'+ df['lev_perc'] +'SocialSupport_In_Count_Person_'\
        +df['c_birth']+'_'+df['sex']
    df.drop(columns=['unit', 'age', 'c_birth', 'lev_perc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df


def _hlth_ehis_ss1c(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,lev_perc,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_lev_perc(df)
    df = _replace_sex(df)
    df = _replace_citizen(df)
    df['SV'] = 'Percent_' + df['lev_perc'] + 'SocialSupport_In_Count_Person_' +\
        df['citizen'] + '_' + df['sex']
    df.drop(columns=['unit', 'age', 'citizen', 'lev_perc', 'sex'], inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df


def _hlth_ehis_ss1d(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9e for concatenation in Final CSV
    
    Args:
        df (pd.DataFrame): the raw df as the input

    Returns:
        df (pd.DataFrame): provides the cleaned df as output
    """
    cols = [
        'unit,lev_perc,sex,age,lev_limit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    df.columns = cols
    df = _split_column(df, cols[0])
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df = df.drop(columns=['EU27_2020', 'EU28'])
    df = _replace_lev_perc(df)
    df = _replace_sex(df)
    df = _replace_lev_limit(df)
    df['SV'] = 'Percent_' + df['lev_perc'] + 'SocialSupport_In_Count_Person_' +\
        df['lev_limit'] + '_' + df['sex']
    df.drop(columns=['unit', 'age', 'lev_limit', 'lev_perc', 'sex'],
            inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
            ,value_name='observation')
    return df


def _replace_sex(df: pd.DataFrame) -> pd.DataFrame:
    """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
    sex = {'F': 'Female', 'M': 'Male', 'T': 'Total'}
    df = df.replace({'sex': sex})
    return df


def _replace_lev_perc(df: pd.DataFrame) -> pd.DataFrame:
    """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
    lev_perc = {'STR': 'Strong', 'INT': 'Intermediate', 'POOR': 'Poor'}
    df = df.replace({'lev_perc': lev_perc})
    return df


def _replace_isced11(df: pd.DataFrame) -> pd.DataFrame:
    """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
    isced11 = {
        'ED0-2': 'EducationalAttainment'+\
        'LessThanPrimaryEducationOrPrimaryEducationOrLowerSecondaryEducation',
        'ED3_4': 'EducationalAttainment'+\
            'UpperSecondaryEducationOrPostSecondaryNonTertiaryEducation',
        'ED5-8': 'EducationalAttainmentTertiaryEducation',
        'TOTAL': 'Total'
        }
    df = df.replace({'isced11': isced11})
    return df


def _replace_deg_urb(df: pd.DataFrame) -> pd.DataFrame:
    """
   Replaces values of a single column into true values
   from metadata returns the DF
   """
    deg_urb = {
        'TOTAL': 'Total',
        'DEG1': 'Urban',
        'DEG2': 'SemiUrban',
        'DEG3': 'Rural',
    }
    df = df.replace({'deg_urb': deg_urb})
    return df


def _replace_assist(df: pd.DataFrame) -> pd.DataFrame:
    """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
    assist = {
        'PROV': 'ProvidingInformalCare',
        'PROV_R': 'Relatives_ProvidingInformalCare',
        'PROV_NR': 'NonRelatives_ProvidingInformalCare',
        'NPROV': 'NotProvidingInformalCare'
    }
    df = df.replace({'assist': assist})
    return df


def _replace_c_birth(df: pd.DataFrame) -> pd.DataFrame:
    """
 Replaces values of a single column into true values
 from metadata returns the DF
 """
    c_birth = {
        'EU28_FOR': 'ForeignBornWithinEU28',
        'NEU28_FOR': 'ForeignBornOutsideEU28',
        'FOR': 'ForeignBorn',
        'NAT': 'Native'
    }
    df = df.replace({'c_birth': c_birth})
    return df


def _replace_citizen(df: pd.DataFrame) -> pd.DataFrame:
    """
 Replaces values of a single column into true values
 from metadata returns the DF
 """
    citizen = {
        'EU28_FOR': 'CitizenOutsideEU28',
        'NEU28_FOR': 'WithinEU28AndNotACitizen',
        'FOR': 'NotACitizen',
        'NAT': 'Citizen'
    }
    df = df.replace({'citizen': citizen})
    return df


def _replace_lev_limit(df: pd.DataFrame) -> pd.DataFrame:
    """
  Replaces values of a single column into true values
  from metadata returns the DF
  """
    lev_limit = {
        'MOD': 'ModerateActivityLimitation',
        'SEV': 'SevereActivityLimitation',
        'SM_SEV': 'LimitedActivityLimitation',
        'NONE': 'NoActivityLimitation'
    }
    df = df.replace({'lev_limit': lev_limit})
    return df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
  Divides a single column into multiple columns and returns the DF
  """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df


class EuroStatSocialEnvironment:
    """
  This Class has requried methods to generate Cleaned CSV,
  MCF and TMCF Files
  """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path

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
        # pylint: disable=R0912
        # pylint: disable=R0915
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            gender = education = lev_perc = assist = frequency = residence = ''
            countryofbirth = citizenship = lev_limit = sv_name = ''
            benificiary = ''

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_property = sv.split("_")
            for prop in sv_property:
                if prop == "Percent":
                    sv_name = sv_name + "Percentage "
                elif prop == "In":
                    sv_name = sv_name + "Among "
                elif prop == "Count":
                    continue
                elif prop == "Person":
                    continue
                if "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Strong" in prop or "Intermediate" in prop \
                    or "Poor" in prop:
                    lev_perc = "\nsocialSupport: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Urban" in prop or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Limitation" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                    sv_name = sv_name + prop + ", "
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "
                elif "InformalCare" in prop:
                    assist = "\nsocialSupportType: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Relatives" in prop:
                    benificiary = "\nsocialSupportBenefciaryType: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "AtLeastOnceAWeek" in prop:
                    frequency = "\nactivityFrequency: \"" + prop + "\""
                    sv_name = sv_name + prop + ", "
            # Making the changes to the SV Name,
            # Removing any extra commas, with keyword and
            # adding Population in the end
            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            sv_name = sv_name.rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace('AWeek','A Week')

            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                       pv2=sv_name,
                                                       pv3=denominator,
                                                       pv4=education,
                                                       pv5=residence,
                                                       pv6=assist,
                                                       pv7=lev_perc,
                                                       pv8=gender,
                                                       pv9=countryofbirth,
                                                       pv10=citizenship,
                                                       pv11=lev_limit,
                                                       pv12=benificiary,
                                                       pv13=frequency) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
        # pylint: enable=R0912
        # pylint: enable=R0915
    
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


    def process(self):
        """
      This Method calls the required methods to generate
      cleaned CSV, MCF, and TMCF file
      """
        final_df = pd.DataFrame(columns=['time','geo','SV','observation',\
            'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        for file_path in self._input_files:
            print(file_path)
            df = pd.read_csv(file_path, sep='\t', skiprows=1)
            file_name = file_path.split("/")[-1][:-4]
            function_dict = {
                "hlth_ehis_ss1e": _hlth_ehis_ss1e,
                "hlth_ehis_ss1u": _hlth_ehis_ss1u,
                "hlth_ehis_ic1e": _hlth_ehis_ic1e,
                "hlth_ehis_ic1u": _hlth_ehis_ic1u,
                "hlth_ehis_ss1b": _hlth_ehis_ss1b,
                "hlth_ehis_ss1c": _hlth_ehis_ss1c,
                "hlth_ehis_ss1d": _hlth_ehis_ss1d
            }
            df = function_dict[file_name](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
        final_df = final_df.drop_duplicates(subset=['time','geo','SV'],\
            keep='first')
        final_df['observation'] = final_df['observation'].astype(str)\
            .str.strip()
        # derived_df generated to get the year/SV/location sets
        # where 'u' exist
        derived_df = final_df[final_df['observation'].astype(str).str.contains(
            'u')]
        u_rows = list(derived_df['SV'] + derived_df['geo'])
        final_df['info'] = final_df['SV'] + final_df['geo']
        # Adding Measurement Method based on a condition, whereever u is found
        # in an observation. The corresponding measurement method for all the
        # years of that perticular SV/Country is made as Low Reliability.
        # Eg: 2014
        #   country/AUT
        #   Percent_AerobicSports_NonWorkRelatedPhysicalActivity_In_Count_Person
        #   77.3 u,
        # so measurement method for both 2014 and 2019 years shall be made
        # low reliability.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_LowReliability',
            'EurostatRegionalStatistics')
        final_df.drop(columns=['info'], inplace=True)
        final_df['observation'] = (
            final_df['observation'].astype(str).str.replace(
                ':', '').str.replace(' ', '').str.replace('u', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
                                                errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()

def main(_):
    input_path = FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "output")
    # Defining Output Files
    csv_name = "eurostat_population_socialenvironment.csv"
    mcf_name = "eurostat_population_socialenvironment.mcf"
    tmcf_name = "eurostat_population_socialenvironment.tmcf"
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    loader = EuroStatSocialEnvironment(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)

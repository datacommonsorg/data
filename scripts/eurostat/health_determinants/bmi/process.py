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
from absl import app
from absl import flags

sys.path.insert(1, '../')
from common.replacement_functions import (_replace_sex, _replace_physact,
                                          _replace_isced11, _replace_quant_inc,
                                          _replace_deg_urb, _replace_levels,
                                          _replace_duration, _replace_c_birth,
                                          _replace_citizen, _replace_lev_limit,
                                          _replace_bmi, _split_column)

# For import util.alpha2_to_dcid
sys.path.insert(1, 'util')
# pylint: disable=import-error
# pylint: disable=wrong-import-position
from util.alpha2_to_dcid import COUNTRY_MAP
from config import map_to_full_form
# pylint: enable=import-error
# pylint: enable=wrong-import-position

pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_files"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


def _age_sex_education(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_bm1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    df_cols = ['unit,bmi,isced11,sex,age,geo', '2019', '2014']
    data_df.columns = df_cols
    multiple_cols = "unit,bmi,isced11,sex,age,geo"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the required rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df, category="education", df_col="isced11")
    data_df['SV'] = 'Count_Person_'+data_df['bmi'] + '_' + \
                    data_df['isced11']+'_' + data_df['sex'] + \
                    '_AsAFractionOf_Count_Person_'+ data_df['isced11']+\
                    '_'+data_df['sex']
    data_df.drop(columns=['unit', 'age', 'isced11', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df


def _age_sex_education_history(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_bm1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    df_cols = [
        'isced11,bmi,sex,age,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES',
        'FR', 'CY', 'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK', 'TR'
    ]
    data_df.columns = df_cols
    multiple_cols = "isced11,bmi,sex,age,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the required rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df, category="education", df_col="isced11")
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+ \
                    data_df['isced11'] +'_'+data_df['sex']+\
                    '_AsAFractionOf_Count_Person_' +data_df['isced11']+\
                    '_' + data_df['sex']
    data_df.drop(columns=['isced11', 'bmi', 'sex', 'age'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_income(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    df_cols = ['unit,bmi,quant_inc,sex,age,geo', '2019', '2014']
    data_df.columns = df_cols
    multiple_cols = "unit,bmi,quant_inc,sex,age,geo"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020', 'EU28']))]
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="income_quantile",
                               df_col="quant_inc")
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+ \
                    data_df['sex'] +'_'+data_df['quant_inc']+\
                    '_AsAFractionOf_Count_Person_' +data_df['sex']+\
                    '_' + data_df['quant_inc']
    data_df.drop(columns=['unit', 'age', 'quant_inc', 'bmi', 'sex'],
                 inplace=True)
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df


def _age_sex_income_history(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_bm1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    df_cols = [
        'bmi,sex,age,quant_inc,time', 'BE', 'BG', 'CZ', 'DE', 'EE', 'EL', 'ES',
        'FR', 'CY', 'LV', 'HU', 'MT', 'AT', 'PL', 'RO', 'SI', 'SK', 'TR'
    ]
    data_df.columns = df_cols
    multiple_cols = "bmi,sex,age,quant_inc,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the required rows and columns
    data_df = data_df[(data_df['age'] == 'TOTAL') &
                      (~(data_df['quant_inc'] == 'UNK'))]
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="income_quantile",
                               df_col="quant_inc")
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+\
                    data_df['sex'] +'_'+data_df['quant_inc']+\
                    '_AsAFractionOf_Count_Person_' +data_df['sex']+\
                    '_' + data_df['quant_inc']

    data_df.drop(columns=['quant_inc', 'bmi', 'sex', 'age'], inplace=True)
    print(data_df['SV'].isna().sum())
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_degree_urbanisation(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'bmi,deg_urb,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = cols
    multiple_cols = "bmi,deg_urb,sex,age,unit,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="degree_of_urbanisation",
                               df_col="deg_urb")
    data_df.drop(columns=['unit', 'age'], inplace=True)
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+ \
                    data_df['sex'] +'_'+data_df['deg_urb']+\
                    '_AsAFractionOf_Count_Person_' +data_df['sex']+\
                    '_' + data_df['deg_urb']
    data_df.drop(columns=['deg_urb', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_birth_country(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,bmi,sex,age,c_birth,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = cols
    multiple_cols = "unit,bmi,sex,age,c_birth,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="birth_country",
                               df_col="c_birth")
    data_df.drop(columns=['unit', 'age'], inplace=True)
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+ \
                    data_df['sex'] +'_'+data_df['c_birth']+\
                    '_AsAFractionOf_Count_Person_' +data_df['sex']+\
                    '_' + data_df['c_birth']
    data_df.drop(columns=['c_birth', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_citizenship_country(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'unit,bmi,sex,age,citizen,time', 'EU27_2020', 'EU28', 'BE', 'BG', 'CZ',
        'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV', 'LT',
        'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI', 'SE',
        'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = cols
    multiple_cols = "unit,bmi,sex,age,citizen,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="citizenship_country",
                               df_col="citizen")
    data_df.drop(columns=['unit', 'age'], inplace=True)
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+\
                    data_df['citizen'] +'_'+data_df['sex']+\
                    '_AsAFractionOf_Count_Person_' +\
                    data_df['citizen']+'_' + data_df['sex']
    data_df.drop(columns=['citizen', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _age_sex_acitivity_limitation(data_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = [
        'bmi,lev_limit,sex,age,unit,time', 'EU27_2020', 'EU28', 'BE', 'BG',
        'CZ', 'DK', 'DE', 'EE', 'IE', 'EL', 'ES', 'FR', 'HR', 'IT', 'CY', 'LV',
        'LT', 'LU', 'HU', 'MT', 'NL', 'AT', 'PL', 'PT', 'RO', 'SI', 'SK', 'FI',
        'SE', 'IS', 'NO', 'UK', 'TR'
    ]
    data_df.columns = cols
    multiple_cols = "bmi,lev_limit,sex,age,unit,time"
    data_df = _split_column(data_df, multiple_cols)
    # Filtering out the wanted rows and columns
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df.drop(columns=['EU27_2020', 'EU28'], inplace=True)
    data_df = map_to_full_form(data_df, category="bmi", df_col="bmi")
    data_df = map_to_full_form(data_df, category="sex", df_col="sex")
    data_df = map_to_full_form(data_df,
                               category="activity_level",
                               df_col="lev_limit")
    data_df.drop(columns=['unit', 'age'], inplace=True)
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+\
                    data_df['sex'] +'_'+data_df['lev_limit']+\
                    '_AsAFractionOf_Count_Person_' +\
                    data_df['sex']+'_' + data_df['lev_limit']
    data_df.drop(columns=['lev_limit', 'bmi', 'sex'], inplace=True)
    data_df = data_df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return data_df


def _split_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col], inplace=True)
    return df


class EuroStatBMI:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str) -> None:
        self.input_files = input_files
        self.cleaned_csv_file_path = csv_file_path
        self.mcf_file_path = mcf_file_path
        self.tmcf_file_path = tmcf_file_path
        self.df = None
        self.file_name = None
        self.scaling_factor = 1

    def _generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.
        Arguments:
            None
        Returns:
            None
        """
        actual_tmcf_template = (
            "Node: E:EuroStat_Population_PhysicalActivity->E0\n"
            "typeOf: dcs:StatVarObservation\n"
            "variableMeasured: C:EuroStat_Population_PhysicalActivity->SV\n"
            "measurementMethod: C:EuroStat_Population_PhysicalActivity->"
            "Measurement_Method\n"
            "observationAbout: C:EuroStat_Population_PhysicalActivity->geo\n"
            "observationDate: C:EuroStat_Population_PhysicalActivity->time\n"
            "value: C:EuroStat_Population_PhysicalActivity->observation\n")
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(actual_tmcf_template.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        # pylint: disable=R0914
        # pylint: disable=R0912
        # pylint: disable=R0915
        actual_mcf_template = (
            "Node: dcid:{}\n"
            "typeOf: dcs:StatisticalVariable\n"
            "populationType: dcs:Person{}{}{}{}{}{}{}{}{}{}{}{}\n"
            "statType: dcs:measuredValue\n"
            "measuredProperty: dcs:count\n")
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = ''
            gender = ''
            education = ''
            healthbehavior = ''
            exercise = ''
            residence = ''
            activity = ''
            duration = ''
            countryofbirth = ''
            citizenship = ''
            lev_limit = ''

            sv_temp = sv.split("_AsAFractionOf_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")

            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "PhysicalActivity" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: dcs:" + prop
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Percentile",\
                        "").replace("To"," ")+" Percentile]"
                elif "Cities" in prop or "TownsAndSuburbs" in prop \
                    or "RuralAreas" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                elif "Activity" in prop:
                    activity = "\nphysicalActivityEffortLevel: dcs:" + prop
                elif "Minutes" in prop:
                    if "OrMoreMinutes" in prop:
                        duration = "\nduration: [" + prop.replace\
                            ("OrMoreMinutes","") + " - Minutes]"
                    elif "To" in prop:
                        duration = "\nduration: [" + prop.replace("Minutes",\
                             "").replace("To", " ") + " Minutes]"
                    else:
                        duration = "\nduration: [Minutes " + prop.replace\
                            ("Minutes","") + "]"
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                elif "ForeignWithin" in prop or "ForeignOutside" in prop\
                    or "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                elif "Moderate" in prop or "Severe" in prop \
                    or "None" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                elif "weight" in prop or "Normal" in prop \
                    or "Obese" in prop or "Obesity" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
            final_mcf_template += actual_mcf_template.format(
                sv, denominator, incomequin, education, healthbehavior,
                exercise, residence, activity, duration, gender, countryofbirth,
                citizenship, lev_limit) + "\n"

        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
        # pylint: enable=R0912
        # pylint: enable=R0915

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file
        """

        final_df = pd.DataFrame()
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        f_names = []
        for file_path in self.input_files:
            file_name_with_ext = os.path.basename(file_path)
            f_names.append(file_name_with_ext)
            file_name_without_ext = os.path.splitext(file_name_with_ext)[0]
            function_dict = {
                "hlth_ehis_bm1e": _age_sex_education,
                "hlth_ehis_bm1i": _age_sex_income,
                "hlth_ehis_bm1u": _age_sex_degree_urbanisation,
                "hlth_ehis_bm1b": _age_sex_birth_country,
                "hlth_ehis_bm1c": _age_sex_citizenship_country,
                "hlth_ehis_bm1d": _age_sex_acitivity_limitation,
                "hlth_ehis_de1": _age_sex_education_history,
                "hlth_ehis_de2": _age_sex_income_history
            }
            df = pd.read_csv(file_path, sep='\t', skiprows=1)
            df = function_dict[file_name_without_ext](df)
            df['SV'] = df['SV'].str.replace('_Total', '')
            df['Measurement_Method'] = np.where(df['observation']\
                .str.contains('u'),'LowReliability/EurostatRegionalStatistics',\
                'EurostatRegionalStatistics')
            df['observation'] = df['observation'].str.replace(':','')\
                .str.replace(' ','').str.replace('u','')
            df['observation'] = pd.to_numeric(df['observation'],
                                              errors='coerce')
            #df['file_name'] = file_name_without_ext
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo'])
        final_df['geo'] = final_df['geo'].map(COUNTRY_MAP)
        final_df.dropna(inplace=True)
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        #print(sv_list)
        sv_list.sort()
        self._generate_mcf(sv_list)
        self._generate_tmcf()


def main(_):
    input_path = FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + \
        "EuroStat_Population_BMI.csv"
    mcf_path = data_file_path + os.sep + \
        "EuroStat_Population_BMI.mcf"
    tmcf_path = data_file_path + os.sep + \
        "EuroStat_Population_BMI.tmcf"
    loader = EuroStatBMI(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)

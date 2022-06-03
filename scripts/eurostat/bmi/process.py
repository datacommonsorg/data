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
import sys
sys.path.insert(0, 'util')
from alpha2_to_dcid import COUNTRY_MAP
from absl import app
from absl import flags
from config import (BMI_VALUES_MAPPER,
                    EDUCATIONAL_VALUES_MAPPER,
                    SEX_VALUES_MAPPER,
                    INCOME_QUANTILE_VALUES_MAPPER,
                    DEGREE_URBANISATION_VALUES_MAPPER)

pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_data"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

def _load_df(file_path: str, skip_rows: int, header: int = None) -> pd.DataFrame:
    data_df = pd.read_csv(file_path, sep="\t", skiprows=skip_rows, header=header)
    return data_df

def _age_sex_education(file_path: str) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_bm1e for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    data_df = _load_df(file_path, 1)
    df_cols = ['unit,bmi,isced11,sex,age,geo', '2019', '2014' ]
    data_df.columns=df_cols
    multiple_cols = "unit,bmi,isced11,sex,age,geo"
    data_df = _split_column(data_df,multiple_cols)
    # Filtering out the required rows and columns    
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020','EU28']))]
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_education(data_df)
    data_df['SV'] = 'Count_Person_'+data_df['bmi'] + '_' + data_df['isced11']+'_'\
        + data_df['sex'] + '_AsAFractionOf_Count_Person_'+\
        data_df['isced11']+'_'+data_df['sex']
    data_df.drop(columns=['unit','age','isced11','bmi','sex'],inplace=True)
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df

def _age_sex_income(file_path: str) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9i for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    data_df = _load_df(file_path, skip_rows=1)
    df_cols = ['unit,bmi,quant_inc,sex,age,geo', '2019', '2014' ]
    data_df.columns=df_cols
    multiple_cols = "unit,bmi,quant_inc,sex,age,geo"
    data_df = _split_column(data_df,multiple_cols)
    # Filtering out the wanted rows and columns    
    data_df = data_df[data_df['age'] == 'TOTAL']
    data_df = data_df[~(data_df['geo'].isin(['EU27_2020','EU28']))]
    data_df = _replace_bmi(data_df)
    data_df = _replace_sex(data_df)
    data_df = _replace_income_quantile(data_df)
    data_df['SV'] = 'Count_Person_'+data_df['bmi']+'_'+ data_df['sex'] +'_'+data_df['quant_inc']+\
        '_AsAFractionOf_Count_Person_' +data_df['sex']+'_' + data_df['quant_inc']
    data_df.drop(columns=['unit','age','quant_inc','bmi','sex'],inplace=True)
    data_df = data_df.melt(id_vars=['SV','geo'], var_name='time'\
            ,value_name='observation')
    return data_df

def _age_sex_degree_urbanisation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the file hlth_ehis_pe9u for concatenation in Final CSV
    Input Taken: DF
    Output Provided: DF
    """
    cols = ['bmi,deg_urb,sex,age,unit,time','EU27_2020','EU28','BG','CZ',
    'DK','DE','EE','IE','EL','ES','FR','HR','IT','CY','LV','LT','LU','HU','MT',
    'AT','PL','PT','RO','SI','SK','FI','SE','IS','NO','UK','TR']
    df.columns=cols
    col1 = "physact,deg_urb,sex,age,unit,time"
    df = _split_column(df,col1)
    # Filtering out the wanted rows and columns
    df = df[df['age'] == 'TOTAL']
    df.drop(columns=['EU27_2020','EU28'],inplace=True)
    df = _replace_bmi(df)
    df = _replace_sex(df)
    df = _replace_deg_urb(df)
    df.drop(columns=['unit','age'],inplace=True)
    df['SV'] = 'Count_Person_'+ df['physact'] +'_'+df['sex']+\
        '_'+'HealthEnhancingPhysicalActivity'+'_'+df['deg_urb']+\
        '_AsAFractionOf_Count_Person_'+df['sex']+'_'+df['deg_urb']
    df.drop(columns=['deg_urb','physact','sex'],inplace=True)
    df = df.melt(id_vars=['SV','time'], var_name='geo'\
        ,value_name='observation')
    return df

def _replace_sex(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df['sex'] = df['sex'].map(SEX_VALUES_MAPPER)
    return df

def _replace_income_quantile(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df['quant_inc'] = df['quant_inc'].map(INCOME_QUANTILE_VALUES_MAPPER)
    return df

def _replace_education(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df['isced11'] = df['isced11'].map(EDUCATIONAL_VALUES_MAPPER)
    return df

def _replace_bmi(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df['bmi'] = df['bmi'].map(BMI_VALUES_MAPPER)
    return df

def _replace_deg_urb(df:pd.DataFrame) -> pd.DataFrame:
    """
    Replaces values of a single column into true values
    from metadata returns the DF
    """
    df['deg_urb'] = df['deg_urb'].map(DEGREE_URBANISATION_VALUES_MAPPER)
    return df

def _split_column(df: pd.DataFrame,col: str) -> pd.DataFrame:
    """
    Divides a single column into multiple columns and returns the DF
    """
    info = col.split(",")
    df[info] = df[col].str.split(',', expand=True)
    df.drop(columns=[col],inplace=True)
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
        dataframe headers and defined TMCF template
        Arguments:
            None
        Returns:
            None
        """
        tmcf_template = """Node: E:EuroStat_Population_PhysicalActivity->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:EuroStat_Population_PhysicalActivity->SV
measurementMethod: C:EuroStat_Population_PhysicalActivity->Measurement_Method
observationAbout: C:EuroStat_Population_PhysicalActivity->geo
observationDate: C:EuroStat_Population_PhysicalActivity->time
value: C:EuroStat_Population_PhysicalActivity->observation 
"""
        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def _generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        mcf_template = """Node: dcid:{}
typeOf: dcs:StatisticalVariable
populationType: dcs:Person{}{}{}{}{}{}{}{}{}{}{}{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = ''
            gender = ''
            education = ''
            healthBehavior = ''
            exercise = ''
            residence = ''
            activity = ''
            duration = ''
            countryofbirth = ''
            citizenship = ''
            lev_limit= ''
            bmi = ''
            sv_temp = sv.split("_AsAFractionOf_")
            denominator = "\nmeasurementDenominator: dcid:"+sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "PhysicalActivity" in prop:
                    healthBehavior = "\nhealthBehavior: dcs:" + prop
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: " + prop
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")
                elif "Quintile" in prop:
                    incomequin = "\nincome: ["+prop.replace("Quintile",\
                        " Quintile").replace("First","1").replace("Second","2")\
                        .replace("Third","3").replace("Fourth","4")\
                        .replace("Fifth","5")+"]"
                elif "Cities" in prop or "TownsAndSuburbs" in prop \
                    or "RuralAreas" in prop:
                    residence = "\nplaceofResidenceClassification: " + prop
                elif "Activity" in prop:
                    activity = "\nphysicalActivityEffortLevel: " + prop
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
                elif "CountryOfBirth" in prop:
                    countryofbirth = "\nnativity: " + prop
                elif "Citizenship" in prop:
                    citizenship = "\ncitizenship: " + prop
                elif "Moderate" in prop or "Severe" in prop \
                    or "None" in prop:
                    lev_limit = "\nglobalActivityLimitationIndicator: "+prop
                elif "weight" in prop or "Normal" in prop \
                    or "Obesity" in prop:
                    lev_limit = "\nbmi: dcs:" + prop
            final_mcf_template += mcf_template.format(sv,denominator,incomequin,
                education,healthBehavior,exercise,residence,activity,duration,
                gender,countryofbirth,citizenship,lev_limit,bmi) + "\n"

        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

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
        for file_path in self.input_files:
            print(file_path)
            if 'hlth_ehis_bm1e' in file_path:
                df = _age_sex_education(file_path)
            elif 'hlth_ehis_bm1i' in file_path:
                df = _age_sex_income(file_path)
            elif 'hlth_ehis_bm1u' in file_path:
                df = _age_sex_degree_urbanisation(file_path)
            df['SV'] = df['SV'].str.replace('_Total','')
            df['Measurement_Method'] = np.where(df['observation']\
                .str.contains('u'),'LowReliability/EurostatRegionalStatistics',\
                'EurostatRegionalStatistics')
            df['observation'] = df['observation'].str.replace(':','')\
                .str.replace(' ','').str.replace('u','')
            df['observation']= pd.to_numeric(df['observation'], errors='coerce')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()
        final_df = final_df.sort_values(by=['time', 'geo'])
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
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

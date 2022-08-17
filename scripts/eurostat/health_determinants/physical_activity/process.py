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
"""
import os
import sys
import re
from absl import app, flags
# For import common.replacement_functions
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
from common.replacement_functions import (_replace_col_values, _split_column)
# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)
import pandas as pd
import numpy as np
from util.alpha2_to_dcid import COUNTRY_MAP

FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv14}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}{pv11}{pv12}{pv13}{pv15}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = (
    "Node: E:eurostat_population_physicalactivity->E0\n"
    "typeOf: dcs:StatVarObservation\n"
    "variableMeasured: C:eurostat_population_physicalactivity->SV\n"
    "measurementMethod: C:eurostat_population_physicalactivity->"
    "Measurement_Method\n"
    "observationAbout: C:eurostat_population_physicalactivity->geo\n"
    "observationDate: C:eurostat_population_physicalactivity->time\n"
    "scalingFactor: 100\n"
    "value: C:eurostat_population_physicalactivity->observation\n")


file_to_sv_mapping = {
        "hlth_ehis_pe9e": "'Percent_'+df['physact']+'_'+"\
            "'HealthEnhancingPhysicalActivity_In_Count_Person_'+"\
            "df['isced11']+'_'+df['sex']",
        "hlth_ehis_pe9i": "'Percent_' + df['physact'] + '_' +"\
        "'HealthEnhancingPhysicalActivity'+ '_In_Count_Person_' + df['sex']"\
        "+ '_' + df['quant_inc']",
        "hlth_ehis_pe9u": "'Percent_' + df['physact'] + '_HealthEnhancingPhysicalActivity'+"\
        "'_In_Count_Person_' + df['deg_urb'] + '_' + df['sex']",
        "hlth_ehis_pe1e": "'Percent_' + 'WorkRelatedPhysicalActivity' + '_' + df['levels']+"\
        "'_In_Count_Person_' + df['isced11'] + '_'+ df['sex']",
        "hlth_ehis_pe1i": "'Percent_' + 'WorkRelatedPhysicalActivity' + '_' + df['levels']+"\
        "'_In_Count_Person_' + df['sex'] + '_' + df['quant_inc']",
        "hlth_ehis_pe1u": "'Percent_' + 'WorkRelatedPhysicalActivity_' + df['levels']"\
        "+ '_In_Count_Person_' + df['deg_urb'] + '_' + df['sex']",
        "hlth_ehis_pe3e": "'Percent_' + df['physact'] + '_NonWorkRelatedPhysicalActivity'+"\
        "'_In_Count_Person_' + df['isced11'] + '_' + df['sex']",
        "hlth_ehis_pe3i": "'Percent_' + df['physact'] + '_NonWorkRelatedPhysicalActivity'+"\
        "'_In_Count_Person_' + df['sex'] + '_' + df['quant_inc']",
        "hlth_ehis_pe3u" : "'Percent_' + df['physact'] + '_' + 'NonWorkRelatedPhysical'+"\
        "'Activity_In_Count_Person_' + df['deg_urb'] + '_'+df['sex']",
        "hlth_ehis_pe2e": "'Percent_' + df['duration'] + '_' + 'HealthEnhancingPhysical'+"\
        "'Activity_In_Count_Person_' + df['isced11'] + '_' + df['sex']",
        "hlth_ehis_pe2i": "'Percent_' + df['duration'] + '_HealthEnhancingPhysical'+"\
        "'Activity_In_Count_Person_' + df['sex'] + '_' + df['quant_inc']",
        "hlth_ehis_pe2u": "'Percent_' + df['duration'] + '_HealthEnhancingPhysicalActivity'"\
        "+ '_In_Count_Person_' + df['deg_urb'] + '_' + df['sex']",
        "hlth_ehis_pe9b": "'Percent_' + df['physact'] + '_HealthEnhancingPhysicalActivity'+"\
        "'_In_Count_Person_' + df['sex'] + '_' + df['c_birth']",
        "hlth_ehis_pe9c":"'Percent_' + df['physact'] + '_HealthEnhancingPhysicalActivity'+"\
        "'_In_Count_Person_' + df['citizen'] + '_' + df['sex']",
        "hlth_ehis_pe9d":"'Percent_' + df['physact'] + '_HealthEnhancingPhysicalActivity'+"\
        "'_In_Count_Person_' + df['sex'] + '_' + df['lev_limit']",
        "hlth_ehis_pe2m":"'Percent_' + df['duration'] + '_NonWorkRelatedPhysicalActivity'+"\
        "'_In_Count_Person_' + df['sex'] + '_' + df['bmi']",
        "hlth_ehis_de9":"'Percent_' + df['isced11'] + '_PhysicalActivity' +"\
        "'_In_Count_Person_' + df['sex']",
        "hlth_ehis_pe6e":"'Percent_' + 'AtLeast30MinutesPerDay' + '_WalkingOrCycling_' +"\
        "'PhysicalActivity' + '_In_Count_Person_' + df['isced11'] +"\
        "'_' + df['sex']"
}


class EuroStatPhysicalActivity:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
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
        # pylint: disable=R0912
        # pylint: disable=R0915
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = healthbehavior = exercise = ''
            residence = activity = duration = countryofbirth = citizenship = ''
            lev_limit = bmi = sv_name = frequency = ''

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
                if "PhysicalActivity" in prop:
                    healthbehavior = "\nhealthBehavior: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Male" in prop or "Female" in prop:
                    gender = "\ngender: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Aerobic" in prop or "MuscleStrengthening" in prop \
                    or "Walking" in prop or "Cycling" in prop:
                    exercise = "\nexerciseType: dcs:" + prop.replace("Or", "__")
                    sv_name = sv_name + prop + ", "
                elif "Education" in prop:
                    education = "\neducationalAttainment: dcs:" + \
                        prop.replace("EducationalAttainment","")\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "Percentile" in prop:
                    incomequin = "\nincome: ["+prop.replace("IncomeOf","")\
                        .replace("To"," ").replace("Percentile"," Percentile")\
                        +"]"
                    sv_name = sv_name + prop.replace("Of","Of ")\
                        .replace("To"," To ") + ", "
                elif "Urban" in prop or "Rural" in prop:
                    residence = "\nplaceOfResidenceClassification: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Limitation" in prop:
                    lev_limit = "\nglobalActivityLimitationindicator: dcs:"\
                        + prop
                    sv_name = sv_name + prop + ", "
                elif "ModerateActivity" in prop or "HeavyActivity" in prop\
                    or "NoActivity" in prop:
                    activity = "\nphysicalActivityEffortLevel: dcs:"\
                    + prop.replace("ModerateActivityOrHeavyActivity",
                        "ModerateActivityLevel__HeavyActivity")+"Level"
                    sv_name = sv_name + prop + ", "
                elif "AtLeast30MinutesPerDay" in prop:
                    frequency = "\nactivityFrequency: dcs:" + prop
                    sv_name = sv_name + prop + ", "
                elif "Minutes" in prop:
                    sv_name = sv_name + prop + ", "
                    if "OrMoreMinutes" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("OrMoreMinutes","") + " - Minute]"
                    elif "To" in prop:
                        duration = "\nactivityDuration: [" + prop.replace\
                            ("Minutes", "").replace("To", " ") + " Minute]"
                    else:
                        duration = "\nactivityDuration: [Minute " +\
                            prop.replace("Minutes","") + "]"
                elif "ForeignBorn" in prop or "Native" in prop:
                    countryofbirth = "\nnativity: dcs:" + \
                        prop.replace("CountryOfBirth","")
                    sv_name = sv_name + prop + ", "
                elif "Citizen" in prop:
                    citizenship = "\ncitizenship: dcs:" + \
                        prop.replace("Citizenship","")
                    sv_name = sv_name + prop + ", "
                elif "weight" in prop or "Normal" in prop \
                    or "Obese" in prop or "Obesity" in prop:
                    bmi = "__" + prop
                    healthbehavior = healthbehavior + bmi
                    sv_name = sv_name + prop + ", "
            # Making the changes to the SV Name,
            # Removing any extra commas, with keyword and
            # adding Population in the end
            sv_name = sv_name.replace(", Among", " Among")
            sv_name = sv_name.rstrip(', ')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""
            sv_name = sv_name.replace("To299", "To 299").replace(
                "To149",
                "To 149").replace("ACitizen",
                                  "A Citizen").replace("Least30", "Least 30")

            final_mcf_template += _MCF_TEMPLATE.format(pv1=sv,
                                                       pv14=sv_name,
                                                       pv2=denominator,
                                                       pv3=incomequin,
                                                       pv4=education,
                                                       pv5=healthbehavior,
                                                       pv6=exercise,
                                                       pv7=residence,
                                                       pv8=activity,
                                                       pv9=duration,
                                                       pv10=gender,
                                                       pv11=countryofbirth,
                                                       pv12=citizenship,
                                                       pv13=lev_limit,
                                                       pv15=frequency) + "\n"

        # Writing Genereated MCF to local path.
        with open(self._mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))
        # pylint: enable=R0914
        # pylint: enable=R0912
        # pylint: enable=R0915
    
    def parse_file(self, file_name: str, df: pd.DataFrame) -> pd.DataFrame:
        split_columns = df.columns.values.tolist()[0]
        df = _split_column(df, split_columns)
        split_columns = split_columns.replace('isced97', 'isced11')\
            .replace('geo\time','geo').replace('geo\\time','geo')\
            .replace('time\geo','time').replace('time\\geo','time')
        df.rename(columns={
            'geo\time': 'geo',
            'geo\\time': 'geo',
            'time\geo': 'time',
            'time\\geo': 'time',
            'isced97': 'isced11'
        },
                  inplace=True)
        df = df[df['age'] == 'TOTAL']

        for col in [
                'sex', 'quant_inc', 'frequenc', 'isced11', 'deg_urb','bmi','duration',
                'c_birth', 'citizen', 'physact', 'lev_limit', 'levels'
        ]:
            if col in df.columns.values.tolist():
                df = _replace_col_values(df, col)

        df['SV'] = eval(file_to_sv_mapping[file_name])

        split_columns_list = split_columns.split(',')
        if 'time' in split_columns_list:
            split_columns_list.remove('time')
            id_vars = ['SV', 'time']
            var_name = 'geo'
        if 'geo' in split_columns_list:
            split_columns_list.remove('geo')
            id_vars = ['SV', 'geo']
            var_name = 'time'

        df.drop(columns=split_columns_list, inplace=True)
        df = df.melt(id_vars=id_vars,
                     var_name=var_name,
                     value_name='observation')
        df['geo'] = df['geo'].str.strip()
        df['time'] = df['time'].str.strip()
        df = df[df['geo'] != 'EU27_2020']
        df = df[df['geo'] != 'EU28']
        return df

    def process(self):
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.
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
            df = self.parse_file(file_name, df)
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
        # Adding Measurement Method based on a condition, wherever u is found
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
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")
    # Defining Output Files
    csv_name = "eurostat_population_physicalactivity.csv"
    mcf_name = "eurostat_population_physicalactivity.mcf"
    tmcf_name = "eurostat_population_physicalactivity.tmcf"
    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)
    loader = EuroStatPhysicalActivity(ip_files, cleaned_csv_path, mcf_path,\
        tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)

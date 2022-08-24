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
# pylint: disable=wrong-import-position
from common.replacement_functions import (_split_column, _replace_col_values)
from common.sv_config import file_to_sv_mapping

# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)

from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=wrong-import-position

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

_MCF_TEMPLATE = ("Node: dcid:{pv1}\n"
                 "{pv11}\n"
                 "typeOf: dcs:StatisticalVariable\n"
                 "populationType: dcs:Person{pv2}{pv3}{pv4}{pv5}"
                 "{pv6}{pv7}{pv8}{pv9}{pv10}\n"
                 "statType: dcs:measuredValue\n"
                 "measuredProperty: dcs:count\n")

_TMCF_TEMPLATE = ("Node: E:eurostat_population_{import_name}->E0\n"
                  "typeOf: dcs:StatVarObservation\n"
                  "variableMeasured: C:eurostat_population_{import_name}->SV\n"
                  "measurementMethod: C:eurostat_population_{import_name}->"
                  "Measurement_Method\n"
                  "observationAbout: C:eurostat_population_{import_name}->geo\n"
                  "observationDate: C:eurostat_population_{import_name}->time\n"
                  "scalingFactor: 100\n"
                  "value: C:eurostat_population_{import_name}->observation\n")


class EuroStat:
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    def __init__(self, input_files: list, csv_file_path: str,
                 mcf_file_path: str, tmcf_file_path: str,
                 import_name: str) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._import_name = import_name

    def _parse_file(self, file_name: str, df: pd.DataFrame,
                    import_name: dict) -> pd.DataFrame:
        split_columns = df.columns.values.tolist()[0]
        df = _split_column(df, split_columns)

        split_columns = split_columns.replace('isced97', 'isced11')\
                .replace('geo\time','geo').replace('geo\\time','geo')\
                .replace('time\geo','time').replace('time\\geo','time')\
                .replace('quantile', 'quant_inc')

        df.rename(columns={
            'geo\time': 'geo',
            'geo\\time': 'geo',
            'time\geo': 'time',
            'time\\geo': 'time',
            'isced97': 'isced11',
            'quantile': 'quant_inc'
        },
                  inplace=True)

        if import_name == "alcohol_consumption":
            split_columns = split_columns.replace('frequenc',
                                                  'frequenc_alcohol')
            df.rename(columns={
                'frequenc': 'frequenc_alcohol',
            }, inplace=True)
        elif import_name == "tobacco_consumption":
            split_columns = split_columns.replace('frequenc',
                                                  'frequenc_tobacco').replace(
                                                      'quantile', 'quant_inc')
            df.rename(columns={
                'frequenc': 'frequenc_tobacco',
                'quantile': 'quant_inc'
            },
                      inplace=True)
        elif import_name == "bmi":
            if 'quant_inc' in df.columns.values.tolist():
                df = df[(~(df['quant_inc'] == 'UNK'))]

        df = df[df['age'] == 'TOTAL']

        for col in [
                'sex', 'quant_inc', 'frequenc', 'frequenc_alcohol',
                'frequenc_tobacco', 'isced11', 'deg_urb', 'bmi', 'duration',
                'c_birth', 'citizen', 'smoking', 'duration', 'physact',
                'lev_limit', 'levels'
        ]:
            if col in df.columns.values.tolist():
                df = _replace_col_values(df, col)

        df['SV'] = eval(file_to_sv_mapping[import_name][file_name])

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
        df = df[df['geo'] != 'EU27_2020']
        df = df[df['geo'] != 'EU28']
        return df

    def process(self) -> list:
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None

        Returns:
            None
        """
        final_df = pd.DataFrame(
            columns=['time', 'geo', 'SV', 'observation', 'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []

        for file_path in self._input_files:
            df = pd.read_csv(file_path, sep='\t', header=0)
            file_name = file_path.split("/")[-1][:-4]
            df.columns = df.columns.str.strip()
            df = self._parse_file(file_name, df, self._import_name)
            df['SV'] = df['SV'].str.replace('_Total', '')
            final_df = pd.concat([final_df, df])
            sv_list += df["SV"].to_list()

        final_df = final_df.sort_values(by=['time', 'geo', 'SV', 'observation'])
        final_df = final_df.drop_duplicates(subset=['time', 'geo', 'SV'],
                                            keep='first')
        final_df['observation'] = final_df['observation'].astype(
            str).str.strip()
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
        #   country/BEL
        #   Percent_AlcoholConsumption_Daily_In_Count_Person
        #   14.2 u,
        # so measurement method for all 2008, 2014 and 2019 years shall be made
        # low reliability.
        final_df['Measurement_Method'] = np.where(
            final_df['info'].isin(u_rows),
            'EurostatRegionalStatistics_LowReliability',
            'EurostatRegionalStatistics')
        derived_df = final_df[final_df['observation'].astype(str).str.contains(
            'd')]
        u_rows = list(derived_df['SV'] + derived_df['geo'])
        final_df['info'] = final_df['SV'] + final_df['geo']
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
        final_df.drop(columns=['info'], inplace=True)
        final_df['observation'] = (
            final_df['observation'].astype(str).str.replace(
                ':', '').str.replace(' ',
                                     '').str.replace('u',
                                                     '').str.replace('d', ''))
        final_df['observation'] = pd.to_numeric(final_df['observation'],
                                                errors='coerce')
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        final_df.to_csv(self._cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        return sv_list

    def generate_mcf(self, sv_list) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            sv_list (list) : List of DataFrame Columns

        Returns:
            None
        """
        # pylint: disable=R0914
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            incomequin = gender = education = frequenc_alcohol =\
                healthbehavior = residence = countryofbirth = citizenship =\
                    sv_name = ''

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
                    frequenc_alcohol = "\nactivityFrequency: dcs:" + prop\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
                elif "NeverOrNotInTheLast12Months" in\
                    prop or "EveryWeek" in prop or "AtLeastOnceAWeek" in prop\
                    or "NeverOrOccasional" in prop:
                    frequenc_alcohol = "\nactivityFrequency: dcs:" + prop\
                        .replace("Or","__")
                    sv_name = sv_name + prop + ", "
            sv_name = sv_name + "Among "
            for prop in sv_prop1:
                if prop in ["Count", "Person"]:
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

            final_mcf_template += _MCF_TEMPLATE.format(
                pv1=sv,
                pv11=sv_name,
                pv2=denominator,
                pv3=healthbehavior,
                pv4=gender,
                pv5=frequenc_alcohol,
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

    def generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template.

        Args:
            None

        Returns:
            None
        """
        tmcf = _TMCF_TEMPLATE.format(import_name=self._import_name)
        # Writing Genereated TMCF to local path.
        with open(self._tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf.rstrip('\n'))

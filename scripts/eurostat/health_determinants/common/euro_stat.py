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
This Python module is generalized to work with different Eurostat import such as
Physical Activity, BMI, Alcohol Consumption, Tobacco Consumption...

EuroStat class in this module provides methods to generate processed CSV, MCF &
TMCF files.

_propety_correction() and _sv_name_correction() are abstract methods, these
method needs to implemented by Subclasses.
"""
import os
import sys
import re
import pandas as pd
import numpy as np
from absl import flags

# For import common.replacement_functions
_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from common.replacement_functions import (split_column, replace_col_values)
from common.sv_config import file_to_sv_mapping

# For import util.alpha2_to_dcid
_COMMON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-order
from util.alpha2_to_dcid import COUNTRY_MAP
# pylint: enable=wrong-import-position
# pylint: enable=wrong-import-order

_FLAGS = flags.FLAGS
default_input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")

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
    EuroStat is a base class which provides common implementation for generating
    CSV, MCF and tMCF files.
    """
    # Below variables will be initialized by sub-class (import specific)
    _import_name = ""
    _mcf_template = ""
    _sv_value_to_property_mapping = {}
    _sv_properties_template = {}
    _sv_properties = {}

    def __init__(self,
                 input_files: list,
                 csv_file_path: str = None,
                 mcf_file_path: str = None,
                 tmcf_file_path: str = None) -> None:
        self._input_files = input_files
        self._cleaned_csv_file_path = csv_file_path
        self._mcf_file_path = mcf_file_path
        self._tmcf_file_path = tmcf_file_path
        self._df = pd.DataFrame()

    # pylint: disable=pointless-statement
    # pylint: disable=no-self-use
    # pylint: disable=unused-argument

    def set_cleansed_csv_file_path(self, cleansed_csv_file_path: str) -> None:
        self._cleaned_csv_file_path = cleansed_csv_file_path

    def set_mcf_file_path(self, mcf_file_path: str) -> None:
        self._mcf_file_path = mcf_file_path

    def set_tmcf_file_path(self, tmcf_file_path: str) -> None:
        self._tmcf_file_path = tmcf_file_path

    def _property_correction(self):
        """
        Abstract method
        Sub class will override this method to standardize / correct proprties 
        of an SV.

        _sv_properties state will be modified in through this method.
        """
        pass

    def _sv_name_correction(self, sv_name: str) -> str:
        """
        Abstract method
        Sub class will override this method, to correct / standardize SV names 
        constructed from data files.
        """
        pass

    def _rename_frequency_column(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    # pylint: enable=pointless-statement
    # pylint: enable=unused-argument
    def _parse_file(self, file_name: str, df: pd.DataFrame,
                    import_name: dict) -> pd.DataFrame:
        """
        Parsing the input file, loading to dataframe and cleaning it.

        Args:
            file_name (str): name of the input file.
            df (pd.DataFrame):
            import_name (dictonary): dictonary of all eurostat imports.

        Returns:
            df (pd.DataFrame):
        """
        original_df_columns = df.columns
        df = split_column(df, df.columns.values.tolist()[0])

        df.rename(columns={
            r'geo\time': 'geo',
            r'time\geo': 'time',
            'isced97': 'isced11',
            'quantile': 'quant_inc'
        },
                  inplace=True)

        df = self._rename_frequency_column(df)

        if 'quant_inc' in df.columns.values.tolist():
            df = df[(~(df['quant_inc'] == 'UNK'))]

        df = df[df['age'] == 'TOTAL']
        df = replace_col_values(df)

        if file_name in file_to_sv_mapping[import_name]:
            df['SV'] = eval(file_to_sv_mapping[import_name][file_name])
        else:
            print(
                '#########\nERROR: File (', file_name,
                ') to SV mapping missing',
                '\nAdd a File - SV mapping statement in common/sv_config.py.',
                '\n#########')
            exit(1)

        del_columns = list(df.columns.difference(original_df_columns))
        if 'time' in del_columns:
            del_columns.remove('time')
            id_vars = ['SV', 'time']
            var_name = 'geo'
        elif 'geo' in del_columns:
            del_columns.remove('geo')
            id_vars = ['SV', 'geo']
            var_name = 'time'
        del_columns.remove('SV')

        df.drop(columns=del_columns, inplace=True)

        df = df.melt(id_vars=id_vars,
                     var_name=var_name,
                     value_name='observation')
        df = df[df['geo'] != 'EU27_2020']
        df = df[df['geo'] != 'EU28']
        return df

    def generate_csv(self) -> pd.DataFrame:
        """
        This Method calls the required methods to generate
        cleaned CSV, MCF, and TMCF file.

        Args:
            None

        Returns:
            df (pd.DataFrame)
        """
        final_df = pd.DataFrame(
            columns=['time', 'geo', 'SV', 'observation', 'Measurement_Method'])
        # Creating Output Directory
        output_path = os.path.dirname(self._cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)

        dfs = []
        for file_path in self._input_files:
            df = pd.read_csv(file_path, sep='\t', header=0)
            file_name = file_path.split("/")[-1][:-4]
            df.columns = df.columns.str.strip()
            df = self._parse_file(file_name, df, self._import_name)
            df['SV'] = df['SV'].str.replace('_Total', '')
            df['SV'] = df['SV'].str.replace('_TOTAL', '')
            dfs.append(df)
        final_df = pd.concat(dfs, axis=0)

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
        for drop_obs_char in [':', ' ', 'u', 'd', 'c']:
            final_df['observation'] = final_df['observation'].astype(
                str).str.replace(drop_obs_char, '')
        final_df['observation'] = pd.to_numeric(final_df['observation'])
        final_df = final_df.replace({'geo': COUNTRY_MAP})
        final_df = final_df.sort_values(by=['geo', 'SV'])
        final_df['observation'].replace('', np.nan, inplace=True)
        final_df.dropna(subset=['observation'], inplace=True)
        self._df = final_df
        final_df.to_csv(
            self._cleaned_csv_file_path,
            columns=['time', 'geo', 'SV', 'observation', 'Measurement_Method'],
            index=False)
        return self._df

    def generate_mcf(self, df: pd.DataFrame = None) -> None:
        """
        This method generates MCF file w.r.t
        dataframe headers and defined MCF template

        Args:
            df (pd.DataFrame) :

        Returns:
            None
        """
        # pylint: disable=R0914
        if df is not None:
            self._df = df

        final_mcf_template = ""
        sv_list = list(set(self._df["SV"].to_list()))
        sv_list.sort()

        for sv in sv_list:
            self._sv_properties = self._sv_properties_template
            self._sv_properties = dict.fromkeys(self._sv_properties, "")
            sv_name = ""

            sv_temp = sv.split("_In_")
            denominator = "\nmeasurementDenominator: dcs:" + sv_temp[1]
            sv_prop = sv_temp[0].split("_")
            sv_prop.append("Among")
            sv_prop.extend(sv_temp[1].split("_"))

            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if prop in ["Percent"]:
                    sv_name = sv_name + "Percentage "
                else:
                    sv_name = sv_name + prop + ", "

                for p in self._sv_value_to_property_mapping.keys():
                    if p in prop:
                        sv_property = self._sv_value_to_property_mapping[p]
                        self._sv_properties[
                            sv_property] = self._sv_properties_template[
                                sv_property].format(property_value=prop)

            sv_name = sv_name.replace(", Among,",
                                      "Among").rstrip(', ').rstrip('with')
            # Adding spaces before every capital letter,
            # to make SV look more like a name.
            sv_name = re.sub(r"(\w)([A-Z])", r"\1 \2", sv_name)
            sv_name = "name: \"" + sv_name + " Population\""

            self._property_correction()
            sv_name = self._sv_name_correction(sv_name)

            mcf_template_parameters = {
                "sv": sv,
                "sv_name": sv_name,
                "denominator": denominator
            }

            mcf_template_parameters.update(self._sv_properties)
            final_mcf_template += self._mcf_template.format(
                **mcf_template_parameters) + "\n"

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

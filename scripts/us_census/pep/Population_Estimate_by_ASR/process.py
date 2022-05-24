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
import pandas as pd

from absl import app
from absl import flags
from national_1900_1959 import national1900
from national_1960_1979 import national1960
from national_1980_1989 import national1980
from national_1990_1999 import national1990
from national_2000_2010 import national2000
from national_2010_2019 import national2010
from state_1970_1979 import state1970
from state_1990_2000 import state1990
from state_2000_2010 import state2000
from state_2010_2020 import state2010
from county_1970_1979 import county1970
from county_1980_1989 import county1980
from county_1990_2000 import county1990
from county_2000_2010 import county2000
from county_2010_2020 import county2010

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

FLAGS = flags.FLAGS
default_input_path = os.path.dirname(
    os.path.abspath(__file__)) + os.sep + "input_data"
flags.DEFINE_string("input_path", default_input_path, "Import Data File's List")


class USCensusPEPByASR:
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

    def __generate_mcf(self, sv_list) -> None:
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
populationType: dcs:Person{}{}{}
statType: dcs:measuredValue
measuredProperty: dcs:count
"""
        final_mcf_template = ""
        for sv in sv_list:
            if "Total" in sv:
                continue
            age = ''
            gender = ''
            race = ''
            sv_prop = sv.split("_")
            for prop in sv_prop:
                if prop in ["Count", "Person"]:
                    continue
                if "Years" in prop:
                    if "OrMoreYears" in prop:
                        age = "\nage: [" + prop.replace("OrMoreYears",
                                                        "") + " - Years]" + "\n"
                    elif "To" in prop:
                        age = "\nage: [" + prop.replace("Years", "").replace(
                            "To", " ") + " Years]" + "\n"
                    else:
                        age = "\nage: [Years " + prop.replace("Years",
                                                              "") + "]" + "\n"
                elif "Male" in prop or "Female" in prop:
                    gender = "gender: dcs:" + prop
                else:

                    if "race" in race:
                        race = race.strip() + "__" + prop + "\n"
                    else:
                        race = "race: dcs:" + prop + "\n"
            if gender == "":
                race = race.strip()
            final_mcf_template += mcf_template.format(sv, age, race,
                                                      gender) + "\n"
        # Writing Genereated MCF to local path.
        with open(self.mcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(final_mcf_template.rstrip('\n'))

    def __generate_tmcf(self) -> None:
        """
        This method generates TMCF file w.r.t
        dataframe headers and defined TMCF template
        Arguments:
            df_cols (list) : List of DataFrame Columns
        Returns:
            None
        """
        tmcf_template = """Node: E:USA_Population_ASR->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:USA_Population_ASR->SVs
measurementMethod: C:USA_Population_ASR->Measurement_Method
observationAbout: C:USA_Population_ASR->geo_ID
observationDate: C:USA_Population_ASR->Year
observationPeriod: \"P1Y\"
value: C:USA_Population_ASR->observation 
"""

        # Writing Genereated TMCF to local path.
        with open(self.tmcf_file_path, 'w+', encoding='utf-8') as f_out:
            f_out.write(tmcf_template.rstrip('\n'))

    def process(self):
        """
        This Method calls the required methods to generate cleaned CSV,
        MCF, and TMCF file
        """

        final_df = pd.DataFrame()
        # Creating Output Directory
        output_path = os.path.dirname(self.cleaned_csv_file_path)
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        sv_list = []
        for file_path in self.input_files:
            data_df = pd.read_csv(file_path)
            final_df = pd.concat([final_df, data_df])
            sv_list += data_df["SVs"].to_list()
        final_df.drop(columns=['Unnamed: 0'], inplace=True)
        final_df = final_df.dropna()
        final_df['Year'] = final_df['Year'].astype(float).astype(int)
        final_df = final_df.sort_values(by=['Year', 'geo_ID'])
        final_df.to_csv(self.cleaned_csv_file_path, index=False)
        sv_list = list(set(sv_list))
        sv_list.sort()
        self.__generate_mcf(sv_list)
        self.__generate_tmcf()


def main(_):
    input_path = FLAGS.input_path
    if not os.path.exists(input_path):
        os.mkdir(input_path)
    # Running the fuctions in individual files by Year and Area
    national1900()
    national1960()
    national1980()
    national1990()
    national2000()
    national2010()
    state1970()
    state1990()
    state2000()
    state2010()
    county1970()
    county1980()
    county1990()
    county2000()
    county2010()

    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]
    data_file_path = os.path.dirname(
        os.path.abspath(__file__)) + os.sep + "output"
    # Defining Output Files
    cleaned_csv_path = data_file_path + os.sep + "USA_Population_ASR.csv"
    mcf_path = data_file_path + os.sep + "USA_Population_ASR.mcf"
    tmcf_path = data_file_path + os.sep + "USA_Population_ASR.tmcf"
    loader = USCensusPEPByASR(ip_files, cleaned_csv_path, mcf_path, tmcf_path)
    loader.process()


if __name__ == "__main__":
    app.run(main)

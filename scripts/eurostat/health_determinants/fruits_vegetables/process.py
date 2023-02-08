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
import pandas as pd

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from common.euro_stat import EuroStat
# pylint: enable=wrong-import-position


class EuroStatFruitsVegetables(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = "fruits_vegetables"

    _mcf_template = ("Node: dcid:{sv}"
                     "\n{sv_name}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "{denominator}"
                     "{education}"
                     "{residence}"
                     "{n_portion}"
                     "{gender}"
                     "{countryofbirth}"
                     "{citizenship}"
                     "{lev_limit}"
                     "{coicop}"
                     "{frequenc_fruitsvegetables}"
                     "{incomequin}"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count\n")

    _sv_properties_template = {
        "education":
            "\neducationalAttainment: dcs:{property_value}",
        "residence":
            "\nplaceOfResidenceClassification: dcs:{property_value}",
        "n_portion":
            "\nconsumptionQuantity: [{property_value}]",
        "gender":
            "\ngender: dcs:{property_value}",
        "countryofbirth":
            "\nnativity: dcs:{property_value}",
        "citizenship":
            "\ncitizenship: dcs:{property_value}",
        "lev_limit":
            "\nglobalActivityLimitationindicator: dcs:{property_value}",
        "frequenc_fruitsvegetables":
            "\nactivityFrequency: dcs:{property_value}",
        "coicop":
            "\nhealthBehavior: dcs:{property_value}",
        "incomequin":
            "\nincome: [{property_value}]",
        "healthbehavior":
            "\healthBehaviour: dcs:{property_value}",
        "healthbehavior_bmi":
            "__{property_value}",
    }

    # mapping values from statvar to mcf property template
    _sv_value_to_property_mapping = {
        "FruitsVegetables": "healthbehavior",
        "Male": "gender",
        "Female": "gender",
        "Education": "education",
        "Percentile": "incomequin",
        "Urban": "residence",
        "Rural": "residence",
        "Limitation": "lev_limit",
        "Daily": "frequenc_fruitsvegetables",
        "Never": "frequenc_fruitsvegetables",
        "AtLeastOnceADay": "frequenc_fruitsvegetables",
        "AtLeastTwiceADay": "frequenc_fruitsvegetables",
        "NeverOrOccasionallyUsage": "frequenc_fruitsvegetables",
        "From1To3TimesAWeek": "frequenc_fruitsvegetables",
        "From4To6TimesAWeek": "frequenc_fruitsvegetables",
        "OnceADay": "frequenc_fruitsvegetables",
        "LessThanOnceAWeek": "frequenc_fruitsvegetables",
        "ForeignBorn": "countryofbirth",
        "Native": "countryofbirth",
        "Percentile": "incomequin",
        "Citizen": "citizenship",
        "weight": "healthbehavior_bmi",
        "Normal": "healthbehavior_bmi",
        "Obese": "healthbehavior_bmi",
        "Obesity": "healthbehavior_bmi",
        "Portion": "n_portion",
        "ConsumptionOf": "coicop",
    }

    # over-ridden parent abstract method
    def _property_correction(self):
        for k, v in self._sv_properties.items():
            if k == "n_portion":
                self._sv_properties[k] = v\
                    .replace("To", " ")\
                    .replace("Portion", " Portion")\
                    .replace("From", "")\
                    .replace("PortionOrMore","")\

            elif k == "incomequin":
                self._sv_properties[k] = v\
                    .replace("To", " ")\
                    .replace("Percentile", " Percentile")\
                    .replace("IncomeOf", "")\

            elif k == "healthbehavior_bmi":
                self._sv_properties["healthbehavior"] += self._sv_properties[
                    "healthbehavior_bmi"]
            elif k == "activity_temp":
                if self._sv_properties["lev_limit"]:
                    self._sv_properties["activity"] = ""
                else:
                    self._sv_properties["activity"] = self._sv_properties[
                        "activity_temp"]

            elif k == "duration_temp" and v:
                if "OrMoreMinutes" in self._sv_properties["duration_temp"]:
                    self._sv_properties[
                        "duration"] = "\nactivityDuration: ["\
                            + self._sv_properties[
                            "duration_temp"].replace("OrMoreMinutes",
                                                     "") + " - Minute]"
                elif "To" in self._sv_properties["duration_temp"]:
                    self._sv_properties[
                        "duration"] = "\nactivityDuration: ["\
                            + self._sv_properties[
                            "duration_temp"].replace("Minutes", "").replace(
                                "To", " ") + " Minute]"
                else:
                    self._sv_properties[
                        "duration"] = "\nactivityDuration: [Minute "\
                            + self._sv_properties[
                            "duration_temp"].replace("Minutes", "") + "]"

            else:
                self._sv_properties["education"] = \
                self._sv_properties["education"].replace("Or","__")
                self._sv_properties["n_portion"] = \
                self._sv_properties["n_portion"].replace("To"," ")
                self._sv_properties["incomequin"] = \
                self._sv_properties["incomequin"].replace("To"," ")
                self._sv_properties["n_portion"] = \
                self._sv_properties["n_portion"].replace("From","")
                self._sv_properties["coicop"] = \
                self._sv_properties["coicop"].replace("Or","__")
                self._sv_properties["frequenc_fruitsvegetables"] = \
                self._sv_properties["frequenc_fruitsvegetables"]\
                    .replace("Atleast","AtLeast")


            self._sv_properties[k] = v\
                .replace("CountryOfBirth","")\
                .replace("Citizenship", "")\
                .replace("IncomeOf", "")\
                .replace("Percentile", " Percentile")\
                .replace("Portion", " Portion")\
                .replace("PortionOrMore","- Portion")\

    # over-ridden parent abstract method
    # pylint: disable=no-self-use
    def _sv_name_correction(self, sv_name: str) -> str:
        return sv_name\
            .replace("Atleast","At Least")\
            .replace("ADay","a Day")\
            .replace("AWeek","a Week")\
            .replace("Last12","Last 12")\
            .replace("ACitizen","a Citizen")\
            .replace("From1","From 1")\
            .replace("From4","From 4")\
            .replace("Portion", " Portions")\
            .replace("To"," To ")\
            .replace("Of","Of ")\
            .replace("  "," ")\
            .replace("weig","weight")

    # pylint: enable=no-self-use
    def _rename_frequency_column(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={'frequenc': 'frequenc_fruitsvegetables'})


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output_files")

    csv_name = "eurostat_population_fruits_vegetables.csv"
    mcf_name = "eurostat_population_fruits_vegetables.mcf"
    tmcf_name = "eurostat_population_fruits_vegetables.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatFruitsVegetables(ip_files, cleaned_csv_path, mcf_path,
                                      tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()

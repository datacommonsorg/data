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

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from common.euro_stat import EuroStat
# pylint: enable=wrong-import-position


class EuroStatPhysicalActivity(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = "physical_activity"

    _mcf_template = ("Node: dcid:{sv}"
                     "\n{sv_name}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "{denominator}"
                     "{incomequin}"
                     "{education}"
                     "{healthbehavior}"
                     "{exercise}"
                     "{residence}"
                     "{activity}"
                     "{duration}"
                     "{gender}"
                     "{countryofbirth}"
                     "{citizenship}"
                     "{lev_limit}"
                     "{frequency}"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count\n")

    _sv_properties_template = {
        "healthbehavior":
            "\nhealthBehavior: dcs:{property_value}",
        "gender":
            "\ngender: dcs:{property_value}",
        "exercise":
            "\nexerciseType: dcs:{property_value}",
        "education":
            "\neducationalAttainment: dcs:{property_value}",
        "incomequin":
            "\nincome: [{property_value}]",
        "residence":
            "\nplaceOfResidenceClassification: dcs:{property_value}",
        "lev_limit":
            "\nglobalActivityLimitationindicator: dcs:{property_value}",
        "activity":
            "",
        "activity_temp":
            "\nphysicalActivityEffortLevel: dcs:{property_value}Level",
        "frequency":
            "\nactivityFrequency: dcs:{property_value}",
        "duration":
            "",
        "duration_temp":
            "{property_value}",
        "countryofbirth":
            "\nnativity: dcs:{property_value}",
        "citizenship":
            "\ncitizenship: dcs:{property_value}",
        "healthbehavior_bmi":
            "__{property_value}",
    }

    _sv_value_to_property_mapping = {
        "PhysicalActivity": "healthbehavior",
        "Male": "gender",
        "Female": "gender",
        "Aerobic": "exercise",
        "MuscleStrengthening": "exercise",
        "Walking": "exercise",
        "Cycling": "exercise",
        "Education": "education",
        "Percentile": "incomequin",
        "Urban": "residence",
        "Rural": "residence",
        "Limitation": "lev_limit",
        "ModerateActivity": "activity_temp",
        "HeavyActivity": "activity_temp",
        "NoActivity": "activity_temp",
        "AtLeast30MinutesPerDay": "frequency",
        "Minutes": "duration_temp",
        "ForeignBorn": "countryofbirth",
        "Native": "countryofbirth",
        "Citizen": "citizenship",
        "weight": "healthbehavior_bmi",
        "Normal": "healthbehavior_bmi",
        "Obese": "healthbehavior_bmi",
        "Obesity": "healthbehavior_bmi",
    }

    # over-ridden parent abstract method
    def _property_correction(self):
        """
        Correcting the property values.
        """
        for k, v in self._sv_properties.items():
            if k == "healthbehavior_bmi":
                self._sv_properties["healthbehavior"] = self._sv_properties[
                    "healthbehavior"].rstrip(
                        "\n") + self._sv_properties["healthbehavior_bmi"]
            elif k == "activity_temp":
                if self._sv_properties["lev_limit"]:
                    self._sv_properties["activity"] = ""
                else:
                    self._sv_properties["activity"] = self._sv_properties[
                        "activity_temp"].replace("ModerateActivityOr",
                                                 "ModerateActivityLevel__")
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
                elif self._sv_properties["frequency"]:
                    self._sv_properties["duration"] = ""
                else:
                    self._sv_properties[
                        "duration"] = "\nactivityDuration: [Minute "\
                            + self._sv_properties[
                            "duration_temp"].replace("Minutes", "") + "]"
            self._sv_properties[k] = v\
                .replace("ModerateActivityOrHeavyActivity","ModerateActivityLevel__HeavyActivityLevel")\
                .replace("Or", "__")\
                .replace("CountryOfBirth","")\
                .replace("Citizenship", "")\
                .replace("Percentile", " Percentile")\
                .replace("IncomeOf", "")\
                .replace("To", " ")\
                .replace("EducationalAttainment","")

    # over-ridden parent abstract method
    # pylint: disable=no-self-use
    def _sv_name_correction(self, sv_name: str) -> str:
        return sv_name\
            .replace("AWeek","A Week")\
            .replace("Last12","Last 12")\
            .replace("ACitizen","A Citizen")\
            .replace("AMonth","A Month")\
            .replace("To299", "To 299")\
            .replace("To149","To 149")\
            .replace("ACitizen","A Citizen")\
            .replace("Least30", "Least 30")\
            .replace("Normalweig", "Normalweight")\
            .replace("Underweig", "Underweight")\
            .replace("Overweig", "Overweight")\
            .replace("To"," To ")\
            .replace("Of","Of ")\
            .replace("  "," ")

    # pylint: enable=no-self-use


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_physicalactivity.csv"
    mcf_name = "eurostat_population_physicalactivity.mcf"
    tmcf_name = "eurostat_population_physicalactivity.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatPhysicalActivity(ip_files, cleaned_csv_path, mcf_path,
                                      tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()

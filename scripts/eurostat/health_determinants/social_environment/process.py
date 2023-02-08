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


class EuroStatSocialEnvironment(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = "social_environment"

    _mcf_template = ("Node: dcid:{sv}"
                     "\n{sv_name}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "{denominator}"
                     "{lev_perc}"
                     "{education}"
                     "{healthbehavior}"
                     "{residence}"
                     "{assist}"
                     "{gender}"
                     "{countryofbirth}"
                     "{lev_limit}"
                     "{citizenship}"
                     "{frequency}"
                     "{benificiary}"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count\n")

    _sv_properties_template = {
        "healthbehavior":
            "\nhealthBehavior: dcs:{property_value}",
        "gender":
            "\ngender: dcs:{property_value}",
        "education":
            "\neducationalAttainment: dcs:{property_value}",
        "lev_perc":
            "\nsocialSupportLevel: dcs:{property_value}",
        "residence":
            "\nplaceOfResidenceClassification: dcs:{property_value}",
        "lev_limit":
            "\nglobalActivityLimitationindicator: dcs:{property_value}",
        "frequency":
            "\nactivityFrequency: dcs:{property_value}",
        "countryofbirth":
            "\nnativity: dcs:{property_value}",
        "citizenship":
            "\ncitizenship: dcs:{property_value}",
        "assist":
            "\nsocialSupportType: dcs:{property_value}",
        "benificiary":
            "\nsocialSupportBeneficiaryType: dcs:{property_value}"
    }

    _sv_value_to_property_mapping = {
        "SocialEnvironment": "healthbehavior",
        "Male": "gender",
        "Female": "gender",
        "Education": "education",
        "Strong": "lev_perc",
        "Intermediate": "lev_perc",
        "Poor": "lev_perc",
        "Urban": "residence",
        "Rural": "residence",
        "Limitation": "lev_limit",
        "AtLeastOnceAWeek": "frequency",
        "ForeignBorn": "countryofbirth",
        "EU28": "countryofbirth",
        "Native": "countryofbirth",
        "Citizen": "citizenship",
        "InformalCare": "assist",
        "Relatives": "benificiary"
    }

    # over-ridden parent abstract method
    def _property_correction(self):
        """
        Correcting the property values.
        """
        for k, v in self._sv_properties.items():
            if k == "healthbehavior_socialenvironment":
                self._sv_properties["healthbehavior"] = self._sv_properties[
                    "healthbehavior"].rstrip("\n") +\
                    self._sv_properties["healthbehavior_socialenvironment"]
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
            else:
                self._sv_properties["education"] = \
                self._sv_properties["education"].replace("Or","__")

            self._sv_properties[k] = v\
                .replace("CountryOfBirth","")\
                .replace("Citizenship", "")\

    # over-ridden parent abstract method
    # pylint: disable=no-self-use
    def _sv_name_correction(self, sv_name: str) -> str:
        return sv_name\
            .replace("AWeek","A Week")\
            .replace("ACitizen","A Citizen")\
            .replace(', Among"', '"')

    # pylint: enable=no-self-use


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output_files")

    csv_name = "eurostat_population_social_environment.csv"
    mcf_name = "eurostat_population_social_environment.mcf"
    tmcf_name = "eurostat_population_social_environment.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatSocialEnvironment(ip_files, cleaned_csv_path, mcf_path,
                                       tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()

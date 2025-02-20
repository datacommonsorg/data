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
from absl import app, flags, logging

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from common.euro_stat import EuroStat
# pylint: enable=wrong-import-position
from common import import_download_details, download

_FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')


class EuroStatBMI(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    _mcf_template = ("Node: dcid:{sv}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count"
                     "{denominator}"
                     "{healthbehavior}"
                     "{education}"
                     "{exercise}"
                     "{residence}"
                     "{activity}"
                     "{duration}"
                     "{citizenship}"
                     "{gender}"
                     "{incomequin}"
                     "{countryofbirth}"
                     "{lev_limit}"
                     "{frequency}"
                     "\n{sv_name}\n")

    # Temporary keys (activity_temp and duration_temp are used here.
    # As we do correction to property in _property_correction method, we cannot
    # replace value for activity and duration key at the same time when we are
    # reading it in loop. Hence temp keys are used.
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
        "ForeignWithin": "citizenship",
        "ForeignOutside": "citizenship",
        "Citizen": "citizenship",
        "weight": "healthbehavior",
        "Normal": "healthbehavior",
        "Obese": "healthbehavior",
        "Obesity": "healthbehavior",
    }

    @staticmethod
    def download_data(import_name):
        """Downloads raw data from Eurostat website and stores it in instance data frame.
        
            Args:
            import_name(str): A string representing the import name.
            
            Returns:True
            
        """
        download_details = import_download_details.download_details[import_name]
        download_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', import_name,
                         "input_files"))
        os.makedirs(download_path, exist_ok=True)

        for file in download_details["filenames"]:
            download_files_urls = [
                download_details["input_url"] + str(file) +
                download_details["file_extension"]
            ]
            download.download_files(download_files_urls, download_path)
        return True

    # over-ridden parent abstract method
    def _property_correction(self):
        """
        Correcting the property values.
        """
        for k, v in self._sv_properties.items():
            if k == "healthbehavior_bmi":
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
            self._sv_properties[k] = v\
                .replace("Or", "__")\
                .replace("CountryOfBirth","")\
                .replace("Citizenship", "")\
                .replace("Percentile", " Percentile")\
                .replace("IncomeOf", "")\
                .replace("To", " ")\
                .replace("EducationalAttainment","")\
                .replace("ModerateActivityOrHeavyActivity",
                "ModerateActivityLevel__HeavyActivity")

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
            .replace("To"," To ")\
            .replace("Of","Of ")\
            .replace("Normalweight","Normal Weight")\
            .replace(" Among Population","")\
            .replace(" Population","")\
            .replace('name: "','name: "Population: ')\
            .replace("  "," ")

    # pylint: enable=no-self-use


def main(_):
    mode = _FLAGS.mode
    global import_name
    import_name = "bmi"
    if mode == "" or mode == "download":
        EuroStatBMI.download_data(import_name)
    if mode == "" or mode == "process":
        try:
            input_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "input_files")
            ip_files = os.listdir(input_path)
            ip_files = [input_path + os.sep + file for file in ip_files]

            # Defining Output Files
            data_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "output")

            csv_name = "eurostat_population_bmi.csv"
            mcf_name = "eurostat_population_bmi.mcf"
            tmcf_name = "eurostat_population_bmi.tmcf"

            cleaned_csv_path = os.path.join(data_file_path, csv_name)
            mcf_path = os.path.join(data_file_path, mcf_name)
            tmcf_path = os.path.join(data_file_path, tmcf_name)

            loader = EuroStatBMI(ip_files, cleaned_csv_path, mcf_path,
                                 tmcf_path, import_name)
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()
            logging.info("Processing completed!")
        except Exception as e:
            logging.fatal(f'Processing error - {e}')


if __name__ == "__main__":
    app.run(main)

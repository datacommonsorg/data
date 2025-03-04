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
from absl import app, flags, logging

_COMMON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(1, _COMMON_PATH)
# pylint: disable=wrong-import-position
from common.euro_stat import EuroStat
# pylint: enable=wrong-import-position
from common import import_download_details, download

_FLAGS = flags.FLAGS
flags.DEFINE_string('mode', '', 'Options: download or process')


class EuroStatTobaccoConsumption(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """

    _mcf_template = ("Node: dcid:{sv}"
                     "\n{sv_name}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "{denominator}"
                     "{frequenc_tobacco}"
                     "{gender}"
                     "{activity}"
                     "{education}"
                     "{incomequin}"
                     "{residence}"
                     "{countryofbirth}"
                     "{citizenship}"
                     "{substance}"
                     "{quantity}"
                     "{history}"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count\n")

    _sv_properties_template = {
        "activity": "\nhealthBehavior: dcs:{property_value}",
        "frequenc_tobacco": "\nactivityFrequency: dcs:{property_value}",
        "quantity": "\nconsumptionQuantity: {property_value}",
        "substance": "\ntobaccoUsageType: dcs:{property_value}",
        "history": "\nactivityDuration: {property_value}",
        "gender": "\ngender: dcs:{property_value}",
        "education": "\neducationalAttainment: dcs:{property_value}",
        "incomequin": "\nincome: [{property_value}]",
        "residence": "\nplaceOfResidenceClassification: dcs:{property_value}",
        "countryofbirth": "\nnativity: dcs:{property_value}",
        "citizenship": "\ncitizenship: dcs:{property_value}",
    }

    _sv_value_to_property_mapping = {
        "TobaccoSmoking": "activity",
        "NonSmoker": "activity",
        "ExposureToTobaccoSmoke": "activity",
        "FormerSmoker": "activity",
        "Daily": "frequenc_tobacco",
        "Occasional": "frequenc_tobacco",
        "AtLeastOneHourPerDay": "frequenc_tobacco",
        "LessThanOneHourPerDay": "frequenc_tobacco",
        "LessThanOnceAWeek": "frequenc_tobacco",
        "AtLeastOnceAWeek": "frequenc_tobacco",
        "RarelyOrNever": "frequenc_tobacco",
        "LessThan20CigarettesPerDay": "quantity",
        "20OrMoreCigarettesPerDay": "quantity",
        "DailyCigaretteSmoker20OrMorePerDay": "quantity",
        "DailyCigaretteSmokerLessThan20PerDay": "quantity",
        "Cigarette": "substance",
        "ECigarettes": "substance",
        "LessThan1Year": "history",
        "From1To5Years": "history",
        "From5To10Years": "history",
        "10YearsOrOver": "history",
        "Male": "gender",
        "Female": "gender",
        "Education": "education",
        "Percentile": "incomequin",
        "Urban": "residence",
        "SemiUrban": "residence",
        "Rural": "residence",
        "ForeignBorn": "countryofbirth",
        "Native": "countryofbirth",
        "WithinEU28AndNotACitizen": "citizenship",
        "CitizenOutsideEU28": "citizenship",
        "Citizen": "citizenship",
        "NotACitizen": "citizenship",
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
            if k == "incomequin":
                self._sv_properties[k] = v\
                    .replace("To", " ")\
                    .replace("Percentile", " Percentile")\
                    .replace("IncomeOf", "")
            elif k == "quantity":
                self._sv_properties[k] = v\
                    .replace("LessThan20CigarettesPerDay","[- 20 Cigarettes]")\
                    .replace("20OrMoreCigarettesPerDay","[20 - Cigarettes]")\
                    .replace("DailyCigaretteSmoker20OrMorePerDay",
                        "[20 - Cigarettes]")\
                    .replace("DailyCigaretteSmokerLessThan20PerDay",
                        "[- 20 Cigarettes]")
            else:
                self._sv_properties[k] = v\
                    .replace("10YearsOrOver","[10 - Years]")\
                    .replace("Or", "__")\
                    .replace("CountryOfBirth","")\
                    .replace("Citizenship", "")\
                    .replace("LessThan1Year","[- 1 Year]")\
                    .replace("From1To5Years","[Years 1 5]")\
                    .replace("From5To10Years","[Years 5 10]")

    # over-ridden parent abstract method
    # pylint: disable=no-self-use
    def _sv_name_correction(self, sv_name: str) -> str:
        return sv_name\
            .replace("AWeek","A Week")\
            .replace("Last12","Last 12")\
            .replace("ACitizen","A Citizen")\
            .replace("From","From ")\
            .replace("Years"," Years")\
            .replace("To"," To ")\
            .replace("To  ","To ")\
            .replace("To bacco","Tobacco")\
            .replace("Of","Of ")\
            .replace("Than","Than ")\
            .replace("  "," ")\
            .replace(", Tobacco Products", "")\
            .replace(", Never Used","")\
            .replace(", Formerly","")

    # over-ridden parent abstract method
    def _rename_frequency_column(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={'frequenc': 'frequenc_tobacco'})

    # pylint: enable=no-self-use


def main(_):
    mode = _FLAGS.mode
    global import_name
    import_name = "tobacco_consumption"
    if mode == "" or mode == "download":
        EuroStatTobaccoConsumption.download_data(import_name)
    if mode == "" or mode == "process":
        try:
            input_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "input_files")
            ip_files = os.listdir(input_path)
            ip_files = [input_path + os.sep + file for file in ip_files]

            # Defining Output Files
            data_file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "output")

            csv_name = "eurostat_population_tobaccoconsumption.csv"
            mcf_name = "eurostat_population_tobaccoconsumption.mcf"
            tmcf_name = "eurostat_population_tobaccoconsumption.tmcf"

            cleaned_csv_path = os.path.join(data_file_path, csv_name)
            mcf_path = os.path.join(data_file_path, mcf_name)
            tmcf_path = os.path.join(data_file_path, tmcf_name)

            loader = EuroStatTobaccoConsumption(ip_files, cleaned_csv_path,
                                                mcf_path, tmcf_path,
                                                import_name)
            loader.generate_csv()
            loader.generate_mcf()
            loader.generate_tmcf()
            logging.info("Processing completed!")
        except Exception as e:
            logging.fatal(f'Processing error - {e}')


if __name__ == "__main__":
    app.run(main)

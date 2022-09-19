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


class EuroStatAlcoholConsumption(EuroStat):
    """
    This Class has requried methods to generate Cleaned CSV,
    MCF and TMCF Files.
    """
    _import_name = "alcohol_consumption"

    _mcf_template = ("Node: dcid:{sv}"
                     "\n{sv_name}"
                     "\ntypeOf: dcs:StatisticalVariable"
                     "\npopulationType: dcs:Person"
                     "{denominator}"
                     "{healthbehavior}"
                     "{gender}"
                     "{frequenc_alcohol}"
                     "{education}"
                     "{incomequin}"
                     "{residence}"
                     "{countryofbirth}"
                     "{citizenship}"
                     "\nstatType: dcs:measuredValue"
                     "\nmeasuredProperty: dcs:count\n")

    _sv_properties_template = {
        "healthbehavior": "\nhealthBehavior: dcs:{property_value}",
        "frequenc_alcohol": "\nactivityFrequency: dcs:{property_value}",
        "gender": "\ngender: dcs:{property_value}",
        "education": "\neducationalAttainment: dcs:{property_value}",
        "incomequin": "\nincome: [{property_value}]",
        "residence": "\nplaceOfResidenceClassification: dcs:{property_value}",
        "countryofbirth": "\nnativity: dcs:{property_value}",
        "citizenship": "\ncitizenship: dcs:{property_value}",
    }

    _sv_value_to_property_mapping = {
        "AlcoholConsumption": "healthbehavior",
        "BingeDrinking": "healthbehavior",
        "HazardousAlcoholConsumption": "healthbehavior",
        "Daily": "frequenc_alcohol",
        "LessThanOnceAMonth": "frequenc_alcohol",
        "EveryMonth": "frequenc_alcohol",
        "NotInTheLast12Months": "frequenc_alcohol",
        "Never": "frequenc_alcohol",
        "NeverOrNotInTheLast12Months": "frequenc_alcohol",
        "EveryWeek": "frequenc_alcohol",
        "AtLeastOnceAWeek": "frequenc_alcohol",
        "NeverOrOccasional": "frequenc_alcohol",
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

    # over-ridden parent abstract method
    def _property_correction(self):
        for k, v in self._sv_properties.items():
            if k == "incomequin":
                self._sv_properties[k] = v\
                    .replace("To", " ")\
                    .replace("Percentile", " Percentile")\
                    .replace("IncomeOf", "")
            else:
                self._sv_properties[k] = v\
                    .replace("Or", "__")\
                    .replace("CountryOfBirth","")\
                    .replace("Citizenship", "")\

    # over-ridden parent abstract method
    # pylint: disable=no-self-use
    def _sv_name_correction(self, sv_name: str) -> str:
        return sv_name\
            .replace("AWeek","A Week")\
            .replace("AMonth","A Month")\
            .replace("Last12","Last 12")\
            .replace("ACitizen","A Citizen")\
            .replace("To"," To ")\
            .replace("Of","Of ")\
            .replace("  "," ")

    # pylint: enable=no-self-use
    def _rename_frequency_column(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns={'frequenc': 'frequenc_alcohol'})


if __name__ == '__main__':
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "input_files")
    ip_files = os.listdir(input_path)
    ip_files = [input_path + os.sep + file for file in ip_files]

    # Defining Output Files
    data_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "output")

    csv_name = "eurostat_population_alcoholconsumption.csv"
    mcf_name = "eurostat_population_alcoholconsumption.mcf"
    tmcf_name = "eurostat_population_alcoholconsumption.tmcf"

    cleaned_csv_path = os.path.join(data_file_path, csv_name)
    mcf_path = os.path.join(data_file_path, mcf_name)
    tmcf_path = os.path.join(data_file_path, tmcf_name)

    loader = EuroStatAlcoholConsumption(ip_files, cleaned_csv_path, mcf_path,
                                        tmcf_path)
    loader.generate_csv()
    loader.generate_mcf()
    loader.generate_tmcf()

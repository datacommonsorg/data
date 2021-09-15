# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import io
import ssl
import urllib.request
import sys

sys.path.insert(1, '../../../util')
from alpha2_to_dcid import COUNTRY_MAP

country_set = set(COUNTRY_MAP.values())

output_columns = [
    'Date', 'GeoId', 'CumulativeCount_Vaccine_COVID_19_Administered',
    'IncrementalCount_Vaccine_COVID_19_Administered',
    'CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedCase',
    'IncrementalCount_MedicalConditionIncident_COVID_19_ConfirmedCase',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased',
    'IncrementalCount_MedicalConditionIncident_COVID_19_PatientDeceased',
    'Count_MedicalConditionIncident_COVID_19_PatientInICU',
    'Count_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'CumulativeCount_MedicalTest_ConditionCOVID_19',
    'IncrementalCount_MedicalTest_ConditionCOVID_19'
]

# Automate Template MCF generation since there are many Statitical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:OurWorldInData_Covid19->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:OurWorldInData_COVID19
observationAbout: C:OurWorldInData_Covid19->GeoId
observationDate: C:OurWorldInData_Covid19->Date
value: C:OurWorldInData_Covid19->{stat_var}
"""


def create_formatted_csv_file(f_in, csv_file_path):
    with open(csv_file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=output_columns,
                                lineterminator='\n')
        writer.writeheader()
        reader = csv.DictReader(f_in)
        for row_dict in reader:
            place_dcid = 'country/%s' % row_dict['iso_code']
            # Skip invalid country ISO code.
            if not place_dcid in country_set:
                continue
            processed_dict = {
                'Date':
                row_dict['date'],
                'GeoId':
                place_dcid,
                'CumulativeCount_Vaccine_COVID_19_Administered':
                row_dict['total_vaccinations'],
                'IncrementalCount_Vaccine_COVID_19_Administered':
                row_dict['new_vaccinations'],
                'CumulativeCount_MedicalConditionIncident_COVID_19_ConfirmedCase':
                row_dict['total_cases'],
                'IncrementalCount_MedicalConditionIncident_COVID_19_ConfirmedCase':
                row_dict['new_cases'],
                'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased':
                row_dict['total_deaths'],
                'IncrementalCount_MedicalConditionIncident_COVID_19_PatientDeceased':
                row_dict['new_deaths'],
                'Count_MedicalConditionIncident_COVID_19_PatientInICU':
                row_dict['icu_patients'],
                'Count_MedicalConditionIncident_COVID_19_PatientHospitalized':
                row_dict['hosp_patients'],
                'CumulativeCount_MedicalTest_ConditionCOVID_19':
                row_dict['total_tests'],
                'IncrementalCount_MedicalTest_ConditionCOVID_19':
                row_dict['new_tests'],
            }

            writer.writerow(processed_dict)


def create_tmcf_file(tmcf_file_path):
    stat_vars = output_columns[2:]
    with open(tmcf_file_path, 'w', newline='') as f_out:
        for i in range(len(stat_vars)):
            f_out.write(
                TEMPLATE_MCF_TEMPLATE.format_map({
                    'index':
                    i,
                    'stat_var':
                    output_columns[2:][i]
                }))


if __name__ == '__main__':
    gcontext = ssl.SSLContext()
    with urllib.request.urlopen(
            'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv',
            context=gcontext) as response:
        f_in = io.TextIOWrapper(response)
        create_formatted_csv_file(f_in, 'OurWorldInData_Covid19.csv')
        create_tmcf_file('OurWorldInData_Covid19.tmcf')

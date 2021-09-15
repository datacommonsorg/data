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
import urllib.request

output_columns = [
    'Date', 'GeoId', 'CumulativeCount_MedicalTest_ConditionCOVID_19',
    'CumulativeCount_MedicalTest_ConditionCOVID_19_Positive',
    'CumulativeCount_MedicalTest_ConditionCOVID_19_Negative',
    'Count_MedicalTest_ConditionCOVID_19_Pending',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased',
    'Count_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientHospitalized',
    'Count_MedicalConditionIncident_COVID_19_PatientInICU',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientInICU',
    'Count_MedicalConditionIncident_COVID_19_PatientOnVentilator',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientOnVentilator'
]
with open('COVIDTracking_States.csv', 'w', newline='') as f_out:
    writer = csv.DictWriter(f_out,
                            fieldnames=output_columns,
                            lineterminator='\n')
    with urllib.request.urlopen(
            'https://covidtracking.com/api/v1/states/daily.csv') as response:
        reader = csv.DictReader(io.TextIOWrapper(response))

        writer.writeheader()
        for row_dict in reader:
            processed_dict = {
                'Date':
                '%s-%s-%s' % (row_dict['date'][:4], row_dict['date'][4:6],
                              row_dict['date'][6:]),
                'GeoId':
                'dcid:geoId/%s' % row_dict['fips'],
                'CumulativeCount_MedicalTest_ConditionCOVID_19':
                row_dict['totalTestResults'],
                'CumulativeCount_MedicalTest_ConditionCOVID_19_Positive':
                row_dict['positive'],
                'CumulativeCount_MedicalTest_ConditionCOVID_19_Negative':
                row_dict['negative'],
                'Count_MedicalTest_ConditionCOVID_19_Pending':
                row_dict['pending'],
                ('CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientRecovered'):
                row_dict['recovered'],
                ('CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientDeceased'):
                row_dict['death'],
                'Count_MedicalConditionIncident_COVID_19_PatientHospitalized':
                row_dict['hospitalizedCurrently'],
                ('CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientHospitalized'):
                row_dict['hospitalizedCumulative'],
                'Count_MedicalConditionIncident_COVID_19_PatientInICU':
                row_dict['inIcuCurrently'],
                ('CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientInICU'):
                row_dict['inIcuCumulative'],
                'Count_MedicalConditionIncident_COVID_19_PatientOnVentilator':
                row_dict['onVentilatorCurrently'],
                ('CumulativeCount_MedicalConditionIncident'
                 '_COVID_19_PatientOnVentilator'):
                row_dict['onVentilatorCumulative'],
            }

            writer.writerow(processed_dict)

# Automate Template MCF generation since there are many Statitical Variables.
TEMPLATE_MCF_TEMPLATE = """
Node: E:COVIDTracking_States->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: dcs:{stat_var}
measurementMethod: dcs:CovidTrackingProject
observationAbout: C:COVIDTracking_States->GeoId
observationDate: C:COVIDTracking_States->Date
value: C:COVIDTracking_States->{stat_var}
"""

stat_vars = output_columns[2:]
with open('COVIDTracking_States.tmcf', 'w', newline='') as f_out:
    for i in range(len(stat_vars)):
        f_out.write(
            TEMPLATE_MCF_TEMPLATE.format_map({
                'index': i,
                'stat_var': output_columns[2:][i]
            }))

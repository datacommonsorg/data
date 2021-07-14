# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pandas as pd
import difflib
"""
Retrieving and preprocessing district-wise daily case counts for India.
Raw data retrieved using API by covid19india.org (https://www.covid19india.org/)
"""

output_columns = [
    'Date', 'District', 'districtCode',
    'Count_MedicalTest_ConditionCOVID_19_Positive',
    'Count_MedicalConditionIncident_COVID_19_PatientRecovered',
    'Count_MedicalConditionIncident_COVID_19_PatientDeceased'
]


def _get_district_code(district):
    lgd_url = 'https://india-local-government-directory-bixhnw23da-el.a.run.app/india-local-government-directory/districts.csv?_size=max'
    dist_code = pd.read_csv(lgd_url)
    if district not in ['Unknown']:
        close_match = difflib.get_close_matches(
            str(district).upper(),
            dist_code['DistrictName(InEnglish)'],
            n=1,
            cutoff=0.8)
        if close_match:
            return dist_code[dist_code['DistrictName(InEnglish)'] ==
                             close_match[0]]['DistrictCode'].values[0]
        else:
            return None


def create_formatted_csv_file(csv_file_path, df):
    # creating dictionary with district vs code mappings
    district_codes = []

    for district in df['District'].unique():
        district_codes.append(_get_district_code(district))
    dist_codes_dict = dict(zip(df['District'].unique().tolist(),
                               district_codes))

    #get the district codes and drop rows that do not have district codes
    df['districtCode'] = df.apply(lambda row: dist_codes_dict[row['District']],
                                  axis=1)
    df = df[~df['districtCode'].isnull()]

    #prepare for exporting
    df = df.rename(
        columns={
            'Confirmed':
                'Count_MedicalTest_ConditionCOVID_19_Positive',
            'Deceased':
                'Count_MedicalConditionIncident_COVID_19_PatientDeceased',
            'Recovered':
                'Count_MedicalConditionIncident_COVID_19_PatientRecovered'
        })
    df = df[output_columns]
    df.to_csv(csv_file_path, index=False, header=True)


if __name__ == '__main__':
    api_url = "https://api.covid19india.org/csv/latest/districts.csv"
    data = pd.read_csv(api_url)

    create_formatted_csv_file('COVID19_cases_indian_districts.csv', data)

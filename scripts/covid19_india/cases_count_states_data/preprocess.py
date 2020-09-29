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

import json
import csv
import pandas as pd
import urllib.request

# 1. All counts are at State/UT level
# 2. Only cumulative counts are available at this point
# 3. 'unassigned' cases are ignored
# 5. Wrong state codes are ignored
# 4. Sometimes reports are published more than once. Then we take the last report on that day

INDIAN_STATE_CODES = [
    "IN-AP", "IN-AR", "IN-AS", "IN-BR", "IN-CT", "IN-GA", "IN-GJ", "IN-HR",
    "IN-HP", "IN-JH", "IN-KA", "IN-KL", "IN-MP", "IN-MH", "IN-MN", "IN-ML",
    "IN-MZ", "IN-NL", "IN-OR", "IN-PB", "IN-RJ", "IN-SK", "IN-TN", "IN-TG",
    "IN-TR", "IN-UT", "IN-UP", "IN-WB", "IN-AN", "IN-CH", "IN-DN", "IN-DD",
    "IN-DL", "IN-JK", "IN-LA", "IN-LD", "IN-PY", "IN-DN_DD"
]

ISOCODE_COUNTRY_STATE_FORMAT = "IN-{state}"

output_columns = [
    'DateTime', 'isoCode',
    'CumulativeCount_MedicalTest_ConditionCOVID_19_Positive',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased'
]


def get_isocode(state):
    iso_code = ISOCODE_COUNTRY_STATE_FORMAT.format(state=state.upper())
    if iso_code not in INDIAN_STATE_CODES:
        return "NOT_VALID_CODE"
    return iso_code


def create_formatted_csv_file(csv_file_path, data):

    df = pd.json_normalize(data["rows"])

    #convert to datetime and then drop the not required columns
    df['value.report_time'] = pd.to_datetime(df['value.report_time'])
    df = df.sort_values(by="value.report_time")
    df['DateTime'] = df['value.report_time'].dt.date
    df = df.drop([
        'id', 'key', 'value._id', 'value._rev', 'value.source', 'value.type',
        'value.confirmed_india', 'value.confirmed_foreign'
    ],
                 axis=1)

    #get the isocode and drop rows that have invalid isocodes
    df['isoCode'] = df['value.state'].apply(lambda x: get_isocode(x))
    df = df[df['isoCode'] != "NOT_VALID_CODE"]
    df = df.groupby([df["DateTime"], df["isoCode"]], as_index=False).last()

    #prepare for exporting
    df = df.rename(
        columns={
            'value.confirmed':
                "CumulativeCount_MedicalTest_ConditionCOVID_19_Positive",
            'value.death':
                'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased',
            'value.cured':
                'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered'
        })
    df = df.drop(['value.report_time', 'value.state'], axis=1)
    df = df[[
        "DateTime", "isoCode",
        "CumulativeCount_MedicalTest_ConditionCOVID_19_Positive",
        "CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered",
        "CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased"
    ]]
    df.to_csv(csv_file_path, index=False, header=True)


if __name__ == '__main__':
    with urllib.request.urlopen(
            "https://raw.githubusercontent.com/datameet/covid19/master/data/mohfw.json"
    ) as response:
        data = json.load(response)
        create_formatted_csv_file('COVID19_cases_indian_states.csv', data)

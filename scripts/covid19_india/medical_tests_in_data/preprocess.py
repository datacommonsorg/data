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

# 1. All counts are at India level, so geographic reference code will always be IN
# 2. Only cumulative counts are available at this point

INDIA = "IN"
output_columns = [
    'Date', 'isoCode', 'CumulativeCount_MedicalTest_ConditionCOVID_19'
]


def create_formatted_csv_file(csv_file_path, data):
    df = pd.json_normalize(data["rows"])

    #convert to datetime and then drop the not required columns
    df['value.report_time'] = pd.to_datetime(df['value.report_time'])
    df = df.sort_values(by="value.report_time")
    df['Date'] = df['value.report_time'].dt.date
    df = df.drop([
        'id', 'key', 'value._id', 'value._rev', 'value.source', 'value.type',
        'value.individuals', 'value.confirmed_positive'
    ],
                 axis=1)

    df['isoCode'] = INDIA
    df = df.groupby([df["Date"], df["isoCode"]], as_index=False).last()

    #prepare for exporting
    df = df.rename(
        columns={
            'value.samples': "CumulativeCount_MedicalTest_ConditionCOVID_19"
        })
    df = df.drop(['value.report_time'], axis=1)
    df = df[[
        "Date", "isoCode", "CumulativeCount_MedicalTest_ConditionCOVID_19"
    ]]
    df.to_csv(csv_file_path, index=False, header=True)


if __name__ == '__main__':
    with urllib.request.urlopen(
            "https://raw.githubusercontent.com/datameet/covid19/master/data/icmr_testing_status.json"
    ) as response:
        data = json.load(response)
        create_formatted_csv_file('COVID19_tests_india.csv', data)

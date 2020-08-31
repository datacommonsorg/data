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
import urllib.request

# 1. All counts are at State/UT level
# 2. Only cumulative counts are available at this point
# 3. 'unassigned' cases are ignored
# 5. Wrong state codes are ignored
# 4. Sometimes reports are published more than once

INDIAN_STATE_CODES = [
    "IN-AP", "IN-AR", "IN-AS", "IN-BR", "IN-CT", "IN-GA", "IN-GJ", "IN-HR",
    "IN-HP", "IN-JH", "IN-KA", "IN-KL", "IN-MP", "IN-MH", "IN-MN", "IN-ML",
    "IN-MZ", "IN-NL", "IN-OR", "IN-PB", "IN-RJ", "IN-SK", "IN-TN", "IN-TG",
    "IN-TR", "IN-UT", "IN-UP", "IN-WB", "IN-AN", "IN-CH", "IN-DN", "IN-DD",
    "IN-DL", "IN-JK", "IN-LA", "IN-LD", "IN-PY"
]

ISOCODE_COUNTRY_STATE_FORMAT = "IN-{state}"

output_columns = [
    'DateTime', 'isoCode', 'CumulativeCount_MedicalTest_COVID_19_Positive',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered',
    'CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased'
]


def create_formatted_csv_file(csv_file_path, data):
    rows = data["rows"]
    with open(csv_file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=output_columns,
                                lineterminator='\n')
        writer.writeheader()
        for row in rows:
            iso_code = ISOCODE_COUNTRY_STATE_FORMAT.format(
                state=(row["value"]["state"]).upper())
            if iso_code not in INDIAN_STATE_CODES:
                continue
            processed_dict = {}
            processed_dict["DateTime"] = row["value"]["report_time"]
            processed_dict["isoCode"] = iso_code
            processed_dict[
                "CumulativeCount_MedicalTest_COVID_19_Positive"] = row["value"][
                    "confirmed"]
            processed_dict[
                "CumulativeCount_MedicalConditionIncident_COVID_19_PatientRecovered"] = row[
                    "value"]["cured"]
            processed_dict[
                "CumulativeCount_MedicalConditionIncident_COVID_19_PatientDeceased"] = row[
                    "value"]["death"]

            writer.writerow(processed_dict)


if __name__ == '__main__':
    with urllib.request.urlopen(
            "https://raw.githubusercontent.com/datameet/covid19/master/data/mohfw.json"
    ) as response:
        data = json.load(response)
        create_formatted_csv_file('COVID19_cases_indian_states.csv', data)

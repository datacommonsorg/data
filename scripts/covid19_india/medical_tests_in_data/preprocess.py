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

# 1. All counts are at India level, so geographic reference code will always be IN
# 2. Only cumulative counts are available at this point

INDIA = "IN"
output_columns = [
    'Date', 'isoCode', 'CumulativeCount_MedicalTest_ConditionCOVID_19'
]


def create_formatted_csv_file(csv_file_path, data):
    rows = data["rows"]
    with open(csv_file_path, 'w', newline='') as f_out:
        writer = csv.DictWriter(f_out,
                                fieldnames=output_columns,
                                lineterminator='\n')
        writer.writeheader()
        for row in rows:
            processed_dict = {}
            processed_dict["Date"] = (row["value"]["report_time"])[:10]
            processed_dict["isoCode"] = INDIA
            processed_dict[
                "CumulativeCount_MedicalTest_ConditionCOVID_19"] = row["value"][
                    "samples"]
            writer.writerow(processed_dict)


if __name__ == '__main__':
    with urllib.request.urlopen(
            "https://raw.githubusercontent.com/datameet/covid19/master/data/icmr_testing_status.json"
    ) as response:
        data = json.load(response)
        create_formatted_csv_file('COVID19_tests_india.csv', data)

# Copyright 2025 Google LLC
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
HEADERS = {'content-type': 'application/json'}

COLUMNS_SELECTOR_URL = "https://nces.ed.gov/ccd/elsi/export.aspx/ExportToCSV"

COLUMNS_SELECTOR = {
    "sSection": "tableGenerator",
    "sZipCode": "",
    "sZipMiles": "",
    "sState": "",
    "sCountyValue": "",
    "sDistrictValue": "",
    "sTableTitle": "",
    "sTableID": "",
    "sState": "",
    "sLevel": None,
    "sYear": "",
    "lYearsSelected": None,
    "lColumnsSelected": None,
    "lFilterNames": [["State", "Static"]],
    "lFilterData": [["allplus"]],
    "lFilterYears": [[]],
    "lFilterMasterData": [[]],
    "lFilterTitles": ["State"],
    "sGroupByColumn": "0",
    "sNYCMerged": "false"
}

COMPRESS_FILE_URL = "https://nces.ed.gov/ccd/elsi/export.aspx/CompressFile"

COMPRESS_FILE = {"sFileName": None}

DOWNLOAD_URL = 'https://nces.ed.gov/{compressed_src_file}'

YEAR_URL = "https://nces.ed.gov/ccd/elsi/tableGenerator.aspx/GetTableGeneratorYearList"

YEAR_PAYLOAD = {'sLevel': '{school_type}'}

NCES_DOWNLOAD_URL = "https://nces.ed.gov/ccd/elsi/tableGenerator.aspx"

COLUMNS_TO_DOWNLOAD_WITH_SINGLE_API_CALL = 59

MAX_RETRIES = 5
RETRY_SLEEP_SECS = 3

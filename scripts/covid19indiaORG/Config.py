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

# Covid 19 India has some other data that we don't need for the import.
# Only store data for the following labels.
DATA_TO_KEEP = set(['confirmed', 'deceased', 'tested', 'active', 'recovered'])

# Every state has its own API.
STATE_APIS = {
    "WB":"https://api.covid19india.org/v4/min/timeseries-WB.min.json",
    "UT":"https://api.covid19india.org/v4/min/timeseries-UT.min.json",
    "UP":"https://api.covid19india.org/v4/min/timeseries-UP.min.json",
    "TR":"https://api.covid19india.org/v4/min/timeseries-TR.min.json",
    "TG":"https://api.covid19india.org/v4/min/timeseries-TG.min.json",
    "TN":"https://api.covid19india.org/v4/min/timeseries-TN.min.json",
    "SK":"https://api.covid19india.org/v4/min/timeseries-SK.min.json",
    "RJ":"https://api.covid19india.org/v4/min/timeseries-RJ.min.json",
    "PB":"https://api.covid19india.org/v4/min/timeseries-PB.min.json",
    "PY":"https://api.covid19india.org/v4/min/timeseries-PY.min.json",
    "OR":"https://api.covid19india.org/v4/min/timeseries-OR.min.json",
    "NL":"https://api.covid19india.org/v4/min/timeseries-NL.min.json",
    "MZ":"https://api.covid19india.org/v4/min/timeseries-MZ.min.json",
    "ML":"https://api.covid19india.org/v4/min/timeseries-ML.min.json",
    "MN":"https://api.covid19india.org/v4/min/timeseries-MN.min.json",
    "MH":"https://api.covid19india.org/v4/min/timeseries-MH.min.json",
    "MP":"https://api.covid19india.org/v4/min/timeseries-MP.min.json",
    "LA":"https://api.covid19india.org/v4/min/timeseries-LA.min.json",
    "KL":"https://api.covid19india.org/v4/min/timeseries-KL.min.json",
    "KA":"https://api.covid19india.org/v4/min/timeseries-KA.min.json",
    "JH":"https://api.covid19india.org/v4/min/timeseries-JH.min.json",
    "JK":"https://api.covid19india.org/v4/min/timeseries-JK.min.json",
    "HP":"https://api.covid19india.org/v4/min/timeseries-HP.min.json",
    "HR":"https://api.covid19india.org/v4/min/timeseries-HR.min.json",
    "GJ":"https://api.covid19india.org/v4/min/timeseries-GJ.min.json",
    "GA":"https://api.covid19india.org/v4/min/timeseries-GA.min.json",
    "DL":"https://api.covid19india.org/v4/min/timeseries-DL.min.json",
    "DN":"https://api.covid19india.org/v4/min/timeseries-DN.min.json",
    "CT":"https://api.covid19india.org/v4/min/timeseries-CT.min.json",
    "CH":"https://api.covid19india.org/v4/min/timeseries-CH.min.json",
    "BR":"https://api.covid19india.org/v4/min/timeseries-BR.min.json",
    "AS":"https://api.covid19india.org/v4/min/timeseries-AS.min.json",
    "AR":"https://api.covid19india.org/v4/min/timeseries-AR.min.json",
    "AP":"https://api.covid19india.org/v4/min/timeseries-AP.min.json",
    "AN":"https://api.covid19india.org/v4/min/timeseries-AN.min.json"
}

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

from typing import Dict

# Covid 19 India has some other data that we don't need for the import.
# Only store data for the following labels.
DATA_TO_KEEP = set(['confirmed', 'deceased', 'tested', 'active', 'recovered'])

# Each API can be generated using the state_iso_code.
# List of state iso codes.
STATE_ISO_CODES = ['WB', 'UT', 'UP', 'TR', 'TG', 'TN', 'SK', 'RJ', 'PB', 'PY',
'OR', 'NL', 'MZ', 'ML', 'MN', 'MH', 'MP', 'LA', 'KL', 'KA', 'JH', 'JK', 'HP',
'HR', 'GJ', 'GA', 'DL', 'DN', 'CT', 'CH', 'BR', 'AS', 'AR', 'AP', 'AN']


def get_state_apis() -> Dict[str, str]:
    """For every state_iso_code, generate the URL of the API.
       NOTE: Each state has its own API.
       Returns a dictionary of {state_iso_code: URL}"""
    output = {}
    for state_iso_code in STATE_ISO_CODES:
        output[state_iso_code] = f"https://api.covid19india.org/v4/min/timeseries-{state_iso_code}.min.json"
    return output

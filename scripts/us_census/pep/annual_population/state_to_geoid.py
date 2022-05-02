# Copyright 2022 Google LLC
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
"""This Script converts State shortform to geoId"""
USSTATE_MAP = {
    'AL': 'geoId/01',
    'AK': 'geoId/02',
    'AZ': 'geoId/04',
    'AR': 'geoId/05',
    'CA': 'geoId/06',
    'CO': 'geoId/08',
    'CT': 'geoId/09',
    'DE': 'geoId/10',
    'DC': 'geoId/11',
    'FL': 'geoId/12',
    'GA': 'geoId/13',
    'HI': 'geoId/15',
    'ID': 'geoId/16',
    'IL': 'geoId/17',
    'IN': 'geoId/18',
    'IA': 'geoId/19',
    'KS': 'geoId/20',
    'KY': 'geoId/21',
    'LA': 'geoId/22',
    'ME': 'geoId/23',
    'MD': 'geoId/24',
    'MA': 'geoId/25',
    'MI': 'geoId/26',
    'MN': 'geoId/27',
    'MS': 'geoId/28',
    'MO': 'geoId/29',
    'MT': 'geoId/30',
    'NE': 'geoId/31',
    'NV': 'geoId/32',
    'NH': 'geoId/33',
    'NJ': 'geoId/34',
    'NM': 'geoId/35',
    'NY': 'geoId/36',
    'NC': 'geoId/37',
    'ND': 'geoId/38',
    'OH': 'geoId/39',
    'OK': 'geoId/40',
    'OR': 'geoId/41',
    'PA': 'geoId/42',
    'RI': 'geoId/44',
    'SC': 'geoId/45',
    'SD': 'geoId/46',
    'TN': 'geoId/47',
    'TX': 'geoId/48',
    'UT': 'geoId/49',
    'VT': 'geoId/50',
    'VA': 'geoId/51',
    'WA': 'geoId/53',
    'WV': 'geoId/54',
    'WI': 'geoId/55',
    'WY': 'geoId/56',
    'AS': 'geoId/60',
    'GU': 'geoId/66',
    'MP': 'geoId/69',
    'PR': 'geoId/72',
    'UM': 'geoId/74',
    'VI': 'geoId/78',
    'US': 'country/USA'
}
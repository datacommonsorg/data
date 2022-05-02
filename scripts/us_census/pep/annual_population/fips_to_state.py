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
"""This Script converts geoID to State Geographic Name"""
FIPSCODE = {
    '00000': 'country/USA',
    '01000': 'geoId/01',
    '02000': 'geoId/02',
    '04000': 'geoId/04',
    '05000': 'geoId/05',
    '06000': 'geoId/06',
    '08000': 'geoId/08',
    '09000': 'geoId/09',
    '10000': 'geoId/10',
    '11000': 'geoId/11',
    '12000': 'geoId/12',
    '13000': 'geoId/13',
    '15000': 'geoId/15',
    '16000': 'geoId/16',
    '17000': 'geoId/17',
    '18000': 'geoId/18',
    '19000': 'geoId/19',
    '20000': 'geoId/20',
    '21000': 'geoId/21',
    '22000': 'geoId/22',
    '23000': 'geoId/23',
    '24000': 'geoId/24',
    '25000': 'geoId/25',
    '26000': 'geoId/26',
    '27000': 'geoId/27',
    '28000': 'geoId/28',
    '29000': 'geoId/29',
    '30000': 'geoId/30',
    '31000': 'geoId/31',
    '32000': 'geoId/32',
    '33000': 'geoId/33',
    '34000': 'geoId/34',
    '35000': 'geoId/35',
    '36000': 'geoId/36',
    '37000': 'geoId/37',
    '38000': 'geoId/38',
    '39000': 'geoId/39',
    '40000': 'geoId/40',
    '41000': 'geoId/41',
    '42000': 'geoId/42',
    '44000': 'geoId/44',
    '45000': 'geoId/45',
    '46000': 'geoId/46',
    '47000': 'geoId/47',
    '48000': 'geoId/48',
    '49000': 'geoId/49',
    '50000': 'geoId/50',
    '51000': 'geoId/51',
    '53000': 'geoId/53',
    '54000': 'geoId/54',
    '55000': 'geoId/55',
    '56000': 'geoId/56',
}

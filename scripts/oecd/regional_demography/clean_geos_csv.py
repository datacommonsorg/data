# Copyright 2020 Google LLC
#
# Licensed under the Apache License',' Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing',' software
# distributed under the License is distributed on an "AS IS" BASIS','
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND',' either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd

df = pd.read_csv('geos.csv', skiprows=2)
df.columns = [
    'containedInCountry', 'Node', 'oecd_territorial_level', 'name',
    'containedInPlace', 'rural_or_urban', 'access_to_city'
]

# Append AA1 to the name of TL2 geos as a hint to the Place Name Resolver
df.loc[df.oecd_territorial_level == '2',
       'name'] = df.loc[df.oecd_territorial_level == '2',
                        'name'] + ' AdministrativeArea1'

# Remove places that do not actually exist

# Remove Non-official grid (NOG)
df = df[df.oecd_territorial_level != 'NOG']

# Remove statistical regions
df = df[~((df.containedInCountry == 'CAN') &
          (df.name.str.startswith('Division')))]
df = df[~((df.containedInCountry == 'CAN') &
          (df.name.str.startswith('Region')))]
df = df[~((df.containedInCountry == 'LVA') &
          (df.oecd_territorial_level == '3'))]
df = df[~((df.containedInCountry == 'MEX') &
          (df.oecd_territorial_level == '3'))]
df = df[~((df.containedInCountry == 'NLD') &
          (df.oecd_territorial_level == '3'))]
df = df[~((df.containedInCountry == 'SVN') &
          (df.oecd_territorial_level == '3'))]
df = df[~((df.containedInCountry == 'USA') &
          (df.oecd_territorial_level == '3'))]
df = df[~((df.containedInCountry == 'BRA') &
          (df.oecd_territorial_level == '3'))]

# Remove Non OECD Member Country (NOMC) containedInPlace=NOMC
df.replace({'NOMC': ''}, regex=True, inplace=True)

df.to_csv('geos_cleaned.csv', index=False)

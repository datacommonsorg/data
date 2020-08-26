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

import json
import numpy as np
import pandas as pd

df = pd.read_csv('geos_resolved.csv')

# Hardcode dcids for countries, ignoring resolver output.
# Take TL1 geos and convert value [A-Z]{3} into country/[A-Z]{3}
country_idx = df['oecd_territorial_level'] == '1'
df.loc[country_idx, 'dcid'] = 'country/' + df.loc[country_idx, 'Node']

# Hardcode dcids for NUTS, ignoring resolver output.
# Take NUTS geos and convert value xxx into nuts/xxx
nuts = dict(json.loads(open('region_nuts_codes.json').read()))
nuts_idx = df['Node'].isin(nuts.keys())
df.loc[nuts_idx, 'dcid'] = 'nuts/' + df.loc[nuts_idx, 'Node']

# Hardcode dcids for US States, ignoring resolver output.
# Take TL2 geos in USA and convert value US[0-9]{2} into geoId/[0-9]{2}
us_state_idx = (df['containedInCountry']
                == 'USA') & (df['oecd_territorial_level'] == '2')

df.loc[us_state_idx, 'dcid'] = 'geoId/' + \
    df.loc[us_state_idx, 'Node'].apply(lambda x: x.replace('US', ''))

# Unset dcids for later rows if multiple rows resolved to the same dcid.
df.loc[df['dcid'].duplicated(), 'dcid'] = np.nan
df.loc[df['dcid'].duplicated(),
       'errors'] = 'DCID resolved to a duplicate parent or previous sibling.'

# Create a new df with no NaNs.
dfs = df[['Node', 'dcid']].dropna()

dfs['dcid'] = 'dcid:' + dfs['dcid'].astype(str)
name2dcid = dict(zip(dfs.Node, dfs.dcid))
with open('regid2dcid.json', 'w') as f_out:
    json.dump(name2dcid, f_out, indent=4, sort_keys=True)

# Uncomment for debugging
# df.to_csv('geos_resolved_cleaned_dbg.csv', index=False)

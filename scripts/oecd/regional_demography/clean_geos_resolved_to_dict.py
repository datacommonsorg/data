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
df.loc[df['dcid'].duplicated(), 'dcid'] = np.nan
df.loc[df['dcid'].duplicated(),
       'errors'] = 'DCID resolved to a duplicate parent or previous sibling.'

dfs = df[['Node', 'dcid']].dropna()
dfs['dcid'] = 'dcid:' + dfs['dcid'].astype(str)
name2dcid = dict(zip(dfs.Node, dfs.dcid))
with open('regid2dcid.json', 'w') as f_out:
    json.dump(name2dcid, f_out, indent=4)

# Uncomment for debugging
# df.to_csv('geos_resolved_cleaned.csv', index=False)

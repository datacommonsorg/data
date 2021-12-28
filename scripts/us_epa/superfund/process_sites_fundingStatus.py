# Copyright 2021 Google LLC
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
"""TODO(sharadshriram): DO NOT SUBMIT without one-line documentation for process_sites_fundingStatus.

TODO(sharadshriram): DO NOT SUBMIT without a detailed description of process_sites_fundingStatus.
"""
import pandas as pd

from typing import Sequence
from absl import app
from .utils import write_tmcf

### 2. Generate the tmcf and csv for the date observations on when NPL site status for a superfund changes



def add_rows_to_status_csv(row):
    status_to_schema = {
        'NPL Site': 'dcid:FinalNPLSite',
        'Deleted NPL Site': 'dcid:DeletedNPLSite',
        'Proposed NPL Site': 'dcid:ProposedNPLSite'
    }
    
    df = pd.DataFrame()
    
    ## add observation to current status StatVar
    df = df.append({
        'observationAbout': 'dcid:epaSuperfundSiteId/' +  row['Site EPA ID'],
        'observationDate': '2021',
        'variableMeasured': 'dcid:FundingStatus_SuperfundSite',
        'value': status_to_schema[row['Status']]
    }, ignore_index=True)
     
    ## add observations for proposed, listing and deletion dates based on notnull()
    if not pd.isnull(row['Proposed Date']):
            df = df.append({
                'observationAbout': 'dcid:epaSuperfundSiteId/' +  row['Site EPA ID'],
                'observationDate': row['Proposed Date'],
                'variableMeasured': 'dcid:FundingStatus_SuperfundSite',
                'value': 'dcid:ProposedNPLSite'
            }, ignore_index=True)
            
    if not pd.isnull(row['Listing Date']):
            df = df.append({
                'observationAbout': 'dcid:epaSuperfundSiteId/' +  row['Site EPA ID'],
                'observationDate': row['Listing Date'],
                'variableMeasured': 'dcid:FundingStatus_SuperfundSite',
                'value': 'dcid:FinalNPLSite'
            }, ignore_index=True)
            
    if not pd.isnull(row['Deletion Date']):
            df = df.append({
                'observationAbout': 'dcid:epaSuperfundSiteId/' +  row['Site EPA ID'],
                'observationDate': row['Deletion Date'],
                'variableMeasured': 'dcid:FundingStatus_SuperfundSite',
                'value': 'dcid:DeletedNPLSite'
            }, ignore_index=True)
    
    return df


npl_sites = pd.read_csv("./data/Superfund National Priorities List (NPL) Sites with Status Information.csv", usecols=['Site EPA ID', 'Status', 'Proposed Date', 'Listing Date', 'Deletion Date'])

status_csv = pd.DataFrame(columns=['observationAbout', 'observationDate', 'variableMeasured', 'value'])

npl_sites['Proposed Date'] = pd.to_datetime(npl_sites['Proposed Date']).dt.strftime('%Y-%m-%d')
npl_sites['Listing Date'] = pd.to_datetime(npl_sites['Listing Date']).dt.strftime('%Y-%m-%d')
npl_sites['Deletion Date'] = pd.to_datetime(npl_sites['Deletion Date']).dt.strftime('%Y-%m-%d')

df_list = [status_csv]
npl_sites.apply(lambda row: df_list.append(add_rows_to_status_csv(row)), axis=1)

status_csv = pd.concat(df_list, ignore_index=True)

_STATUS_TEMPALTE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->observationAbout
observationDate: C:SuperfundSite->observationDate
variableMeasured: C:SuperfundSite->variableMeasured
value: C:SuperfundSite->value
"""

f = open("./superfund_fundingStatus.tmcf", "w")
f.write(_STATUS_TEMPALTE_MCF)
f.close()

status_csv.to_csv("./superfund_fundingStatus.csv", index=False)

status_csv

def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')


if __name__ == '__main__':
  app.run(main)

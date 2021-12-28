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
"""Script proceses data files to create nodes for EPA NPL Superfund sites

What are EPA NPL Superfund sites?

About this script:
"""

from typing import Sequence
from absl import app
from .utils import write_tmcf, make_list_of_geos_to_resolve, resolve_with_recon

import numpy as np
import pandas as pd
import json
import csv


## If file is empty
## List of all NPL Sites with statuses from https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1
npl_sites = pd.read_csv("./data/Superfund National Priorities List (NPL) Sites with Status Information.csv", usecols=['Latitude', 'Longitude'])

npl_sites.apply(lambda row: make_list_of_geos_to_resolve(row['Latitude'], row['Longitude']) if not pd.isna(row['Latitude']) else '', axis=1)
resolve_with_recon(output_path='./')

f = open("./resolved_superfund_site_geoIds.json", 'r')
_GEO_MAP = json.load(f)
f.close()

## List of all NPL Sites with statuses from https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1
npl_sites = pd.read_csv("./data/Superfund National Priorities List (NPL) Sites with Status Information.csv", usecols=['Site Name', 'Site Score', 'Status', 'Site EPA ID', 'Region ID', 'Latitude', 'Longitude'])

## Remedy Component Data for Decision Documents by Media, FYs 1982-2017 (Final NPL, Deleted NPL, and Superfund Alternative Approach Sites)
site_ownership = pd.read_excel("./data/401052.xlsx", header=1, usecols=['EPA ID', 'Federal Facility'])
site_ownership.columns = ['epaId', 'establishmentOwnership']
site_ownership['establishmentOwnership'] = pd.Series(np.where(site_ownership['establishmentOwnership'].values == 'Y','FederalGovernmentOwned','PrivatelyOwned'), site_ownership.index)

### 1. Generate the tmcf and csv for making the nodes of superfund sites
_SITE_TEMPLATE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:SuperfundSite
dcid: C:SuperfundSite->dcid
name: C:SuperfundSite->siteName
epaSuperfundSiteId: C:SuperfundSite->epaId
epaRegionCode: C:SuperfundSite->regionCode
containedInPlace: C:SuperfundSite->containedInPlace
location: C:SuperfundSite->location
establishmentOwnership: C:SuperfundSite->establishmentOwnership
"""

def get_geoId(row, geo_map=_GEO_MAP):
    loc = f"{str(row['Latitude'])},{str(row['Longitude'])}"
    try:
        return geo_map[loc]
    except:
        print(loc)

site_csv = npl_sites[['Site Name', 'Site EPA ID', 'Status', 'Region ID', 'Latitude', 'Longitude']]
site_csv['dcid'] = 'epaSuperfundSiteId/' + site_csv['Site EPA ID']
site_csv['location'] = site_csv.apply(lambda row: f"[latLong {row['Latitude']} {row['Longitude']}]" if not pd.isna(row['Latitude']) else '', axis=1)
site_csv['containedInPlace'] = site_csv.apply(get_geoId, axis=1)
site_csv.drop(columns=['Latitude', 'Longitude'], inplace=True)
site_csv.rename(columns={'Site Name': 'siteName', 'Site EPA ID':'epaId', 'Region ID':'regionCode'}, inplace=True)
site_csv = pd.merge(site_csv, site_ownership, on='epaId', how='left')
site_csv.drop_duplicates(inplace=True)
site_csv.to_csv("./superfund_sites.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

f = open("superfund_sites.tmcf", "w")
f.write(_SITE_TEMPLATE_MCF)
f.close()


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')


if __name__ == '__main__':
  app.run(main)

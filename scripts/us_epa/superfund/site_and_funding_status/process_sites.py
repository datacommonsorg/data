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
"""Script proceses data files to create nodes for EPA NPL Superfund sites

About this script:
This script processes data from two files namely:

- ./data/Superfund National Priorities List (NPL) Sites with Status Information.csv
  This file lists all superfund sites on the NPL with a note on the site's status on the NPL. This file also provides the location of the superfund site with latitude and longitude. This dataset is exported from the data view in  https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1

- ./data/401063.xlsx
  This file lists the different remedial actions carried out different superfund sites based on the contaminated media between 1982 to 2017. In this script, this dataset is used to map the ownership type (government-owned, privately-owned) of the site.
"""
from absl import app, flags
import os
import sys
import numpy as np
import pandas as pd
import json
import csv

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../..'))  # for utils
from us_epa.util.superfund_helper import make_list_of_geos_to_resolve, resolve_with_recon

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

_SITE_DATA = "./Superfund National Priorities List (NPL) Sites with Status Information.csv"

_OWNERSHIP_DATA = "./401063.xlsx"

_COL_NAME_MAP = {
        'Site Name': 'siteName',
        'Site EPA ID': 'epaId',
        'Region ID': 'regionCode',
        'Site Score': 'siteScore'
}

def check_geo_resolution()->dict:
    """
    Get a map with geoIds resolved using the DC Recon API from lat/long.
    """
    ## Data on the superfund sites on the NPL
    site_geos_csv_path = os.path.join(
        _SCRIPT_PATH,
        "./data/Superfund National Priorities List (NPL) Sites with Status Information.csv"
    )
    site_geos = pd.read_csv(site_geos_csv_path,
                            usecols=['Latitude', 'Longitude'])

    site_geos.apply(lambda row: make_list_of_geos_to_resolve(
        row['Latitude'], row['Longitude'])
                    if not pd.isna(row['Latitude']) else '',
                    axis=1)
    geo_map = resolve_with_recon(output_path='')
    return geo_map


def get_geoId(row: str, geo_map: dict) -> str:
    """
    Dataframe utility function to map DC geoId based on latitude, longitude 
    """
    loc = f"{str(row['Latitude'])},{str(row['Longitude'])}"
    try:
        return ', '.join(geo_map[loc])
    except:
        print(f"{loc} -- does not exist in the map")


def process_sites(input_path: str, output_path: str, geo_map:dict) -> int:
    """
    Process the input files and create clean csv + tmcf files.
    """
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ## Data on superfund sites on the National Priority List (NPL)
    npl_sites_path = os.path.join(input_path, _SITE_DATA)
    npl_sites = pd.read_csv(npl_sites_path,
                            usecols=[
                                'Site Name', 'Site Score', 'Site EPA ID',
                                'Region ID', 'Latitude', 'Longitude'
                            ])

    ## Data on superfund sites based on clean-up operations done
    site_ownership_path = os.path.join(input_path, _OWNERSHIP_DATA)
    site_ownership = pd.read_excel(site_ownership_path,
                                   header=1,
                                   usecols=['EPA ID', 'Federal Facility'])
    site_ownership.columns = ['epaId', 'establishmentOwnership']
    site_ownership['establishmentOwnership'] = pd.Series(
        np.where(site_ownership['establishmentOwnership'].values == 'Y',
                 'FederalGovernmentOwned', 'PrivatelyOwned'),
        site_ownership.index)
    # The way we used this dataset, we have a lot of duplicates
    site_ownership.drop_duplicates(inplace=True)

    site_csv = npl_sites[[
        'Site Name', 'Site EPA ID', 'Site Score', 'Region ID', 'Latitude',
        'Longitude'
    ]]
    site_csv['dcid'] = 'epaSuperfundSiteId/' + site_csv['Site EPA ID']
    site_csv['location'] = site_csv.apply(
        lambda row: f"[latLong {row['Latitude']} {row['Longitude']}]"
        if not pd.isna(row['Latitude']) else '',
        axis=1)
    site_csv['containedInPlace'] = site_csv.apply(get_geoId, args=(geo_map,), axis=1)
    site_csv.drop(columns=['Latitude', 'Longitude'], inplace=True)
    site_csv.rename(columns=_COL_NAME_MAP, inplace=True)
    # We processed 1,715 superfund sites -- initially all of them did not have `establishmentOwnership`.
    # After the merge, we have 1,317 PrivatelyOwned sites, 158 FederalGovernmentOwned sites and 240 sites do not have a value for the establishmentOwnership property.
    site_csv = pd.merge(site_csv, site_ownership, on='epaId', how='left')
    site_csv['siteName'] = site_csv['siteName'].str.replace(', Inc.', ' Inc.')

    # Save file only when output_path is non-null / non-empty
    site_csv.to_csv(os.path.join(output_path, "superfund_sites.csv"),
                    index=False,
                    quoting=csv.QUOTE_NONNUMERIC)
    f = open(os.path.join(output_path, "superfund_sites.tmcf"), 'w')
    f.write(_SITE_TEMPLATE_MCF)
    f.close()

    site_count = len(site_csv['dcid'].unique())
    return int(site_count)


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string('input_path', './data',
                        'Path to the directory with input files')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')
    geo_map = check_geo_resolution()
    site_count = process_sites(FLAGS.input_path, FLAGS.output_path, geo_map)
    print(f"Processing of {site_count} superfund sites is complete.")


if __name__ == '__main__':
    app.run(main)

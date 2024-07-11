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
"""Script proceses data files for fundingStatus of EPA NPL Superfund sites

About this script:
This script processes data from:
- ./data/superfund_sites_with_status.csv
  This file lists all superfund sites on the NPL with a note on the site's status on the NPL. This file also provides different dates when the NPL status of a site changed. This dataset is exported from the data view in  https://epa.maps.arcgis.com/apps/webappviewer/index.html?id=33cebcdfdd1b4c3a8b51d416956c41f1
"""
from absl import app, flags
import os
import sys
import pandas as pd

FLAGS = flags.FLAGS
flags.DEFINE_string('site_funding_input_path', './data',
                    'Path to the directory with input files')
flags.DEFINE_string(
    'site_funding_output_path', './data/output',
    'Path to the directory where generated files are to be stored.')

_DATASET_NAME = "./superfund_sites_with_status.csv"

_STATUS_TEMPALTE_MCF = """Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->observationAbout
observationDate: C:SuperfundSite->observationDate
variableMeasured: C:SuperfundSite->variableMeasured
value: C:SuperfundSite->value
"""

_STATUS_SCHEMA_MAP = {
    'NPL Site': 'dcs:FinalNPLSite',
    'Deleted NPL Site': 'dcs:DeletedNPLSite',
    'Proposed NPL Site': 'dcs:ProposedNPLSite'
}


def add_rows_to_status_csv(row):
    """
    Utility function that creates the clean csv from each row of source dataset.
    """
    df_list = []

    ## add observation to current status StatVar
    df_list.append(
        pd.DataFrame(
            {
                'observationAbout': 'epaSuperfundSiteId/' + row['Site EPA ID'],
                'observationDate': '2021',
                'variableMeasured': 'dcid:SuperfundFundingStatus_SuperfundSite',
                'value': _STATUS_SCHEMA_MAP[row['Status']]
            },
            index=[0]))

    ## add observations for proposed, listing and deletion dates based on notnull()
    if not pd.isnull(row['Proposed Date']):
        df_list.append(
            pd.DataFrame(
                {
                    'observationAbout':
                        'epaSuperfundSiteId/' + row['Site EPA ID'],
                    'observationDate':
                        row['Proposed Date'],
                    'variableMeasured':
                        'dcid:SuperfundFundingStatus_SuperfundSite',
                    'value':
                        'dcs:ProposedNPLSite'
                },
                index=[0]))

    if not pd.isnull(row['Listing Date']):
        df_list.append(
            pd.DataFrame(
                {
                    'observationAbout':
                        'epaSuperfundSiteId/' + row['Site EPA ID'],
                    'observationDate':
                        row['Listing Date'],
                    'variableMeasured':
                        'dcid:SuperfundFundingStatus_SuperfundSite',
                    'value':
                        'dcs:FinalNPLSite'
                },
                index=[0]))

    if not pd.isnull(row['Deletion Date']):
        df_list.append(
            pd.DataFrame(
                {
                    'observationAbout':
                        'epaSuperfundSiteId/' + row['Site EPA ID'],
                    'observationDate':
                        row['Deletion Date'],
                    'variableMeasured':
                        'dcid:SuperfundFundingStatus_SuperfundSite',
                    'value':
                        'dcs:DeletedNPLSite'
                },
                index=[0]))
    return pd.concat(df_list)


def process_site_funding(input_path: str, output_path: str) -> int:
    """
    Process input files to generate clean csv and tmcf files
    """
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ## Data on National Priority List (NPL) status for superfund sites
    npl_site_status_path = os.path.join(input_path, _DATASET_NAME)
    npl_sites = pd.read_csv(npl_site_status_path,
                            usecols=[
                                'Site EPA ID', 'Status', 'Proposed Date',
                                'Listing Date', 'Deletion Date'
                            ])

    status_csv = pd.DataFrame(columns=[
        'observationAbout', 'observationDate', 'variableMeasured', 'value'
    ])

    # convert dates to appropriate format
    npl_sites['Proposed Date'] = pd.to_datetime(
        npl_sites['Proposed Date']).dt.strftime('%Y-%m-%d')
    npl_sites['Listing Date'] = pd.to_datetime(
        npl_sites['Listing Date']).dt.strftime('%Y-%m-%d')
    npl_sites['Deletion Date'] = pd.to_datetime(
        npl_sites['Deletion Date']).dt.strftime('%Y-%m-%d')

    df_list = [status_csv]
    npl_sites.apply(lambda row: df_list.append(add_rows_to_status_csv(row)),
                    axis=1)

    status_csv = pd.concat(df_list, ignore_index=True)

    status_csv.to_csv(os.path.join(output_path, "superfund_fundingStatus.csv"),
                      index=False)
    f = open(os.path.join(output_path, "superfund_fundingStatus.tmcf"), "w")
    f.write(_STATUS_TEMPALTE_MCF)
    f.close()

    site_count = len(status_csv['observationAbout'].unique())
    return int(site_count)


def main(_) -> None:
    site_count = process_site_funding(FLAGS.site_funding_input_path,
                                      FLAGS.site_funding_output_path)
    print(f"Processing of {site_count} superfund sites is complete.")


if __name__ == '__main__':
    app.run(main)

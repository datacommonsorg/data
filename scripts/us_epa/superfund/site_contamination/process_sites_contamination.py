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
"""Contaminant of concern dataset for superfund sites import

This import uses the dataset:
- ./data/401062.xlsx
    This file describes Contaminant of concern data from Superfund decision documents issued in fiscal years 1982-2017. Includes sites 1) final or deleted on the National Priorities List (NPL); and 2) sites with a Superfund Alternative Approach (SAA) Agreement in place. The only sites included that are 1) not on the NPL; 2) proposed for NPL; or 3) removed from proposed NPL, are those with an SAA Agreement in place.
"""

from absl import app, flags
import os
import sys
import pandas as pd

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../../..'))  # for utils
from us_epa.util.superfund_vars import _CONTAMINATED_THING_DCID_MAP, _CHEM_MAP

sys.path.append(os.path.join(_SCRIPT_PATH,
                             '../../../../util/'))  # for statvar_dcid_generator
from statvar_dcid_generator import get_statvar_dcid

_TEMPLATE_MCF = """
Node: E:SuperfundSite->E0
typeOf: dcs:StatVarObservation
observationAbout: C:SuperfundSite->observationAbout
observationDate: C:SuperfundSite->observationDate
variableMeasured: C:SuperfundSite->variableMeasured
value: C:SuperfundSite->value
"""

_DATASET_NAME = "./401062.xlsx"
_COL_NAME_MAP = {
    'EPA ID': 'observationAbout',
    'Actual Completion Date': 'observationDate'
}


def make_contamination_svobs(df: pd.DataFrame,
                             output_path: str) -> pd.DataFrame:
    """
    Function makes SVObs of contaminated medium at the site concatenated with '&' as the observed value.
    """
    df = df.drop_duplicates()
    # there are some rows where contaminatedThing is nan, which we drop
    df = df.dropna()
    df['Media'] = df['Media'].apply(lambda x: _CONTAMINATED_THING_DCID_MAP[x])
    df = df.groupby(['EPA ID', 'Actual Completion Date'],
                    as_index=False)['Media'].apply('&'.join).reset_index()
    # The groupby is handled differently in Python3.7 and Pytohn3.9, hence we have this check. In python3.9, the column is preserved but in 3.7 the column name in groupby is replaced with 0
    if 'Media' not in df.columns and 0 in df.columns:
        df.columns = ['EPA ID', 'Actual Completion Date', 'Media']
    else:
        df.drop(columns='index', inplace=True)

    df['Media'] = 'dcs:' + df['Media']
    df['variableMeasured'] = 'dcs:ContaminatedThing_SuperfundSite'
    df.rename(columns={
        'EPA ID': 'observationAbout',
        'Actual Completion Date': 'observationDate',
        'Media': 'value'
    },
              inplace=True)
    df = df[[
        'observationAbout', 'observationDate', 'variableMeasured', 'value'
    ]]

    ## write or create the statvar.mcf file
    f = open(os.path.join(output_path, "superfund_sites_contamination.mcf"),
             "w")
    node_str = f"Node: dcid:ContaminatedThing_SuperfundSite\n"
    node_str += "typeOf: dcs:StatisticalVariable\n"
    node_str += "populationType: dcs:SuperfundSite\n"
    node_str += "statType: dcs:measurementResult\n"
    node_str += "measuredProperty: dcs:contaminatedThing\n\n"
    f.write(node_str)
    f.close()

    return df


def write_sv_to_file(row, file_obj):
    """
    Function generates Statistical Variables for the contaminant + contaminatedThing as properites. The value observed for the generated Statistical Variables is a boolean, and is always True
    """
    try:
        contaminated_thing = _CONTAMINATED_THING_DCID_MAP[row['Media']]
        contaminant = _CHEM_MAP[row['Contaminant Name'].title()]

        sv_dict = {
            "contaminatedThing": f"{contaminated_thing}",
            "measuredProperty": "isContaminated",
            "contaminant": f"{contaminant}"
        }
        dcid_str = get_statvar_dcid(sv_dict)

        node_str = f"Node: dcid:{dcid_str}\n"
        node_str += "typeOf: dcs:StatisticalVariable\n"
        node_str += "populationType: dcs:SuperfundSite\n"
        node_str += "statType: dcs:measurementResult\n"
        node_str += f"contaminant: {contaminant}\n"
        node_str += f"contaminatedThing: dcs:{contaminated_thing}\n"
        node_str += "measuredProperty: dcs:isContaminated\n\n"

        ## append generated statvars to statvar.mcf file
        file_obj.write(node_str)

        row['variableMeasured'] = dcid_str
        row['value'] = True
        return row

    except KeyError:
        row['variableMeasured'] = None
        row['value'] = None
        return row


def process_site_contamination(input_path: str, output_path: str) -> int:
    """
    Function to process the raw dataset and generate clean csv + tmcf files.
    """
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    contamination_data_path = os.path.join(input_path, _DATASET_NAME)

    contamination_data = pd.read_excel(contamination_data_path,
                                       header=1,
                                       usecols=[
                                           'EPA ID', 'Actual Completion Date',
                                           'Media', 'Contaminant Name'
                                       ])
    contamination_data['Actual Completion Date'] = pd.to_datetime(
        contamination_data['Actual Completion Date']).dt.strftime('%Y-%m-%d')
    contamination_data[
        'EPA ID'] = 'epaSuperfundSiteId/' + contamination_data['EPA ID']

    clean_csv = pd.DataFrame()
    df = make_contamination_svobs(
        contamination_data[['EPA ID', 'Actual Completion Date', 'Media']],
        output_path)
    clean_csv = pd.concat([clean_csv, df], ignore_index=True)
    del df

    c = contamination_data[['Media', 'Contaminant Name']]
    c = c.drop_duplicates()
    c = c.dropna()
    f = open(os.path.join(output_path, "superfund_sites_contamination.mcf"),
             "a")
    c = c.apply(write_sv_to_file, args=(f,), axis=1)
    f.close()

    c = c.dropna(subset=['variableMeasured', 'value'])

    contamination_data = pd.merge(contamination_data,
                                  c,
                                  on=['Media', 'Contaminant Name'],
                                  how='inner')
    contamination_data.drop(columns=['Media', 'Contaminant Name'], inplace=True)
    contamination_data.rename(columns=_COL_NAME_MAP, inplace=True)

    clean_csv = pd.concat([clean_csv, contamination_data], ignore_index=True)
    clean_csv.to_csv(os.path.join(output_path,
                                  "superfund_sites_contamination.csv"),
                     index=False)
    f = open(os.path.join(output_path, "superfund_sites_contamination.tmcf"),
             'w')
    f.write(_TEMPLATE_MCF)
    f.close()

    site_count = len(clean_csv['observationAbout'].unique())
    return int(site_count)


def main(_) -> None:
    FLAGS = flags.FLAGS
    flags.DEFINE_string('input_path', './data',
                        'Path to the directory with input files')
    flags.DEFINE_string(
        'output_path', './data/output',
        'Path to the directory where generated files are to be stored.')
    site_count = process_site_contamination(FLAGS.input_path, FLAGS.output_path)
    print(f"Processing of {site_count} superfund sites is complete.")


if __name__ == '__main__':
    app.run(main)

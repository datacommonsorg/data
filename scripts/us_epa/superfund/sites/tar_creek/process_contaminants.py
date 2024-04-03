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
"""
This script generates clean csv and tmcf files for statistics about the contamination at Tar Creek using the csv file genereated by the ./process_report2020.py script.
"""
# NOTE: Please run ./process_report2020.py before running this script.
import os
import numpy as np
import pandas as pd
from absl import app, flags

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'report_input_file', './data/tar_creek_2020_corrected.csv',
    'Location of the intermediate csv file from process_report2020.py script')
flags.DEFINE_string(
    'processed_output_path', './data/output',
    'Path to the directory where generated files are to be stored.')

_UNIT_MAP = {
    "Cond.": "dcs:MicroseimensPerCentimeter",
    "pH": "",
    "Hardness": "dcs:MilligramsCaCO3PerLitre",
    "temp": "dcs:Celsius",
    "D.O.": "dcs:MilligramsPerLitre",
    "Sulfate": "dcs:MilligramsPerLitre",
    "Iron": "dcs:MilligramsPerLitre",
    "Lead": "dcs:MilligramsPerLitre",
    "Zinc": "dcs:MilligramsPerLitre",
    "Cadmium": "dcs:MilligramsPerLitre"
}

_BASE_SV_MAP = {
    "Cond.": {
        "populationType": "BodyOfWater",
        "waterSource": "GroundWater",
        "measuredProperty": "electricalConductivity",
    },
    "pH": {
        "populationType": "BodyOfWater",
        "waterSource": "GroundWater",
        "measuredProperty": "potentialOfHydrogen"
    },
    "Hardness": {
        "populationType": "BodyOfWater",
        "waterSource": "GroundWater",
        "measuredProperty": "waterHardness"
    },
    "temp": {
        "populationType": "BodyOfWater",
        "waterSource": "GroundWater",
        "measuredProperty": "temperature"
    },
    "D.O.": {
        "populationType": "BodyOfWater",
        "waterSource": "GroundWater",
        "solute": "Oxygen",
        "solvent": "Water",
        "measuredProperty": "concentration"
    },
    "Sulfate": {
        "populationType": "BodyOfWater",
        "contaminatedThing": "GroundWater",
        "contaminant": "Sulfate",
        "measuredProperty": "concentration"
    },
    "Iron": {
        "populationType": "BodyOfWater",
        "contaminatedThing": "GroundWater",
        "contaminant": "Iron",
        "measuredProperty": "concentration"
    },
    "Lead": {
        "populationType": "BodyOfWater",
        "contaminatedThing": "GroundWater",
        "contaminant": "Lead",
        "measuredProperty": "concentration"
    },
    "Zinc": {
        "populationType": "BodyOfWater",
        "contaminatedThing": "GroundWater",
        "contaminant": "ZincElement",
        "measuredProperty": "concentration"
    },
    "Cadmium": {
        "populationType": "BodyOfWater",
        "contaminatedThing": "GroundWater",
        "contaminant": "Cadmium",
        "measuredProperty": "concentration"
    }
}
_FILENAME_PREFIX = "superfund_sites_tarcreek"
_CLEAN_CSV_FRAMES = []
_TEMPLATE_MCF = """
Node: E:EPASuperfundTarCreek->E0
typeOf: dcs:StatVarObservation
observationAbout: C:EPASuperfundTarCreek->observationAbout
observationDate: C:EPASuperfundTarCreek->observationDate
variableMeasured: C:EPASuperfundTarCreek->variableMeasured
value: C:EPASuperfundTarCreek->value
unit: C:EPASuperfundTarCreek->units
"""


def gen_statvar_dcid(sv_dict: dict) -> str:
    """
    generates dcid for statvars like Concentration_DissolvedContaminant_Iron_BodyOfWater_GroundWater
    """
    dcid_str = []
    if 'measuredProperty' in sv_dict.keys():
        dcid_str.append(sv_dict['measuredProperty'])
    if 'contaminantStatus' in sv_dict.keys():
        dcid_str.append(sv_dict['contaminantStatus'])
    if 'contaminant' in sv_dict.keys():
        # Handle the case where for contaminant = zinc, dcid is the name and not the InChiKey
        if sv_dict['contaminant'] == 'ZincElement':
            dcid_str.append('Zinc')
        else:
            dcid_str.append(sv_dict['contaminant'])
    if 'populationType' in sv_dict.keys():
        dcid_str.append(sv_dict['populationType'])
    if 'contaminatedThing' in sv_dict.keys():
        dcid_str.append(sv_dict['contaminatedThing'])
    if 'waterSource' in sv_dict.keys():
        dcid_str.append(sv_dict['waterSource'])
    dcid_str = '_'.join(dcid_str)
    dcid_str = dcid_str[0].upper() + dcid_str[1:]
    if dcid_str == 'Concentration_BodyOfWater_GroundWater':
        return 'DissolvedOxygen_BodyOfWater_GroundWater'
    return dcid_str


#TODO[sharadshriram]: Complete the implementation
def gen_stavar_name(sv_dict: dict) -> str:
    pass


def make_stat_var_dict(contaminant_type: list,
                       column_list: list) -> (dict, dict):
    ignore_columns = ['observationAbout', 'observationDate', 'contaminantType']
    sv_dict = {}
    sv_column_map = {}

    for contaminant_state in contaminant_type:
        for column in column_list:
            if column not in ignore_columns:
                base_sv = {}

                # add pvs
                base_sv.update(_BASE_SV_MAP[column])

                if contaminant_state == 'Dissolved':
                    base_sv['contaminantStatus'] = 'DissolvedContaminant'
                dcid_str = gen_statvar_dcid(base_sv)
                if 'ZincElement' in dcid_str:
                    dcid_str = dcid_str.replace('ZincElement', 'Zinc')
                key = 'Node: dcid:' + dcid_str
                base_sv['typeOf'] = 'StatisticalVariable'
                base_sv['statType'] = 'measuredValue'

                if key not in sv_dict.keys():
                    sv_dict[key] = base_sv
                    sv_column_map[column + '_' + contaminant_state] = dcid_str
    return sv_dict, sv_column_map


def write_sv_mcf(output_path: str, sv_dict: dict, sv_list: list) -> None:
    sv_list = ['Node: ' + x for x in sv_list]
    f = open(output_path, 'w')
    for k, pvs in sv_dict.items():
        if k in sv_list:
            fstr = k + "\n"
            for p, v in pvs.items():
                if v.startswith('dcs:'):
                    fstr += f"{p}: {v}\n"
                else:
                    fstr += f"{p}: dcs:{v}\n"
            fstr += "\n"
            f.write(fstr)
    f.close()


def clean_dataset(row: pd.Series, column_list: list, sv_map: dict) -> None:
    clean_csv = [
        pd.DataFrame(columns=[
            'observationAbout', 'observationDate', 'variableMeasured', 'value',
            'units'
        ])
    ]

    ignore_list = ['-', ' - ', 'NaN', 'n.a.', np.nan]
    ignore_columns = ['observationAbout', 'observationDate', 'contaminantType']

    for column in column_list:
        if column not in ignore_columns:
            if row[column] not in ignore_list:
                sv_key = column + '_' + row['contaminantType']

                # add data to clean csv
                clean_csv.append(
                    pd.DataFrame(
                        {
                            'observationAbout': row['observationAbout'],
                            'observationDate': row['observationDate'],
                            'variableMeasured': 'dcid:' + sv_map[sv_key],
                            'value': row[column],
                            'units': _UNIT_MAP[column]
                        },
                        index=[0]))

    ## append to a list of dataframes
    _CLEAN_CSV_FRAMES.append(pd.concat(clean_csv))


def process_intermediate_csv(input_file: str, output_path: str) -> None:
    ## Create output directory if not present
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    df = pd.read_csv(input_file)
    df.replace(to_replace=r'^<.*$', value=0, regex=True,
               inplace=True)  #remove < from SVObs values

    contaminant_list = df['contaminantType'].unique().tolist()
    sv_dict, sv_column_map = make_stat_var_dict(contaminant_list,
                                                df.columns.tolist())

    df.apply(clean_dataset, args=(
        df.columns.tolist(),
        sv_column_map,
    ), axis=1)

    clean_csv = pd.concat(_CLEAN_CSV_FRAMES, ignore_index=True)
    clean_csv = clean_csv[~(clean_csv['value'] == '.') &
                          ~(clean_csv['value'] == 'na') &
                          ~(clean_csv['value'] == 'n .a .')]
    clean_csv['value'] = clean_csv['value'].astype(float)
    # there are multiple samples taken during the same day from the same well. For these cases, we aggregate the values to the maxValue
    clean_csv['value'] = clean_csv.groupby(
        ['observationAbout', 'observationDate', 'variableMeasured', 'units'],
        as_index=False)['value'].transform(max)

    write_sv_mcf(os.path.join(output_path, f"{_FILENAME_PREFIX}.mcf"), sv_dict,
                 clean_csv['variableMeasured'].unique().tolist())
    f = open(os.path.join(output_path, f"{_FILENAME_PREFIX}.tmcf"), "w")
    f.write(_TEMPLATE_MCF)
    f.close()

    clean_csv.to_csv(os.path.join(output_path, f"{_FILENAME_PREFIX}.csv"),
                     index=False)


def main(_) -> None:
    process_intermediate_csv(FLAGS.report_input_file,
                             FLAGS.processed_output_path)


if __name__ == '__main__':
    app.run(main)

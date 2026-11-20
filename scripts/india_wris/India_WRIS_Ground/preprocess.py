# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Preprocesses India WRIS Ground Water Quality data and generates MCF/TMCF."""

import argparse
import csv
import os
import sys

from absl import logging

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, _SCRIPTS_ROOT)

from india_wris.base import WaterQualityBase

DATASET_NAME = 'India_WRIS_Ground'
RETAINED_DATASET_NAME = 'India_WRIS_Ground_Prod_Retained'

SOLUTE_MCF_NODES = """Node: dcid:Concentration_{variable}_BodyOfWater_GroundWater
name: Concentration of {variable}, Ground Water
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
contaminatedThing: dcs:GroundWater
contaminant: dcs:{variable}
measuredProperty: dcs:concentration
measurementMethod: dcs:IndiaWRIS
statType: dcs:measuredValue

"""

CHEMPROP_MCF_NODES = """Node: dcid:{variable}_BodyOfWater_GroundWater
name: {variable}, Ground Water
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:GroundWater
measuredProperty: dcs:{dcid}
measurementMethod: dcs:IndiaWRIS
statType: dcs:measuredValue

"""

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
dcid: C:{dataset_name}->dcid
typeOf: dcs:WaterQualitySite

"""

SOLUTE_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Date Collection
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1Y"
variableMeasured: dcid:Concentration_{variable}_BodyOfWater_GroundWater
measurementMethod: dcs:IndiaWRIS
value: C:{dataset_name}->{name}
"""

CHEMPROP_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Date Collection
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1Y"
variableMeasured: dcid:{variable}_BodyOfWater_GroundWater
measurementMethod: dcs:IndiaWRIS
value: C:{dataset_name}->{name}
"""

UNIT = """unit: dcid:{unit}

"""

RETAINED_TMCF_TEMPLATE = """Node: E:India_WRIS_Ground_Prod_Retained->E0
typeOf: dcs:StatVarObservation
variableMeasured: C:India_WRIS_Ground_Prod_Retained->variable_measured
observationAbout: C:India_WRIS_Ground_Prod_Retained->observation_about
observationDate: C:India_WRIS_Ground_Prod_Retained->observation_date
observationPeriod: "P1Y"
measurementMethod: C:India_WRIS_Ground_Prod_Retained->measurement_method
unit: C:India_WRIS_Ground_Prod_Retained->unit
value: C:India_WRIS_Ground_Prod_Retained->value

"""

template_strings = {
    'solute_mcf': SOLUTE_MCF_NODES,
    'solute_tmcf': SOLUTE_TMCF_NODES,
    'chemprop_mcf': CHEMPROP_MCF_NODES,
    'chemprop_tmcf': CHEMPROP_TMCF_NODES,
    'site_dcid': TMCF_ISOCODE,
    'unit_node': UNIT,
}


def process_retained_data(retained_input_csv, output_dir):
    """Sanitizes concatenated rows in retained Ground Water CSV and writes TMCF."""
    if not retained_input_csv or not os.path.exists(retained_input_csv):
        logging.info(
            'Retained CSV %s not found; skipping retained dataset generation.',
            retained_input_csv,
        )
        return

    os.makedirs(output_dir, exist_ok=True)
    out_csv = os.path.join(output_dir, f'{RETAINED_DATASET_NAME}.csv')
    out_tmcf = os.path.join(output_dir, f'{RETAINED_DATASET_NAME}.tmcf')
    tmp_csv = f'{out_csv}.tmp'
    tmp_tmcf = f'{out_tmcf}.tmp'

    row_count = 0
    with (
            open(retained_input_csv, 'r', encoding='utf-8') as infile,
            open(tmp_csv, 'w', encoding='utf-8', newline='') as outfile,
    ):
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            if not row:
                continue
            # Repair manual merge missing-newline artifact where two 7-column rows
            # were concatenated on a single line (13 fields).
            if len(row) == 13 and any(
                    prefix in row[6]
                    for prefix in ('Concentration_', 'Water', 'Electrical',
                                   'Potential', 'Residual', 'Sodium', 'Total')):
                for prefix in (
                        'Concentration_',
                        'Water',
                        'Electrical',
                        'Potential',
                        'Residual',
                        'Sodium',
                        'Total',
                ):
                    idx = row[6].find(prefix)
                    if idx >= 0:
                        val1 = row[6][:idx]
                        sv2 = row[6][idx:]
                        writer.writerow(row[:6] + [val1])
                        writer.writerow([sv2] + row[7:])
                        row_count += 2
                        break
            else:
                writer.writerow(row)
                row_count += 1

    with open(tmp_tmcf, 'w', encoding='utf-8') as tmcf_f:
        tmcf_f.write(RETAINED_TMCF_TEMPLATE)

    os.replace(tmp_csv, out_csv)
    os.replace(tmp_tmcf, out_tmcf)
    logging.info(
        'Processed %d rows for %s into %s',
        row_count,
        RETAINED_DATASET_NAME,
        output_dir,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Preprocess India WRIS Ground Water Quality dataset.')
    parser.add_argument(
        '--input_csv',
        default=os.path.join(_SCRIPT_DIR, '..', 'data', 'groundWater.csv'),
        help='Path to raw groundWater.csv input file.',
    )
    parser.add_argument(
        '--retained_input_csv',
        default=os.path.join(_SCRIPT_DIR, '..', 'data',
                             f'{RETAINED_DATASET_NAME}.csv'),
        help='Path to retained production ground water CSV file.',
    )
    parser.add_argument(
        '--output_dir',
        default=_SCRIPT_DIR,
        help='Directory to write generated CSV, MCF, and TMCF files.',
    )
    args = parser.parse_args(argv)

    preprocessor = WaterQualityBase(
        dataset_name=DATASET_NAME,
        util_names='groundWater',
        template_strings=template_strings,
        input_csv_path=args.input_csv,
        output_dir=args.output_dir,
    )
    preprocessor.create_dcids_in_csv()
    preprocessor.create_mcfs()
    process_retained_data(args.retained_input_csv, args.output_dir)


if __name__ == '__main__':
    main()

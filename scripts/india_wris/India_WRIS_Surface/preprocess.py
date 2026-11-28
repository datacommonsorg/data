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
"""Preprocesses India WRIS Surface Water Quality data and generates MCF/TMCF."""

import argparse
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, '..', '..'))
if _SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, _SCRIPTS_ROOT)

from india_wris.base import WaterQualityBase

DATASET_NAME = 'India_WRIS_Surface'

SOLUTE_MCF_NODES = """Node: dcid:Concentration_{variable}_BodyOfWater_SurfaceWater
name: Concentration of {variable}, SurfaceWater
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
contaminatedThing: dcs:SurfaceWater
contaminant: dcs:{variable}
measuredProperty: dcs:concentration
statType: dcs:measuredValue

"""

CHEMPROP_MCF_NODES = """Node: dcid:{variable}_BodyOfWater_SurfaceWater
name: {variable}, Surface Water
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:SurfaceWater
measuredProperty: dcs:{dcid}
statType: dcs:measuredValue

"""

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
dcid: C:{dataset_name}->dcid
typeOf: dcs:WaterQualitySite

"""

SOLUTE_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Month
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1M"
variableMeasured: dcid:Concentration_{variable}_BodyOfWater_SurfaceWater
measuredProperty: dcs:concentration
value: C:{dataset_name}->{name}
measurementMethod: dcs:IndiaWRIS
"""

CHEMPROP_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: C:{dataset_name}->Month
observationAbout: E:{dataset_name}->E0
observationPeriod: "P1M"
variableMeasured: dcid:{variable}_BodyOfWater_SurfaceWater
measuredProperty: dcs:{dcid}
value: C:{dataset_name}->{name}
measurementMethod: dcs:IndiaWRIS
"""

UNIT = """unit: dcid:{unit}

"""

template_strings = {
    'solute_mcf': SOLUTE_MCF_NODES,
    'solute_tmcf': SOLUTE_TMCF_NODES,
    'chemprop_mcf': CHEMPROP_MCF_NODES,
    'chemprop_tmcf': CHEMPROP_TMCF_NODES,
    'site_dcid': TMCF_ISOCODE,
    'unit_node': UNIT,
}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Preprocess India WRIS Surface Water Quality dataset.')
    parser.add_argument(
        '--input_csv',
        default=os.path.join(_SCRIPT_DIR, '..', 'data', 'surfaceWater.csv'),
        help='Path to raw surfaceWater.csv input file.',
    )
    parser.add_argument(
        '--output_dir',
        default=_SCRIPT_DIR,
        help='Directory to write generated CSV, MCF, and TMCF files.',
    )
    args = parser.parse_args(argv)

    preprocessor = WaterQualityBase(
        dataset_name=DATASET_NAME,
        util_names='surfaceWater',
        template_strings=template_strings,
        input_csv_path=args.input_csv,
        output_dir=args.output_dir,
    )
    preprocessor.create_dcids_in_csv()
    preprocessor.create_mcfs()


if __name__ == '__main__':
    main()

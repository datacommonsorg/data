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

import os
import json
import pandas as pd

DATASET_NAME = 'India_WRIS_Surface'

## Defining MCF and TMCF template nodes

SOLUTE_MCF_NODES = """Node: dcid:WaterQuality_Concentration_SurfaceWater_{variable}
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:SurfaceWater
measuredProperty: dcs:concentration
solute: dcs:{variable}
measurementMethod: WRIS_India
statType: measuredValue

"""

CHEMPROP_MCF_NODES = """Node: dcid:WaterQuality_SurfaceWater_{variable}
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
waterSource: dcs:SurfaceWater
measuredProperty: dcs:{dcid}
measurementMethod: WRIS_India
statType: measuredValue

"""

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: dcs:City
dcid: C:{dataset_name}->location_id

"""

SOLUTE_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: E:{dataset_name}->Year
observationAbout: E:{dataset_name}->dcid
observationPeriod: "P1M"
variableMeasured: dcid:WaterQuality_Concentration_SurfaceWater_{variable}
measuredProperty: dcs:concentration
value: E:{dataset_name}->{name}
"""

CHEMPROP_TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: E:{dataset_name}->Year
observationAbout: E:{dataset_name}->dcid
observationPeriod: "P1M"
variableMeasured: dcid:WaterQuality_SurfaceWater_{variable}
measuredProperty: dcs:{dcid}
value: E:{dataset_name}->{name}
"""

# TMCF unit property is written if unit is known, else omitted
UNIT = """unit: {unit}

"""

## Importing data and creating mcf and tmcf files

module_dir = os.path.dirname(__file__)
json_file_path = os.path.join(module_dir, "../util/surfaceWater.json")

tmcf_file = os.path.join(module_dir, "{}.tmcf".format(DATASET_NAME))
mcf_file = os.path.join(module_dir, "{}.mcf".format(DATASET_NAME))

## Importing water quality indices

with open(json_file_path, 'r') as j:
    properties = json.loads(j.read())

pollutants, chem_props = properties
idx = 1

## Writing MCF and TMCF files

with open(mcf_file, 'w') as mcf, open(tmcf_file, 'w') as tmcf:

    # Writing TMCF Location Node
    tmcf.write(TMCF_ISOCODE.format(dataset_name=DATASET_NAME))
    
    
    # Pollutant nodes are written first
    for pollutant in pollutants['Pollutant']:
        name = pollutant['name']
        statvar = pollutant['statvar']
        unit = pollutant['unit']

        # Writing MCF Node
        mcf.write(
            SOLUTE_MCF_NODES.format(variable=statvar)
            )
        
        # Writing TMCF Property Node
        tmcf.write(
            SOLUTE_TMCF_NODES.format(dataset_name=DATASET_NAME,
                              index=idx,
                              variable=statvar,
                              name=name))

        # If unit is available for a property, unit is written in TMCF
        if unit:
            tmcf.write(UNIT.format(unit=unit))
        # else, unit is omitted from the node
        else:
            tmcf.write('\n')

        idx += 1

    # Chemical properties are written second
    for chem_prop in chem_props['ChemicalProperty']:
        name = chem_prop['name']
        statvar = chem_prop['statvar']
        unit = chem_prop['unit']
        dcid = chem_prop['dcid']

        mcf.write(
            CHEMPROP_MCF_NODES.format(variable=statvar,
                             dcid=dcid,
                             statvar=statvar))
        tmcf.write(
            CHEMPROP_TMCF_NODES.format(dataset_name=DATASET_NAME,
                              index=idx,
                              unit=unit,
                              variable=statvar,
                              dcid=dcid,
                              name=name))
        if unit:
            tmcf.write(UNIT.format(unit=unit))
        else:
            tmcf.write('\n')

        idx += 1

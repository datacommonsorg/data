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

# def date_formatter(month_year):

DATASET_NAME = 'India_WRIS_Surface'

## Defining MCF and TMCF template nodes

MCF_NODES = """Node: dcid:WaterQualityIndex_SurfaceWater_{variable}
typeOf: dcs:StatisticalVariable
populationType: dcs:BodyOfWater
measuredProperty: dcs:waterQualityIndex
waterLocation: dcs:SurfaceWater
waterProperty: dcs:{propertyType}
water{propertyType}: dcs:{statvar}
measurementMethod: WRIS_India
statType: measuredValue

"""

TMCF_ISOCODE = """Node: E:{dataset_name}->E0
typeOf: dcs:City
dcid: C:{dataset_name}->dcid

"""

TMCF_NODES = """Node: E:{dataset_name}->E{index}
typeOf: dcid:StatVarObservation
observationDate: E:{dataset_name}->ObsMonth
observationAbout: E:{dataset_name}->dcid
observationPeriod: "P1M"
variableMeasured: dcid:WaterQualityIndex_SurfaceWater_{variable}
measuredProperty: dcs:waterQualityIndex
value: E:{dataset_name}->{name}
"""

# TMCF unit property is written if unit is known, else omitted
UNIT = """unit: {unit}

"""

## Importing data and creating mcf and tmcf files

module_dir = os.path.dirname(__file__)
json_file_path = os.path.join(module_dir, "../util/surfaceWater.json")
data = pd.read_csv(os.path.join(module_dir, '{}.csv'.format(DATASET_NAME)))

tmcf_file = os.path.join(module_dir, "{}.tmcf".format(DATASET_NAME))
mcf_file = os.path.join(module_dir, "{}.mcf".format(DATASET_NAME))

## Importing water quality indices

with open(json_file_path, 'r') as j:
    properties = json.loads(j.read())

pollutants, chem_props = properties
idx = 1

## Writing MCF and TMCF files

with open(mcf_file, 'w') as mcf, open(tmcf_file, 'w') as tmcf:

    # Pollutant nodes are written first
    for pollutant in pollutants['Pollutant']:
        name = pollutant['name']
        statvar = pollutant['statvar']
        unit = pollutant['unit']
        property_type = pollutant['property']

        # 'variable' contains StatVar name
        # Example: Arsenic (As) -> Pollutant_Arsenic
        variable = '_'.join([property_type, statvar])
        
        # Writing MCF Node
        mcf.write(
            MCF_NODES.format(variable=variable,
                             propertyType=property_type,
                             statvar=statvar))
        # Writing TMCF Location Node
        tmcf.write(
            TMCF_ISOCODE.format(dataset_name=DATASET_NAME)
                )
        # Writing TMCF Property Node
        tmcf.write(
            TMCF_NODES.format(dataset_name=DATASET_NAME,
                              index=idx,
                              variable=variable,
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
        property_type = chem_prop['property']

        # Example: Total Dissolved Solids -> ChemicalProperty_TotalDissolvedSolids
        variable = '_'.join([property_type, statvar])

        mcf.write(
            MCF_NODES.format(variable=variable,
                             propertyType=property_type,
                             statvar=statvar))
        tmcf.write(
            TMCF_NODES.format(dataset_name=DATASET_NAME,
                              index=idx,
                              unit=unit,
                              variable=variable,
                              name=name))
        if unit:
            tmcf.write(UNIT.format(unit=unit))
        else:
            tmcf.write('\n')

        idx += 1
